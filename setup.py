#!/usr/bin/env python3
"""Setup script for MCP Jive Server."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text() if (this_directory / "README.md").exists() else ""

# Read requirements
requirements = []
if (this_directory / "requirements.txt").exists():
    with open(this_directory / "requirements.txt") as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="mcp-jive",
    version="1.4.0",
    description="AI-powered task and workflow management server implementing the Model Context Protocol (MCP)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="MCP Jive Team",
    author_email="team@mcpjive.com",
    url="https://github.com/mcpjive/mcp-jive",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "mypy>=1.7.0",
            "flake8>=6.1.0",
            "coverage>=7.3.0",
        ],
        "docs": [
            "sphinx>=7.1.0",
            "sphinx-rtd-theme>=1.3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "mcp-jive=main:main",
            "mcp-jive-server=main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: Office/Business :: Scheduling",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    keywords="mcp model-context-protocol ai task-management workflow automation",
    project_urls={
        "Bug Reports": "https://github.com/mcpjive/mcp-jive/issues",
        "Source": "https://github.com/mcpjive/mcp-jive",
        "Documentation": "https://docs.mcpjive.com",
    },
    include_package_data=True,
    zip_safe=False,
)