#!/usr/bin/env python3
"""
NexaDB Setup Configuration
Zero-dependency LSM-Tree database with professional admin UI
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read version from veloxdb_core.py
version = "2.1.0"

setup(
    name="nexadb",
    version=version,
    description="Next-gen AI database with enterprise security, HNSW vector search, and 40-50% LLM cost savings",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Krish",
    author_email="krishcdbry@gmail.com",
    url="https://github.com/krishcdbry/nexadb",
    project_urls={
        "Bug Tracker": "https://github.com/krishcdbry/nexadb/issues",
        "Documentation": "https://github.com/krishcdbry/nexadb#readme",
        "Source Code": "https://github.com/krishcdbry/nexadb",
    },
    license="MIT",

    # Package configuration
    packages=find_packages(exclude=["tests", "tests.*", "docs", "examples"]),
    py_modules=[
        "nexadb_server",
        "nexadb_binary_server",
        "admin_server",
        "nexadb_cli",
        "veloxdb_core",
        "storage_engine",
        "security",
        "index_manager",
        "toon_format",
        "toon_cli",
    ],

    # Include non-Python files
    package_data={
        "": [
            "nexadb_admin_modern.html",
            "logo-light.svg",
            "logo-dark.svg",
            "*.md",
        ],
    },
    include_package_data=True,

    # Python version requirement
    python_requires=">=3.8",

    # No external dependencies!
    install_requires=[],

    # Optional dependencies for development
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
        ],
        "docs": [
            "sphinx>=4.0.0",
            "sphinx-rtd-theme>=1.0.0",
        ],
    },

    # Entry points for command-line scripts
    entry_points={
        "console_scripts": [
            "nexadb=nexadb_cli:main",
            "nexadb-server=nexadb_server:main",
            "nexadb-binary=nexadb_binary_server:main",
            "nexadb-admin=admin_server:main",
            "toon=toon_cli:main",
        ],
    },

    # Classifiers for PyPI
    classifiers=[
        # Development status
        "Development Status :: 5 - Production/Stable",

        # Intended audience
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",

        # Topic
        "Topic :: Database",
        "Topic :: Database :: Database Engines/Servers",
        "Topic :: Software Development :: Libraries :: Python Modules",

        # License
        "License :: OSI Approved :: MIT License",

        # Python versions
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3 :: Only",

        # Operating systems
        "Operating System :: OS Independent",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
        "Operating System :: Microsoft :: Windows",

        # Other
        "Natural Language :: English",
        "Typing :: Typed",
    ],

    # Keywords for PyPI search
    keywords=[
        "database",
        "nosql",
        "ai-database",
        "vector-database",
        "vector-search",
        "hnsw",
        "semantic-search",
        "embeddings",
        "llm",
        "toon-format",
        "enterprise-security",
        "aes-256",
        "rbac",
        "lsm-tree",
        "document-database",
        "zero-dependency",
        "lightweight",
        "fast",
        "python",
        "indexing",
        "b-tree",
        "full-text-search",
    ],

    # Ensure wheel is built as universal
    options={
        "bdist_wheel": {
            "universal": False,  # Not Python 2 compatible
        },
    },
)
