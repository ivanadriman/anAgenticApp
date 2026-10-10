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
| 📖 **[User Guide (USER_GUIDE.md)](USER_GUIDE.md)** | Step-by-step user manual covering features, language switching, model quotas, literature grounding, exact quoting, and CTRL+F verification. |
| 🛠️ **[Developer Guide (DEVELOPER_GUIDE.md)](DEVELOPER_GUIDE.md)** | Technical reference for developers covering architecture, open API integrations, inverted index reconstruction, agent prompts, and Playwright test automation. |

---

## ✨ Key Features

- **🔄 Two-Agent Iterative Feedback Loop**:
  - **Writer Agent**: Gathers peer-reviewed sources, writes drafts, and integrates verbatim quotes with numbered citations.
  - **Critic Agent**: Meticulously audits drafts against scholarly abstracts, checking factual accuracy and formatting, outputting structured scores (1.0 to 10.0) and actionable revision items.
- **🌐 Multilingual Interface & Scientific Routing**:
  - Full support for **🇬🇧 English** and **🇮🇩 Bahasa Indonesia**.
  - Automatically translates non-English topics into global English STEM terminology for international scientific repositories while maintaining native terms for regional encyclopedias.
- **📚 Multi-Source Academic Grounding**:
  - **arXiv Preprints**: Fast-moving AI, physics, CS, and mathematics preprints.
  - **Crossref DOIs**: 150M+ verified peer-reviewed publisher articles.
  - **Semantic Scholar API**: High-impact papers with citation rankings.
  - **OpenAlex Global & Regional Catalog**: 250M+ institutional works.
  - **PubMed Central / Europe PMC**: Biomedical, health, and life-sciences literature with open abstracts.
  - **Wikipedia Encyclopedia**: Encyclopedic overviews in regional and global editions.
  - **Local Documents**: Client-side parsing of uploaded `.pdf` and `.txt` documents.
- **🔍 Verbatim Quotations & CTRL+F Verifiability**:
  - Quoted evidence is formatted as `"... exact words ..."` `[n]`.
  - Quotes are extracted character-for-character from source abstracts, allowing readers to press <kbd>Ctrl</kbd> + <kbd>F</kbd> in the source paper to instantly find the full context.
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
# English run with arXiv and PubMed
python dev_pipeline.py --topic "Speech perception" --lang en --arxiv --pubmed

# Indonesian run with all scholarly sources
python dev_pipeline.py \
  --topic "Persepsi wicara" \
  --lang id \
  --model gemini-3.8-flash \
  --arxiv --crossref --semantic-scholar --openalex --pubmed --wikipedia
```

Reports with full revision history and Critic audits are saved automatically to `output/<topic_slug>.md`.

---

## 🧪 Automated Testing

Run the automated browser test suite (Playwright):
```bash
# Install Chromium browser binary
playwright install chromium

# Run test suite
python test_browser.py
```

The test validates language switching, query translation, live progression updates, exact quotation regex formatting (`"..." [n]`), and numbered bibliography integrity.

---

## 📄 License
MIT License. Open source and free for academic and commercial use.
