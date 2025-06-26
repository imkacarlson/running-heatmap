#!/usr/bin/env python3
"""
Mobile build script for running heatmap.
Converts runs.pkl to static JSON files for JavaScript-only mobile app.
"""

import pickle
import json
import os
import shutil
from shapely.geometry import mapping
from rtree import index
import math

def build_mobile_app():
    """Build mobile version of the running heatmap app."""
    
    print("🚀 Building mobile version of running heatmap...")
    
    # Load runs data
    print("📁 Loading runs.pkl...")
    with open('runs.pkl', 'rb') as f:
        runs = pickle.load(f)
    
    print(f"✅ Loaded {len(runs)} runs")
    
    # Create mobile output directory
    mobile_dir = '../mobile'
    if os.path.exists(mobile_dir):
        shutil.rmtree(mobile_dir)
    os.makedirs(mobile_dir)
    os.makedirs(os.path.join(mobile_dir, 'data'))
    
    print(f"📂 Created output directory: {mobile_dir}")
    
    # Export runs data
    print("🔄 Converting runs data...")
    
    # Convert runs to JSON-serializable format
    runs_data = {}
    spatial_index = []
    
    for rid, run in runs.items():
        # Convert geometries to GeoJSON
        geoms = {}
        for level, geom in run['geoms'].items():
            geoms[level] = mapping(geom)
        
        # Convert metadata to JSON-serializable format
        metadata = run.get('metadata', {
            'start_time': None,
            'end_time': None,
            'distance': 0,
            'duration': 0,
            'source_file': 'unknown'
        })
        
        # Convert datetime objects to ISO strings
        json_metadata = {}
        for key, value in metadata.items():
            if hasattr(value, 'isoformat'):  # datetime object
                json_metadata[key] = value.isoformat()
            else:
                json_metadata[key] = value
        
        runs_data[str(rid)] = {
            'geoms': geoms,
            'bbox': run['bbox'],
            'metadata': json_metadata
        }
        
        # Add to spatial index data
        spatial_index.append({
            'id': rid,
            'bbox': run['bbox']
        })
    
    # Write runs data
    runs_file = os.path.join(mobile_dir, 'data', 'runs.json')
    print(f"💾 Writing runs data to {runs_file}...")
    with open(runs_file, 'w') as f:
        json.dump(runs_data, f, separators=(',', ':'))
    
    # Write spatial index
    index_file = os.path.join(mobile_dir, 'data', 'spatial_index.json')
    print(f"🗂️ Writing spatial index to {index_file}...")
    with open(index_file, 'w') as f:
        json.dump(spatial_index, f, separators=(',', ':'))
    
    # Calculate data size
    runs_size = os.path.getsize(runs_file) / (1024 * 1024)
    index_size = os.path.getsize(index_file) / (1024 * 1024)
    
    print(f"📊 Data export complete:")
    print(f"   - Runs data: {runs_size:.1f} MB")
    print(f"   - Spatial index: {index_size:.1f} MB")
    print(f"   - Total: {runs_size + index_size:.1f} MB")
    
    return mobile_dir, len(runs)

