# Gemini Agentic Studio 🤖✍️🔬

An autonomous, iterative multi-agent research and composition platform grounded in peer-reviewed academic literature, powered by Google Gemini models.

Built with dual implementations:
1. **🌐 Web Application (`index.html`)**: Client-side single-page app running in modern browsers, deployable directly to GitHub Pages.
2. **💻 Python CLI Pipeline (`dev_pipeline.py`)**: Terminal workflow built with Google's official `google-genai` SDK, `pydantic`, and `rich`.

👉 **[Launch Live Web Application](https://ivanadriman.github.io/anAgenticApp/)**

---

## 📚 Documentation

| Document | Purpose & Audience |
| :--- | :--- |
| 🎯 **[Use Cases Guide (USE_CASES.md)](USE_CASES.md)** | Real-world applications, user personas, recommended pipeline configurations, prompt examples, and chatbot comparison matrix. |
| 📖 **[User Guide (USER_GUIDE.md)](USER_GUIDE.md)** | Step-by-step user manual covering features, language switching, model quotas, literature grounding, exact quoting, and CTRL+F verification. |
| 🛠️ **[Developer Guide (DEVELOPER_GUIDE.md)](DEVELOPER_GUIDE.md)** | Technical reference for developers covering architecture, open API integrations, inverted index reconstruction, agent prompts, and Playwright test automation. |

---

## ✨ Key Features

- **🔄 Two-Agent Iterative Feedback Loop**:
  - **Writer Agent**: Gathers peer-reviewed sources, writes drafts, and integrates verbatim quotes with numbered citations.
  - **Critic Agent**: Meticulously audits drafts against scholarly abstracts, checking factual accuracy and formatting, outputting structured scores (1.0 to 10.0) and actionable revision items.
- **🛡️ 3-Layer Publication Integrity Auditor (`source-checking-guide.md`)**:
  - Audits drafts against 11 rigorous publication criteria across source ceiling, construct alignment, sample scope, and the Verb Ladder (downgrading causal verbs to correlational).
  - Automatically triggers targeted surgical paragraph patching or full rebuilds until achieving a 100% Verified Seal.
- **🌐 Multilingual Interface & Scientific Routing**:
  - Full support for **🇬🇧 English** and **🇮🇩 Bahasa Indonesia**.
  - Automatically translates non-English topics into global English STEM terminology for international scientific repositories while maintaining native terms for regional encyclopedias.
- **📚 13-Source Academic & Technical Grounding Suite**:
  - **arXiv Preprints**: Fast-moving AI, physics, CS, and mathematics preprints.
  - **Semantic Scholar API**: High-impact papers with citation rankings and AI summaries.
  - **PubMed Central / Europe PMC**: Biomedical, health, and clinical life-sciences literature.
  - **OpenAlex Global & Regional Catalog**: 250M+ global works and institutional author networks.
  - **Crossref DOIs**: 150M+ verified peer-reviewed publisher articles and official cross-citations.
  - **Wikipedia Reference**: Foundational encyclopedic overviews in regional and global editions.
  - **Google Scholar**: Universal academic literature indexing with 1-click citation lookup.
  - **IEEE Xplore**: Specialized electrical engineering, hardware, robotics, and computing papers.
  - **SSRN**: Economics, finance, policy, law, and social science research working papers.
  - **CORE**: Open-access full-text PDFs aggregated across global university repositories.
  - **DOAJ**: Peer-reviewed open-access journal catalog with universal CORS endpoints.
  - **SpringerLink**: Peer-reviewed journals and scientific book chapters across STEM disciplines.
  - **Google Patents**: International patent filings, technical claims, and engineering specifications.
  - **Local Documents**: Client-side parsing of uploaded `.pdf` and `.txt` documents via PDF.js.
- **🔍 Verbatim Quotations & W3C Deep Text-Fragment Highlighting**:
  - Quoted evidence is formatted as `"... exact words ..."` `[n]` character-for-character from source abstracts, enabling instant <kbd>Ctrl</kbd> + <kbd>F</kbd> verification.
  - Generates W3C Scroll-to-Text Fragment deep links (`#:~:text=start,end`) taking readers directly to highlighted target passages on source publisher pages.
  - Interactive Citation Inspector modal and mobile bottom sheet for instant abstract preview and 1-click quote copying.
  - Numbered bibliography at the end (`## 📚 Referensi & Sumber Terkutip` / `## 📚 References & Cited Sources`) mapping every `[n]` citation.
- **🚦 Client-Side Quota Probing**:
  - Tests daily quotas across all Gemini models in real time, sorting available models from exhausted ones.

---

## 🚀 Quickstart

### 1. Web Application
Simply open [`index.html`](index.html) in your browser or visit the **[Live Hosted App](https://ivanadriman.github.io/anAgenticApp/)**. Enter your Gemini API key from [Google AI Studio](https://aistudio.google.com/) and begin researching!

### 2. Python CLI Pipeline

#### Setup
```bash
git clone https://github.com/ivanadriman/anAgenticApp.git
cd anAgenticApp

# Create environment file
echo "GEMINI_API_KEY=your_gemini_api_key" > .env

# Install dependencies
pip install -r requirements.txt
```

#### Run CLI Pipeline
```bash
# English run with arXiv, IEEE, and Google Scholar
python dev_pipeline.py --topic "Robotic grasping algorithms" --lang en --arxiv --ieee --google-scholar

# Indonesian run with multi-source engineering & medical grounding
python dev_pipeline.py \
  --topic "Persepsi wicara" \
  --lang id \
  --model gemini-3.8-flash \
  --arxiv --crossref --semantic-scholar --openalex --pubmed --wikipedia --doaj --springer
```

Reports with full revision history and Critic audits are saved automatically to `output/<topic_slug>.md`.

---

## 🧪 Automated Testing

### 1. Offline Unit Tests (Pytest)
Run the 59 offline unit tests (zero network, zero API key required):
```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

### 2. Browser Integration Tests (Playwright)
Run the browser test suite in headless Chromium:
```bash
# Install Chromium browser binary (first time only)
playwright install chromium

# Run in offline mode (UI, layout, mobile, and security regression)
python test_browser.py --no-key

# Run full live pipeline (requires GEMINI_API_KEY in environment or .env)
python test_browser.py
```

---

## 📄 License
MIT License. Open source and free for academic and commercial use.
