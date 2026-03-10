import pytest
from pathlib import Path
from app.services.validator import validate_script


def test_valid_script(tmp_path):
    p = tmp_path / "script.py"
    p.write_text("x = 1\nprint(x)\n")
    result = validate_script(p)
    assert result.valid is True
    assert result.syntax_error is None


def test_syntax_error(tmp_path):
    p = tmp_path / "bad.py"
    p.write_text("def f(\n")
    result = validate_script(p)
    assert result.valid is False
    assert result.syntax_error is not None
    assert len(result.syntax_error) > 0


def test_empty_file(tmp_path):
    p = tmp_path / "empty.py"
    p.write_text("")
    result = validate_script(p)
    assert result.valid is True
    assert result.syntax_error is None


def test_nonexistent_file(tmp_path):
    p = tmp_path / "missing.py"
    with pytest.raises(FileNotFoundError):
        validate_script(p)
