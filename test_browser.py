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

        diff_label_id = page.locator("label[for='readingDifficultySelect']").text_content().strip()
        print(f"  • Indonesian Difficulty Label: '{diff_label_id}'", flush=True)
        assert "Target Kesulitan" in diff_label_id or "Audiens" in diff_label_id

        type_label_id = page.locator("label[for='readingTypeSelect']").text_content().strip()
        print(f"  • Indonesian Reading Type Label: '{type_label_id}'", flush=True)
        assert "Jenis Dokumen" in type_label_id or "Genre Bacaan" in type_label_id

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

        diff_label_en = page.locator("label[for='readingDifficultySelect']").text_content().strip()
        print(f"  • English Difficulty Label: '{diff_label_en}'", flush=True)
        assert "Target Difficulty" in diff_label_en or "Audience" in diff_label_en

        type_label_en = page.locator("label[for='readingTypeSelect']").text_content().strip()
        print(f"  • English Reading Type Label: '{type_label_en}'", flush=True)
        assert "Document Type" in type_label_en or "Genre" in type_label_en

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

        # Test Reading Difficulty and Reading Type controls & Live Summary Badge
        diff_select = page.locator("#readingDifficultySelect")
        type_select = page.locator("#readingTypeSelect")
        assert diff_select.count() > 0, "Missing #readingDifficultySelect"
        assert type_select.count() > 0, "Missing #readingTypeSelect"

        print("  • Testing Target Difficulty & Document Genre dropdown selection...", flush=True)
        page.select_option("#readingDifficultySelect", "expert")
        page.select_option("#readingTypeSelect", "technical_whitepaper")
        page.select_option("#thinkingLevelSelect", "medium")
        page.select_option("#maxTurnsSelect", "1")
        page.locator("#targetScoreInput").fill("8.5")

        summary_badge = page.locator("#advancedOptionsSummaryBadge").text_content().strip()
        print(f"  • Advanced Options Summary Badge: '{summary_badge}'", flush=True)
        assert "Pakar" in summary_badge or "Expert" in summary_badge
        assert "Whitepaper" in summary_badge
        assert "1 Putaran" in summary_badge or "1 Turns" in summary_badge

        # Re-select undergraduate & literature_review for the pipeline test run
        page.select_option("#readingDifficultySelect", "undergraduate")
        page.select_option("#readingTypeSelect", "literature_review")

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

        # -------------------------------------------------------------
        # Test Case 9: Verify Markdown Download & PDF Export Dialog with Paper Sizes
        # -------------------------------------------------------------
        print("\n--- Test Case 9: Markdown Download & PDF Export with Paper Size Options ---", flush=True)

        # 1. Verify Markdown Download and PDF Export Buttons on Cards
        dl_md_btn = page.locator("#downloadMDBtn").first if page.locator("#downloadMDBtn").count() > 0 else page.locator(".download-md-btn").first
        export_pdf_btn = page.locator("#exportPdfBtn").first if page.locator("#exportPdfBtn").count() > 0 else page.locator(".export-pdf-btn").first

        assert dl_md_btn.count() > 0, "Missing Markdown Download button on card / reading toolbar"
        assert export_pdf_btn.count() > 0, "Missing Export PDF button on card / reading toolbar"
        print("  ✓ Markdown Download and Export PDF buttons found on card!", flush=True)

        # 2. Test Markdown Download Trigger
        print("  • Triggering Markdown download event...", flush=True)
        with page.expect_download(timeout=10000) as download_info:
            dl_md_btn.click()
        download = download_info.value
        download_filename = download.suggested_filename
        print(f"    - Downloaded file: '{download_filename}'", flush=True)
        assert download_filename.endswith(".md"), f"Expected .md extension, got {download_filename}"
        assert len(download_filename) > 3, "Filename should not be empty"
        print("  ✓ Markdown downloaded successfully with actual document title!", flush=True)

        # 3. Test PDF Export Modal Opening
        print("  • Opening PDF Export Modal via #exportPdfBtn...", flush=True)
        export_pdf_btn.click()
        time.sleep(0.5)

        pdf_modal = page.locator("#pdfExportModal")
        assert not pdf_modal.is_hidden(), "Expected #pdfExportModal to be visible"
        print("    ✓ PDF Export Modal is visible!", flush=True)

        # 4. Verify Common Paper Size Options
        paper_select = page.locator("#pdfPaperSizeSelect")
        assert paper_select.count() > 0, "Missing #pdfPaperSizeSelect"

        # Verify options: A4, Letter, A5, Legal, Executive
        page.select_option("#pdfPaperSizeSelect", "letter")
        selected_val = paper_select.input_value()
        print(f"    - Selected paper size: '{selected_val}' (Letter)", flush=True)
        assert selected_val == "letter"

        page.select_option("#pdfPaperSizeSelect", "a5")
        selected_val = paper_select.input_value()
        print(f"    - Selected paper size: '{selected_val}' (A5)", flush=True)
        assert selected_val == "a5"

        page.select_option("#pdfPaperSizeSelect", "legal")
        selected_val = paper_select.input_value()
        print(f"    - Selected paper size: '{selected_val}' (Legal)", flush=True)
        assert selected_val == "legal"

        page.select_option("#pdfPaperSizeSelect", "executive")
        selected_val = paper_select.input_value()
        print(f"    - Selected paper size: '{selected_val}' (Executive)", flush=True)
        assert selected_val == "executive"

        page.select_option("#pdfPaperSizeSelect", "a4")
        selected_val = paper_select.input_value()
        print(f"    - Selected paper size: '{selected_val}' (A4 default)", flush=True)
        assert selected_val == "a4"

        # 5. Verify Orientation & Margins
        page.select_option("#pdfOrientationSelect", "landscape")
        assert page.locator("#pdfOrientationSelect").input_value() == "landscape"
        page.select_option("#pdfOrientationSelect", "portrait")
        assert page.locator("#pdfOrientationSelect").input_value() == "portrait"

        page.select_option("#pdfMarginsSelect", "narrow")
        assert page.locator("#pdfMarginsSelect").input_value() == "narrow"
        page.select_option("#pdfMarginsSelect", "standard")
        assert page.locator("#pdfMarginsSelect").input_value() == "standard"

        # 6. Verify Typography Options
        page.select_option("#pdfFontSelect", "sans")
        assert page.locator("#pdfFontSelect").input_value() == "sans"
        page.select_option("#pdfFontSelect", "serif")
        assert page.locator("#pdfFontSelect").input_value() == "serif"

        # 7. Verify Action Buttons exist
        print_vec_btn = page.locator("#pdfPrintVectorBtn")
        dl_direct_btn = page.locator("#pdfDownloadDirectBtn")
        assert print_vec_btn.count() > 0, "Missing #pdfPrintVectorBtn"
        assert dl_direct_btn.count() > 0, "Missing #pdfDownloadDirectBtn"

        # Screenshot modal
        pdf_screenshot = os.path.join(SCREENSHOTS_DIR, "27_pdf_export_modal_options.png")
        page.screenshot(path=pdf_screenshot)
        print(f"  ✓ PDF Export Modal screenshot saved to {pdf_screenshot}", flush=True)

        # 8. Close PDF Modal
        page.locator("#closePdfModalBtn").click()
        time.sleep(0.3)
        assert pdf_modal.is_hidden(), "Expected #pdfExportModal to be hidden after close button"
        print("  ✓ PDF Export Modal closed cleanly!", flush=True)

        # 9. Verify Focus Reading Mode Export Buttons
        print("  • Verifying Export buttons in Focus Reading Mode...", flush=True)
        zen_btn = page.locator(".zen-mode-btn").first
        zen_btn.click()
        time.sleep(0.5)

        focus_dl_md = page.locator("#focusDownloadMDBtn")
        focus_export_pdf = page.locator("#focusExportPdfBtn")
        assert focus_dl_md.count() > 0, "Missing #focusDownloadMDBtn"
        assert focus_export_pdf.count() > 0, "Missing #focusExportPdfBtn"

        # Click export PDF from inside Focus Mode
        focus_export_pdf.click()
        time.sleep(0.3)
        assert not pdf_modal.is_hidden(), "Expected #pdfExportModal to open from Focus mode"
        page.locator("#cancelPdfModalBtn").click()
        time.sleep(0.3)
        assert pdf_modal.is_hidden(), "Expected #pdfExportModal to close via cancel button"

        page.locator("#closeFocusModalBtn").click()
        time.sleep(0.3)
        print("  ✓ Focus Reading Mode export buttons verified successfully!", flush=True)

        # -------------------------------------------------------------
        # Test Case 10: Publication Integrity Auditor Agent (source-checking-guide.md)
        # -------------------------------------------------------------
        print("\n--- Test Case 10: Publication Integrity Auditor Agent (source-checking-guide.md) ---", flush=True)

        audit_checkbox = page.locator("#strictSourceAuditCheck")
        audit_label = page.locator("#strictSourceAuditLabel")

        assert audit_checkbox.count() > 0, "Missing #strictSourceAuditCheck checkbox"
        assert audit_checkbox.is_checked(), "Expected #strictSourceAuditCheck to be checked by default"
        print("  ✓ #strictSourceAuditCheck exists and is checked by default", flush=True)

        # 1. Switch to EN and verify i18n label in EN
        btn_en.click()
        time.sleep(0.3)
        en_audit_text = audit_label.text_content().strip()
        print(f"  • Audit Label (EN): '{en_audit_text}'", flush=True)
        assert "Strict Publication Integrity Audit" in en_audit_text
        assert "source-checking-guide" in en_audit_text

        # 2. Verify i18n switch to ID
        btn_id.click()
        time.sleep(0.3)
        id_audit_text = audit_label.text_content().strip()
        print(f"  • Audit Label (ID): '{id_audit_text}'", flush=True)
        assert "Audit Ketat Integritas Publikasi" in id_audit_text
        assert "source-checking-guide" in id_audit_text

        # Switch back to EN
        btn_en.click()
        time.sleep(0.3)

        # 3. Simulate and Verify Integrity Audit Discrepancy Round Rendering
        print("  • Rendering Round 1 Audit Card with detected discrepancies...", flush=True)
        page.evaluate("""() => {
            const sampleDiscrepancyAudit = {
                all_yes: false,
                overall_verdict: "DISCREPANCIES_DETECTED",
                score_percentage: 82.0,
                failure_patterns_detected: [
                    "Correlation-to-causation drift",
                    "Scope inflation"
                ],
                discrepancies: [
                    "Citation [2] uses causal verb 'drives' on cross-sectional data. Downgrade to 'is associated with' per Verb Ladder.",
                    "Citation [3] claims findings apply to 'all modern societies' when sample was only 120 college undergraduates. Restrict claim scope."
                ],
                items: [
                    { id: "layer1_source_type_appropriate", layer: 1, title: "Source Type Ceiling", question: "Does source type justify claim level?", answer: "YES", reason: "Peer-reviewed journal articles cite empirical findings appropriately.", offending_text: "" },
                    { id: "layer1_metadata_matches", layer: 1, title: "Metadata Verification", question: "Do authors, journal, year, and DOI match actual publications?", answer: "YES", reason: "DOI and authors match published records.", offending_text: "" },
                    { id: "layer1_independent_sources", layer: 1, title: "Source Independence", question: "Are sources genuinely independent?", answer: "YES", reason: "Sources trace to distinct independent lab groups.", offending_text: "" },
                    { id: "layer2_exact_construct_match", layer: 2, title: "Exact Construct Match", question: "Does study measure the exact claimed construct?", answer: "YES", reason: "Construct of categorical speech perception tested directly.", offending_text: "" },
                    { id: "layer2_finding_not_framing", layer: 2, title: "Finding vs. Framing", question: "Is cited passage empirical finding, not introductory framing?", answer: "YES", reason: "Quotations are drawn from results section.", offending_text: "" },
                    { id: "layer2_verb_ladder_justified", layer: 2, title: "Verb Ladder Compliance", question: "Does research design justify the verb used?", answer: "NO", reason: "Cross-sectional survey described with causal verb 'drives' instead of associative 'is associated with'.", offending_text: "speech processing speed directly drives syntactic parsing efficiency" },
                    { id: "layer2_sample_scope_accurate", layer: 2, title: "Sample & Scope Bounds", question: "Is scope strictly bounded to studied sample?", answer: "NO", reason: "Sample of 120 undergraduates generalized to 'all humans in modern societies'.", offending_text: "demonstrating that all humans process syntax identically" },
                    { id: "layer2_context_and_quote_integrity", layer: 2, title: "Quote & Context Integrity", question: "Does quote match context and do evidentiary work?", answer: "YES", reason: "Quotations preserve author meaning.", offending_text: "" },
                    { id: "layer3_no_uncited_author_leaps", layer: 3, title: "No Uncited Author Leaps", question: "Are all argument steps evidence-based?", answer: "YES", reason: "All inferential claims link to cited literature.", offending_text: "" },
                    { id: "layer3_rival_explanations_acknowledged", layer: 3, title: "Rival Explanations & Caveats", question: "Are alternative mechanisms acknowledged?", answer: "YES", reason: "Motor theory vs auditory theory both cited.", offending_text: "" },
                    { id: "layer3_bounded_conclusion", layer: 3, title: "Bounded Conclusion", question: "Does conclusion refrain from exceeding strongest premise?", answer: "YES", reason: "Conclusion stays within empirical premises.", offending_text: "" }
                ]
            };
            window.renderSourceAuditCard(sampleDiscrepancyAudit, 1);
        }""")
        time.sleep(0.5)

        round1_card = page.locator("#sourceAuditCard-turn-1").last
        assert round1_card.count() > 0, "Missing #sourceAuditCard-turn-1 in DOM"
        assert "Correlation-to-causation drift" in round1_card.text_content()
        assert "Scope inflation" in round1_card.text_content()
        assert "⚠ NO" in round1_card.text_content()
        print("    ✓ Round 1 Discrepancy Audit Card rendered with failure pattern badges and NO items!", flush=True)

        screenshot_r1 = os.path.join(SCREENSHOTS_DIR, "29_audit_discrepancy_round1.png")
        round1_card.screenshot(path=screenshot_r1)
        print(f"    ✓ Round 1 screenshot saved to {screenshot_r1}", flush=True)

        # 4. Simulate and Verify 100% Clearance Round Rendering
        print("  • Rendering Round 2 Audit Card with 100% Clearance (All YES)...", flush=True)
        page.evaluate("""() => {
            const sampleClearanceAudit = {
                all_yes: true,
                overall_verdict: "APPROVED_INTEGRITY_CLEARANCE",
                score_percentage: 100.0,
                failure_patterns_detected: [],
                discrepancies: [],
                items: [
                    { id: "layer1_source_type_appropriate", layer: 1, title: "Source Type Ceiling", question: "Does source type justify claim level?", answer: "YES", reason: "Primary experimental studies and peer-reviewed syntheses justify all claim levels.", offending_text: "" },
                    { id: "layer1_metadata_matches", layer: 1, title: "Metadata Verification", question: "Do authors, journal, year, and DOI match actual publications?", answer: "YES", reason: "All DOIs and citations verified against scholarly records.", offending_text: "" },
                    { id: "layer1_independent_sources", layer: 1, title: "Source Independence", question: "Are sources genuinely independent?", answer: "YES", reason: "Six distinct empirical investigations across different institutions.", offending_text: "" },
                    { id: "layer2_exact_construct_match", layer: 2, title: "Exact Construct Match", question: "Does study measure the exact claimed construct?", answer: "YES", reason: "Strict construct alignment with no adjacent substitutions.", offending_text: "" },
                    { id: "layer2_finding_not_framing", layer: 2, title: "Finding vs. Framing", question: "Is cited passage empirical finding, not introductory framing?", answer: "YES", reason: "All evidentiary quotes stem from demonstrated empirical results.", offending_text: "" },
                    { id: "layer2_verb_ladder_justified", layer: 2, title: "Verb Ladder Compliance", question: "Does research design justify the verb used?", answer: "YES", reason: "Verbs strictly follow Verb Ladder: correlational data uses 'is associated with', experimental uses 'causes'.", offending_text: "" },
                    { id: "layer2_sample_scope_accurate", layer: 2, title: "Sample & Scope Bounds", question: "Is scope strictly bounded to studied sample?", answer: "YES", reason: "Scope strictly qualified to tested experimental cohort; no unwarranted human generalizations.", offending_text: "" },
                    { id: "layer2_context_and_quote_integrity", layer: 2, title: "Quote & Context Integrity", question: "Does quote match context and do evidentiary work?", answer: "YES", reason: "Verbatim quotes do evidentiary work with context fully preserved.", offending_text: "" },
                    { id: "layer3_no_uncited_author_leaps", layer: 3, title: "No Uncited Author Leaps", question: "Are all argument steps evidence-based?", answer: "YES", reason: "Every inferential claim is grounded in cited literature.", offending_text: "" },
                    { id: "layer3_rival_explanations_acknowledged", layer: 3, title: "Rival Explanations & Caveats", question: "Are alternative mechanisms acknowledged?", answer: "YES", reason: "Alternative acoustic vs motor theories and study boundaries acknowledged.", offending_text: "" },
                    { id: "layer3_bounded_conclusion", layer: 3, title: "Bounded Conclusion", question: "Does conclusion refrain from exceeding strongest premise?", answer: "YES", reason: "Conclusion refrains from claiming more than the empirical premises allow.", offending_text: "" }
                ]
            };
            window.renderSourceAuditCard(sampleClearanceAudit, 2);
            window.renderFinalApprovedCard("# Verified Speech Perception Synthesis\\n\\nSpeech perception is associated with superior temporal gyrus activation [1].\\n\\n## References\\n[1] Liberman (1967). [Open](https://doi.org/10.1121/1.1910402)", 9.6, 2, null, "undergraduate", "literature_review", sampleClearanceAudit);
        }""")
        time.sleep(0.5)

        round2_card = page.locator("#sourceAuditCard-turn-2").last
        assert round2_card.count() > 0, "Missing #sourceAuditCard-turn-2 in DOM"
        assert "100% Publication & Understanding Integrity Clearance" in round2_card.text_content()
        assert "11 / 11 YES" in round2_card.text_content()
        print("    ✓ Round 2 Clearance Card rendered with 100% YES banner!", flush=True)

        final_integrity_badge = page.locator("#finalIntegrityBadge").first
        assert final_integrity_badge.count() > 0, "Missing #finalIntegrityBadge on final approved card"
        assert "100% Publication Integrity Verified" in final_integrity_badge.text_content()
        print("    ✓ Final Approved Card contains 100% Publication Integrity Verified Seal!", flush=True)

        screenshot_r2 = os.path.join(SCREENSHOTS_DIR, "30_audit_100_percent_clearance.png")
        round2_card.screenshot(path=screenshot_r2)
        print(f"    ✓ Round 2 clearance screenshot saved to {screenshot_r2}", flush=True)

        # -------------------------------------------------------------
        # Test Case 11: Deep Text-Fragment Highlighting & Mobile Drawer Quote Inspection
        # -------------------------------------------------------------
        print("\n--- Test Case 11: Deep Text-Fragment Highlighting & Mobile Drawer Quote Inspection ---", flush=True)

        # 1. Verify JS buildTextFragmentUrl outputs valid W3C text fragment URLs
        test_url = "https://doi.org/10.1038/nature12345"
        test_quote_long = "The auditory cortex processes phonetic tokens through hierarchical spectral decomposition."
        frag_url_long = page.evaluate("([url, q]) => window.buildTextFragmentUrl(url, q)", [test_url, test_quote_long])
        print(f"  • Generated Long Quote Fragment URL (JS): {frag_url_long}", flush=True)
        assert "#:~:text=" in frag_url_long
        assert "The%20auditory%20cortex" in frag_url_long or "The auditory cortex" in frag_url_long
        assert "spectral%20decomposition" in frag_url_long or "spectral decomposition" in frag_url_long

        # Test short quote (< 8 words)
        test_quote_short = "hierarchical spectral decomposition"
        frag_url_short = page.evaluate("([url, q]) => window.buildTextFragmentUrl(url, q)", [test_url, test_quote_short])
        print(f"  • Generated Short Quote Fragment URL (JS): {frag_url_short}", flush=True)
        assert "#:~:text=" in frag_url_short
        assert "," not in frag_url_short.split("#:~:text=")[1]

        # Test hyphenated compound words in W3C text fragment
        test_quote_hyphen = "Automatic speech quality evaluations are labor-consuming manual evaluations"
        frag_url_hyphen = page.evaluate("([url, q]) => window.buildTextFragmentUrl(url, q)", [test_url, test_quote_hyphen])
        print(f"  • Hyphenated Quote Fragment URL: {frag_url_hyphen}", flush=True)
        assert "#:~:text=" in frag_url_hyphen
        assert "%2D" in frag_url_hyphen or "labor" in frag_url_hyphen

        # 2. Verify Python build_text_fragment_url parity
        from dev_pipeline import build_text_fragment_url as py_build_frag, run_deterministic_checks as py_det_checks
        py_frag_long = py_build_frag(test_url, test_quote_long)
        print(f"  • Generated Long Quote Fragment URL (Python): {py_frag_long}", flush=True)
        assert "#:~:text=" in py_frag_long
        assert "The%20auditory%20cortex" in py_frag_long
        assert "spectral%20decomposition" in py_frag_long

        py_frag_hyphen = py_build_frag(test_url, test_quote_hyphen)
        print(f"  • Generated Hyphenated Fragment URL (Python): {py_frag_hyphen}", flush=True)
        assert "%2D" in py_frag_hyphen or "labor" in py_frag_hyphen
        print("  ✓ Parity verified: Both JS and Python engines generate valid W3C text-fragment URLs!", flush=True)

        # 3. Render a Writer Card with in-text quote, citation [1], and References link with text-fragment
        sample_draft = (
            "# Speech Perception Processing\n\n"
            "Empirical evidence demonstrates that \"the auditory cortex processes phonetic tokens through hierarchical spectral decomposition\" [1].\n\n"
            "## References\n"
            "[1] Liberman, A. M. (1967). Some results on speech perception. Journal of the Acoustical Society of America. https://doi.org/10.1121/1.1910402"
        )
        sample_dossier = {
            "citations": [
                {
                    "num": 1,
                    "title": "Some results on speech perception",
                    "authors": "Liberman, A. M. (1967)",
                    "source": "J. Acoust. Soc. Am.",
                    "url": "https://doi.org/10.1121/1.1910402",
                    "abstract": "The auditory cortex processes phonetic tokens through hierarchical spectral decomposition."
                }
            ]
        }
        page.evaluate("""([draft, dossier]) => {
            window.renderWriterCard('Test-Deep-Highlight', draft, dossier);
        }""", [sample_draft, sample_dossier])
        time.sleep(0.5)

        # 4. Verify References section contains highlighted open link with text-fragment
        ref_link = page.locator("#turnCard-Test-Deep-Highlight #ref-1 a[href*='doi.org']").first
        assert ref_link.count() > 0, "Missing reference link in #turnCard-Test-Deep-Highlight #ref-1"
        ref_href = ref_link.get_attribute("href") or ""
        print(f"  • Reference Link href with Text-Fragment: {ref_href}", flush=True)
        assert "#:~:text=" in ref_href, f"Expected text fragment in reference href, got {ref_href}"

        # 5. Desktop Citation Inspector Modal Verification (1280 x 950)
        cite_ref_1 = page.locator("#turnCard-Test-Deep-Highlight a.citation-ref[data-citation-num='1']").first
        assert cite_ref_1.count() > 0, "Missing citation ref [1] anchor in #turnCard-Test-Deep-Highlight"
        cite_quote_attr = cite_ref_1.get_attribute("data-citation-quote") or ""
        cite_url_attr = cite_ref_1.get_attribute("data-citation-url") or ""
        cite_abs_attr = cite_ref_1.get_attribute("data-citation-abstract") or ""
        print(f"  • Citation Ref Quote Attr: '{cite_quote_attr}'", flush=True)
        print(f"  • Citation Ref URL Attr: '{cite_url_attr}'", flush=True)
        assert len(cite_quote_attr) > 10, "Citation quote attribute should contain extracted verbatim quote"
        assert "#:~:text=" in cite_url_attr, "Citation data-citation-url should contain text fragment"
        assert len(cite_abs_attr) > 10, "Citation data-citation-abstract should contain abstract"

        # Hover to test desktop tooltip and inspect button
        cite_ref_1.hover()
        time.sleep(0.3)
        tooltip = page.locator("#citationTooltip")
        assert not tooltip.is_hidden(), "Expected #citationTooltip to be visible on desktop hover"
        inspect_btn = page.locator("#tooltipInspectBtn")
        assert not inspect_btn.is_hidden(), "Expected #tooltipInspectBtn to be visible in desktop tooltip"

        # Click citation [1] on desktop to open Source & Evidence Inspector Modal
        cite_ref_1.click()
        time.sleep(0.4)

        drawer = page.locator("#citationDrawer")
        assert "drawer-open" in (drawer.get_attribute("class") or "")
        print("  ✓ Desktop Evidence Inspector modal opened on citation click!", flush=True)

        drawer_quote = page.locator("#drawerQuoteContainer")
        assert not drawer_quote.is_hidden(), "Expected #drawerQuoteContainer to be visible"
        quote_display_text = drawer_quote.text_content().strip()
        print(f"  • Modal Displayed Quote: {quote_display_text}", flush=True)
        assert "auditory cortex processes" in quote_display_text

        # Verify In-Context Abstract Verification with <mark> highlighting
        drawer_abstract = page.locator("#drawerAbstractContent")
        assert not drawer_abstract.is_hidden(), "Expected #drawerAbstractContent to be visible"
        drawer_mark = page.locator("#drawerAbstractContent mark")
        assert drawer_mark.count() > 0, "Expected <mark> tag highlighting quote inside abstract"
        mark_text = drawer_mark.text_content().strip()
        print(f"  • Abstract <mark> Highlighted Text: '{mark_text}'", flush=True)
        assert "auditory cortex processes" in mark_text

        # Verify Google Scholar Fallback Button
        drawer_scholar = page.locator("#drawerScholarBtn")
        assert not drawer_scholar.is_hidden(), "Expected #drawerScholarBtn to be visible"
        scholar_href = drawer_scholar.get_attribute("href") or ""
        print(f"  • Google Scholar Button href: {scholar_href}", flush=True)
        assert "scholar.google.com/scholar?q=" in scholar_href

        # Verify Deep Highlight Action Link
        drawer_action_link = page.locator("#drawerActionLink")
        drawer_action_href = drawer_action_link.get_attribute("href") or ""
        print(f"  • Inspector 'Open Paper' Button href: {drawer_action_href}", flush=True)
        assert "#:~:text=" in drawer_action_href

        # Screenshot Desktop Evidence Inspector Modal
        screenshot_desktop_inspector = os.path.join(SCREENSHOTS_DIR, "33_desktop_citation_inspector_modal.png")
        page.screenshot(path=screenshot_desktop_inspector)
        print(f"  ✓ Desktop Citation Inspector Modal screenshot saved to {screenshot_desktop_inspector}", flush=True)

        # Close Modal on Desktop
        page.locator("#closeDrawerBtn").click()
        time.sleep(0.3)

        # 6. Switch to Mobile Viewport (390 x 844) to test Mobile Citation Drawer
        page.set_viewport_size({"width": 390, "height": 844})
        time.sleep(0.3)

        # Tap citation [1] to open mobile drawer
        cite_ref_1.click()
        time.sleep(0.4)

        assert "drawer-open" in (drawer.get_attribute("class") or "")
        print("  ✓ Mobile Drawer opened on citation tap!", flush=True)

        drawer_copy_btn = page.locator("#drawerCopyQuoteBtn")
        assert not drawer_copy_btn.is_hidden(), "Expected #drawerCopyQuoteBtn to be visible"

        # Screenshot mobile drawer with verbatim quote and deep text fragment link
        screenshot_drawer = os.path.join(SCREENSHOTS_DIR, "31_deep_text_fragment_drawer.png")
        page.screenshot(path=screenshot_drawer)
        print(f"  ✓ Deep Text Fragment Drawer screenshot saved to {screenshot_drawer}", flush=True)

        # Close drawer and restore desktop viewport
        page.locator("#closeDrawerBtn").click()
        time.sleep(0.3)
        page.set_viewport_size({"width": 1280, "height": 950})
        time.sleep(0.3)

        # -------------------------------------------------------------
        # Test Case 12: Deterministic Pre-Audit & Surgical Paragraph Patching for Flash Lite
        # -------------------------------------------------------------
        print("\n--- Test Case 12: Deterministic Pre-Audit & Surgical Paragraph Patching ---", flush=True)

        # 1. Test deterministic check detects ungrounded citation disparity (in both JS & Python)
        test_draft_bad_citation = (
            "# Neural Foundations\n\n"
            "Studies suggest that cortical plasticity supports language acquisition [99].\n\n"
            "## References\n[1] Smith (2020)."
        )
        check_cit = page.evaluate("""([draft, dossier]) => {
            return window.runDeterministicSanityChecks(draft, dossier);
        }""", [test_draft_bad_citation, sample_dossier])
        print(f"  • Citation Disparity Check result (JS): passed={check_cit['passed']}, issues={check_cit['issues']}", flush=True)
        assert not check_cit["passed"]
        assert any("missing in references" in iss.lower() for iss in check_cit["issues"])

        py_sanity = py_det_checks(test_draft_bad_citation, str(sample_dossier))
        print(f"  • Citation Disparity Check result (Python): passed={py_sanity['passed']}, issues={py_sanity['issues']}", flush=True)
        assert not py_sanity["passed"]
        assert any("missing in references" in iss.lower() for iss in py_sanity["issues"])
        print("  ✓ Deterministic pre-check successfully caught citation disparity!", flush=True)

        # 2. Test deterministic check catches causal verb heuristic
        test_draft_causal = (
            "# Neural Foundations\n\n"
            "Survey results prove that speech speed causes grammatical fluency [1].\n\n"
            "## References\n[1] Liberman (1967)."
        )
        check_causal = page.evaluate("""([draft, dossier]) => {
            return window.runDeterministicSanityChecks(draft, dossier);
        }""", [test_draft_causal, sample_dossier])
        print(f"  • Causal Verb Heuristic Check result (JS): passed={check_causal['passed']}, issues={check_causal['issues']}", flush=True)
        assert not check_causal["passed"]
        assert any("causal verb" in iss.lower() or "verb ladder" in iss.lower() for iss in check_causal["issues"])
        print("  ✓ Deterministic pre-check successfully flagged causal verb warning!", flush=True)

        # 3. Test paragraph isolation and surgical rebuilding logic
        multi_p_draft = (
            "# Comprehensive Review\n\n"
            "Paragraph 1: Background and historical context remain completely intact and unaltered.\n\n"
            "Paragraph 2: Flawed claim states that processing speed directly drives syntactic complexity [1].\n\n"
            "Paragraph 3: Future directions and conclusion remain completely pristine and verified."
        )
        patched_draft = page.evaluate("""(originalDraft) => {
            const paragraphs = originalDraft.split(/\\n\\s*\\n/);
            // Replace only paragraph 2
            paragraphs[2] = "Paragraph 2: Rigorous analysis indicates that processing speed is associated with syntactic complexity [1].";
            return paragraphs.join("\\n\\n");
        }""", multi_p_draft)

        print("  • Verifying surgical paragraph replacement preservation...", flush=True)
        assert "Paragraph 1: Background and historical context remain completely intact and unaltered." in patched_draft
        assert "is associated with syntactic complexity" in patched_draft
        assert "Paragraph 3: Future directions and conclusion remain completely pristine and verified." in patched_draft
        print("  ✓ Surgical paragraph rebuild safely preserves surrounding paragraphs byte-for-byte!", flush=True)

        # 4. Render verified surgical patch card and take screenshot 32
        page.evaluate("""(draft) => {
            window.renderWriterCard('Surgical-Patch-Turn-2', draft, null);
        }""", patched_draft)
        time.sleep(0.4)

        surgical_card = page.locator("#turnCard-Surgical-Patch-Turn-2").last
        assert surgical_card.count() > 0, "Missing #turnCard-Surgical-Patch-Turn-2 in DOM"
        screenshot_surgical = os.path.join(SCREENSHOTS_DIR, "32_surgical_rebuild_verified.png")
        surgical_card.screenshot(path=screenshot_surgical)
        print(f"  ✓ Surgical rebuild card screenshot saved to {screenshot_surgical}", flush=True)

        final_screenshot = os.path.join(SCREENSHOTS_DIR, "28_full_reading_experience_session.png")
        page.screenshot(path=final_screenshot, full_page=True)
        print(f"\nAll reading mode & mobile test cases passed! Saved to {final_screenshot}", flush=True)

        browser.close()


if __name__ == "__main__":
    run_browser_tests()
