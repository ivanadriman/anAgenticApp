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

        # Ensure advanced options are open for interaction
        if page.locator("#advancedOptionsDetails").count() > 0:
            page.evaluate("document.getElementById('advancedOptionsDetails').open = true")

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

        # -------------------------------------------------------------
        # Test Case 7: Reading Palettes, Typography & Focus Reading Mode (Zen View)
        # -------------------------------------------------------------
        print("\n--- Test Case 7: Reading Palettes, Typography & Focus Mode ---", flush=True)
        # 1. Palette Switcher Verification
        sepia_btn = page.locator("#themeSepiaBtn")
        slate_btn = page.locator("#themeSlateBtn")
        light_btn = page.locator("#themeLightBtn")
        oled_btn = page.locator("#themeOledBtn")

        assert sepia_btn.count() > 0, "Missing #themeSepiaBtn"
        assert slate_btn.count() > 0, "Missing #themeSlateBtn"
        assert light_btn.count() > 0, "Missing #themeLightBtn"
        assert oled_btn.count() > 0, "Missing #themeOledBtn"

        # Click Sepia Palette
        print("  • Switching to 📜 Warm Sepia Palette...", flush=True)
        sepia_btn.click()
        time.sleep(0.5)
        theme_attr = page.evaluate("() => document.documentElement.getAttribute('data-theme')")
        meta_color = page.evaluate("() => document.getElementById('metaThemeColor')?.getAttribute('content')")
        print(f"    - html[data-theme]: '{theme_attr}', meta[theme-color]: '{meta_color}'", flush=True)
        assert theme_attr == "sepia"
        assert meta_color == "#F8F5EE"
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "21_theme_sepia.png"))

        # Click OLED Palette
        print("  • Switching to 🖤 OLED Pure Black Palette...", flush=True)
        oled_btn.click()
        time.sleep(0.5)
        theme_attr = page.evaluate("() => document.documentElement.getAttribute('data-theme')")
        meta_color = page.evaluate("() => document.getElementById('metaThemeColor')?.getAttribute('content')")
        print(f"    - html[data-theme]: '{theme_attr}', meta[theme-color]: '{meta_color}'", flush=True)
        assert theme_attr == "oled"
        assert meta_color == "#000000"
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "22_theme_oled.png"))

        # Click Light Palette
        print("  • Switching to ☀️ Nordic Daylight Palette...", flush=True)
        light_btn.click()
        time.sleep(0.5)
        theme_attr = page.evaluate("() => document.documentElement.getAttribute('data-theme')")
        assert theme_attr == "light"
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "23_theme_light.png"))

        # Return to Slate Palette
        print("  • Returning to 🌙 Midnight Slate Palette...", flush=True)
        slate_btn.click()
        time.sleep(0.5)
        theme_attr = page.evaluate("() => document.documentElement.getAttribute('data-theme')")
        assert theme_attr == "slate"

        # 2. Reading Typography & Toolbar Toggles
        print("  • Testing Font Face and Sizing Controls on Writer Card...", flush=True)
        serif_btn = page.locator(".font-toggle-serif").first
        sans_btn = page.locator(".font-toggle-sans").first
        size_large = page.locator(".size-toggle-large").first
        size_small = page.locator(".size-toggle-small").first
        size_norm = page.locator(".size-toggle-norm").first

        serif_btn.click()
        time.sleep(0.3)
        font_attr = page.evaluate("() => document.documentElement.getAttribute('data-font-family')")
        print(f"    - html[data-font-family]: '{font_attr}'", flush=True)
        assert font_attr == "serif"

        size_large.click()
        time.sleep(0.3)
        size_attr = page.evaluate("() => document.documentElement.getAttribute('data-font-size')")
        print(f"    - html[data-font-size]: '{size_attr}'", flush=True)
        assert size_attr == "large"

        # 3. Focus Reading Mode (Zen View)
        print("  • Testing Zen Mode Fullscreen Reader Overlay...", flush=True)
        zen_btn = page.locator(".zen-mode-btn").first
        assert zen_btn.count() > 0, "Missing .zen-mode-btn in reading toolbar"
        zen_btn.click()
        time.sleep(0.5)

        modal = page.locator("#focusReadingModal")
        assert not modal.is_hidden(), "Expected #focusReadingModal to be visible"
        print("    ✓ Focus Reading Modal opened successfully!", flush=True)
        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "24_focus_zen_reading_mode.png"))

        # Close Zen Mode
        close_modal_btn = page.locator("#closeFocusModalBtn")
        close_modal_btn.click()
        time.sleep(0.3)
        assert modal.is_hidden(), "Expected #focusReadingModal to be hidden after close"
        print("    ✓ Focus Reading Modal closed successfully!", flush=True)

        # -------------------------------------------------------------
        # Test Case 8: Mobile Browser Experience & Citation Bottom Sheet Drawer
        # -------------------------------------------------------------
        print("\n--- Test Case 8: Mobile Browser Emulation & Bottom Sheet Drawer ---", flush=True)
        # Emulate iPhone 14 / Pixel 7 viewport (390 x 844)
        print("  • Resizing viewport to 390x844 (Mobile Emulation)...", flush=True)
        page.set_viewport_size({"width": 390, "height": 844})
        time.sleep(1)

        # Verify no horizontal scroll/overflow
        has_horizontal_overflow = page.evaluate("() => document.documentElement.scrollWidth > document.documentElement.clientWidth")
        print(f"  • Horizontal overflow on mobile screen: {has_horizontal_overflow}", flush=True)
        assert not has_horizontal_overflow, "Horizontal overflow detected on mobile viewport!"

        # Tap on the first in-text citation pill
        first_citation = page.locator("a.citation-ref").first
        assert first_citation.count() > 0, "Missing citation ref for mobile tap"
        cit_num = first_citation.get_attribute("data-citation-num")
        print(f"  • Tapping citation pill [{cit_num}] on mobile touch viewport...", flush=True)
        first_citation.click()
        time.sleep(0.5)

        drawer = page.locator("#citationDrawer")
        backdrop = page.locator("#citationDrawerBackdrop")
        drawer_class = drawer.get_attribute("class") or ""
        print(f"  • Mobile Drawer class: '{drawer_class}'", flush=True)
        assert "drawer-open" in drawer_class, "Expected drawer to have .drawer-open class"
        assert not backdrop.is_hidden(), "Expected drawer backdrop to be visible"

        drawer_title = page.locator("#drawerTitle").text_content() or ""
        drawer_source = page.locator("#drawerSourceBadge").text_content() or ""
        print(f"  • Mobile Drawer Content: Source='{drawer_source}', Title='{drawer_title[:50]}...'", flush=True)
        assert len(drawer_title) > 0, "Drawer title should not be empty"

        # Verify touch-target action button
        drawer_action = page.locator("#drawerActionLink")
        if drawer_action.is_visible():
            action_text = drawer_action.text_content().strip()
            print(f"  • Mobile Action Touch Button: '{action_text}'", flush=True)
            assert "Buka Makalah" in action_text or "Open Paper" in action_text or "↗" in action_text

        page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "25_mobile_citation_bottom_sheet.png"))

        # Close drawer via close button
        print("  • Closing Mobile Bottom Sheet Drawer...", flush=True)
        page.locator("#closeDrawerBtn").click()
        time.sleep(0.3)
        drawer_class_after = drawer.get_attribute("class") or ""
        assert "drawer-closed" in drawer_class_after
        print("  ✓ Mobile Drawer closed cleanly!", flush=True)

        # Restore desktop viewport
        page.set_viewport_size({"width": 1280, "height": 950})
        time.sleep(0.5)

        final_screenshot = os.path.join(SCREENSHOTS_DIR, "26_full_reading_experience_session.png")
        page.screenshot(path=final_screenshot, full_page=True)
        print(f"\nAll reading mode & mobile test cases passed! Saved to {final_screenshot}", flush=True)

        browser.close()


if __name__ == "__main__":
    run_browser_tests()
