import json
from pathlib import Path


def _has_cdp_support(driver) -> bool:
    """Check if driver supports Chrome DevTools Protocol commands."""
    return hasattr(driver, 'execute_cdp_cmd')


def _inject_css_coverage_js(driver) -> None:
    """Inject JavaScript-based CSS coverage tracking into the page."""
    coverage_script = """
    window.__css_coverage__ = {
        stylesheets: new Map(),
        rules: new Map(),
        initialized: false,
        
        init: function() {
            console.log('CSS Coverage: Initializing...');
            console.log('CSS Coverage: document.readyState =', document.readyState);
            console.log('CSS Coverage: document.styleSheets.length =', document.styleSheets.length);
            
            // Track all stylesheets and rules
            for (let i = 0; i < document.styleSheets.length; i++) {
                const sheet = document.styleSheets[i];
                try {
                    const sheetId = 'sheet_' + i;
                    console.log('CSS Coverage: Processing sheet', i, 'href:', sheet.href || 'inline');
                    
                    this.stylesheets.set(sheetId, {
                        href: sheet.href || 'inline',
                        rules: []
                    });
                    
                    // Track all rules in this stylesheet
                    if (sheet.cssRules) {
                        for (let j = 0; j < sheet.cssRules.length; j++) {
                            const rule = sheet.cssRules[j];
                            const ruleId = sheetId + '_rule_' + j;
                            this.rules.set(ruleId, {
                                sheetId: sheetId,
                                selector: rule.selectorText || rule.cssText,
                                text: rule.cssText,
                                used: false
                            });
                            this.stylesheets.get(sheetId).rules.push(ruleId);
                        }
                        console.log('CSS Coverage: Sheet', i, 'has', sheet.cssRules.length, 'rules');
                    } else {
                        console.log('CSS Coverage: Sheet', i, 'has no accessible cssRules');
                    }
                } catch (e) {
                    // CORS or other restrictions - skip this sheet
                    console.log('CSS Coverage: Could not access stylesheet', i, ':', e.message);
                }
            }
            
            console.log('CSS Coverage: Total rules tracked:', this.rules.size);
            this.initialized = true;
            
            // Start tracking rule usage via mutation observer
            this.startTracking();
        },
        
        reinit: function() {
            // Clear existing data and re-initialize (useful after dynamic content loads)
            this.stylesheets.clear();
            this.rules.clear();
            this.initialized = false;
            this.init();
        },
        
        startTracking: function() {
            if (document.body) {
                const observer = new MutationObserver((mutations) => {
                    this.checkRuleUsage();
                });
                
                observer.observe(document.body, {
                    childList: true,
                    subtree: true,
                    attributes: true,
                    attributeOldValue: true
                });
                
                // Initial check
                this.checkRuleUsage();
            } else {
                // Body not ready, retry later
                setTimeout(() => this.startTracking(), 100);
            }
        },
        
        checkRuleUsage: function() {
            // Check if any elements match each rule's selector
            this.rules.forEach((ruleData, ruleId) => {
                if (!ruleData.used && ruleData.selector && (ruleData.selector.includes('.') || ruleData.selector.includes('#'))) {
                    try {
                        if (document.querySelector(ruleData.selector)) {
                            ruleData.used = true;
                        }
                    } catch (e) {
                        // Invalid selector - mark as used to avoid repeated errors
                        ruleData.used = true;
                    }
                }
            });
        },
        
        getReport: function() {
            console.log('CSS Coverage: Generating report, rules tracked:', this.rules.size);
            const report = [];
            this.rules.forEach((ruleData, ruleId) => {
                report.push({
                    ruleId: ruleId,
                    styleSheetId: ruleData.sheetId,
                    selector: ruleData.selector,
                    text: ruleData.text,
                    used: ruleData.used
                });
            });
            console.log('CSS Coverage: Report generated with', report.length, 'entries');
            return report;
        },
        
        getDebugInfo: function() {
            return {
                initialized: this.initialized,
                totalStylesheets: document.styleSheets.length,
                accessibleSheets: this.stylesheets.size,
                totalRules: this.rules.size,
                usedRules: Array.from(this.rules.values()).filter(r => r.used).length
            };
        }
    };
    
    // Multiple initialization strategies for different page load states
    console.log('CSS Coverage: Setting up initialization...');
    
    // Try immediate initialization
    if (document.readyState === 'complete') {
        console.log('CSS Coverage: Document complete, initializing immediately');
        setTimeout(() => window.__css_coverage__.init(), 100); // Small delay to ensure stylesheets are processed
    } else if (document.readyState === 'interactive') {
        console.log('CSS Coverage: Document interactive, waiting for load event');
        window.addEventListener('load', () => {
            setTimeout(() => window.__css_coverage__.init(), 100);
        });
    } else {
        console.log('CSS Coverage: Document still loading, waiting for DOMContentLoaded');
        document.addEventListener('DOMContentLoaded', () => {
            setTimeout(() => window.__css_coverage__.init(), 100);
        });
    }
    
    // Also try reinitializing after a delay (for dynamic content)
    setTimeout(() => {
        if (!window.__css_coverage__.initialized || window.__css_coverage__.rules.size === 0) {
            console.log('CSS Coverage: Reinitializing after delay...');
            window.__css_coverage__.reinit();
        }
    }, 2000);
    """
    
    try:
        driver.execute_script(coverage_script)
        print("CSS coverage JavaScript injected successfully")
    except Exception as e:
        # Log error but don't fail the test
        print(f"Could not inject CSS coverage JavaScript: {e}")


