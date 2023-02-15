#!/bin/sh

fatal() {
    echo "$1"
    exit 1
}

# Get directory of CMakeLists.txt
PROJECT_ROOT="$(dirname "$(dirname "$(readlink -f "$0")")")"

# Create a temporary build directory and cd into it
BUILD_DIR="$HOME/.cache/endplay-cmake"
mkdir -p "$BUILD_DIR" \
      || fatal "could not create build directory $BUILD_DIR"
cd $BUILD_DIR\
    || fatal "could not enter build directory"

# Run CMake with exporting compile commands on
CMAKE_OUTPUT="$(mktemp)"
trap 'rm -rf -- "$CMAKE_OUTPUT"' EXIT
cmake \
    -DCMAKE_EXPORT_COMPILE_COMMANDS=on\
    -DCMAKE_INSTALL_PREFIX="$PROJECT_ROOT/src/endplay/"\
    "$PROJECT_ROOT" >"$CMAKE_OUTPUT" 2>&1\
    || fatal "CMake failed to run correctly:\n$(cat "$CMAKE_OUTPUT")"

# move compile commands to CMakeLists.txt directory
mv "compile_commands.json" "$PROJECT_ROOT" \
    || fatal "Could not copy compile_commands.json to project tree"

cmake --build . --target install \
    || fatal "Failed to build endplay"
