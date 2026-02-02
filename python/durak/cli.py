"""Command-line interface for Durak NLP toolkit.

Provides utilities for text processing, stopword management, and
corpus cleaning via the command line.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import click

from durak import (
    Lemmatizer,
    StopwordManager,
    attach_detached_suffixes,
    clean_text,
    load_stopword_resource,
    tokenize,
)


@click.group()
@click.version_option(version="0.4.0")
def cli() -> None:
    """Durak - Turkish NLP toolkit.

    A high-performance text processing toolkit for Turkish with
    tokenization, normalization, lemmatization, and stopword management.
    """
    pass


@cli.command()
@click.argument("input_file", type=click.Path(exists=True, allow_dash=True))
@click.option("--output", "-o", type=click.Path(), help="Output file (default: stdout)")
@click.option("--remove-stopwords", "-s", is_flag=True, help="Remove stopwords")
@click.option("--attach-suffixes", "-a", is_flag=True, help="Attach detached suffixes")
@click.option("--lowercase", "-l", is_flag=True, default=True, help="Lowercase text")
@click.option("--keep-emoji", "-e", is_flag=True, help="Keep emojis in output")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["text", "json", "jsonl"]),
    default="text",
    help="Output format (default: text)",
)
def process(input_file: str, output: str | None, **kwargs: Any) -> None:
    """Process a text file through the Durak pipeline.

    INPUT_FILE: Path to input text file (or '-' for stdin)

    Example:
        durak process --remove-stopwords input.txt
        echo "İSTANBUL'da" | durak process
    """
    # Read input
    if input_file == "-":
        text = sys.stdin.read()
    else:
        text = Path(input_file).read_text(encoding="utf-8")

    # Clean text with options
    emoji_mode = "keep" if kwargs["keep_emoji"] else "remove"
    cleaned = clean_text(text, emoji_mode=emoji_mode)

    # Tokenize
    tokens = tokenize(cleaned)

    # Attach suffixes
    if kwargs["attach_suffixes"]:
        tokens = attach_detached_suffixes(tokens)

    # Remove stopwords
    if kwargs["remove_stopwords"]:
        tokens = [t for t in tokens if not StopwordManager().is_stopword(t)]

    # Format output
    output_format = kwargs.get("format", "text")

    if output_format == "json":
        result = json.dumps(
            {"tokens": tokens, "count": len(tokens)},
            ensure_ascii=False,
            indent=2,
        )
    elif output_format == "jsonl":
        result = "\n".join(json.dumps({"token": t}, ensure_ascii=False) for t in tokens)
    else:  # text
        result = " ".join(tokens)

    # Write output
    if output:
        Path(output).write_text(result, encoding="utf-8")
        click.echo(f"Processed text written to {output}")
    else:
        click.echo(result)


@cli.command()
@click.option(
    "--resource",
    "-r",
    default="base/turkish",
    help="Stopword resource name (default: base/turkish)",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["txt", "json"]),
    default="txt",
    help="Output format (default: txt)",
)
@click.option("--output", "-o", type=click.Path(), help="Output file (default: stdout)")
def stopwords(resource: str, output: str | None, **kwargs: Any) -> None:
    """List stopwords from a resource.

    Default resource: base/turkish
    Available resources: base/turkish, domains/social_media
    """
    words = load_stopword_resource(resource)

    # Format output
    output_format = kwargs.get("format", "txt")
    if output_format == "json":
        result = json.dumps(sorted(words), ensure_ascii=False, indent=2)
    else:
        result = "\n".join(sorted(words))

    # Write output
    if output:
        Path(output).write_text(result, encoding="utf-8")
        click.echo(f"Stopwords written to {output}")
    else:
        click.echo(result)


@cli.command()
@click.argument("tokens", nargs=-1)
@click.option(
    "--strategy",
    "-s",
    type=click.Choice(["lookup", "heuristic", "hybrid"]),
    default="hybrid",
    help="Lemmatization strategy (default: hybrid)",
)
@click.option("--metrics", "-m", is_flag=True, help="Show performance metrics")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["text", "json", "jsonl"]),
    default="text",
    help="Output format (default: text)",
)
def lemmatize(
    tokens: tuple[str, ...], strategy: str, metrics: bool, **kwargs: Any
) -> None:
    """Lemmatize words.

    TOKENS: Words to lemmatize (space-separated)

    Example:
        durak lemmatize kitaplar evler geliyorum
        durak lemmatize --strategy hybrid kitaplar --format json
    """
    if not tokens:
        click.echo("Error: No tokens provided", err=True)
        sys.exit(1)

    # Create lemmatizer
    lemmatizer_obj = Lemmatizer(strategy=strategy, collect_metrics=metrics)

    # Process tokens
    results = [lemmatizer_obj(token) for token in tokens]

    # Format output
    output_format = kwargs.get("format", "text")

    if output_format == "json":
        result = json.dumps(
            {"tokens": list(tokens), "lemmas": results},
            ensure_ascii=False,
            indent=2,
        )
    elif output_format == "jsonl":
        result = "\n".join(
            json.dumps(
                {"token": t, "lemma": lemma},
                ensure_ascii=False,
            )
            for t, lemma in zip(tokens, results)
        )
    else:  # text
        for token, lemma in zip(tokens, results):
            click.echo(f"{token} → {lemma}")
        result = ""  # Already printed

    # Show metrics if requested
    if metrics:
        if output_format != "text":
            metrics_json = lemmatizer_obj.get_metrics()
            if output_format == "json":
                result = result.rstrip("}") + f', "metrics": {metrics_json}}}'
            else:  # jsonl
                result += "\n" + json.dumps(
                    {"metrics": metrics_json}, ensure_ascii=False
                )
        else:
            click.echo("\n" + str(lemmatizer_obj.get_metrics()))

    # Write output (for non-text formats)
    if output_format != "text":
        click.echo(result)


@cli.command(name="tokenize")
@click.argument("input_file", type=click.Path(exists=True, allow_dash=True))
@click.option("--output", "-o", type=click.Path(), help="Output file (default: stdout)")
@click.option("--stopwords", "-s", is_flag=True, help="Remove stopwords")
@click.option("--suffixes", "-a", is_flag=True, help="Attach detached suffixes")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["text", "json", "jsonl"]),
    default="text",
    help="Output format (default: text)",
)
def tokenize_cmd(
    input_file: str, output: str | None, stopwords: bool, suffixes: bool, **kwargs: Any
) -> None:
    """Tokenize a text file.

    INPUT_FILE: Path to input text file (or '-' for stdin)

    Example:
        durak tokenize --remove-stopwords --rejoin-suffixes input.txt
        echo "Merhaba dünya" | durak tokenize --format json
    """
    # Read input
    if input_file == "-":
        text = sys.stdin.read()
    else:
        text = Path(input_file).read_text(encoding="utf-8")

    # Clean and tokenize
    cleaned = clean_text(text)
    tokens = tokenize(cleaned)

    # Attach suffixes
    if suffixes:
        tokens = attach_detached_suffixes(tokens)

    # Remove stopwords
    if stopwords:
        tokens = [t for t in tokens if not StopwordManager().is_stopword(t)]

    # Format output
    output_format = kwargs.get("format", "text")

    if output_format == "json":
        result = json.dumps(
            {"tokens": tokens, "count": len(tokens)},
            ensure_ascii=False,
            indent=2,
        )
    elif output_format == "jsonl":
        result = "\n".join(json.dumps({"token": t}, ensure_ascii=False) for t in tokens)
    else:  # text - one token per line
        result = "\n".join(tokens)

    # Write output
    if output:
        Path(output).write_text(result, encoding="utf-8")
        click.echo(f"Tokens written to {output}")
    else:
        click.echo(result)


@cli.command()
@click.argument("input_file", type=click.Path(exists=True, allow_dash=True))
@click.option("--output", "-o", type=click.Path(), help="Output file (default: stdout)")
@click.option("--lowercase", "-l", is_flag=True, default=True, help="Lowercase text")
@click.option("--keep-emoji", "-e", is_flag=True, help="Keep emojis in output")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format (default: text)",
)
def clean(input_file: str, output: str | None, **kwargs: Any) -> None:
    """Clean Turkish text (normalization and basic cleanup).

    INPUT_FILE: Path to input text file (or '-' for stdin)

    Example:
        durak clean input.txt > output.txt
        echo "İSTANBUL'da" | durak clean
    """
    # Read input
    if input_file == "-":
        text = sys.stdin.read()
    else:
        text = Path(input_file).read_text(encoding="utf-8")

    # Clean text with options
    emoji_mode = "keep" if kwargs["keep_emoji"] else "remove"
    cleaned = clean_text(text, emoji_mode=emoji_mode)

    # Apply lowercase if requested
    if kwargs["lowercase"]:
        cleaned = cleaned.lower()

    # Format output
    output_format = kwargs.get("format", "text")

    if output_format == "json":
        result = json.dumps(
            {"text": cleaned, "char_count": len(cleaned)},
            ensure_ascii=False,
            indent=2,
        )
    else:  # text
        result = cleaned

    # Write output
    if output:
        Path(output).write_text(result, encoding="utf-8")
        click.echo(f"Cleaned text written to {output}")
    else:
        click.echo(result)


@cli.command()
@click.argument("input_file", type=click.Path(exists=True, allow_dash=True))
@click.option("--output", "-o", type=click.Path(), help="Output file (default: stdout)")
@click.option(
    "--turkish-i", is_flag=True, default=True, help="Handle Turkish I/ı conversion"
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format (default: text)",
)
def normalize(
    input_file: str, output: str | None, turkish_i: bool, **kwargs: Any
) -> None:
    """Normalize text (lowercase and handle Turkish I/ı).

    INPUT_FILE: Path to input text file (or '-' for stdin)

    Example:
        durak normalize input.txt
        echo "İSTANBUL" | durak normalize --format json
    """
    # Read input
    if input_file == "-":
        text = sys.stdin.read()
    else:
        text = Path(input_file).read_text(encoding="utf-8")

    # Normalize
    if turkish_i:
        from durak.normalizer import Normalizer

        normalizer = Normalizer(lowercase=True, handle_turkish_i=True)
        result = normalizer(text)
    else:
        from durak.cleaning import normalize_case

        result = normalize_case(text, mode="lower")

    # Format output
    output_format = kwargs.get("format", "text")

    if output_format == "json":
        result = json.dumps(
            {"text": result, "char_count": len(result)},
            ensure_ascii=False,
            indent=2,
        )

    # Write output
    if output:
        Path(output).write_text(result, encoding="utf-8")
        click.echo(f"Normalized text written to {output}")
    else:
        click.echo(result)


@cli.command()
def version() -> None:
    """Show version information."""
    click.echo("Durak v0.4.0 - Turkish NLP Toolkit")
    click.echo("https://github.com/fbkaragoz/durak")


def main() -> None:
    """Entry point for the CLI."""
    cli(obj={})


if __name__ == "__main__":
    main()
