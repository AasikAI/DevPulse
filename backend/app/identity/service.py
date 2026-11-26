from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.common.clock import utcnow
from app.common.errors import NotAuthenticatedError, NotConfiguredError
from app.common.security import hash_token, new_token, tokens_match
from app.config import Settings
from app.github_integration.client import GitHubClient
from app.github_integration.errors import GitHubAuthorizationError
from app.identity.errors import InvalidSignInStateError, SignInError
from app.identity.repository import IdentityRepository
from app.identity.schemas import CurrentUser

SIGN_IN_PURPOSE = "sign_in"


@dataclass(frozen=True)
class SignInStart:
    authorize_url: str
    # Goes into a cookie so the callback must come from the same browser.
    nonce: str


@dataclass(frozen=True)
class SignInResult:
    user: CurrentUser
    session_token: str
    expires_at: datetime


class IdentityService:
    def __init__(
        self,
        *,
        repository: IdentityRepository,
        github: GitHubClient,
        settings: Settings,
        clock: Callable[[], datetime] = utcnow,
    ) -> None:
        self._repository = repository
        self._github = github
        self._settings = settings
        self._clock = clock

    @property
    def _callback_url(self) -> str:
        return f"{self._settings.frontend_origin}/api/auth/github/callback"

    async def start_sign_in(self) -> SignInStart:
        if not self._github.is_configured:
            raise NotConfiguredError()

        now = self._clock()
        state = new_token()
        nonce = new_token()
        await self._repository.purge_oauth_states_expired_before(now - timedelta(days=1))
        await self._repository.create_oauth_state(
            state_hash=hash_token(state),
            nonce_hash=hash_token(nonce),
            purpose=SIGN_IN_PURPOSE,
            expires_at=now + timedelta(minutes=self._settings.oauth_state_ttl_minutes),
        )
        await self._repository.commit()
        url = self._github.authorize_url(state=state, redirect_uri=self._callback_url)
        return SignInStart(authorize_url=url, nonce=nonce)

    async def complete_sign_in(
        self,
        *,
        code: str | None,
        state: str | None,
        nonce: str | None,
        previous_session_token: str | None,
    ) -> SignInResult:
        if not code or not state or not nonce:
            raise InvalidSignInStateError()

        now = self._clock()
        # The state is spent even if a later step fails, so it can never be replayed.
        nonce_hash = await self._repository.consume_oauth_state(
            state_hash=hash_token(state), purpose=SIGN_IN_PURPOSE, now=now
        )
        await self._repository.commit()
        if nonce_hash is None or not tokens_match(nonce_hash, hash_token(nonce)):
            raise InvalidSignInStateError()

        # The GitHub user token lives only inside this block and is never stored.
        try:
            user_token = await self._github.exchange_code(
                code=code, redirect_uri=self._callback_url
            )
            github_user = await self._github.get_authenticated_user(user_token)
        except GitHubAuthorizationError:
            raise SignInError() from None
        del user_token

        user = await self._repository.upsert_user(
            github_user_id=github_user.id,
            login=github_user.login,
            name=github_user.name,
            avatar_url=github_user.avatar_url,
            email=github_user.email,
            now=now,
        )
        # A new credential on every sign-in; an old one from this browser is ended.
        if previous_session_token:
            await self._repository.revoke_session(
                token_hash=hash_token(previous_session_token), now=now
            )
        session_token = new_token()
        expires_at = now + timedelta(days=self._settings.session_lifetime_days)
        await self._repository.create_session(
            user_id=user.id,
            token_hash=hash_token(session_token),
            now=now,
            expires_at=expires_at,
        )
        await self._repository.commit()
        return SignInResult(
            user=CurrentUser.model_validate(user),
            session_token=session_token,
            expires_at=expires_at,
        )

    async def authenticate(self, session_token: str | None) -> CurrentUser:
        if not session_token:
            raise NotAuthenticatedError()
        user = await self._repository.get_user_for_active_session(
            token_hash=hash_token(session_token), now=self._clock()
        )
        if user is None:
            raise NotAuthenticatedError()
        return CurrentUser.model_validate(user)

    async def sign_out(self, session_token: str | None) -> None:
        """End only this browser's session. Safe to call twice."""
        if not session_token:
            return
        await self._repository.revoke_session(
            token_hash=hash_token(session_token), now=self._clock()
        )
        await self._repository.commit()