def start_css_coverage(driver) -> None:
    """Begin CSS rule usage tracking via CDP or JavaScript fallback."""
    if _has_cdp_support(driver):
        try:
            driver.execute_cdp_cmd("DOM.enable", {})
            driver.execute_cdp_cmd("CSS.enable", {})
            driver.execute_cdp_cmd("CSS.startRuleUsageTracking", {})
            return
        except Exception:
            # CDP failed, fall back to JavaScript
            pass
    
    # Use JavaScript-based tracking as fallback
    _inject_css_coverage_js(driver)


def _inject_dom_coverage_js(driver) -> None:
    """Inject a lightweight DOM coverage tracker into the page.

    Tracks:
      - Elements seen (added to DOM)
      - Visibility (via IntersectionObserver)
      - Interactions (click/touch/input/change)
    """
    dom_script = r"""
    (function(){
      if (window.__dom_coverage__) return; // idempotent

      function cssPath(el){
        if (!el || !el.nodeType || el.nodeType !== 1) return '';
        const parts = [];
        let node = el;
        while (node && node.nodeType === 1 && parts.length < 8) {
          let selector = node.nodeName.toLowerCase();
          if (node.id) {
            selector += '#' + node.id;
            parts.unshift(selector);
            break;
          }
          if (node.classList && node.classList.length) {
            selector += '.' + Array.from(node.classList).slice(0,3).join('.');
          }
          // position among type siblings
          let sib = node, idx = 1;
          while (sib = sib.previousElementSibling) {
            if (sib.nodeName === node.nodeName) idx++;
          }
          selector += ':nth-of-type(' + idx + ')';
          parts.unshift(selector);
          node = node.parentElement;
        }
        return parts.join(' > ');
      }

      function textSnippet(el){
        try{
          const t = (el.textContent || '').trim().replace(/\s+/g,' ');
          return t.length > 80 ? t.slice(0,77)+'...' : t;
        }catch(e){return ''}
      }

      window.__dom_coverage__ = {
        elements: new Map(),
        interactions: 0,
        initialized: false,

        ensure(el){
          if (!el || !el.nodeType || el.nodeType !== 1) return null;
          const key = cssPath(el);
          if (!key) return null;
          if (!this.elements.has(key)){
            this.elements.set(key, {
              key,
              tag: el.nodeName.toLowerCase(),
              id: el.id || '',
              classes: el.className || '',
              snippet: textSnippet(el),
              seen: 0,
              visible: 0,
              interacted: 0
            });
          }
          return this.elements.get(key);
        },

        markSeen(el){
          const rec = this.ensure(el);
          if (rec) rec.seen++;
        },

        markVisible(entry){
          const el = entry.target;
          if (!el) return;
          const rec = this.ensure(el);
          if (rec && entry.isIntersecting) rec.visible++;
        },

        markInteracted(el){
          const rec = this.ensure(el);
          if (rec) rec.interacted++;
          this.interactions++;
        },

        init(){
          try{
            // Track interactions
            const handler = (e)=>{
              const el = e.target && e.target.closest ? e.target.closest('*') : e.target;
              if (el) this.markInteracted(el);
            };
            ['click','touchstart','input','change'].forEach(evt => document.addEventListener(evt, handler, {capture:true}));

            // Observe visibility
            const io = new IntersectionObserver((entries)=>{
              for (const entry of entries) this.markVisible(entry);
            }, {root: null, rootMargin: '0px', threshold: [0, 0.01, 0.5, 1]});

            // Seed current elements (limit to avoid perf issues)
            const all = document.querySelectorAll('*');
            const max = Math.min(2000, all.length);
            for (let i=0; i<max; i++){
              const el = all[i];
              this.markSeen(el);
              try { io.observe(el); } catch(e){}
            }

            // Watch DOM mutations to catch later elements
            const mo = new MutationObserver((mutations)=>{
              for (const m of mutations){
                if (m.type === 'childList'){
                  m.addedNodes && m.addedNodes.forEach(n => {
                    if (n && n.nodeType === 1){
                      this.markSeen(n);
                      try { io.observe(n); } catch(e){}
                    }
                  });
                }
                if (m.type === 'attributes' && m.target && m.target.nodeType === 1){
                  this.markSeen(m.target);
                }
              }
            });
            mo.observe(document.documentElement || document.body, {subtree:true, childList:true, attributes:true});

            this.initialized = true;
          }catch(e){
            console.log('DOM Coverage init error', e && e.message);
          }
        },

        getReport(){
          const out = [];
          this.elements.forEach((rec)=> out.push(rec));
          return out;
        },

        getSummary(){
          let seen=0, visible=0, interacted=0;
          this.elements.forEach(r=>{ if (r.seen) seen++; if (r.visible) visible++; if (r.interacted) interacted++; });
          return { total: this.elements.size, seen, visible, interacted, interactions: this.interactions, initialized: this.initialized };
        }
      };

      if (document.readyState === 'complete' || document.readyState === 'interactive'){
        setTimeout(()=> window.__dom_coverage__.init(), 50);
      } else {
        document.addEventListener('DOMContentLoaded', ()=> setTimeout(()=> window.__dom_coverage__.init(), 50));
      }
    })();
    """

    try:
        driver.execute_script(dom_script)
        print("DOM coverage JavaScript injected successfully")
    except Exception as e:
        print(f"Could not inject DOM coverage JavaScript: {e}")


