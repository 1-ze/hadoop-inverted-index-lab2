#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p build/classes
javac -encoding UTF-8 --release 11 -cp "$(hadoop classpath --glob)" -d build/classes src/main/java/edu/lab/InvertedIndex.java
jar cfe build/inverted-index.jar edu.lab.InvertedIndex -C build/classes .
echo 'BUILD_OK build/inverted-index.jar'
