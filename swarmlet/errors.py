"""Error hierarchy for Swarmlet."""


class SwarmletError(Exception):
    """Root exception for all Swarmlet errors."""
    pass


class SwarmletStaticError(SwarmletError):
    """Raised for lexer, parser, and analyzer errors."""

    def __init__(self, line=None, col=None, message=""):
        self.line = line
        self.col = col
        self.message = message
        super().__init__(str(self))

    def __str__(self):
        if self.line is not None and self.col is not None:
            return f"SwarmletStaticError at line {self.line}, col {self.col}: {self.message}"
        elif self.line is not None:
            return f"SwarmletStaticError at line {self.line}: {self.message}"
        return f"SwarmletStaticError: {self.message}"


class SwarmletRuntimeError(SwarmletError):
    """Raised for evaluator and engine errors."""

    def __init__(self, message="", line=None):
        self.line = line
        self.message = message
        super().__init__(str(self))

    def __str__(self):
        if self.line is not None:
            return f"SwarmletRuntimeError at line {self.line}: {self.message}"
        return f"SwarmletRuntimeError: {self.message}"
