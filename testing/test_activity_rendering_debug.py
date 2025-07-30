"""
Debug test to figure out why test activity isn't visible on map
"""
import time
from base_test import BaseTest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


class TestActivityRenderingDebug(BaseTest):
    
    def test_debug_activity_rendering(self):
        """Debug why test activity isn't showing up visually"""
        print("🔍 Debugging activity rendering...")
        
        # Give app time to load
        time.sleep(8)
        self.switch_to_webview()
        self.wait_for_map_load()
        
        # Get detailed map information
        map_info = self.driver.execute_script("""
            if (typeof map !== 'undefined') {
                const style = map.getStyle();
                const sources = style.sources || {};
                const layers = style.layers || [];
                
                return {
                    zoom: map.getZoom(),
                    center: map.getCenter(),
                    sources: Object.keys(sources).map(key => ({
                        id: key,
                        type: sources[key].type,
                        url: sources[key].url || 'no url',
                        data: sources[key].data || 'no data'
                    })),
                    layers: layers.map(l => ({
                        id: l.id,
                        type: l.type,
                        source: l.source,
                        layout: l.layout || {},
                        paint: l.paint || {}
                    }))
                };
            }
            return null;
        """)
        
        if map_info:
            print(f"🗺️ Current zoom: {map_info['zoom']}")
            print(f"📍 Current center: {map_info['center']}")
            print("📂 Sources:")
            for source in map_info['sources']:
                print(f"  - {source['id']}: {source['type']} | {source['url']}")
            print("🎨 Layers:")
            for layer in map_info['layers']:
                print(f"  - {layer['id']}: {layer['type']} from {layer['source']}")
                if layer['type'] == 'line':
                    print(f"    Paint: {layer['paint']}")
                    print(f"    Layout: {layer['layout']}")
        
        # Pan to our test area with different zoom levels
        test_lat = 39.4168
        test_lon = -77.4169
        
        for zoom in [12, 14, 16, 18]:
            print(f"🔍 Testing zoom level {zoom}...")
            
            self.driver.execute_script(f"""
                map.flyTo({{"center": [{test_lon}, {test_lat}], "zoom": {zoom}}});
            """)
            time.sleep(3)
            
            # Query for features at this zoom
            features = self.driver.execute_script("""
                try {
                    const features = map.queryRenderedFeatures();
                    const sourceFeatures = map.querySourceFeatures('runsVec');
                    return {
                        rendered: features.length,
                        source: sourceFeatures.length,
                        renderedTypes: features.map(f => f.geometry.type),
                        sourceTypes: sourceFeatures.map(f => f.geometry.type),
                        sampleRendered: features[0] || null,
                        sampleSource: sourceFeatures[0] || null
                    };
                } catch (e) {
                    return { error: e.message };
                }
            """)
            
            print(f"  📊 Zoom {zoom}: {features['rendered']} rendered, {features['source']} in source")
            if features['sampleSource']:
                geom_type = features['sampleSource']['geometry']['type']
                coords_count = len(features['sampleSource']['geometry']['coordinates']) if geom_type == 'LineString' else 0
                print(f"  📍 Sample feature: {geom_type} with {coords_count} coordinates")
            
            self.take_screenshot(f"debug_zoom_{zoom}")
            
        # Check if the PMTiles file is actually being loaded
        pmtiles_debug = self.driver.execute_script("""
            // Try to get more info about PMTiles loading
            if (typeof map !== 'undefined') {
                const source = map.getSource('runsVec');
                return {
                    sourceExists: !!source,
                    sourceType: source ? source.type : null,
                    // Try to access PMTiles-specific info
                    bounds: source && source._options ? source._options.bounds : null
                };
            }
            return null;
        """)
        
        print(f"🗺️ PMTiles debug: {pmtiles_debug}")
        
        # Try to manually trigger data loading
        print("🔄 Attempting to manually trigger data refresh...")
        self.driver.execute_script("""
            if (typeof map !== 'undefined') {
                // Try to force reload the source
                try {
                    map.getSource('runsVec').reload();
                } catch (e) {
                    console.log('Reload failed:', e);
                }
                
                // Try to trigger a repaint
                map.triggerRepaint();
            }
        """)
        
        time.sleep(3)
        self.take_screenshot("debug_after_manual_refresh")
        
        # Check console logs for any errors
        logs = self.driver.execute_script("""
            // Get any console logs if available
            if (window.console && window.console.history) {
                return window.console.history;
            }
            return [];
        """)
        
        if logs:
            print("📋 Console logs:")
            for log in logs[-10:]:  # Last 10 logs
                print(f"  {log}")
        
        print("✅ Debug test completed - check screenshots")


if __name__ == '__main__':
    import unittest
    unittest.main()