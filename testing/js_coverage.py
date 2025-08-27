import json
from pathlib import Path

def collect_js_coverage(driver, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Debug coverage collection
    debug_file = Path(__file__).parent / "js_coverage_debug.txt"
    with open(debug_file, "w") as f:
        f.write("=== JS COVERAGE COLLECTION DEBUG ===\n")
        
        try:
            contexts = driver.contexts
            f.write(f"Available contexts: {contexts}\n")
            webviews = [c for c in contexts if c.startswith("WEBVIEW")]
            f.write(f"WebView contexts: {webviews}\n")
            
            if webviews:
                f.write(f"Switching to WebView: {webviews[0]}\n")
                driver.switch_to.context(webviews[0])
                f.write("Context switch successful\n")
            else:
                f.write("No WebView contexts found\n")
        except Exception as e:
            f.write(f"Context handling error: {e}\n")

        cov = None
        try:
            f.write("Executing: return window.__coverage__ || null\n")
            cov = driver.execute_script("return window.__coverage__ || null")
            f.write(f"Raw coverage result: {cov}\n")
            f.write(f"Coverage type: {type(cov)}\n")
            if cov:
                f.write(f"Coverage keys: {list(cov.keys()) if isinstance(cov, dict) else 'not a dict'}\n")
        except Exception as e:
            f.write(f"Coverage script execution error: {e}\n")

        # Also try alternative coverage access methods
        try:
            f.write("Trying window.nyc: ")
            nyc = driver.execute_script("return window.nyc || null")
            f.write(f"{nyc}\n")
        except Exception as e:
            f.write(f"Error: {e}\n")
            
        try:
            f.write("Trying window.__NYC__: ")
            nyc2 = driver.execute_script("return window.__NYC__ || null")  
            f.write(f"{nyc2}\n")
        except Exception as e:
            f.write(f"Error: {e}\n")

        cov = cov or {}
        f.write(f"Final coverage object: {cov}\n")
        f.write(f"Writing to: {out_dir / 'coverage-final.json'}\n")

    (out_dir / "coverage-final.json").write_text(json.dumps(cov))
