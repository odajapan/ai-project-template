class ProjectError(Exception):
    """Base for all project-specific errors."""


class LLMError(ProjectError):
    """Wraps Anthropic API errors with project context."""


class DataValidationError(ProjectError):
    """Input failed schema validation."""
