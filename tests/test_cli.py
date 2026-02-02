"""Tests for CLI module."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

# Use python3 explicitly since 'python' may not be available
PYTHON_CMD = sys.executable


def test_cli_exists():
    """Test that CLI module exists and is importable."""
    from durak import cli

    assert cli is not None
    assert cli.cli is not None


def test_cli_clean_command():
    """Test clean command via subprocess."""
    test_text = "İSTANBUL'da harika bir gün!"
    result = subprocess.run(
        [PYTHON_CMD, "-m", "durak.cli", "clean", "-"],
        input=test_text,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0
    assert "istanbul" in result.stdout.lower()


def test_cli_clean_with_json_format():
    """Test clean command with JSON output format."""
    test_text = "İSTANBUL"
    result = subprocess.run(
        [PYTHON_CMD, "-m", "durak.cli", "clean", "-", "--format", "json"],
        input=test_text,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert "text" in data
    assert "char_count" in data


def test_cli_tokenize_command():
    """Test tokenize command via subprocess."""
    test_text = "Merhaba dünya"
    result = subprocess.run(
        [PYTHON_CMD, "-m", "durak.cli", "tokenize", "-"],
        input=test_text,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0
    assert "merhaba" in result.stdout.lower()
    assert "dünya" in result.stdout.lower()


def test_cli_tokenize_with_json_format():
    """Test tokenize command with JSON output format."""
    test_text = "Merhaba dünya"
    result = subprocess.run(
        [PYTHON_CMD, "-m", "durak.cli", "tokenize", "-", "--format", "json"],
        input=test_text,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert "tokens" in data
    assert "count" in data
    assert data["count"] == 2


def test_cli_lemmatize_command():
    """Test lemmatize command via subprocess."""
    result = subprocess.run(
        [PYTHON_CMD, "-m", "durak.cli", "lemmatize", "kitaplar", "evler"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0
    assert "kitap" in result.stdout
    assert "ev" in result.stdout


def test_cli_stopwords_command():
    """Test stopwords command via subprocess."""
    result = subprocess.run(
        [PYTHON_CMD, "-m", "durak.cli", "stopwords", "--format", "json"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0
    words = json.loads(result.stdout)
    assert isinstance(words, list)
    assert len(words) > 0
    assert "ve" in words


def test_cli_version_command():
    """Test version command via subprocess."""
    result = subprocess.run(
        [PYTHON_CMD, "-m", "durak.cli", "version"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0
    assert "0.4.0" in result.stdout or "Durak" in result.stdout


def test_cli_normalize_command():
    """Test normalize command via subprocess."""
    test_text = "İSTANBUL"
    result = subprocess.run(
        [PYTHON_CMD, "-m", "durak.cli", "normalize", "-"],
        input=test_text,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0
    assert "istanbul" in result.stdout.lower()


def test_cli_process_command():
    """Test process command via subprocess."""
    test_text = "Merhaba dünya"
    result = subprocess.run(
        [PYTHON_CMD, "-m", "durak.cli", "process", "-"],
        input=test_text,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0
    assert "merhaba" in result.stdout.lower()