def start_dom_coverage(driver) -> None:
    """Begin DOM coverage tracking via JavaScript injection."""
    _inject_dom_coverage_js(driver)


def _inject_worker_coverage_js(driver) -> None:
    """Inject support to track Web Workers and merge their coverage into window.__coverage__."""
    script = r"""
    (function(){
      if (window.__worker_cov__ && window.__worker_cov__.__wrapped) return;
      const OriginalWorker = window.Worker;
      const merge = (base, inc) => {
        if (!inc) return base;
        if (!base) return inc;
        try {
          // Both are Istanbul coverage maps: filename -> {s,f,b, ...}
          for (const file in inc) {
            if (!base[file]) { base[file] = inc[file]; continue; }
            const a = base[file], b = inc[file];
            if (a && b) {
              if (a.s && b.s) { for (const k in b.s) { a.s[k] = (a.s[k]||0) + (b.s[k]||0); } }
              if (a.f && b.f) { for (const k in b.f) { a.f[k] = (a.f[k]||0) + (b.f[k]||0); } }
              if (a.b && b.b) { for (const k in b.b) {
                const arrA = a.b[k] || []; const arrB = b.b[k] || [];
                const len = Math.max(arrA.length, arrB.length);
                const merged = new Array(len);
                for (let i=0;i<len;i++){ merged[i] = (arrA[i]||0) + (arrB[i]||0); }
                a.b[k] = merged;
              } }
            }
          }
        } catch(e) { /* ignore merge errors */ }
        return base;
      };

      window.__worker_cov__ = {
        __wrapped: true,
        workers: [],
        pending: 0,
        mergeIntoWindowCoverage: function(cov){
          if (window.__coverage__) {
            merge(window.__coverage__, cov);
          } else {
            window.__coverage__ = cov || {};
          }
        }
      };

      window.Worker = function(url, opts){
        const w = new OriginalWorker(url, opts);
        try {
          window.__worker_cov__.workers.push(w);
          w.addEventListener('message', function(ev){
            const d = ev && ev.data;
            if (d && d.type === '__coverage__'){
              try { window.__worker_cov__.mergeIntoWindowCoverage(d.coverage); } catch(e){}
              if (typeof window.__worker_cov__.pending === 'number' && window.__worker_cov__.pending > 0) {
                window.__worker_cov__.pending -= 1;
              }
            }
          });
        } catch(e){}
        return w;
      };
      window.Worker.toString = function(){ return OriginalWorker.toString(); };
    })();
    """
    try:
        driver.execute_script(script)
        print("Worker coverage bridge injected successfully")
    except Exception as e:
        print(f"Could not inject Worker coverage bridge: {e}")


