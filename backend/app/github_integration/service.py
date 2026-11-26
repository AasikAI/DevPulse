import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.exc import IntegrityError

from app.common.clock import utcnow
from app.common.errors import NotConfiguredError
from app.github_integration.client import GitHubClient
from app.github_integration.dispatcher import SyncDispatcher
from app.github_integration.errors import (
    PERMISSION_MISSING,
    SUSPENDED,
    GitHubAccessError,
    InstallationNotAllowedError,
    InstallFailedError,
    InvalidInstallStateError,
)
from app.github_integration.repository import ConnectionRepository
from app.github_integration.schemas import ConnectionInfo, ConnectionStatusResponse
from app.identity.schemas import CurrentUser
from app.identity.service import IdentityService
from app.repositories.service import RepositoryService

logger = logging.getLogger(__name__)

INSTALL_PURPOSE = "install"
# Permissions DevPulse needs on the installation (both read-only).
REQUIRED_PERMISSIONS = ("metadata", "pull_requests")


@dataclass(frozen=True)
class InstallStart:
    url: str
    # Goes into a cookie so the callback must come from the same browser.
    nonce: str


class ConnectionService:
    """The signed-in user's view of their GitHub connection: install and status."""

    def __init__(
        self,
        *,
        repository: ConnectionRepository,
        identity: IdentityService,
        repositories: RepositoryService,
        github: GitHubClient,
        dispatcher: SyncDispatcher,
        clock: Callable[[], datetime] = utcnow,
    ) -> None:
        self._repository = repository
        self._identity = identity
        self._repositories = repositories
        self._github = github
        self._dispatcher = dispatcher
        self._clock = clock

    async def get_status(self, user: CurrentUser) -> ConnectionStatusResponse:
        connection = await self._repository.get_for_user(user_id=user.id)
        if connection is None:
            return ConnectionStatusResponse(status="not_connected")
        count = await self._repositories.count_available(connection_id=connection.id)
        return ConnectionStatusResponse(
            status="needs_attention" if connection.status == "needs_attention" else "active",
            reason=connection.status_reason,
            account_login=connection.github_account_login,
            connected_at=connection.created_at,
            last_checked_at=connection.last_checked_at,
            repositories_synced_at=connection.repositories_synced_at,
            repository_count=count,
        )

    async def start_install(self, user: CurrentUser) -> InstallStart:
        if not self._github.is_app_configured:
            raise NotConfiguredError()
        issued = await self._identity.issue_oauth_state(
            purpose=INSTALL_PURPOSE, user_id=user.id
        )
        return InstallStart(url=self._github.install_url(state=issued.state), nonce=issued.nonce)

    async def complete_install(
        self,
        *,
        user: CurrentUser,
        installation_id: str | None,
        state: str | None,
        nonce: str | None,
        setup_action: str | None,
    ) -> ConnectionInfo:
        """Link the GitHub App installation to this user, after proving it is theirs."""
        if installation_id is None or not installation_id.isdecimal():
            raise InstallFailedError()
        github_installation_id = int(installation_id)

        if state is None and setup_action == "update":
            # GitHub's "Redirect on update" sends no state. Only an installation that
            # is already this user's connection may be refreshed this way.
            existing = await self._repository.get_for_user(user_id=user.id)
            if existing is None or existing.installation_id != github_installation_id:
                raise InvalidInstallStateError()
        elif not await self._identity.consume_oauth_state(
            purpose=INSTALL_PURPOSE, state=state, nonce=nonce, expected_user_id=user.id
        ):
            raise InvalidInstallStateError()

        # The ID in the URL comes from the browser, so it is checked with GitHub:
        # it must be an installation on this user's own personal account.
        try:
            installation = await self._github.get_installation(github_installation_id)
        except GitHubAccessError:
            raise InstallationNotAllowedError() from None
        if installation.account_type != "User" or installation.account_id != user.github_user_id:
            raise InstallationNotAllowedError()

        linked = await self._repository.get_by_installation_id(installation.id)
        if linked is not None and linked.user_id != user.id:
            raise InstallationNotAllowedError()

        status, reason = "active", None
        if installation.suspended:
            status, reason = "needs_attention", SUSPENDED
        elif any(
            installation.permissions.get(name) not in ("read", "write")
            for name in REQUIRED_PERMISSIONS
        ):
            status, reason = "needs_attention", PERMISSION_MISSING

        try:
            connection = await self._repository.upsert_for_user(
                user_id=user.id,
                installation_id=installation.id,
                github_account_id=installation.account_id,
                github_account_login=installation.account_login,
                account_type=installation.account_type,
                permissions=installation.permissions,
                status=status,
                status_reason=reason,
                now=self._clock(),
            )
            await self._repository.commit()
        except IntegrityError:
            # Lost a race with a request linking the same installation to someone else.
            await self._repository.rollback()
            raise InstallationNotAllowedError() from None

        if status == "active":
            # Queued only after the commit, so the worker always finds the connection.
            queued = await self._dispatcher.dispatch_repository_list(connection.id, "connected")
            if not queued:
                logger.warning(
                    "could not queue the repository list job",
                    extra={"connection_id": str(connection.id)},
                )
        return ConnectionInfo.model_validate(connection)


class ConnectionStateService:
    """Connection updates made by background jobs, which know only a connection ID."""

    def __init__(
        self,
        *,
        repository: ConnectionRepository,
        clock: Callable[[], datetime] = utcnow,
    ) -> None:
        self._repository = repository
        self._clock = clock

    async def get_for_sync(self, connection_id: uuid.UUID) -> ConnectionInfo | None:
        connection = await self._repository.get_by_id(connection_id)
        return None if connection is None else ConnectionInfo.model_validate(connection)

    async def mark_needs_attention(self, connection_id: uuid.UUID, reason: str) -> None:
        await self._repository.mark_needs_attention(
            connection_id=connection_id, reason=reason, now=self._clock()
        )
        await self._repository.commit()

    async def mark_repositories_synced(self, connection_id: uuid.UUID) -> None:
        await self._repository.mark_repositories_synced(
            connection_id=connection_id, now=self._clock()
        )
        await self._repository.commit()
