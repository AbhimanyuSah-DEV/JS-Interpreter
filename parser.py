import esprima

class JSSyntaxError(SyntaxError):
    """Custom syntax error for JS compilation containing line, column, and description."""
    def __init__(self, message, line, column, index):
        super().__init__(message)
        self.line = line
        self.column = column
        self.index = index

    def __str__(self):
        return f"JSSyntaxError: {self.msg} (at line {self.line}, column {self.column})"

def parse_js(code: str):
    """
    Parses a string of JavaScript code into an Esprima AST.
    Raises JSSyntaxError if there is a parsing syntax error.
    """
    try:
        # We parse with locations enabled to have line/col info if needed
        # parseScript is standard, but we can also use parseModule if imports/exports are present.
        # We use parseScript as the default.
        return esprima.parseScript(code, {"loc": True})
    except esprima.error_handler.Error as e:
        raise JSSyntaxError(
            message=e.message,
            line=e.lineNumber,
            column=e.column,
            index=e.index
        ) from e
    except Exception as e:
        raise JSSyntaxError(
            message=str(e),
            line=1,
            column=1,
            index=0
        ) from e
