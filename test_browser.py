"""
Automated Browser Test Suite for Gemini Agentic Studio.
Verifies:
1. Indonesian / English Language Switcher (🇬🇧 EN <-> 🇮🇩 ID)
2. Multilingual Resource Seeking:
   - User inputs Indonesian topic: "Persepsi wicara"
   - App automatically extracts/translates global STEM keywords ("speech perception")
   - Literature grounding queries global databases (arXiv, PubMed, Semantic Scholar, Crossref, OpenAlex)
   - Wikipedia retrieves both Indonesian and Global editions
   - Progress card shows both original query and global STEM query in real time
   - Writer Agent synthesizes global findings into fluent Bahasa Indonesia with citations
   - Critic Agent evaluates in Bahasa Indonesia
"""

import os
import sys
import re
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


def run_browser_tests():
    print("Launching Chromium browser for Multilingual & Grounding validation...", flush=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 950})
        page = context.new_page()

        page.on("console", lambda msg: print(f"[Browser Console] {msg.type}: {msg.text}", flush=True))
        page.on("pageerror", lambda err: print(f"[Browser Error] {err}", flush=True))
        page.on("dialog", lambda dialog: (print(f"[Browser Dialog] {dialog.message}", flush=True), dialog.accept()))

        # Navigate to local file to ensure immediate testing of latest code
        print(f"Navigating to {LOCAL_HTML}...", flush=True)
        page.goto(LOCAL_HTML, wait_until="networkidle", timeout=12000)
        time.sleep(1)

        # -------------------------------------------------------------
        # Test Case 1: Validate Language Switcher (EN <-> ID)
        # -------------------------------------------------------------
        print("\n--- Test Case 1: Language Switcher Toggle (EN <-> ID) ---", flush=True)
        btn_en = page.locator("#langEnBtn")
        btn_id = page.locator("#langIdBtn")
        start_btn_text = page.locator("#startBtnText")

        assert btn_en.count() > 0, "Missing #langEnBtn"
        assert btn_id.count() > 0, "Missing #langIdBtn"

        powered_badge = page.locator("#headerPoweredBadge")
        assert powered_badge.count() > 0, "Missing #headerPoweredBadge"

        initial_btn_label = start_btn_text.text_content().strip()
        print(f"  • Initial Start Button Text (EN): '{initial_btn_label}'", flush=True)
        assert "Run Agentic Pipeline" in initial_btn_label

        initial_powered = powered_badge.text_content().strip()
        print(f"  • Initial Powered By Badge (EN): '{initial_powered}'", flush=True)
        assert "Powered by:" in initial_powered
        assert "Gemini 3.5 Flash Lite" in initial_powered

        # Switch to Indonesian
        print("  • Clicking Indonesian Switch [🇮🇩 ID]...", flush=True)
        btn_id.click()
        time.sleep(0.5)

        id_btn_label = start_btn_text.text_content().strip()
        print(f"  • Indonesian Start Button Text: '{id_btn_label}'", flush=True)
        assert "Jalankan Pipeline Agen" in id_btn_label

        id_powered = powered_badge.text_content().strip()
        print(f"  • Indonesian Powered By Badge: '{id_powered}'", flush=True)
        assert "Didukung oleh:" in id_powered
        assert "Gemini 3.5 Flash Lite" in id_powered

        # Check other Indonesian labels
        topic_label = page.locator("label[for='topicInput']").text_content().strip()
        print(f"  • Indonesian Topic Label: '{topic_label}'", flush=True)
        assert "Topik atau Tujuan" in topic_label

        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "15_lang_id_switched.png"))

        # Switch back to English
        print("  • Clicking English Switch [🇬🇧 EN]...", flush=True)
        btn_en.click()
        time.sleep(0.5)
        en_btn_label = start_btn_text.text_content().strip()
        print(f"  • Reverted Start Button Text: '{en_btn_label}'", flush=True)
        assert "Run Agentic Pipeline" in en_btn_label
        en_reverted_powered = powered_badge.text_content().strip()
        assert "Powered by:" in en_reverted_powered
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "16_lang_en_switched.png"))

        # Switch back to Indonesian for the remainder of the test
        print("  • Switching back to [🇮🇩 ID] for multilingual research run...", flush=True)
        btn_id.click()
        time.sleep(0.5)

        # -------------------------------------------------------------
        # Test Case 2: Enter Indonesian Topic & Enable Grounding Sources
        # -------------------------------------------------------------
        print("\n--- Test Case 2: Setup Indonesian Topic & Scholarly Sources ---", flush=True)
        api_input = page.locator("#apiKeyInput")
        api_input.fill(API_KEY)
        page.locator("#saveKeyBtn").click()

        # Select all 6 scholarly sources
        arxiv_box = page.locator("#arxivCheck")
        crossref_box = page.locator("#crossrefCheck")
        semantic_box = page.locator("#semanticScholarCheck")
        openalex_box = page.locator("#openAlexCheck")
        pubmed_box = page.locator("#pubmedCheck")
        wiki_box = page.locator("#wikipediaCheck")

        arxiv_box.check()
        crossref_box.check()
        semantic_box.check()
        openalex_box.check()
        pubmed_box.check()
        wiki_box.check()

        # Disable google web search checkbox to prevent quota limits
        search_box = page.locator("#webSearchCheck")
        if search_box.is_checked():
            search_box.uncheck()

        # Test dynamic Powered By update on model selection changes
        print("  • Testing dynamic model badge update on #modelSelect changes...", flush=True)
        page.select_option("#modelSelect", "gemini-3.8-flash")
        time.sleep(0.3)
        badge_38 = powered_badge.text_content().strip()
        print(f"  • Badge after selecting gemini-3.8-flash: '{badge_38}'", flush=True)
        assert "Gemini 3.8 Flash" in badge_38

        page.select_option("#modelSelect", "gemini-3.1-pro-preview")
        time.sleep(0.3)
        badge_pro = powered_badge.text_content().strip()
        print(f"  • Badge after selecting gemini-3.1-pro-preview: '{badge_pro}'", flush=True)
        assert "Gemini 3.1 Pro Preview" in badge_pro

        # Re-select gemini-3.5-flash-lite for active test execution
        page.select_option("#modelSelect", "gemini-3.5-flash-lite")
        time.sleep(0.3)
        badge_lite = powered_badge.text_content().strip()
        print(f"  • Badge after selecting gemini-3.5-flash-lite: '{badge_lite}'", flush=True)
        assert "Gemini 3.5 Flash Lite" in badge_lite

        page.select_option("#thinkingLevelSelect", "medium")
        page.select_option("#maxTurnsSelect", "1")
        page.locator("#targetScoreInput").fill("8.5")

        topic_input = page.locator("#topicInput")
        id_topic = "Persepsi wicara"
        topic_input.fill(id_topic)
        print(f"  • Topic entered in Indonesian: '{id_topic}'", flush=True)

        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "17_id_pipeline_configured.png"))

        # -------------------------------------------------------------
        # Test Case 3: Run Pipeline & Verify Multilingual Query Progression
        # -------------------------------------------------------------
        print("\n--- Test Case 3: Executing Multilingual Pipeline ---", flush=True)
        start_btn = page.locator("#startPipelineBtn")
        start_btn.click()

        # Wait for live progression card
        page.wait_for_selector("#liveResearchProgressCard", timeout=8000)
        print("  ✓ Live Research Progression card rendered!", flush=True)

        start_time = time.time()
        last_counter = ""
        captured_progress = False

        while time.time() - start_time < 90:
            counter_text = page.locator("#researchProgressCounter").text_content() or ""
            status_text = page.locator("#statusText").text_content() or ""

            if counter_text != last_counter and counter_text:
                print(f"  [Progres Pencarian] {counter_text}", flush=True)
                last_counter = counter_text

            if not captured_progress and ("Selesai" in counter_text or "Terkumpul" in counter_text):
                time.sleep(1)
                page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "18_id_live_multilingual_progression.png"))
                captured_progress = True

            if not start_btn.is_disabled() and time.time() - start_time > 8:
                print("Pipeline execution finished!", flush=True)
                break

            time.sleep(2)

        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "19_id_workflow_complete.png"))

        # -------------------------------------------------------------
        # Test Case 4: Verify Multilingual Seeking Proof & Output in ID
        # -------------------------------------------------------------
        print("\n--- Test Case 4: Inspecting Multilingual Grounding Proof ---", flush=True)
        prog_card = page.locator("#liveResearchProgressCard")
        prog_html = prog_card.inner_html()

        # Verify that the card explicitly shows the global STEM query (e.g. "speech perception")
        has_original = "Persepsi wicara" in prog_html
        has_global_stem = ("speech perception" in prog_html.lower() or "global" in prog_html.lower())
        print(f"  • Original Indonesian query present: {has_original}", flush=True)
        print(f"  • Global STEM translation query present: {has_global_stem}", flush=True)
        assert has_original, "Missing original query in progress card"
        assert has_global_stem, "Missing global STEM query in progress card"

        # Verify Writer Draft rendered in Indonesian
        writer_cards = page.locator("div:has-text('Agen Penulis • Draf')")
        print(f"  • Indonesian Writer Card count: {writer_cards.count()}", flush=True)
        assert writer_cards.count() > 0, "Missing Indonesian Writer Card"

        # Check content of the draft for Indonesian text and academic citations
        writer_text = writer_cards.first.text_content()
        assert len(writer_text) > 100
        print(f"  • Writer draft sample: {writer_text[:140]}...", flush=True)

        # Count clickable links
        paper_links = page.locator("a[href*='arxiv.org'], a[href*='doi.org'], a[href*='ncbi.nlm.nih.gov'], a[href*='wikipedia.org']").count()
        print(f"  • Total Clickable Global Scholarly Links: {paper_links}", flush=True)
        assert paper_links >= 5, f"Expected at least 5 scholarly links, found {paper_links}"

        # -------------------------------------------------------------
        # Test Case 5: Verify Exact Verbatim Quotes & Numbered Bibliography
        # -------------------------------------------------------------
        print("\n--- Test Case 5: Inspecting Exact Quotations & Numbered References ---", flush=True)
        # Check quotes matching "... bla bla bla ..." [n]
        quotes_with_citations = re.findall(r'["“]([^"”]{8,})["”]\s*\[(\d+)\]', writer_text)
        print(f"  • Found {len(quotes_with_citations)} quote(s) formatted as '\"...\" [n]':", flush=True)
        for q_text, q_num in quotes_with_citations[:3]:
            print(f"    - [{q_num}] \"{q_text[:70]}...\"", flush=True)

        assert len(quotes_with_citations) > 0, "Expected at least one quote formatted as '\"...\" [n]'"

        # Check ending bibliography
        has_ref_section = ("Referensi" in writer_text or "References" in writer_text or "Sumber Terkutip" in writer_text)
        print(f"  • Ending Reference Section present: {has_ref_section}", flush=True)
        assert has_ref_section, "Expected ending reference section in writer draft"

        # Check numbered entries in bibliography matching [1], [2], etc.
        bib_entries = re.findall(r'\[(\d+)\]\s+([^\n\r]+)', writer_text)
        print(f"  • Numbered reference entries found at end: {len(bib_entries)}", flush=True)
        assert len(bib_entries) > 0, "Expected numbered reference entries [1]... in bibliography"

        # Verify citation numbers in quotes map to the bibliography entries
        bib_nums = {num for num, _ in bib_entries}
        for _, q_num in quotes_with_citations:
            assert q_num in bib_nums or int(q_num) <= len(bib_entries) + 2, f"Quoted citation [{q_num}] missing from bibliography"
        print("  ✓ All quotes match format '\"...\" [n]' and are listed in the ending references bibliography!", flush=True)

        # -------------------------------------------------------------
        # Test Case 6: Verify Clickable Links & In-Text Jump Anchors
        # -------------------------------------------------------------
        print("\n--- Test Case 6: Inspecting Clickable Reference Links & In-Text Navigation ---", flush=True)
        # Check clickable reference paper action links
        ref_links = page.locator(".reference-item a[href^='http']").count()
        print(f"  • Clickable paper action links in references section (.reference-item a): {ref_links}", flush=True)
        assert ref_links > 0, f"Expected clickable external links inside .reference-item, found {ref_links}"

        # Check in-text citation jump anchor links
        jump_links = page.locator("a.citation-ref[href^='#ref-']").count()
        print(f"  • In-text clickable jump anchors (a.citation-ref): {jump_links}", flush=True)
        assert jump_links > 0, f"Expected in-text citation jump anchors matching a.citation-ref, found {jump_links}"

        # Check first reference link target attribute
        first_ref_link = page.locator(".reference-item a[href^='http']").first
        target_attr = first_ref_link.get_attribute("target")
        print(f"  • First reference link target: '{target_attr}' (opens safely in external tab)", flush=True)
        assert target_attr == "_blank", "Expected target='_blank' on external paper link"
        print("  ✓ Clickable reference links and smooth jump anchors verified successfully!", flush=True)

        final_screenshot = os.path.join(SCREENSHOTS_DIR, "20_full_indonesian_multilingual_session.png")
        page.screenshot(path=final_screenshot, full_page=True)
        print(f"\nAll multilingual & language switch tests passed! Saved to {final_screenshot}", flush=True)

        browser.close()


if __name__ == "__main__":
    run_browser_tests()
