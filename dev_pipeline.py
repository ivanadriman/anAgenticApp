"""
Two-Agent Writer & Critic Pipeline Prototype.
Demonstrates iterative multi-agent collaboration using Gemini 3.8 Flash.
"""

import os
import sys
import re
import json
import argparse
from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from google import genai
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Load environment variables
load_dotenv()

API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is missing. Check your .env file.")

DEFAULT_MODEL = "gemini-3.8-flash"
console = Console(force_terminal=True, legacy_windows=False)
client = genai.Client(api_key=API_KEY)


class CritiqueResult(BaseModel):
    score: float = Field(description="Rating from 1.0 to 10.0")
    status: str = Field(description="'APPROVED' if score >= 8.5 else 'NEEDS_REVISION'")
    strengths: list[str] = Field(description="List of positive aspects of the draft")
    weaknesses: list[str] = Field(description="List of weak areas or flaws found")
    actionable_revisions: list[str] = Field(description="Clear, numbered instructions for the writer to improve the next draft")


def run_writer_draft(topic: str, instructions: Optional[str] = None, model: str = DEFAULT_MODEL, enable_search: bool = False, thinking_level: str = "medium") -> str:
    """Writer agent creates the first draft."""
    system_prompt = (
        "You are an expert, engaging, and articulate Writer Agent. "
        "Your goal is to produce well-structured, clear, and compelling content based on the user's prompt. "
        "Use Markdown formatting with headings and bullet points where appropriate."
    )
    if enable_search:
        system_prompt += " Use Google Search to look up up-to-date facts, data points, and references."

    user_prompt = f"Topic/Goal: {topic}\n"
    if instructions:
        user_prompt += f"Special Instructions: {instructions}\n"
    user_prompt += "Please write Draft 1."

    tools = [{"type": "google_search"}] if enable_search else None
    response = client.interactions.create(
        model=model,
        system_instruction=system_prompt,
        input=user_prompt,
        tools=tools,
        generation_config={"thinking_level": thinking_level}
    )
    return response.output_text or ""


def run_writer_revision(original_topic: str, previous_draft: str, critique: CritiqueResult, turn: int, model: str = DEFAULT_MODEL, enable_search: bool = False, thinking_level: str = "medium") -> str:
    """Writer agent revises the draft incorporating the critic's points."""
    system_prompt = (
        "You are an expert Writer Agent in an iterative feedback loop. "
        "Carefully study the Critic's feedback, weaknesses, and required action items, and address each one thoroughly "
        "while retaining the strengths of your previous draft. Deliver the updated draft in full."
    )
    if enable_search:
        system_prompt += " Use Google Search to look up up-to-date information for the Critic's points."

    revisions_formatted = "\n".join(f"- {item}" for item in critique.actionable_revisions)
    prompt = f"""
Original Topic: {original_topic}

Your Previous Draft (Draft {turn}):
\"\"\"
{previous_draft}
\"\"\"

Critic Feedback (Score: {critique.score}/10):
Weaknesses:
{chr(10).join(f"- {w}" for w in critique.weaknesses)}

Required Improvements:
{revisions_formatted}

Please write the complete revised version (Draft {turn + 1}) addressing all feedback.
"""
    tools = [{"type": "google_search"}] if enable_search else None
    response = client.interactions.create(
        model=model,
        system_instruction=system_prompt,
        input=prompt,
        tools=tools,
        generation_config={"thinking_level": thinking_level}
    )
    return response.output_text or ""


def run_critic_review(topic: str, draft: str, turn: int, model: str = DEFAULT_MODEL, thinking_level: str = "medium") -> CritiqueResult:
    """Critic agent rigorously reviews the draft and returns structured feedback."""
    system_prompt = (
        "You are a meticulous, discerning Senior Editor and Critic Agent. "
        "Evaluate drafts strictly on clarity, depth, coherence, factual grounding, tone, and engagement. "
        "Be constructive but hold a high bar. Scores above 8.5 qualify for 'APPROVED'. "
        "You MUST respond ONLY with valid JSON conforming to this schema:\n"
        "{\n"
        '  "score": float (1.0 to 10.0),\n'
        '  "status": "APPROVED" | "NEEDS_REVISION",\n'
        '  "strengths": ["string", ...],\n'
        '  "weaknesses": ["string", ...],\n'
        '  "actionable_revisions": ["string", ...]\n'
        "}"
    )

    prompt = f"""
Goal / Prompt: {topic}
Iteration Turn: {turn}

Draft to Review:
\"\"\"
{draft}
\"\"\"

Analyze the draft thoroughly and output your evaluation as a valid JSON object only.
"""

    response = client.interactions.create(
        model=model,
        system_instruction=system_prompt,
        input=prompt,
        generation_config={"thinking_level": thinking_level}
    )

    raw_text = response.output_text or ""
    # Extract JSON even if wrapped in markdown code fence
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    
    data = json.loads(cleaned)
    return CritiqueResult(**data)


