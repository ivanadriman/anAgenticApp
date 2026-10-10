# 📖 User Guide: Gemini Agentic Studio

Welcome to **Gemini Agentic Studio** — an autonomous, iterative multi-agent research and composition platform powered by Google Gemini models. 

This guide provides end-users, students, researchers, technical writers, and content creators with comprehensive instructions on how to use the web application and the Python command-line interface (CLI).

---

## 🌟 Table of Contents
1. [Overview & Core Concepts](#-overview--core-concepts)
2. [Getting Started](#-getting-started)
   - [Live Web Application (Recommended)](#1-live-web-application-recommended)
   - [Local Web Browser](#2-local-web-browser)
   - [Command-Line Interface (CLI)](#3-command-line-interface-cli)
3. [Language Switcher (English & Bahasa Indonesia)](#-language-switcher)
4. [API Key Setup & Security](#-api-key-setup--security)
5. [Model Selection & Quota Health Check](#-model-selection--quota-health-check)
6. [Scholarly Literature & Reference Grounding](#-scholarly-literature--reference-grounding)
   - [Grounding Repositories](#supported-academic-sources)
   - [Multilingual Scientific Lookup](#multilingual-scientific-lookup)
   - [Local Document Upload (PDF / TXT)](#local-document-upload)
7. [Verbatim Quotations & CTRL+F Verifiability](#-verbatim-quotations--ctrlf-verifiability)
8. [The Two-Agent Collaboration Workflow](#-the-two-agent-collaboration-workflow)
   - [Writer Agent](#writer-agent)
   - [Critic Agent](#critic-agent)
   - [Iterative Loop & Approval Threshold](#iterative-refinement-loop)
9. [Reading Ergonomics, Palettes & Focus Mode](#-reading-ergonomics-palettes--focus-mode)
   - [Four Reading Color Palettes](#1-four-reading-color-palettes)
   - [Typographic Ergonomics & Reader Toolbar](#2-typographic-ergonomics--reader-toolbar)
   - [Interactive Citation Micro-Previews & Mobile Bottom Sheet Drawer](#3-interactive-citation-micro-previews--mobile-bottom-sheet-drawer)
   - [Zen Mode Focus Reading Overlay](#4-zen-mode-focus-reading-overlay)
10. [CLI Usage & Command Reference](#-cli-usage--command-reference)
11. [Troubleshooting & FAQs](#-troubleshooting--faqs)

---

## 💡 Overview & Core Concepts

Traditional AI tools often produce content in a single shot without verification, leading to potential hallucinations, shallow synthesis, or untraceable claims.

**Gemini Agentic Studio** solves this through a synchronized two-agent architecture grounded in verified academic research:
- **Writer Agent**: Gathers peer-reviewed papers and encyclopedic records, writes an in-depth draft, embeds exact verbatim quotes, and compiles a complete bibliography.
- **Critic Agent**: Acts as an uncompromising peer reviewer and editor. It audits every claim, checks verbatim quotation accuracy against source abstracts, grades the draft on a 1.0 to 10.0 scale, and provides actionable revision items.
- **Academic Grounding Engine**: Queries global scientific indexes (arXiv, PubMed / Europe PMC, Crossref, Semantic Scholar, OpenAlex, Wikipedia) in real time before writing begins.

---

## 🚀 Getting Started

### 1. Live Web Application (Recommended)
You can access the live hosted version without installing anything:
👉 **[Launch Gemini Agentic Studio on GitHub Pages](https://ivanadriman.github.io/anAgenticApp/)**

### 2. Local Web Browser
1. Clone or download the repository:
   ```bash
   git clone https://github.com/ivanadriman/anAgenticApp.git
   ```
2. Double-click [`index.html`](file:///c:/Users/kiris/OneDrive/Documents/AI%20Projects/anAgenticApp/index.html) or open it in Google Chrome, Microsoft Edge, Mozilla Firefox, or Apple Safari.
3. No server or Node.js environment is required; the app runs entirely in your browser using modern Web APIs.

### 3. Command-Line Interface (CLI)
For automated batch pipelines or terminal environments:
```bash
# Clone the repository
git clone https://github.com/ivanadriman/anAgenticApp.git
cd anAgenticApp

# Install Python dependencies
pip install -r requirements.txt

# Run the pipeline
python dev_pipeline.py --topic "Speech perception" --arxiv --pubmed
```

---

## 🌐 Language Switcher

Gemini Agentic Studio features a built-in multilingual interface toggle in the top-right header:
- **🇬🇧 EN (English)**: Standard international mode. All UI controls, prompts, writer outputs, critic reviews, and citations are rendered in English.
- **🇮🇩 ID (Bahasa Indonesia)**: Full Indonesian mode. All labels, placeholder text, status messages, writer essays, critic evaluations, and bibliography headings are localized into formal, academic Bahasa Indonesia.

> **Note on Multilingual Sources:** Switching to Bahasa Indonesia does **not** limit your research to Indonesian papers. The system automatically formulates global English STEM queries behind the scenes to retrieve international literature from PubMed, arXiv, and Semantic Scholar, and seamlessly synthesizes those findings into fluent Bahasa Indonesia.

---

## 🔑 API Key Setup & Security

To generate content, you need a Google Gemini API Key:
1. Visit **[Google AI Studio](https://aistudio.google.com/)** and click **Get API Key**.
2. Paste your API key into the **Gemini API Key** field at the top of the app.
3. Click **Save Key**.

### 🔒 Client-Side Privacy & Security Guarantee
- Your API key is stored **exclusively in your browser's private `localStorage`**.
- The key is **never transmitted to any third-party server, proxy, or backend database**.
- API calls are dispatched directly from your browser to Google's official endpoints (`generativelanguage.googleapis.com`).

---

## ⚙️ Model Selection & Quota Health Check

### Supported Models
| Model Name | Best Used For | Speed | Cost / Quota |
| :--- | :--- | :--- | :--- |
| **`gemini-3.5-flash-lite`** | High-throughput, rapid drafting, generous free tier | ⚡ Ultra Fast | Extremely economical |
| **`gemini-3.5-flash`** | Balanced general synthesis and fast reasoning | ⚡ Fast | Balanced |
| **`gemini-3.8-flash`** *(Recommended)* | Complex agentic workflows and advanced synthesis | 🚀 Fast | Standard |
| **`gemini-flash-latest`** | Always runs the latest production Flash model | ⚡ Fast | Standard |
| **`gemini-3.1-pro-preview`** | Deep philosophical analysis and complex critique | 🧠 Deliberate | Higher quota consumption |

### 🟢 Quota Health Checker
Click the **"Check All Quotas"** button next to the API key input:
- The app probes each model in parallel.
- Models with active daily quota appear under `🟢 Available (Active Quota)`.
- Models that have hit rate limits or daily quotas appear under `🔴 Quota Reached (Daily limit)`.
- It also tests the **Google Search tool** quota to let you know if live web research is available.

---

## 📚 Scholarly Literature & Reference Grounding

Before the Writer Agent drafts a single sentence, the platform compiles a verified research dossier from your selected sources:

### Supported Academic Sources
1. **📚 arXiv Preprints**: Open-access preprints in physics, computer science, mathematics, quantitative biology, and AI.
2. **🏷️ Crossref Verified DOIs**: Official digital object identifiers from over 150 million publisher-verified journals and conference proceedings.
3. **🔬 Semantic Scholar API**: High-impact academic works with citation counts and citation-graph rankings.
4. **🏛️ OpenAlex Global Catalog**: 250+ million scholarly works cataloging global and regional institutional research.
5. **🧬 PubMed Central / Europe PMC**: Millions of biomedical, health, life sciences, and clinical research papers with open full-text abstracts.
6. **📖 Wikipedia Reference**: Background encyclopedic overviews from both regional editions and the global English encyclopedia.

### Multilingual Scientific Lookup
If you enter a topic in Bahasa Indonesia (e.g., *"Persepsi wicara"* or *"Dampak kecerdasan buatan pada diagnosis medis"*):
1. The app detects the concept and generates high-impact English STEM terminology (*"speech perception auditory processing"*).
2. International scientific databases (arXiv, PubMed, Semantic Scholar) are queried with the English terminology.
3. Regional indexes (Indonesian Wikipedia, regional OpenAlex) are queried with the native terminology.
4. The live progress card displays both queries and shows real-time progress rows for each database.

### 📄 Local Document Upload
You can also ground the agent in your own documents:
- Click **"Upload PDF / Text"** and select any `.pdf` or `.txt` file.
- The document is parsed directly in your browser using PDF.js.
- Text content is extracted and injected into the dossier alongside academic papers.

---

## 🔍 Verbatim Quotations & CTRL+F Verifiability

One of the most powerful features of Gemini Agentic Studio is **exact character-for-character quoting**:

### The Problem It Solves
Often, AI summaries paraphrase findings in ways that make it difficult or impossible to locate the original context in a 30-page research paper.

### How It Works Here
1. When citing evidence or findings, the model quotes exact substrings from the authors' abstracts enclosed in double quotes:
   ```markdown
   "While the perception task dynamically uses all frequencies with more prominent peaks..." [4]
   ```
2. The bracketed number `[n]` directly indicates the citation.
3. **Instant CTRL+F Verification & Direct Clickable Links**:
   - **In-Text Citation Navigation**: Every in-text citation `[n]` is an interactive jump anchor. Clicking `[n]` smoothly navigates down to card `#ref-n` in the references section and highlights it in glowing cyan.
   - **Direct External Paper Buttons**: Every entry in the bibliography contains a prominent clickable action button: `🔗 Open Paper / Source ↗` (or `🔗 Buka Makalah / Sumber ↗`).
   - Clicking this button opens the original academic paper, publisher DOI, arXiv preprint, or PubMed article in a new tab (`target="_blank" rel="noopener noreferrer"`).
   - Press <kbd>Ctrl</kbd> + <kbd>F</kbd> (or <kbd>Cmd</kbd> + <kbd>F</kbd> on macOS) in the opened paper, paste the quoted sentence, and immediately verify the statement in its full original context.
4. **Ending References Section**:
   - At the bottom of the article, every number `[1]`, `[2]`, `[3]` is listed with author names, year, paper title, journal/source venue, and direct clickable hyperlink/DOI.

---

## 🔄 The Two-Agent Collaboration Workflow

```mermaid
sequenceDiagram
    autonumber
    actor User as User / Researcher
    participant Grounding as Scholarly Grounding
    participant Writer as Writer Agent
    participant Critic as Critic Agent

    User->>Grounding: Submit Topic & Select Sources
    Grounding->>Grounding: Query arXiv, PubMed, Crossref, Semantic Scholar, etc.
    Grounding->>Writer: Verified Dossier with Exact Abstracts
    loop Iterative Refinement Loop
        Writer->>Writer: Compose Draft with Quotes & References
        Writer->>Critic: Submit Draft for Audit
        Critic->>Critic: Audit Quotes, CTRL+F Exactness & Depth (Score 1-10)
        alt Score >= Target (e.g. 8.5)
            Critic-->>User: APPROVED! Deliver Polished Article
        else Score < Target & Turns Remaining
            Critic->>Writer: Actionable Revision Instructions
        end
    end
```

### Writer Agent
- Analyzes the research dossier and organizes content into structured Markdown sections.
- Synthesizes findings across multiple disciplines.
- Incorporates verbatim quotes with citation numbers and creates the final bibliography.

### Critic Agent
- Reviews drafts according to strict academic standards:
  - **Factual Grounding**: Does the draft align with the papers provided?
  - **Quotation Audit**: Are quotes enclosed in `"... ..."` with `[n]` citation numbers?
  - **CTRL+F Accuracy**: Are quotes verbatim substrings rather than paraphrases?
  - **Bibliography Integrity**: Does every `[n]` match an entry in the references list?
- Issues an overall score (1.0 to 10.0) and specific, numbered revision instructions if the score is below the approval threshold.

### Exporting Your Content
Once approved:
- Click **"📋 Copy Markdown"** to copy the full article and bibliography to your clipboard.
- Paste directly into Obsidian, Notion, GitHub, Google Docs, or your Markdown editor of choice.

---

## 🎨 Reading Ergonomics, Palettes & Focus Mode

Gemini Agentic Studio is designed for long-form reading comfort, scientific synthesis, and literature review. Readers can customize every visual and typographic aspect of their reading environment.

### 1. Four Reading Color Palettes
Switch between four tailored palettes in the top header:
- **📜 Warm Sepia (Paper / Kindle Style)**: Amber parchment background (`#F8F5EE`), soft charcoal text (`#2D2820`), and warm chestnut headings. Ideal for daytime reading and reducing blue light fatigue.
- **🌙 Midnight Slate (Soft Dark Mode)**: Deep blue-slate background (`#0B0F19`), high-contrast slate text (`#E2E8F0`), and electric cyan highlights. Perfect for low-light desk sessions.
- **☀️ Nordic Daylight (Editorial Light)**: Crisp, clean editorial white (`#F8FAFC`) with deep navy typography (`#0F172A`). Inspired by modern academic journals and publishing houses.
- **🖤 OLED Pure Black (AMOLED Battery Saver)**: True pitch black (`#000000`) with zinc typography (`#D4D4D8`). Maximizes OLED display power efficiency and eliminates screen glow at night.

All palettes dynamically synchronize with the mobile device's system status bar via dynamic `<meta name="theme-color">` updates, creating a seamless native app-like experience.

### 2. Typographic Ergonomics & Reader Toolbar
Every Writer draft and approved article features an interactive reader toolbar:
- **Serif vs. Sans Typeface**:
  - **Serif**: Sets typography to classic editorial serif faces (`Charter`, `Georgia`, `Baskerville`, `Cambria`) for natural rhythmic cadence in long papers.
  - **Sans**: Switches to clean, modern sans-serif typography (`Inter`, `system-ui`, `-apple-system`, `Roboto`).
- **Font Size Stepper**:
  - `A-` (Small, 15px): High data density.
  - `A` (Normal, 16.5px): Standard optimal reading size.
  - `A+` (Large, 18.5px): Enhanced legibility for long sessions or smaller screens.
- **Optimal Measure**: Content is automatically constrained to a golden reading measure of 65–75 characters per line (`max-width: 72ch`) with generous 1.74 leading to prevent eye wandering.
- **Verbatim Evidence Highlights**: Verbatim quotations `"..." [n]` are gently highlighted with custom accent borders and soft tinting, making verified empirical quotes visually distinct from general synthesis.

### 3. Interactive Citation Micro-Previews & Mobile Bottom Sheet Drawer
When reading through a draft:
- **Desktop Hover Tooltip**: Hovering your cursor over any citation pill like `[1]` or `[4]` displays a floating preview card showing the paper title, author list, publishing venue/source, and a direct `🔗 Open Paper ↗` link without needing to scroll away from your reading position.
- **Mobile Bottom Sheet Drawer**: On smartphones and touchscreens, tapping any citation pill slides up an elegant native-style bottom sheet drawer from the bottom of your screen. The drawer displays paper metadata and a large, comfortable 48px touch-target button `🔗 Buka Makalah / Open Paper ↗`. Tapping the backdrop or the close button smoothly dismisses the drawer.

### 4. Zen Mode Focus Reading Overlay
Click **`📖 Zen View`** (or **`📖 Mode Baca`** in Indonesian) on any card to enter a distraction-free, full-window reading modal:
- Expands to full dynamic viewport height (`100dvh`).
- Displays a real-time reading progress bar at the very top of the screen tracking your position through the paper.
- Retains full typography controls (`Serif/Sans`, `A-/A/A+`).
- Includes a one-click print/PDF button (`🖨️`) optimized for clean paper formatting.
- Press <kbd>Esc</kbd> anytime to return to the studio dashboard.

---

## 💻 CLI Usage & Command Reference

The command-line interface (`dev_pipeline.py`) offers full terminal automation with rich colored output and saved report artifacts.

### Basic Execution
```bash
python dev_pipeline.py --topic "Quantum computing cryptography"
```

### Full Options & Flags
```bash
python dev_pipeline.py \
  --topic "Persepsi wicara" \
  --lang id \
  --model gemini-3.8-flash \
  --thinking-level medium \
  --max-turns 2 \
  --target-score 8.5 \
  --arxiv \
  --crossref \
  --semantic-scholar \
  --openalex \
  --pubmed \
  --wikipedia \
  --doc path/to/my_paper.pdf
```

### Command Flags Reference
| Flag | Description | Default |
| :--- | :--- | :--- |
| `--topic "<string>"` | Topic, research prompt, or essay goal | `"Speech perception"` |
| `--lang {en,id}` | Language mode: `en` (English) or `id` (Bahasa Indonesia) | `en` |
| `--model <name>` | `gemini-3.8-flash`, `gemini-3.5-flash-lite`, `gemini-3.1-pro-preview` | `gemini-3.5-flash-lite` |
| `--thinking-level {low,medium,high}` | Depth of Gemini internal reasoning | `medium` |
| `--web-search` | Enable Google Search grounding | `False` |
| `--arxiv` | Enable arXiv preprints index | `False` |
| `--crossref` | Enable Crossref 150M+ verified DOI index | `False` |
| `--semantic-scholar` | Enable Semantic Scholar citation index | `False` |
| `--openalex` | Enable OpenAlex global catalog | `False` |
| `--pubmed` | Enable PubMed / Europe PMC biomedical articles | `False` |
| `--wikipedia` | Enable Wikipedia encyclopedic reference | `False` |
| `--doc <path>` | Path to a local `.pdf` or `.txt` document to ground in | `None` |
| `--max-turns <int>` | Maximum number of Writer-Critic iterations | `2` |
| `--target-score <float>` | Score threshold required for Critic approval (1.0 - 10.0) | `8.5` |

All outputs are automatically saved to `output/<topic_slug>.md` along with the full revision history and Critic review logs.

---

## ❓ Troubleshooting & FAQs

### Q: Why do I see "Quota Reached (429)" errors?
> **Answer**: Free-tier Gemini API keys have rate limits (requests per minute and daily quotas). If you encounter this, open the Model dropdown, click **"Check All Quotas"**, and select an active model (such as `gemini-3.5-flash-lite` which has high daily limits).

### Q: What if an academic API is temporarily down?
> **Answer**: Every academic source in the app has an automatic fallback:
> - If the direct Semantic Scholar API is busy, it falls back to OpenAlex citation rankings.
> - If OpenAlex arXiv is unavailable, it queries Crossref preprint DOIs.
> - If Europe PMC is unreachable, it falls back to NCBI PubMed Central.

### Q: Why does a quote say "abstract unavailable"?
> **Answer**: A small number of older or paywalled preprints do not publish open-access abstracts to metadata registries. The system still provides the verified title, author, year, and DOI link for reading.

### Q: Can I run this offline?
> **Answer**: The user interface runs locally in your browser, but querying Gemini and external academic registries requires an internet connection.
