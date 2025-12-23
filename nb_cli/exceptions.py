class ModuleLoadFailed(RuntimeError):
    """Raised when a module fails to load."""


class PythonInterpreterError(RuntimeError):
    """Raised when the Python version is not supported."""


class PipError(RuntimeError):
    """Raised when pip is not installed."""


class NoneBotError(RuntimeError):
    """Raised when NoneBot is not installed."""


class ProjectNotFoundError(RuntimeError):
    """Raised when project root directory not found."""


class ProjectInvalidError(RuntimeError):
    """Raised when project config is invalid."""


class LocalCacheExpired(RuntimeError):
    """Raised when local metadata cache is outdated."""


class NoSelectablePackageError(RuntimeError):
    """Raised when there is no selectable package."""


class ProcessExecutionError(RuntimeError):
    """Raised when a subprocess execution fails."""