def start_worker_coverage(driver) -> None:
    """Enable Web Worker coverage tracking/merging in the page."""
    _inject_worker_coverage_js(driver)

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

        # Try to gather coverage from any tracked Web Workers and merge
        try:
            f.write("Initiating worker coverage handshake...\n")
            info = driver.execute_script(
                """
                try{
                  if (window.__worker_cov__ && Array.isArray(window.__worker_cov__.workers)){
                    const W = window.__worker_cov__;
                    W.pending = 0;
                    for (const w of W.workers){ try { W.pending++; w.postMessage({type:'__dump_coverage__'}); } catch(e){} }
                    return {workers: W.workers.length, pending: W.pending};
                  }
                  return {workers: 0, pending: 0};
                }catch(e){ return {error: String(e)} }
                """
            )
            f.write(f"Worker handshake: {info}\n")
            # Poll for a short while for pending to reach 0
            import time
            start = time.time()
            while time.time() - start < 1.5:
                try:
                    pending = driver.execute_script("return (window.__worker_cov__ && window.__worker_cov__.pending) || 0")
                except Exception:
                    pending = 0
                f.write(f"Worker pending: {pending}\n")
                if not pending:
                    break
                time.sleep(0.2)
            # Re-read window.__coverage__ after merges
            cov2 = driver.execute_script("return window.__coverage__ || null")
            if cov2 and isinstance(cov2, dict):
                cov = cov2
                f.write("Merged worker coverage into window.__coverage__\n")
        except Exception as e:
            f.write(f"Worker coverage handshake error: {e}\n")

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


def collect_dom_coverage(driver, out_dir: Path):
    """Collect DOM coverage from the page and generate a simple HTML report."""
    out_dir.mkdir(parents=True, exist_ok=True)
    debug_file = Path(__file__).parent / "dom_coverage_debug.txt"

    with open(debug_file, "w") as f:
        f.write("=== DOM COVERAGE COLLECTION DEBUG ===\n")
        try:
            contexts = driver.contexts
            f.write(f"Available contexts: {contexts}\n")
            webviews = [c for c in contexts if c.startswith("WEBVIEW")]
            if webviews:
                driver.switch_to.context(webviews[0])
                f.write(f"Switched to WebView: {webviews[0]}\n")
            else:
                f.write("No WebView contexts found\n")
        except Exception as e:
            f.write(f"Context handling error: {e}\n")

        try:
            summary = driver.execute_script("return window.__dom_coverage__ ? window.__dom_coverage__.getSummary() : {error:'no dom coverage'}")
            report = driver.execute_script("return window.__dom_coverage__ ? window.__dom_coverage__.getReport() : []")
            f.write(f"Summary: {summary}\n")
            f.write(f"Report length: {len(report)}\n")
        except Exception as e:
            summary = {"error": str(e)}
            report = []
            f.write(f"DOM script execution error: {e}\n")

    # Persist JSON
    (out_dir / "dom-coverage.json").write_text(json.dumps(report, indent=2))
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2))

    _generate_dom_html_report(out_dir, summary, report)


