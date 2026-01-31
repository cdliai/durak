# Contributing to Durak

Thanks for your interest in improving Durak! This project welcomes contributions that strengthen Turkish NLP tooling. Please review the guidelines below before opening an issue or submitting a pull request.

## Code of Conduct

Durak follows the standards in [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md). By participating you agree to uphold these guidelines.

## Getting Started

1. Fork the repository and create a feature branch from `main`.
2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies in editable mode:
   ```bash
   pip install -e .[dev]
   ```
4. Run the test suite to ensure everything passes:
   ```bash
   pytest
   ```

## Development Workflow

- Keep changes focused and atomic.
- Add or update unit tests alongside code changes.
- Run formatting and static analysis before submitting:
  ```bash
  black .
  ruff check .
  mypy python
  ```
- Update documentation and the roadmap when behaviour changes.
- Append a new entry to `CHANGELOG.md` under the **Unreleased** section (create it if missing).

## Pull Requests

- Use descriptive titles (e.g., `Add StopwordManager export options`).
- Fill out the PR template if available and link relevant issues.
- Ensure CI passes; GitHub Actions run linting, typing, and unit tests.
- Be responsive to review feedback; maintainers may request changes before merging.

## Reporting Issues

- Search existing issues before opening a new one.
- Provide clear reproduction steps, environment details, and expected vs. actual behaviour.
- For security-sensitive reports, please email `dev@karagoz.io` instead of opening a public issue.

We appreciate your contributions and look forward to collaborating!*** End Patch

## Running Tests

After building the package, run:

```bash
pytest
```

### Property-Based Testing

Durak uses [Hypothesis](https://hypothesis.readthedocs.io/) for property-based testing. These tests verify mathematical properties across thousands of randomly generated Turkish text examples.

Run property tests with statistics:

```bash
pytest tests/test_properties.py --hypothesis-show-statistics -v
```

See [docs/PROPERTY_TESTING.md](docs/PROPERTY_TESTING.md) for detailed guidance on writing property tests.
