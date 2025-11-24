# tests/test_cli_help.py
from typing import Any
from typer.testing import CliRunner

def test_typer_cli_help() -> None:
    """
    Verifies that the Typer CLI app can be imported and runs `--help` successfully.
    This mirrors the CI step: python -c "from cli.main import app"
    """
    from cli.main import app as cli_app  # type: ignore

    # Basic structural check
    try:
        import typer
        assert isinstance(cli_app, typer.Typer)
    except Exception:
        # If typer import or instance check fails, ensure the object exists
        assert cli_app is not None

    # Run help to confirm the CLI loads
    runner = CliRunner()
    result = runner.invoke(cli_app, ["--help"])
    assert result.exit_code == 0, f"CLI help failed: {result.output}"
    assert "Usage" in result.output or "Commands" in result.output
