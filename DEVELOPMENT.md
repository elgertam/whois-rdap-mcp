# Development Setup

This guide explains how to set up the WhoisMCP development environment using `uv`.

## Why uv?

[uv](https://github.com/astral-sh/uv) is an extremely fast Python package installer and resolver, written in Rust. It's 10-100x faster than pip and provides better dependency resolution.

## Installation

### Install uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with pip (slower)
pip install uv
```

### Clone and Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/whoismcp.git
cd whoismcp

# Create a virtual environment with uv
uv venv

# Activate it
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# Install the package and all dependencies
uv pip install -e ".[dev]"
```

## Common Development Tasks

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=whoismcp

# Run specific test file
uv run pytest tests/test_mcp_server.py
```

### Code Quality

```bash
# Format code
uv run black src/ tests/

# Lint code
uv run ruff check src/ tests/

# Type checking
uv run mypy src/
```

### Building Binaries

```bash
# Install build dependencies
uv pip install pyinstaller

# Run build script
python scripts/build.py
```

### Managing Dependencies

```bash
# Add a new dependency
uv pip install some-package

# Then update pyproject.toml manually

# Sync environment with pyproject.toml
uv pip sync

# Upgrade all dependencies
uv pip install -e ".[dev]" --upgrade
```

## Virtual Environment Management

### Create project-specific venv

```bash
# uv creates venvs in .venv by default
uv venv

# Or specify Python version
uv venv --python 3.11
```

### Install from requirements.txt

If you have a requirements file:

```bash
uv pip install -r requirements.txt
```

### Generate requirements

```bash
# Generate requirements from current environment
uv pip freeze > requirements.txt

# Or better, use pip-tools format
uv pip compile pyproject.toml -o requirements.txt
```

## CI/CD with uv

The GitHub Actions workflow is already configured to use `uv`. For other CI systems:

```yaml
# Example: GitLab CI
before_script:
  - curl -LsSf https://astral.sh/uv/install.sh | sh
  - source $HOME/.cargo/env
  - uv venv
  - source .venv/bin/activate
  - uv pip install -e ".[dev]"
```

## Performance Comparison

Typical installation times for this project:

- `pip install -e ".[dev]"`: ~30-60 seconds
- `uv pip install -e ".[dev]"`: ~2-5 seconds

## Troubleshooting

### uv not found

Make sure `~/.cargo/bin` is in your PATH:

```bash
echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Permission errors

Use `--user` flag or ensure you're in a virtual environment:

```bash
uv pip install --user pyinstaller
```

### Cache issues

Clear uv cache if needed:

```bash
uv cache clean
```

## Advanced Usage

### Compile requirements with hashes

For reproducible builds:

```bash
uv pip compile pyproject.toml --generate-hashes -o requirements.lock
```

### Install with specific index

```bash
uv pip install --index-url https://pypi.org/simple/ package-name
```

### Offline installation

```bash
# Download packages first
uv pip download -r requirements.txt -d ./offline

# Install offline
uv pip install --find-links ./offline -r requirements.txt
```

## VS Code Integration

Add to `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.terminal.activateEnvironment": true,
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black"
}
```

## Pre-commit Hooks

If using pre-commit:

```bash
# Install pre-commit
uv pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```