def _generate_dom_html_report(out_dir: Path, summary, report) -> None:
    try:
        html_dir = out_dir / "html"
        html_dir.mkdir(parents=True, exist_ok=True)

        # Simple summary header
        header = (
            f"<h2>Summary</h2>"
            f"<ul>"
            f"<li>Total tracked: {summary.get('total','?')}</li>"
            f"<li>Seen: {summary.get('seen','?')}</li>"
            f"<li>Visible≥once: {summary.get('visible','?')}</li>"
            f"<li>Interacted≥once: {summary.get('interacted','?')}</li>"
            f"<li>Interactions: {summary.get('interactions','?')}</li>"
            f"</ul>"
        )

        # Build rows sorted by interacted, then visible, then seen
        def esc(s: str) -> str:
            if s is None:
                return ''
            return (
                str(s)
                .replace('&','&amp;')
                .replace('<','&lt;')
                .replace('>','&gt;')
            )

        rows = []
        for r in sorted(report, key=lambda x: (-(x.get('interacted',0)), -(x.get('visible',0)), -(x.get('seen',0)))):
            rows.append(
                "<tr>"
                f"<td><code>{esc(r.get('key',''))}</code></td>"
                f"<td>{esc(r.get('tag',''))}</td>"
                f"<td>{esc(r.get('id',''))}</td>"
                f"<td>{esc(r.get('classes',''))}</td>"
                f"<td>{r.get('seen',0)}</td>"
                f"<td>{r.get('visible',0)}</td>"
                f"<td>{r.get('interacted',0)}</td>"
                f"<td><pre>{esc(r.get('snippet',''))}</pre></td>"
                "</tr>"
            )

        html = (
            "<html><body><h1>DOM Coverage</h1>"
            + header +
            "<table border='1'>"
            "<tr><th>Path</th><th>tag</th><th>id</th><th>classes</th><th>seen</th><th>visible</th><th>interacted</th><th>text</th></tr>"
            + "".join(rows) +
            "</table></body></html>"
        )
        (html_dir / "index.html").write_text(html)
    except Exception as e:
        print(f"Could not generate DOM HTML report: {e}")


def _collect_cdp_css_coverage(driver, out_dir: Path, debug_file) -> bool:
    """Collect CSS coverage using Chrome DevTools Protocol."""
    try:
        usage_data = driver.execute_cdp_cmd("CSS.stopRuleUsageTracking", {})
        rule_usage = usage_data.get("ruleUsage", [])
        debug_file.write(f"CDP - Raw rule usage entries: {len(rule_usage)}\n")

        # Retrieve style sheet sources so we can provide line numbers
        sheets = {}
        for entry in rule_usage:
            sid = entry.get("styleSheetId")
            if sid in sheets:
                continue
            try:
                sheet = driver.execute_cdp_cmd(
                    "CSS.getStyleSheetText", {"styleSheetId": sid}
                )
                sheets[sid] = sheet.get("text", "")
            except Exception as e:  # noqa: BLE001 - best effort only
                debug_file.write(f"Could not fetch style sheet {sid}: {e}\n")
                sheets[sid] = ""

        # Build a richer coverage structure with line numbers/snippets
        coverage = []
        for entry in rule_usage:
            text = sheets.get(entry.get("styleSheetId"), "")
            start = int(entry.get("startOffset", 0))
            end = int(entry.get("endOffset", 0))
            snippet = text[start:end]
            start_line = text.count("\n", 0, start) + 1
            end_line = text.count("\n", 0, end) + 1
            coverage.append(
                {
                    "styleSheetId": entry.get("styleSheetId"),
                    "used": entry.get("used"),
                    "startLine": start_line,
                    "endLine": end_line,
                    "snippet": snippet,
                    "method": "cdp"
                }
            )

        (out_dir / "css-coverage.json").write_text(json.dumps(coverage, indent=2))
        debug_file.write(f"CDP - Final CSS coverage entries: {len(coverage)}\n")
        return True
        
    except Exception as e:
        debug_file.write(f"CDP CSS coverage collection error: {e}\n")
        return False


