#!/usr/bin/env python3
"""
Build script for creating MCP Jive PyPI package.
This script prepares the package for distribution via PyPI.
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Build the package for PyPI distribution."""
    project_root = Path(__file__).parent.parent

    print("🏗️  Building MCP Jive package for PyPI distribution...")

    # 1. Clean previous builds
    print("\n📦 Cleaning previous builds...")
    dist_dir = project_root / "dist"
    build_dir = project_root / "build"
    egg_dir = project_root / "src" / "mcp_jive.egg-info"

    for dir_path in [dist_dir, build_dir, egg_dir]:
        if dir_path.exists():
            import shutil
            shutil.rmtree(dir_path)
            print(f"   ✓ Removed {dir_path}")

    # 2. Build the package
    print("\n📦 Building distribution packages...")

    # Check if build module is available
    try:
        subprocess.run(
            [sys.executable, "-m", "build", "--version"],
            check=True,
            capture_output=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("   ⚠️  'build' module not found. Installing...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "build"],
                check=True
            )
            print("   ✓ Installed 'build' module")
        except subprocess.CalledProcessError as e:
            print(f"   ✗ Failed to install 'build': {e}")
            return 1

    # Now build the package
    try:
        subprocess.run(
            [sys.executable, "-m", "build"],
            cwd=project_root,
            check=True
        )
        print("   ✓ Built wheel and source distribution")
    except subprocess.CalledProcessError as e:
        print(f"   ✗ Build failed: {e}")
        return 1

    #  3. Show built files
    print("\n📋 Built packages:")
    for file in dist_dir.glob("*"):
        print(f"   • {file.name}")

    print("\n✅ Package build complete!")
    print("\n📤 To publish to PyPI:")
    print("   python -m twine upload dist/*")
    print("\n📥 To install locally for testing:")
    print(f"   pip install {dist_dir.name}/*.whl")
    print("\n🎯 To install from PyPI (after publishing):")
    print("   uvx mcp-jive --port 3454")

    return 0

if __name__ == "__main__":
    sys.exit(main())
