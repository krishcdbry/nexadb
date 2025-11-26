#!/bin/bash
#
# Build script for Nexa CLI (NexaDB Interactive Terminal)
# Builds binaries for all platforms

set -e

echo "Building Nexa CLI for all platforms..."

# Install cross if not installed
if ! command -v cross &> /dev/null; then
    echo "Installing cross..."
    cargo install cross
fi

# Platforms to build
TARGETS=(
    "x86_64-apple-darwin"
    "aarch64-apple-darwin"
    "x86_64-unknown-linux-gnu"
    "aarch64-unknown-linux-gnu"
    "x86_64-pc-windows-msvc"
)

mkdir -p dist

for target in "${TARGETS[@]}"; do
    echo ""
    echo "Building for $target..."

    if [[ "$target" == *"linux"* ]] && [[ "$OSTYPE" != "linux-gnu"* ]]; then
        # Use cross for Linux targets on non-Linux hosts
        cross build --release --target "$target"
    else
        cargo build --release --target "$target"
    fi

    # Copy to dist folder
    if [[ "$target" == *"windows"* ]]; then
        cp "target/$target/release/nexa.exe" "dist/nexa-$target.exe"
    else
        cp "target/$target/release/nexa" "dist/nexa-$target"
        # Strip binary to reduce size
        strip "dist/nexa-$target" 2>/dev/null || true
    fi

    echo "✓ Built: dist/nexa-$target"
done

echo ""
echo "All builds complete! Binaries in ./dist/"
ls -lh dist/
