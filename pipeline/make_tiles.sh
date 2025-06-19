#!/usr/bin/env bash

# Bake vector tiles from processed GeoJSON into MBTiles
# Usage: ./make_tiles.sh
set -euo pipefail

# Input GeoJSON (output of import_runs.py)
INPUT="../data/processed/all_runs.geojson"
# Output MBTiles
OUTPUT="../tiles/runs.mbtiles"

# Generate multi-zoom vector tiles with Tippecanoe
# Aggressive simplification at low zoom, full fidelity when zoomed in

tippecanoe \
  --named-layer=runs \
  --output="$OUTPUT" \
  --coalesce-densest-as-needed \
  --drop-densest-as-needed \
  --minimum-zoom=0 \
  --maximum-zoom=14 \
  "$INPUT"

# Done
echo "Tiles baked to $OUTPUT"
