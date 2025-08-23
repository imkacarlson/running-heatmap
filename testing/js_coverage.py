import json
from pathlib import Path

def collect_js_coverage(driver, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        webviews = [c for c in driver.contexts if c.startswith("WEBVIEW")]
        if webviews:
            driver.switch_to.context(webviews[0])
    except Exception:
        pass

    cov = None
    try:
        cov = driver.execute_script("return window.__coverage__ || null")
    except Exception:
        pass

    cov = cov or {}
    (out_dir / "coverage-final.json").write_text(json.dumps(cov))
