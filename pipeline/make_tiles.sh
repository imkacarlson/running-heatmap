#!/usr/bin/env bash

# Bake vector tiles from processed GeoJSON into a directory of .pbf
set -euo pipefail

# Input GeoJSON (from import_runs.py)
INPUT="data/processed/all_runs.geojson"
# Output directory for .pbf tiles
TILEDIR="tiles"

# Ensure output directory exists
mkdir -p "$TILEDIR"

# Generate tiles (only lines, drop any polygon geometry)
tippecanoe \
  -L "runs:$INPUT" \
  --output-to-directory="$TILEDIR" \
  --drop-polygons \
  --coalesce-densest-as-needed \
  --drop-densest-as-needed \
  --minimum-zoom=0 \
  --maximum-zoom=14

# Done
echo "Tiles baked into $TILEDIR/"