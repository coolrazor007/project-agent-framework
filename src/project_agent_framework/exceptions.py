"""Framework exceptions."""


class FrameworkError(Exception):
    """Base framework error."""


class TodoValidationError(FrameworkError):
    """Raised when TODO.yml is invalid."""


class MutationPermissionError(FrameworkError):
    """Raised when a role mutates forbidden state."""


class AgentRunError(FrameworkError):
    """Raised when a role execution fails."""


class NoRunnableTasksError(FrameworkError):
    """Raised when work remains but no task is eligible."""


class GitCheckpointError(FrameworkError):
    """Raised when git checkpointing fails."""

