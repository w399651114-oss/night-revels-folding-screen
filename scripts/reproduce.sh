#!/usr/bin/env bash
# Run from any directory with Blender 5.2.4 and Python 3 on PATH.
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ -z "${BLENDER:-}" && -x /Applications/Blender.app/Contents/MacOS/Blender ]]; then
    BLENDER=/Applications/Blender.app/Contents/MacOS/Blender
fi
BLENDER="${BLENDER:-blender}"
out="${1:-build/reproduction}"
mkdir -p "$out/data" "$out/layouts"
flags=()
if [[ "$(uname -sm)" != "Darwin arm64" ]]; then flags+=(--portable); fi
for case in main control; do
    scene=night-revels
    report=measurements
    gap=3.30
    if [[ "$case" == control ]]; then
        scene=gap-control
        report=control-measurements
        gap=1.10
    fi
    "$BLENDER" --factory-startup -b "scene/$scene.blend" --python-exit-code 1 -P scripts/validate_scene.py -- --compare "docs/$report.json" ${flags[@]+"${flags[@]}"}
    "$BLENDER" --factory-startup -b --python-exit-code 1 -P scripts/build.py -- --gap-length "$gap" --out "$out/$scene.blend"
    "$BLENDER" --factory-startup -b "$out/$scene.blend" --python-exit-code 1 -P scripts/validate_scene.py -- --compare "docs/$report.json" ${flags[@]+"${flags[@]}"} --report "$out/$report.json" --layout "$out/layouts/$case-layout.json"
    "$BLENDER" --factory-startup -b "$out/$scene.blend" --python-exit-code 1 -P scripts/measure_walks.py -- --out "$out/data"
    "$BLENDER" --factory-startup -b "$out/$scene.blend" --python-exit-code 1 -P scripts/render.py -- --out "$out/$case" --frames 25,391 --percent 25 --samples 3
done
python3 scripts/check_walks.py --data "$out/data" --layouts "$out/layouts" --reference docs/data
python3 scripts/check_release.py