def orchestrate_pipeline(topic: str, max_turns: int = 2, target_score: float = 8.5, model: str = DEFAULT_MODEL, web_search: bool = False, thinking_level: str = "medium") -> dict:
    """Coordinates the interaction loop between Writer and Critic."""
    search_label = " (🌐 Web Search Enabled)" if web_search else ""
    console.print(Panel(f"[bold cyan]Two-Agent Pipeline Initialized[/bold cyan]\n[white]Topic:[/white] {topic}\n[white]Model:[/white] {model} | [white]🧠 Thinking:[/white] {thinking_level}{search_label}", border_style="cyan"))

    history = []
    current_draft = ""
    latest_critique: Optional[CritiqueResult] = None

    for turn in range(1, max_turns + 1):
        console.rule(f"[bold yellow]Iteration {turn} / {max_turns}[/bold yellow]")

        # 1. Writer Turn
        console.print("[bold green]>>> Writer Agent is thinking & composing...[/bold green]")
        if turn == 1:
            current_draft = run_writer_draft(topic, model=model, enable_search=web_search, thinking_level=thinking_level)
        else:
            assert latest_critique is not None
            current_draft = run_writer_revision(topic, current_draft, latest_critique, turn - 1, model=model, enable_search=web_search, thinking_level=thinking_level)

        console.print(Panel(Markdown(current_draft), title=f"[bold green]Writer Agent - Draft {turn}[/bold green]", border_style="green"))

        # 2. Critic Turn
        console.print("[bold magenta]>>> Critic Agent is evaluating draft...[/bold magenta]")
        latest_critique = run_critic_review(topic, current_draft, turn, model=model, thinking_level=thinking_level)

        critique_md = (
            f"**Score:** {latest_critique.score:.1f}/10.0  \n"
            f"**Status:** `{'APPROVED' if latest_critique.score >= target_score else 'NEEDS_REVISION'}`  \n\n"
            f"**Strengths:**\n" + "\n".join(f"- {s}" for s in latest_critique.strengths) + "\n\n"
            f"**Weaknesses:**\n" + "\n".join(f"- {w}" for w in latest_critique.weaknesses) + "\n\n"
            f"**Actionable Revisions:**\n" + "\n".join(f"- {r}" for r in latest_critique.actionable_revisions)
        )
        border = "bright_green" if latest_critique.score >= target_score else "bright_yellow"
        console.print(Panel(Markdown(critique_md), title=f"[bold magenta]Critic Review (Draft {turn})[/bold magenta]", border_style=border))

        history.append({
            "turn": turn,
            "draft": current_draft,
            "score": latest_critique.score,
            "status": latest_critique.status,
            "strengths": latest_critique.strengths,
            "weaknesses": latest_critique.weaknesses,
            "actionable_revisions": latest_critique.actionable_revisions,
        })

        if latest_critique.score >= target_score:
            console.print(f"\n[bold green]✓ Approved by Critic with score {latest_critique.score:.1f} >= {target_score}![/bold green]\n")
            break
        elif turn == max_turns:
            console.print(f"\n[bold yellow]Reached maximum limit of {max_turns} iterations.[/bold yellow]\n")

    # Save to output file
    os.makedirs("output", exist_ok=True)
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", topic.strip().lower())[:40].strip("_")
    filename = os.path.join("output", f"{slug}.md")
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# Final Draft: {topic}\n\n")
        f.write(f"**Model:** `{model}`\n")
        f.write(f"**Thinking Mode:** `{thinking_level}`\n")
        f.write(f"**Web Search:** `{'Enabled' if web_search else 'Disabled'}`\n")
        f.write(f"**Final Score:** {latest_critique.score:.1f}/10.0\n")
        f.write(f"**Total Iterations:** {len(history)}\n\n")
        f.write("## Content\n\n")
        f.write(current_draft)
        f.write("\n\n---\n## Revision History & Critic Log\n\n")
        for h in history:
            f.write(f"### Draft {h['turn']} (Score: {h['score']:.1f}/10)\n")
            f.write(f"**Critic Status:** `{h['status']}`\n")
            f.write("**Actionable Feedback:**\n")
            for item in h["actionable_revisions"]:
                f.write(f"- {item}\n")
            f.write("\n")

    console.print(Panel(f"[bold cyan]Artifact saved successfully:[/bold cyan] {filename}", border_style="cyan"))
    return {
        "final_draft": current_draft,
        "score": latest_critique.score,
        "history": history,
        "saved_path": filename
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Two-Agent Writer & Critic pipeline")
    parser.add_argument("--topic", type=str, default="Explain how Agentic AI architectures work to software engineers with a concrete example", help="Prompt or topic for content")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL, choices=["gemini-3.8-flash", "gemini-3.5-flash-lite", "gemini-3.1-pro-preview", "gemini-flash-latest"], help="Gemini model to use")
    parser.add_argument("--thinking-level", type=str, default="medium", choices=["low", "medium", "high"], help="Thinking depth: low, medium, or high")
    parser.add_argument("--web-search", action="store_true", help="Enable Google Search grounding for research")
    parser.add_argument("--max-turns", type=int, default=2, help="Maximum number of refinement iterations")
    parser.add_argument("--target-score", type=float, default=8.5, help="Score threshold for approval (1-10)")

    args = parser.parse_args()
    orchestrate_pipeline(topic=args.topic, max_turns=args.max_turns, target_score=args.target_score, model=args.model, web_search=args.web_search, thinking_level=args.thinking_level)
