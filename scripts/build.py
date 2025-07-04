#!/usr/bin/env python3
"""
Build script for creating WhoisMCP server binaries using PyInstaller.
"""

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def get_platform_name():
    """Get the platform-specific binary name."""
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "darwin":
        if machine == "arm64":
            return "whoismcp-server-macos-arm64"
        return "whoismcp-server-macos-x86_64"
    elif system == "windows":
        return "whoismcp-server-windows-x86_64.exe"
    elif system == "linux":
        return "whoismcp-server-linux-x86_64"
    else:
        return f"whoismcp-server-{system}-{machine}"


def clean_build_dirs():
    """Clean up build directories."""
    dirs_to_clean = ["build", "dist", "__pycache__"]
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"Cleaning {dir_name}/")
            shutil.rmtree(dir_name)

    # Clean .spec file if it exists (we'll use our custom one)
    default_spec = "mcp_server.spec"
    if os.path.exists(default_spec):
        os.remove(default_spec)


def install_dependencies():
    """Install required dependencies."""
    print("Installing dependencies...")

    # Check if uv is available
    try:
        subprocess.run(["uv", "--version"], check=True, capture_output=True)
        use_uv = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Warning: uv not found, falling back to pip")
        use_uv = False

    if use_uv:
        # Install with uv
        subprocess.check_call(["uv", "pip", "install", "--upgrade", "pip"])
        subprocess.check_call(["uv", "pip", "install", "pyinstaller"])
        subprocess.check_call(["uv", "pip", "install", "-e", "."])
    else:
        # Fallback to pip
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", "."])


def build_binary():
    """Build the binary using PyInstaller."""
    print("Building binary with PyInstaller...")

    # Check if spec file exists
    if not os.path.exists("whoismcp.spec"):
        print("Error: whoismcp.spec not found!")
        print("Please ensure the PyInstaller spec file is in the current directory.")
        return False

    try:
        subprocess.check_call(["pyinstaller", "whoismcp.spec", "--clean"])
        return True
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        return False


def test_binary():
    """Test the built binary."""
    print("\nTesting binary...")

    binary_path = Path("dist") / "whoismcp-server"
    if platform.system() == "Windows":
        binary_path = Path("dist") / "whoismcp-server.exe"

    if not binary_path.exists():
        print(f"Error: Binary not found at {binary_path}")
        return False

    try:
        # Test --help command
        result = subprocess.run([str(binary_path), "--help"], capture_output=True, text=True)
        if result.returncode == 0:
            print("Binary test passed!")
            print("\nHelp output:")
            print(result.stdout)
            return True
        else:
            print(f"Binary test failed with return code {result.returncode}")
            print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"Failed to test binary: {e}")
        return False


def rename_binary():
    """Rename the binary to platform-specific name."""
    platform_name = get_platform_name()

    source = Path("dist") / "whoismcp-server"
    if platform.system() == "Windows":
        source = Path("dist") / "whoismcp-server.exe"

    dest = Path("dist") / platform_name

    if source.exists():
        print(f"\nRenaming binary to {platform_name}")
        shutil.move(str(source), str(dest))
        return dest
    else:
        print(f"Error: Source binary {source} not found!")
        return None


def main():
    """Main build process."""
    print("WhoisMCP Server Build Script")
    print("============================")
    print(f"Platform: {platform.system()} {platform.machine()}")
    print(f"Python: {sys.version}")

    # Change to project root directory (parent of scripts/)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    os.chdir(project_root)

    # Clean previous builds
    clean_build_dirs()

    # Install dependencies
    install_dependencies()

    # Build binary
    if not build_binary():
        print("\nBuild failed!")
        return 1

    # Test binary
    if not test_binary():
        print("\nBinary test failed!")
        return 1

    # Rename to platform-specific name
    final_binary = rename_binary()
    if final_binary:
        print(f"\nBuild successful!")
        print(f"Binary location: {final_binary}")
        print(f"Binary size: {final_binary.stat().st_size / 1024 / 1024:.2f} MB")
    else:
        print("\nFailed to rename binary!")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
