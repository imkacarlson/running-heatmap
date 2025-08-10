# testing/test_02_extras_last_activity_filter.py
import time
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from base_mobile_test import BaseMobileTest

@pytest.mark.mobile
@pytest.mark.core
class TestExtrasOnlyLastActivity(BaseMobileTest):
    def test_extras_last_activity_toggle(self, mobile_driver):
        driver = mobile_driver["driver"]
        wait: WebDriverWait = mobile_driver["wait"]

        # Let the app initialize (aligned with your other tests)
        time.sleep(12)
        self.switch_to_webview(driver)
        self.wait_for_map_load(driver, wait, verbose=True)

        # Pan/zoom to the area where your test data reliably renders multiple runs
        driver.execute_script("map.jumpTo({ center: [-77.4169, 39.4168], zoom: 14 });")
        driver.execute_async_script("""
            const cb = arguments[arguments.length - 1];
            if (typeof map === 'undefined') return cb(false);
            map.once('idle', () => cb(true));
        """)

        # --- Open Extras panel ---
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#extras-btn"))).click()
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#extras-panel.open")))

        # --- Click 'Show only this activity' in Extras ---
        checkbox = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#extras-panel .last-activity-checkbox")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", checkbox)
        checkbox.click()

        # --- Zoom to level 12 (same as second lasso polygon test) for better visibility ---
        driver.execute_script("map.jumpTo({ center: [-77.4169, 39.4168], zoom: 12 });")
        driver.execute_async_script("""
            const cb = arguments[arguments.length - 1];
            if (typeof map === 'undefined') return cb(false);
            map.once('idle', () => cb(true));
        """)

        # --- Minimize Extras panel after setting filter (creates sliver) ---
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#extras-collapse"))).click()
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#extras-panel.collapsed")))

        # Optionally minimize the side panel (if present). This should not affect filtering.
        try:
            collapse = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#panel-collapse"))
            )
            collapse.click()
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#side-panel.collapsed"))
            )
        except TimeoutException:
            # If your UI doesn't expose a collapse control here, filtering is still the thing we care about.
            pass

        # --- Verify: only one activity is rendered on runsVec-backed layers ---
        def unique_ids():
            return driver.execute_script("""
                const layers = (map.getStyle()?.layers || []).filter(l => l.source === 'runsVec').map(l => l.id);
                if (!layers.length) return { ok:false, reason:'no runsVec layers', ids:[] };
                const feats = map.queryRenderedFeatures(undefined, { layers });
                const ids = Array.from(new Set(feats.map(f => f.properties && f.properties.id).filter(v => v !== undefined)));
                return { ok:true, ids };
            """)
        only_one = WebDriverWait(driver, 10).until(lambda d: len(unique_ids()["ids"]) == 1)
        # Grab the single id for later comparison if needed
        selected_id = unique_ids()["ids"][0]

        # --- Reopen side panel (if we collapsed it), expand extras from sliver to uncheck filter ---
        try:
            expand = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#panel-collapse"))
            )
            expand.click()
        except TimeoutException:
            pass

        # Expand Extras panel from collapsed sliver state to uncheck the filter (cleanup)
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#extras-expand-btn"))).click()
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "#extras-panel.collapsed")))

        # Uncheck the Extras checkbox to clear filter
        checkbox = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#extras-panel .last-activity-checkbox")))
        if checkbox.is_selected():
            checkbox.click()

        # Close Extras via its X button (final cleanup)
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#extras-close"))).click()
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "#extras-panel.open")))

        # Zoom out slightly to ensure multiple runs are in view for the all-runs assertion
        driver.execute_script("map.setZoom(10);")
        driver.execute_async_script("""
            const cb = arguments[arguments.length - 1];
            map.once('idle', () => cb(true));
        """)

        # --- Verify: multiple distinct activities are visible again ---
        def multiple_ids():
            return len(unique_ids()["ids"]) >= 2

        assert WebDriverWait(driver, 10).until(lambda d: multiple_ids()), \
            "Expected multiple activities after unchecking + closing Extras."

        # (Optional sanity: ensure the previously-filtered id is among those now visible)
        now_ids = set(unique_ids()["ids"])
        assert str(selected_id) in {str(x) for x in now_ids}, \
            f"Previously selected id {selected_id} not visible after clearing filter."
