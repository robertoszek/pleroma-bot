from .i18n import _


class TimeoutLocker(TimeoutError):
    """Raised when the lock could not be acquired in *timeout* seconds."""

    def __init__(self, lock_file: str) -> None:
        #: The path of the file lock.
        self.lock_file = lock_file

    def __str__(self) -> str:
        return _(
            "The file lock '{}' could not be acquired. Is another instance "
            "of pleroma-bot running?"
        ).format(self.lock_file)