def create_mobile_spatial_lib():
    """Create JavaScript spatial library for client-side querying."""
    
    mobile_dir = '../mobile'
    js_dir = os.path.join(mobile_dir, 'js')
    os.makedirs(js_dir, exist_ok=True)
    
    spatial_js = '''
/**
 * Client-side spatial library for mobile running heatmap
 * Replaces server-side Python spatial operations
 */

class MobileSpatialIndex {
    constructor() {
        this.runs = {};
        this.spatialIndex = [];
        this.loaded = false;
    }
    
    async loadData() {
        if (this.loaded) return;
        
        console.log('Loading spatial data...');
        
        try {
            // Load runs data
            const runsResponse = await fetch('./data/runs.json');
            this.runs = await runsResponse.json();
            
            // Load spatial index
            const indexResponse = await fetch('./data/spatial_index.json');
            this.spatialIndex = await indexResponse.json();
            
            this.loaded = true;
            console.log(`Loaded ${Object.keys(this.runs).length} runs`);
        } catch (error) {
            console.error('Failed to load spatial data:', error);
            throw error;
        }
    }
    
    /**
     * Find runs intersecting with bounding box
     */
    queryBBox(minLng, minLat, maxLng, maxLat) {
        const candidates = [];
        
        for (const item of this.spatialIndex) {
            const [itemMinLng, itemMinLat, itemMaxLng, itemMaxLat] = item.bbox;
            
            // Check if bounding boxes intersect
            if (itemMaxLng >= minLng && itemMinLng <= maxLng &&
                itemMaxLat >= minLat && itemMinLat <= maxLat) {
                candidates.push(item.id);
            }
        }
        
        return candidates;
    }
    
    /**
     * Get runs data for map display
     */
    getRunsForBounds(minLat, minLng, maxLat, maxLng, zoom) {
        const candidateIds = this.queryBBox(minLng, minLat, maxLng, maxLat);
        
        // Choose geometry level based on zoom
        let geomLevel;
        if (zoom >= 15) geomLevel = 'full';
        else if (zoom >= 12) geomLevel = 'high';
        else if (zoom >= 9) geomLevel = 'mid';
        else if (zoom >= 6) geomLevel = 'low';
        else geomLevel = 'coarse';
        
        const features = [];
        
        for (const rid of candidateIds) {
            const run = this.runs[rid];
            if (!run) continue;
            
            const geom = run.geoms[geomLevel];
            if (!geom) continue;
            
            // Simple clipping check - if run bbox is fully contained, no clipping needed
            const [runMinLng, runMinLat, runMaxLng, runMaxLat] = run.bbox;
            
            if (runMinLng >= minLng && runMinLat >= minLat && 
                runMaxLng <= maxLng && runMaxLat <= maxLat) {
                // Fully contained
                features.push({
                    type: 'Feature',
                    geometry: geom,
                    properties: { run_id: parseInt(rid) }
                });
            } else {
                // Would need clipping, but for mobile we'll just include it
                // TODO: Implement client-side geometry clipping if needed
                features.push({
                    type: 'Feature',
                    geometry: geom,
                    properties: { run_id: parseInt(rid) }
                });
            }
        }
        
        return {
            type: 'FeatureCollection',
            features: features
        };
    }
    
    /**
     * Find runs intersecting with polygon
     */
    getRunsInPolygon(polygonCoords) {
        const polygon = this.createPolygonBBox(polygonCoords);
        const candidateIds = this.queryBBox(polygon.minLng, polygon.minLat, polygon.maxLng, polygon.maxLat);
        
        const intersectingRuns = [];
        
        for (const rid of candidateIds) {
            const run = this.runs[rid];
            if (!run) continue;

            // Check if any point of the run's full geometry is inside the polygon
            let intersects = false;
            let parts = run.geoms.full.type === 'LineString'
                ? [run.geoms.full.coordinates]
                : run.geoms.full.coordinates;

            for (const part of parts) {
                for (const point of part) {
                    if (this.pointInPolygon(point, polygonCoords)) {
                        intersects = true;
                        break;
                    }
                }
                if (intersects) break;
            }

            if (intersects) {
                intersectingRuns.push({
                    id: parseInt(rid),
                    geometry: run.geoms.full,
                    metadata: run.metadata
                });
            }
        }
        
        return intersectingRuns;
    }
    
    createPolygonBBox(coords) {
        let minLng = Infinity, minLat = Infinity;
        let maxLng = -Infinity, maxLat = -Infinity;
        
        for (const [lng, lat] of coords) {
            minLng = Math.min(minLng, lng);
            minLat = Math.min(minLat, lat);
            maxLng = Math.max(maxLng, lng);
            maxLat = Math.max(maxLat, lat);
        }
        
        return { minLng, minLat, maxLng, maxLat };
    }

    pointInPolygon(point, polygon) {
        let [lng, lat] = point;
        let isInside = false;
        for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
            let [xi, yi] = polygon[i];
            let [xj, yj] = polygon[j];

            let intersect = ((yi > lat) !== (yj > lat))
                && (lng < (xj - xi) * (lat - yi) / (yj - yi) + xi);
            if (intersect) isInside = !isInside;
        }

        return isInside;
    }
    
    /**
     * Filter runs by selected IDs
     */
    filterRunsByIds(runIds, minLat, minLng, maxLat, maxLng, zoom) {
        const runIdSet = new Set(runIds);
        const allRuns = this.getRunsForBounds(minLat, minLng, maxLat, maxLng, zoom);
        
        return {
            type: 'FeatureCollection',
            features: allRuns.features.filter(feature => 
                runIdSet.has(feature.properties.run_id)
            )
        };
    }
}

// Create global instance
window.spatialIndex = new MobileSpatialIndex();
'''
    
    spatial_file = os.path.join(js_dir, 'spatial.js')
    with open(spatial_file, 'w') as f:
        f.write(spatial_js)
    
    print(f"📝 Created spatial library: {spatial_file}")
    return spatial_file

