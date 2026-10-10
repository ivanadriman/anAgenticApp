"""
Automated Browser Test Suite for Gemini Agentic Studio.
Verifies the new Scholarly & Reference Grounding features:
- 6 Independent Sources: arXiv, Crossref, Semantic Scholar, OpenAlex, PubMed, Wikipedia
- Live Research & Literature Grounding Progress tracker with per-source status and links
- Verified Academic & Reference Research Dossier card
- Tested on topic: "Speech perception"
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

        # Check GitHub Pages or fallback to local index.html if GitHub Pages is building
        print(f"Navigating to {PAGE_URL}...", flush=True)
        try:
            page.goto(PAGE_URL, wait_until="networkidle", timeout=12000)
            time.sleep(1)
            crossref_count = page.locator("#crossrefCheck").count()
            if crossref_count == 0:
                print("GitHub Pages build in progress; switching to local index.html for verification...", flush=True)
                page.goto(LOCAL_HTML, wait_until="networkidle", timeout=10000)
            else:
                print("GitHub Pages has the latest deployment active with 6 scholarly sources!", flush=True)
        except Exception as e:
            print(f"Navigating to local index.html: {e}", flush=True)
            page.goto(LOCAL_HTML, wait_until="networkidle", timeout=10000)

        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "10_initial_page.png"))

        # -------------------------------------------------------------
        # Test Case 1: Verify All 6 Scholarly Sources & Controls
        # -------------------------------------------------------------
        print("\n--- Test Case 1: Verifying All 6 Scholarly Grounding Checkboxes ---", flush=True)
        api_input = page.locator("#apiKeyInput")
        api_input.fill(API_KEY)
        page.locator("#saveKeyBtn").click()

        arxiv_box = page.locator("#arxivCheck")
        crossref_box = page.locator("#crossrefCheck")
        semantic_box = page.locator("#semanticScholarCheck")
        openalex_box = page.locator("#openAlexCheck")
        pubmed_box = page.locator("#pubmedCheck")
        wiki_box = page.locator("#wikipediaCheck")
        upload_btn = page.locator("#uploadDocBtn")

        print(f"  • arXiv Preprints checkbox: {arxiv_box.count() > 0}")
        print(f"  • Crossref DOI Index checkbox: {crossref_box.count() > 0}")
        print(f"  • Semantic Scholar checkbox: {semantic_box.count() > 0}")
        print(f"  • OpenAlex Catalog checkbox: {openalex_box.count() > 0}")
        print(f"  • PubMed Central checkbox: {pubmed_box.count() > 0}")
        print(f"  • Wikipedia Reference checkbox: {wiki_box.count() > 0}")
        print(f"  • Local PDF Upload button: {upload_btn.count() > 0}")

        assert arxiv_box.count() > 0
        assert crossref_box.count() > 0
        assert semantic_box.count() > 0
        assert openalex_box.count() > 0
        assert pubmed_box.count() > 0
        assert wiki_box.count() > 0

        # -------------------------------------------------------------
        # Test Case 2: Select Sources & Topic "Speech perception"
        # -------------------------------------------------------------
        print("\n--- Test Case 2: Selecting Sources for 'Speech perception' ---", flush=True)
        arxiv_box.check()
        crossref_box.check()
        semantic_box.check()
        openalex_box.check()
        pubmed_box.check()
        wiki_box.uncheck()  # specifically uncheck Wikipedia to test that scholarly sources run on their own!

        # Uncheck Google Search to avoid 429 quota
        search_box = page.locator("#webSearchCheck")
        if search_box.is_checked():
            search_box.uncheck()

        page.select_option("#modelSelect", "gemini-3.5-flash-lite")
        page.select_option("#thinkingLevelSelect", "medium")
        page.select_option("#maxTurnsSelect", "1")
        page.locator("#targetScoreInput").fill("8.5")

        topic_box = page.locator("#topicInput")
        topic_box.fill("Speech perception")

        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "11_sources_selected.png"))

        # -------------------------------------------------------------
        # Test Case 3: Execute Pipeline & Monitor Live Progression
        # -------------------------------------------------------------
        print("\n--- Test Case 3: Running Pipeline & Monitoring Live Lookup Progression ---", flush=True)
        start_btn = page.locator("#startPipelineBtn")
        start_btn.click()

        # Wait for live research progress card to appear
        page.wait_for_selector("#liveResearchProgressCard", timeout=6000)
        print("  ✓ Live Research & Literature Grounding Progress card appeared in browser UI!", flush=True)

        # Monitor live progress and execution
        start_time = time.time()
        last_counter = ""
        captured_progress = False

        while time.time() - start_time < 90:
            counter_text = page.locator("#researchProgressCounter").text_content() or ""
            status_text = page.locator("#statusText").text_content() or ""
            
            if counter_text != last_counter and counter_text:
                print(f"  [Grounding Progression] {counter_text}", flush=True)
                last_counter = counter_text

            if not captured_progress and "Completed" in counter_text:
                time.sleep(1)
                page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "12_live_progression_card.png"))
                captured_progress = True

            # Check if execution finished
            if not start_btn.is_disabled() and time.time() - start_time > 8:
                print("Pipeline execution completed!", flush=True)
                break

            time.sleep(2)

        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "13_workflow_complete.png"))

        # -------------------------------------------------------------
        # Test Case 4: Verify Retrieved Items and Final Dossier
        # -------------------------------------------------------------
        print("\n--- Test Case 4: Inspecting Results & Dossier ---", flush=True)
        progress_card = page.locator("#liveResearchProgressCard")
        dossier_card = page.locator("div:has-text('Verified Academic & Reference Research Dossier')")
        writer_cards = page.locator("div:has-text('Writer Agent • Draft')")
        critic_cards = page.locator("div:has-text('Critic Agent • Review')")

        print(f"  • Progress Tracker Card Present: {progress_card.count() > 0}")
        print(f"  • Final Dossier Card Present: {dossier_card.count() > 0}")
        print(f"  • Writer Draft Cards: {writer_cards.count()}")
        print(f"  • Critic Review Cards: {critic_cards.count()}")

        # Count clickable links
        paper_links = page.locator("a[href*='arxiv.org'], a[href*='doi.org'], a[href*='ncbi.nlm.nih.gov']").count()
        print(f"  • Total Clickable Paper Links (arXiv / DOI / PubMed): {paper_links}")

        assert progress_card.count() > 0, "Missing #liveResearchProgressCard"
        assert dossier_card.count() > 0, "Missing Verified Dossier card"
        assert writer_cards.count() > 0, "Missing Writer Draft card"
        assert paper_links >= 5, f"Expected at least 5 scholarly links, found {paper_links}"

        final_screenshot = os.path.join(SCREENSHOTS_DIR, "14_full_detailed_scholarly_workflow.png")
        page.screenshot(path=final_screenshot, full_page=True)
        print(f"\nAll tests passed successfully! Full screenshot saved to {final_screenshot}")

        browser.close()


if __name__ == "__main__":
    run_scholarly_browser_tests()
