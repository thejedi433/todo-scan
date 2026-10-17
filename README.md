# todo-scan

Scan source files for TODO/FIXME/HACK comments.

## Installation

```bash
pip install todo-scan
```

## Usage

```bash
# Scan current directory (summary view)
todo-scan

# Scan specific directory
todo-scan /path/to/project

# Detailed view with line numbers
todo-scan --detailed src/

# Filter by file extensions
todo-scan --ext .py --ext .js .

# Summary view (default)
todo-scan --summary .
```

## Example Output

### Summary View (default)
```
FIXME: 3
HACK: 1
TODO: 12
XXX: 2

Total: 18 TODOs
```

### Detailed View
```
/path/to/file.py:
  Line 10: [TODO]: implement this function
  Line 45: [FIXME]: handle edge case

/another/file.js:
  Line 23: [HACK]: temporary workaround
```

## Features

- Scans recursively through directories
- Supports multiple comment styles: TODO, FIXME, HACK, XXX
- Case-insensitive matching
- Automatically excludes common directories (.git, node_modules, __pycache__, etc.)
- Filter by file extensions
- JSON output support (coming soon)

## Development

```bash
# Install with dev dependencies
uv pip install -e .[dev]

# Run tests
pytest

# Run tests with coverage
pytest --cov=todo_scan --cov-report=term-missing
```

## License

MIT