def copy_mobile_templates(mobile_dir):
    """Copy mobile HTML and service worker templates."""
    
    # Copy mobile HTML template
    src_html = 'mobile_template.html'
    dst_html = os.path.join(mobile_dir, 'index.html')
    
    if os.path.exists(src_html):
        shutil.copy2(src_html, dst_html)
        print(f"📄 Copied mobile HTML template")
    else:
        print(f"⚠️ Mobile HTML template not found: {src_html}")
    
    # Copy service worker template
    src_sw = 'sw_template.js'
    dst_sw = os.path.join(mobile_dir, 'sw.js')
    
    if os.path.exists(src_sw):
        shutil.copy2(src_sw, dst_sw)
        print(f"🔧 Copied service worker")
    else:
        print(f"⚠️ Service worker template not found: {src_sw}")
    
    # Update HTML to register service worker
    if os.path.exists(dst_html):
        with open(dst_html, 'r') as f:
            html_content = f.read()
        
        # Add service worker registration before closing body
        sw_registration = '''
    <script>
      // Register service worker for offline functionality
      if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
          navigator.serviceWorker.register('./sw.js')
            .then((registration) => {
              console.log('SW registered: ', registration);
              showStatus('App ready for offline use');
            })
            .catch((registrationError) => {
              console.log('SW registration failed: ', registrationError);
            });
        });
      }
    </script>
  </body>'''
        
        html_content = html_content.replace('</body>', sw_registration)
        
        with open(dst_html, 'w') as f:
            f.write(html_content)
        
        print(f"✅ Updated HTML with service worker registration")

def run_full_build_and_package():
    """Run complete mobile build and Android packaging."""
    
    try:
        # Step 1: Build mobile app
        mobile_dir, run_count = build_mobile_app()
        create_mobile_spatial_lib()
        copy_mobile_templates(mobile_dir)
        
        print(f"\n🎉 Mobile build complete!")
        print(f"📱 Output directory: {mobile_dir}")
        print(f"🏃‍♂️ {run_count} runs exported")
        
        # Step 2: Package for Android and build APK
        print(f"\n🔄 Starting Android packaging...")
        
        # Import and run the Android packaging
        import package_android
        
        # Run the full Android packaging process
        package_android.main()
        
    except FileNotFoundError as e:
        print(f"❌ Error: runs.pkl not found. Please run import_runs.py first.")
        print(f"   Make sure you're in the server/ directory.")
    except Exception as e:
        print(f"❌ Build failed: {e}")
        raise

if __name__ == '__main__':
    import sys
    
    # Check if user wants full build (including APK)
    if len(sys.argv) > 1 and sys.argv[1] == '--full':
        run_full_build_and_package()
    else:
        try:
            mobile_dir, run_count = build_mobile_app()
            create_mobile_spatial_lib()
            copy_mobile_templates(mobile_dir)
            
            print(f"\n🎉 Mobile build complete!")
            print(f"📱 Output directory: {mobile_dir}")
            print(f"🏃‍♂️ {run_count} runs exported")
            
            print(f"\nNext steps:")
            print(f"• Package for Android: python package_android.py")
            print(f"• Or run full build: python build_mobile.py --full")
            
        except FileNotFoundError as e:
            print(f"❌ Error: runs.pkl not found. Please run import_runs.py first.")
            print(f"   Make sure you're in the server/ directory.")
        except Exception as e:
            print(f"❌ Build failed: {e}")
            raise