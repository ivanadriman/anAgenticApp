"""
Automated Browser Test Suite for Gemini Agentic Studio.
Verifies the new Scholarly & Reference Grounding features (arXiv, Semantic Scholar,
OpenAlex, Wikipedia, PDF/Document upload) using Playwright.
"""

import os
import sys
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()
API_KEY = os.environ.get("GEMINI_API_KEY", "")
PAGE_URL = "https://ivanadriman.github.io/anAgenticApp/"
LOCAL_HTML = f"file:///{os.path.abspath('index.html').replace(os.sep, '/')}"
SCREENSHOTS_DIR = os.path.join(os.getcwd(), "test_screenshots")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def run_scholarly_browser_tests():
    print(f"Launching automated Chromium browser...", flush=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 950})
        page = context.new_page()

        # Listen to console logs and errors
        page.on("console", lambda msg: print(f"[Browser Console] {msg.type}: {msg.text}", flush=True))
        page.on("pageerror", lambda err: print(f"[Browser Error] {err}", flush=True))
        page.on("dialog", lambda dialog: (print(f"[Browser Dialog] {dialog.message}", flush=True), dialog.accept()))

        # Try GitHub Pages first; if not yet updated with new commit, test local file directly
        print(f"Checking deployment at {PAGE_URL}...", flush=True)
        try:
            page.goto(PAGE_URL, wait_until="networkidle", timeout=15000)
            time.sleep(1)
            arxiv_count = page.locator("#arxivCheck").count()
            if arxiv_count == 0:
                print("GitHub Pages deployment in progress; loading local index.html for instant verification...", flush=True)
                page.goto(LOCAL_HTML, wait_until="networkidle", timeout=10000)
            else:
                print("GitHub Pages has the latest deployment active!", flush=True)
        except Exception as e:
            print(f"Navigating to local index.html: {e}", flush=True)
            page.goto(LOCAL_HTML, wait_until="networkidle", timeout=10000)

        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "05_page_loaded.png"))
        print("Captured initial page screenshot.", flush=True)

        # -------------------------------------------------------------
        # Test Case 1: Configure API Key & Verify Checkboxes
        # -------------------------------------------------------------
        print("\n--- Test Case 1: Verifying Scholarly Grounding Controls ---", flush=True)
        api_input = page.locator("#apiKeyInput")
        api_input.fill(API_KEY)
        page.locator("#saveKeyBtn").click()

        # Check all 4 scholarly checkboxes & document upload button
        arxiv_box = page.locator("#arxivCheck")
        semantic_box = page.locator("#semanticScholarCheck")
        openalex_box = page.locator("#openAlexCheck")
        wiki_box = page.locator("#wikipediaCheck")
        upload_btn = page.locator("#uploadDocBtn")
        file_status = page.locator("#docFileStatus")

        print(f"  • arXiv Preprints checkbox present: {arxiv_box.count() > 0}")
        print(f"  • Semantic Scholar checkbox present: {semantic_box.count() > 0}")
        print(f"  • OpenAlex Catalog checkbox present: {openalex_box.count() > 0}")
        print(f"  • Wikipedia Reference checkbox present: {wiki_box.count() > 0}")
        print(f"  • Document Upload button present: {upload_btn.count() > 0}")

        assert arxiv_box.count() > 0, "Missing #arxivCheck element"
        assert semantic_box.count() > 0, "Missing #semanticScholarCheck element"
        assert openalex_box.count() > 0, "Missing #openAlexCheck element"
        assert wiki_box.count() > 0, "Missing #wikipediaCheck element"
        assert upload_btn.count() > 0, "Missing #uploadDocBtn element"

        # -------------------------------------------------------------
        # Test Case 2: Select Scholarly Sources & Set Options
        # -------------------------------------------------------------
        print("\n--- Test Case 2: Enabling arXiv, OpenAlex, and Wikipedia Grounding ---", flush=True)
        arxiv_box.check()
        wiki_box.check()
        openalex_box.check()

        print(f"  • arXiv checked: {arxiv_box.is_checked()}")
        print(f"  • Wikipedia checked: {wiki_box.is_checked()}")
        print(f"  • OpenAlex checked: {openalex_box.is_checked()}")

        # Ensure Google search is unchecked (bypassing exhausted Google Search quota)
        search_box = page.locator("#webSearchCheck")
        if search_box.is_checked():
            search_box.uncheck()
        print(f"  • Google Web Search unchecked: {not search_box.is_checked()}")

        # Select model and thinking depth
        page.select_option("#modelSelect", "gemini-3.5-flash-lite")
        page.select_option("#thinkingLevelSelect", "medium")
        page.select_option("#maxTurnsSelect", "1")
        page.locator("#targetScoreInput").fill("8.5")

        # Set topic for research paper grounding
        topic_box = page.locator("#topicInput")
        topic_box.fill("Explain Self-Attention in Transformers with verified academic papers")

        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "06_scholarly_configured.png"))

        # -------------------------------------------------------------
        # Test Case 3: Execute Agentic Pipeline with Grounding
        # -------------------------------------------------------------
        print("\n--- Test Case 3: Running Pipeline with Academic Grounding ---", flush=True)
        start_btn = page.locator("#startPipelineBtn")
        start_btn.click()

        # Wait for status bar
        page.wait_for_selector("#statusCard:not(.hidden)", timeout=5000)
        print("Pipeline running. Monitoring turns and research dossier retrieval...", flush=True)

        start_time = time.time()
        last_status = ""
        dossier_detected = False

        while time.time() - start_time < 90:
            status_text = page.locator("#statusText").text_content() or ""
            step_text = page.locator("#stepCounter").text_content() or ""
            if status_text != last_status:
                print(f"[Pipeline Progress] {step_text} -> {status_text}", flush=True)
                last_status = status_text

            # Check if dossier card is rendered
            dossier_card = page.locator("div:has-text('Verified Academic & Reference Research Dossier')")
            if not dossier_detected and dossier_card.count() > 0:
                dossier_detected = True
                print("  ✓ Verified Academic & Reference Research Dossier card rendered in browser UI!", flush=True)
                page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "07_dossier_rendered.png"))

            # Check if pipeline completed
            if not start_btn.is_disabled() and time.time() - start_time > 6:
                print("Pipeline execution completed!", flush=True)
                break

            time.sleep(2)

        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "08_execution_done.png"))

        # -------------------------------------------------------------
        # Test Case 4: Verify Generated Cards & Citations
        # -------------------------------------------------------------
        print("\n--- Test Case 4: Inspecting Grounded Results & Citations ---", flush=True)
        dossier_count = page.locator("div:has-text('Verified Academic & Reference Research Dossier')").count()
        writer_cards = page.locator("div:has-text('Writer Agent • Draft')").count()
        critic_cards = page.locator("div:has-text('Critic Agent • Review')").count()
        final_cards = page.locator("div:has-text('Final Polish Approved')").count()

        print(f"  • Academic Dossier Cards: {dossier_count}")
        print(f"  • Writer Draft Cards: {writer_cards}")
        print(f"  • Critic Review Cards: {critic_cards}")
        print(f"  • Final Polish Cards: {final_cards}")

        # Check for citation links in the rendered markdown
        rendered_links = page.locator("a[href*='arxiv.org'], a[href*='wikipedia.org'], a[href*='doi.org']").count()
        print(f"  • Clickable Academic Links (arXiv / Wikipedia / DOI): {rendered_links}")

        assert dossier_count > 0, "Expected research dossier card to be present"
        assert writer_cards > 0, "Expected Writer Draft card to be present"
        assert critic_cards > 0, "Expected Critic Review card to be present"
        assert final_cards > 0, "Expected Final Polish card to be present"
        assert rendered_links > 0, "Expected clickable academic links in output"

        # Capture full-page screenshot
        final_screenshot = os.path.join(SCREENSHOTS_DIR, "09_full_scholarly_workflow.png")
        page.screenshot(path=final_screenshot, full_page=True)
        print(f"\nAll browser test use cases passed! Full page screenshot saved to {final_screenshot}")

        browser.close()


if __name__ == "__main__":
    run_scholarly_browser_tests()
