# Scripts Directory

This directory contains utility scripts for building and maintaining the WhoisMCP server.

## Available Scripts

### `build.py`

Builds standalone executables of the WhoisMCP server using PyInstaller.

**Usage:**

```bash
python scripts/build.py
```

This script:

- Detects your platform (Linux/macOS/Windows)
- Installs required dependencies
- Builds a standalone binary using PyInstaller
- Tests the binary
- Creates a platform-specific executable in the `dist/` directory

**Output:**

- Linux: `dist/whoismcp-server-linux-x86_64`
- macOS Intel: `dist/whoismcp-server-macos-x86_64`
- macOS ARM: `dist/whoismcp-server-macos-arm64`
- Windows: `dist/whoismcp-server-windows-x86_64.exe`

## Adding New Scripts

When adding new scripts to this directory:

1. Include a shebang line: `#!/usr/bin/env python3`
2. Add documentation in this README
3. Use relative imports to access the main package
4. Handle working directory changes appropriately

## Notes

- All scripts assume they're run from the project root or scripts directory
- The build script automatically changes to the project root before executing
- Scripts should be compatible with Python 3.11+
