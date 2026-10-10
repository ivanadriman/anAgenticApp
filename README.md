# Two-Agent "Writer & Critic" App 🤖✍️🔍

An autonomous multi-agent pipeline built with Python and Google's official `google-genai` SDK using `gemini-3.8-flash`.

## How It Works
1. **Writer Agent (`gemini-3.8-flash`)**: Composes the initial draft and iteratively revises it based on specific editorial feedback.
2. **Critic Agent (`gemini-3.8-flash`)**: Evaluates drafts on clarity, depth, coherence, and accuracy, returning structured scores (1-10) and actionable revision items.
3. **Orchestrator**: Coordinates turns, provides colored terminal feedback, and saves the final polished draft with an audit trail to `output/`.

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
Execute the pipeline:
```bash
# Default topic
python dev_pipeline.py

# Custom topic with options
python dev_pipeline.py --topic "Guide to Git branching strategies for teams" --max-turns 3 --target-score 8.8
```

Output reports and revision logs are automatically saved to `output/<topic_slug>.md`.
