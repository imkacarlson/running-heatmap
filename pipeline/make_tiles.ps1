Param(
  [string]$Input  = 'data/processed/all_runs.geojson',
  [string]$Output = 'tiles/runs.mbtiles'
)

# Ensure output folder
if (-Not (Test-Path tiles)) { New-Item -ItemType Directory -Path tiles | Out-Null }

# Run Tippecanoe
tippecanoe `
  --layer runs --layer-type line `
  --output $Output `
  --coalesce-densest-as-needed --drop-densest-as-needed `
  --minimum-zoom=0 --maximum-zoom=14 `
  $Input

Write-Host "Tiles baked to $Output"
