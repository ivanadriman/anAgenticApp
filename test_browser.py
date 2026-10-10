"""
Automated Browser Test Suite for Gemini Agentic Studio.
Visits https://ivanadriman.github.io/anAgenticApp/, configures the key and parameters,
runs the live multi-agent loop, tests the use cases, and takes screenshots.
"""

import os
import sys
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()
API_KEY = os.environ.get("GEMINI_API_KEY", "")
PAGE_URL = "https://ivanadriman.github.io/anAgenticApp/"
SCREENSHOTS_DIR = os.path.join(os.getcwd(), "test_screenshots")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

def run_browser_tests():
    print(f"Launching automated browser to visit: {PAGE_URL}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()

        # Listen to console logs and errors
        page.on("console", lambda msg: print(f"[Browser Console] {msg.type}: {msg.text}", flush=True))
        page.on("pageerror", lambda err: print(f"[Browser Error] {err}", flush=True))
        page.on("dialog", lambda dialog: (print(f"[Browser Dialog] {dialog.message}", flush=True), dialog.accept()))

        # Navigate to GitHub Pages
        print(f"Navigating to {PAGE_URL}...", flush=True)
        response = page.goto(PAGE_URL, wait_until="networkidle", timeout=30000)
        print(f"Page loaded with status: {response.status if response else 'unknown'}", flush=True)

        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "01_page_initial.png"))
        print("Captured initial page screenshot.")

        # Test Case 1: Enter API Key and verify save
        print("\n--- Test Case 1: Configuring API Key ---")
        api_input = page.locator("#apiKeyInput")
        api_input.fill(API_KEY)
        page.locator("#saveKeyBtn").click()

        # Check local storage
        stored_key = page.evaluate("() => localStorage.getItem('GEMINI_USER_API_KEY')")
        print(f"Stored key in localStorage matches API_KEY: {bool(stored_key and stored_key == API_KEY)}")

        # Test Case 2: Select Model and Options
        print("\n--- Test Case 2: Setting Parameters, Thinking Mode & Toggles ---", flush=True)
        page.select_option("#modelSelect", "gemini-3.5-flash-lite")
        
        # Test Thinking Mode selection
        thinking_box = page.locator("#thinkingLevelSelect")
        print(f"Thinking Mode selector present: {thinking_box.count() > 0}", flush=True)
        page.select_option("#thinkingLevelSelect", "high")
        print(f"Selected thinking mode: {thinking_box.input_value()}", flush=True)

        page.select_option("#maxTurnsSelect", "2")
        page.locator("#targetScoreInput").fill("9.2")
        
        # Check Force All Turns
        force_box = page.locator("#forceAllTurnsCheck")
        force_box.check()
        print(f"Force all turns checked: {force_box.is_checked()}", flush=True)

        # Check Live Web Search toggle
        search_box = page.locator("#webSearchCheck")
        print(f"Live Web Search toggle present: {search_box.count() > 0}", flush=True)

        # Test Topic
        topic_box = page.locator("#topicInput")
        topic_box.fill("Explain how the Event Loop works in modern JavaScript runtimes")

        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "02_configured_form.png"))

        # Test Case 3: Trigger Pipeline Execution
        print("\n--- Test Case 3: Executing Agentic Pipeline ---")
        start_btn = page.locator("#startPipelineBtn")
        start_btn.click()

        # Wait for status bar to appear
        page.wait_for_selector("#statusCard:not(.hidden)", timeout=5000)
        print("Status card active. Monitoring turns...")

        # Monitor loop for up to 90 seconds
        start_time = time.time()
        last_status = ""
        while time.time() - start_time < 90:
            status_text = page.locator("#statusText").text_content() or ""
            step_text = page.locator("#stepCounter").text_content() or ""
            if status_text != last_status:
                print(f"[Pipeline Progress] {step_text} -> {status_text}")
                last_status = status_text

            # Check if button is re-enabled (pipeline done)
            btn_disabled = start_btn.is_disabled()
            if not btn_disabled and time.time() - start_time > 5:
                print("Pipeline execution completed!")
                break

            time.sleep(2)

        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "03_execution_complete.png"))

        # Inspect Cards
        writer_cards = page.locator("div:has-text('Writer Agent • Draft')").count()
        critic_cards = page.locator("div:has-text('Critic Agent • Review')").count()
        final_card = page.locator("#copyArtifactBtn").count()

        print(f"\nResults Summary:")
        print(f"- Writer Draft Cards Generated: {writer_cards}")
        print(f"- Critic Review Cards Generated: {critic_cards}")
        print(f"- Final Approved Artifact Card Present: {final_card > 0}")

        # Check Final Score and copy button
        if final_card > 0:
            page.locator("#copyArtifactBtn").click()
            print("Successfully clicked Copy Markdown button.")

        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "04_final_state.png"), full_page=True)
        print(f"Full page screenshot saved to {os.path.join(SCREENSHOTS_DIR, '04_final_state.png')}")

        browser.close()

if __name__ == "__main__":
    run_browser_tests()
