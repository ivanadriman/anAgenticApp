# Two-Agent "Writer & Critic" App 🤖✍️🔍

An autonomous multi-agent pipeline built with Python and Google's official `google-genai` SDK using `gemini-3.8-flash`.

## How It Works
1. **Writer Agent (`gemini-3.8-flash`)**: Composes the initial draft and iteratively revises it based on specific editorial feedback.
2. **Critic Agent (`gemini-3.8-flash`)**: Evaluates drafts on clarity, depth, coherence, and accuracy, returning structured scores (1-10) and actionable revision items.
3. **Orchestrator**: Coordinates turns, provides colored terminal feedback, and saves the final polished draft with an audit trail to `output/`.

---

## Supported Gemini Models
The app is configured to use Google's latest models:
- **`gemini-3.8-flash`** *(Default / Recommended)* — Ultra-fast, highly capable reasoning and agentic workflows.
- **`gemini-3.5-flash-lite`** — Ultra-fast, cost-efficient high-throughput execution.
- **`gemini-flash-latest`** — Always uses the latest production flash checkpoint.
- **`gemini-3.1-pro-preview`** — For deep reasoning and complex critique.

---

## Quickstart

### 1. Requirements
- Python 3.11+
- A Google Gemini API Key

### 2. Setup
Create a `.env` file in the project root:
```env
GEMINI_API_KEY=your_api_key_here
```

Install dependencies:
```bash
pip install -r requirements.txt
```

### 3. Run

#### Web App (GitHub Pages or Local Browser)
Simply open `index.html` in any web browser or deploy directly to GitHub Pages! You can select your model from the dropdown.

#### Python CLI Pipeline
```bash
# Default (gemini-3.8-flash)
python dev_pipeline.py

# Specify model and options
python dev_pipeline.py --model gemini-3.8-flash --topic "Guide to Git branching strategies" --max-turns 3 --target-score 8.8
```

Output reports and revision logs are automatically saved to `output/<topic_slug>.md`.