def _collect_js_css_coverage(driver, out_dir: Path, debug_file) -> bool:
    """Collect CSS coverage using JavaScript-based tracking."""
    try:
        # Get debug info first
        debug_info = driver.execute_script(
            "return window.__css_coverage__ ? window.__css_coverage__.getDebugInfo() : {error: 'CSS coverage object not found'}"
        )
        debug_file.write(f"JS - Debug info: {debug_info}\n")
        
        # Check if the system was properly initialized
        if not debug_info.get('initialized', False):
            debug_file.write("JS - CSS coverage was not initialized, attempting manual initialization...\n")
            driver.execute_script(
                "if (window.__css_coverage__) { window.__css_coverage__.reinit(); }"
            )
            # Wait a moment for initialization
            import time
            time.sleep(1)
            
            # Get updated debug info
            debug_info = driver.execute_script(
                "return window.__css_coverage__ ? window.__css_coverage__.getDebugInfo() : {error: 'Still not found'}"
            )
            debug_file.write(f"JS - Debug info after reinit: {debug_info}\n")
        
        # Get the coverage report from our injected JavaScript
        coverage_data = driver.execute_script(
            "return window.__css_coverage__ ? window.__css_coverage__.getReport() : []"
        )
        
        debug_file.write(f"JS - Retrieved {len(coverage_data)} CSS rules\n")
        
        # Get additional debugging from the browser console
        try:
            console_logs = driver.execute_script(
                "return window.__css_coverage_logs__ || 'No console logs captured'"
            )
            debug_file.write(f"JS - Console logs: {console_logs}\n")
        except:
            debug_file.write("JS - Could not retrieve console logs\n")
        
        # Convert to similar format as CDP for consistency
        coverage = []
        for rule in coverage_data:
            coverage.append({
                "styleSheetId": rule.get("styleSheetId", "unknown"),
                "used": rule.get("used", False),
                "selector": rule.get("selector", ""),
                "snippet": rule.get("text", ""),
                "method": "javascript"
            })
        
        (out_dir / "css-coverage.json").write_text(json.dumps(coverage, indent=2))
        debug_file.write(f"JS - Final CSS coverage entries: {len(coverage)}\n")
        return True
        
    except Exception as e:
        debug_file.write(f"JavaScript CSS coverage collection error: {e}\n")
        return False


def _generate_css_html_report(out_dir: Path) -> None:
    """Generate HTML report from CSS coverage data."""
    try:
        coverage_file = out_dir / "css-coverage.json"
        if not coverage_file.exists():
            return
            
        coverage = json.loads(coverage_file.read_text())
        
        html_dir = out_dir / "html"
        html_dir.mkdir(parents=True, exist_ok=True)
        
        rows = []
        method_used = coverage[0].get("method", "unknown") if coverage else "unknown"
        
        for c in coverage:
            method = c.get("method", "unknown")
            sheet_id = c.get("styleSheetId", "unknown")
            
            if method == "cdp":
                lines = f"{c.get('startLine', 'N/A')}-{c.get('endLine', 'N/A')}"
            else:
                lines = "N/A (JS method)"
            
            status = 'used' if c.get('used', False) else 'unused'
            snippet = c.get('snippet', c.get('selector', ''))
            
            rows.append(
                "<tr>"
                f"<td>{sheet_id}</td>"
                f"<td>{lines}</td>"
                f"<td>{status}</td>"
                f"<td><pre>{snippet}</pre></td>"
                "</tr>"
            )
            
        html = (
            "<html><body><h1>CSS Coverage</h1>"
            f"<p>Collection Method: {'Chrome DevTools Protocol' if method_used == 'cdp' else 'JavaScript-based tracking'}</p>"
            "<table border='1'>"
            "<tr><th>StyleSheet</th><th>Lines</th><th>Status</th><th>Rule</th></tr>"
            + "".join(rows)
            + "</table></body></html>"
        )
        (html_dir / "index.html").write_text(html)
        
    except Exception as e:
        print(f"Could not generate CSS HTML report: {e}")


def stop_css_coverage(driver, out_dir: Path) -> None:
    """Stop CSS tracking and persist results to ``out_dir``.

    Uses CDP when available, falls back to JavaScript-based tracking.
    The resulting JSON contains CSS rule usage information.
    """

    out_dir.mkdir(parents=True, exist_ok=True)
    debug_file_path = Path(__file__).parent / "css_coverage_debug.txt"
    
    with open(debug_file_path, "w") as debug_file:
        debug_file.write("=== CSS COVERAGE COLLECTION DEBUG ===\n")
        
        # Try CDP first if supported
        if _has_cdp_support(driver):
            debug_file.write("Attempting CDP collection...\n")
            if _collect_cdp_css_coverage(driver, out_dir, debug_file):
                debug_file.write("CDP collection successful\n")
            else:
                debug_file.write("CDP collection failed, trying JavaScript...\n")
                _collect_js_css_coverage(driver, out_dir, debug_file)
        else:
            debug_file.write("No CDP support detected, using JavaScript collection...\n")
            _collect_js_css_coverage(driver, out_dir, debug_file)
    
    # Generate HTML report from collected data
    _generate_css_html_report(out_dir)
