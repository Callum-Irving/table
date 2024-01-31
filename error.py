from dataclasses import dataclass


@dataclass
class Location:
    file: str
    posn: int
    line: int
    col: int

    def __str__(self):
        return f"{self.file}:{self.line+1}.{self.col+1}"

    def copy(self):
        """Return a deep copy of self."""
        return Location(self.file, self.posn, self.line, self.col)


class TableError(Exception):
    msg: str
    loc: Location | None

    def __init__(self, msg: str, loc: Location | None = None):
        self.msg = msg
        self.loc = loc

    def __str__(self):
        if self.loc:
            return error_fmt(f"ERROR ({self.loc}): {self.msg}")
        else:
            return error_fmt(f"ERROR: {self.msg}")


def error_fmt(msg: str) -> str:
    """Format msg in red using ANSI escape codes."""
    return f"\033[1;31m{msg}\033[0m"
