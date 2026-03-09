import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ValidationResult:
    syntax_ok: bool
    syntax_error: str | None  # None if syntax_ok

    @property
    def valid(self) -> bool:
        return self.syntax_ok


def validate_script(script_path: Path) -> ValidationResult:
    try:
        source = script_path.read_text(encoding="utf-8")
        ast.parse(source, filename=str(script_path))
    except SyntaxError as e:
        return ValidationResult(syntax_ok=False, syntax_error=str(e))
    return ValidationResult(syntax_ok=True, syntax_error=None)
