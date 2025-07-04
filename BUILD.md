# Building WhoisMCP Server

This document describes how to build standalone binaries of the WhoisMCP server for distribution.

## Prerequisites

- Python 3.11 or higher
- uv (recommended) or pip
- Git

### Installing uv (recommended)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Quick Build (Local)

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/whoismcp.git
   cd whoismcp
   ```

2. Run the build script:

   ```bash
   python scripts/build.py
   ```

This will create a platform-specific binary in the `dist/` directory.

## Manual Build

1. Install dependencies:

   ```bash
   uv pip install -e .
   uv pip install pyinstaller
   ```

2. Build with PyInstaller:

   ```bash
   pyinstaller whoismcp.spec
   ```

3. The binary will be in `dist/whoismcp-server` (or `dist/whoismcp-server.exe` on Windows)

## GitHub Actions Build

The project includes a GitHub Actions workflow that automatically builds binaries for multiple platforms when you create a new release tag.

### Creating a Release

1. Update the version in `src/whoismcp/__init__.py`

2. Commit and push changes:

   ```bash
   git add .
   git commit -m "Bump version to x.y.z"
   git push
   ```

3. Create and push a tag:

   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

4. GitHub Actions will automatically:
   - Build binaries for Linux, macOS (Intel & ARM), and Windows
   - Create a GitHub release with all binaries attached

### Manual Workflow Trigger

You can also manually trigger the build workflow from the GitHub Actions tab in your repository.

## Supported Platforms

The build process creates binaries for:

- **Linux**: x86_64
- **macOS**: x86_64 (Intel)
- **macOS**: arm64 (Apple Silicon)
- **Windows**: x86_64

## Binary Details

### What's Included

The PyInstaller bundle includes:

- The WhoisMCP server application
- All Python dependencies
- Python interpreter
- Required system libraries

### What's NOT Included

- Configuration files (use environment variables)
- Cache data (created at runtime)
- Log files (written to stderr)

### Size Optimization

The binaries are optimized using:

- UPX compression (where available)
- Exclusion of development dependencies
- Minimal Python standard library inclusion

Typical binary sizes:

- Linux: ~15-20 MB
- macOS: ~15-20 MB
- Windows: ~20-25 MB

## Troubleshooting

### Build Fails

1. Ensure all dependencies are installed:

   ```bash
   uv pip install -e .
   uv pip install pyinstaller
   ```

2. Check Python version (must be 3.11+):

   ```bash
   python --version
   ```

3. Clean build artifacts and retry:

   ```bash
   rm -rf build/ dist/ *.spec
   python scripts/build.py
   ```

### Binary Won't Run

1. **Linux/macOS**: Ensure executable permissions:

   ```bash
   chmod +x whoismcp-server-*
   ```

2. **macOS**: If you see "developer cannot be verified":

   ```bash
   xattr -d com.apple.quarantine whoismcp-server-*
   ```

3. **Windows**: Check Windows Defender or antivirus - PyInstaller binaries sometimes trigger false positives

### Missing Modules

If you see import errors when running the binary, add the missing module to `hiddenimports` in `whoismcp.spec`:

```python
hiddenimports=[
    'whoismcp',
    'missing_module_name',  # Add here
    ...
]
```

## Testing Binaries

After building, test the binary:

```bash
# Basic test
./dist/whoismcp-server-* --help

# Version check
./dist/whoismcp-server-* --version

# CLI whois lookup
./dist/whoismcp-server-* whois example.com

# CLI RDAP lookup
./dist/whoismcp-server-* rdap example.com
```

## Distribution

### File Naming Convention

Binaries follow this naming pattern:

- `whoismcp-server-{platform}-{architecture}`
- Examples:
  - `whoismcp-server-linux-x86_64`
  - `whoismcp-server-macos-arm64`
  - `whoismcp-server-windows-x86_64.exe`

### Checksums

For releases, consider providing checksums:

```bash
# Generate SHA256 checksums
cd dist/
sha256sum whoismcp-server-* > checksums.txt
```

### Code Signing

For production releases, consider code signing:

- **macOS**: Use `codesign` with a Developer ID certificate
- **Windows**: Use `signtool` with a code signing certificate
- **Linux**: Use GPG signatures

## Development Notes

### Updating Dependencies

When adding new dependencies:

1. Add to `pyproject.toml`
2. Update `hiddenimports` in `whoismcp.spec` if needed
3. Test the build locally before pushing

### Platform-Specific Issues

- **Linux**: Builds on older glibc versions for compatibility
- **macOS**: Universal binaries not supported via GitHub Actions (build separately for Intel/ARM)
- **Windows**: May need Visual C++ Redistributables on target systems

### CI/CD Improvements

Consider adding:

- Automated tests before building
- Virus scanning of binaries
- Upload to package managers (Homebrew, Chocolatey, etc.)
- Docker images as an alternative distribution method
