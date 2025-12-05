# backend/utils/errors.py
from typing import Optional

class PipelineError(Exception):
    """Base class for pipeline-related errors."""
    def __init__(self, message: str, *, cause: Optional[Exception] = None):
        super().__init__(message)
        self.cause = cause

class TranscriptParseError(PipelineError):
    """Raised when parsing an uploaded transcript fails."""

class ExtractorError(PipelineError):
    """Raised when text extraction/cleaning/chunking fails."""

class GenerationError(PipelineError):
    """Raised when LLM generation or parsing of LLM output fails."""

class PipelineRunError(PipelineError):
    """Raised when the overall pipeline run fails (AgentManager-level)."""
