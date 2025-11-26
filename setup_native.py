#!/usr/bin/env python3
"""
NexaDB Native C++ Extensions Setup
===================================

Build high-performance C++ extensions for vector operations

Installation:
    python3 setup_native.py build_ext --inplace

Requirements:
    - C++17 compatible compiler (gcc 7+, clang 5+, MSVC 2017+)
    - pybind11

Features:
    - SIMD optimizations (AVX2/AVX-512)
    - Multi-threaded batch operations
    - 50-100x faster than pure Python
"""

import sys
import platform
from pathlib import Path
from pybind11.setup_helpers import Pybind11Extension, build_ext
from setuptools import setup

# Determine compiler flags based on platform
def get_compile_args():
    """Get platform-specific compiler flags"""
    system = platform.system()

    if system == "Darwin":  # macOS
        return [
            '-std=c++17',
            '-O3',                    # Maximum optimization
            '-march=native',          # Use CPU-specific instructions
            '-ffast-math',            # Fast math optimizations
            '-DNDEBUG',              # Disable debug assertions
        ]
    elif system == "Linux":
        return [
            '-std=c++17',
            '-O3',
            '-march=native',
            '-ffast-math',
            '-DNDEBUG',
            '-fopenmp',              # OpenMP for multi-threading
        ]
    elif system == "Windows":
        return [
            '/std:c++17',
            '/O2',                   # Maximum optimization
            '/arch:AVX2',            # Enable AVX2 instructions
            '/DNDEBUG',
        ]
    else:
        return ['-std=c++17', '-O3']

def get_link_args():
    """Get platform-specific linker flags"""
    system = platform.system()

    if system == "Linux":
        return ['-fopenmp']
    else:
        return []

# Define the C++ extension
ext_modules = [
    Pybind11Extension(
        "nexadb_native",
        ["nexadb/native/bindings.cpp"],
        include_dirs=[
            "nexadb/native",
        ],
        extra_compile_args=get_compile_args(),
        extra_link_args=get_link_args(),
        cxx_std=17,
        language='c++',
    ),
]

setup(
    name="nexadb_native",
    version="2.2.0",
    author="NexaDB Team",
    description="High-performance C++ vector operations for NexaDB",
    long_description=__doc__,
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
    zip_safe=False,
    python_requires=">=3.8",
)

if __name__ == "__main__":
    print("=" * 80)
    print("Building NexaDB Native C++ Extensions")
    print("=" * 80)
    print()
    print(f"Platform:  {platform.system()} {platform.machine()}")
    print(f"Python:    {sys.version.split()[0]}")
    print(f"Compiler:  {get_compile_args()}")
    print()
    print("Features:")
    print("  ✓ SIMD optimizations (AVX2/AVX-512)")
    print("  ✓ Multi-threaded batch operations")
    print("  ✓ 50-100x faster than pure Python")
    print()
    print("=" * 80)
    print()
