"""Tests for CLI module."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYTHON_SRC = PROJECT_ROOT / "python"


def run_cli(args: list[str], input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    """Run CLI commands with PYTHONPATH configured for subprocess execution."""
    env = os.environ.copy()
    current_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        f"{PYTHON_SRC}{os.pathsep}{current_pythonpath}"
        if current_pythonpath
        else str(PYTHON_SRC)
    )
    return subprocess.run(
        [sys.executable, "-m", "durak.cli", *args],
        input=input_text,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )


def test_cli_exists():
    """Test that CLI module exists and is importable."""
    from durak import cli

    assert cli is not None
    assert cli.cli is not None


def test_cli_clean_command():
    """Test clean command via subprocess."""
    test_text = "İSTANBUL'da harika bir gün!"
    result = run_cli(["clean", "-"], input_text=test_text)
    assert result.returncode == 0
    assert "istanbul" in result.stdout.lower()


def test_cli_clean_with_json_format():
    """Test clean command with JSON output format."""
    test_text = "İSTANBUL"
    result = run_cli(["clean", "-", "--format", "json"], input_text=test_text)
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert "text" in data
    assert "char_count" in data


def test_cli_tokenize_command():
    """Test tokenize command via subprocess."""
    test_text = "Merhaba dünya"
    result = run_cli(["tokenize", "-"], input_text=test_text)
    assert result.returncode == 0
    assert "merhaba" in result.stdout.lower()
    assert "dünya" in result.stdout.lower()


def test_cli_tokenize_with_json_format():
    """Test tokenize command with JSON output format."""
    test_text = "Merhaba dünya"
    result = run_cli(["tokenize", "-", "--format", "json"], input_text=test_text)
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert "tokens" in data
    assert "count" in data
    assert data["count"] == 2


def test_cli_lemmatize_command():
    """Test lemmatize command via subprocess."""
    result = run_cli(["lemmatize", "kitaplar", "evler"])
    assert result.returncode == 0
    assert "kitap" in result.stdout
    assert "ev" in result.stdout


def test_cli_stopwords_command():
    """Test stopwords command via subprocess."""
    result = run_cli(["stopwords", "--format", "json"])
    assert result.returncode == 0
    words = json.loads(result.stdout)
    assert isinstance(words, list)
    assert len(words) > 0
    assert "ve" in words


def test_cli_version_command():
    """Test version command via subprocess."""
    result = run_cli(["version"])
    assert result.returncode == 0
    assert "0.4.0" in result.stdout or "Durak" in result.stdout


def test_cli_normalize_command():
    """Test normalize command via subprocess."""
    test_text = "İSTANBUL"
    result = run_cli(["normalize", "-"], input_text=test_text)
    assert result.returncode == 0
    assert "istanbul" in result.stdout.lower()


def test_cli_process_command():
    """Test process command via subprocess."""
    test_text = "Merhaba dünya"
    result = run_cli(["process", "-"], input_text=test_text)
    assert result.returncode == 0
    assert "merhaba" in result.stdout.lower()


def test_cli_process_with_stopwords():
    """Test process command with stopword removal."""
    test_text = "Bu bir test"
    result = run_cli(["process", "-", "--remove-stopwords"], input_text=test_text)
    assert result.returncode == 0
    assert "test" in result.stdout.lower()


def test_cli_lemmatize_with_strategy():
    """Test lemmatize command with specific strategy."""
    result = run_cli(["lemmatize", "--strategy", "lookup", "kitaplar"])
    assert result.returncode == 0
