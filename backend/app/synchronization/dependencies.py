from app.synchronization.dispatcher import CelerySyncDispatcher


def get_sync_dispatcher() -> CelerySyncDispatcher:
    return CelerySyncDispatcher()
