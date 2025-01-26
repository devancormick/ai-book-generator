#!/usr/bin/env python3
"""
AI Book Generator – local script to generate a murder mystery novel (20k–30k words)
using OpenAI API or local Llama via Ollama. Outputs a .docx manuscript.
"""

import os
import re
import sys
import json
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv:
    load_dotenv()

import requests
from docx import Document
from docx.shared import Pt
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OLLAMA_BASE = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

TARGET_CHAPTERS = 11
TARGET_WORDS_PER_CHAPTER = 2500
GENRE = "murder mystery"


def use_openai():
    return bool(OPENAI_API_KEY and OPENAI_API_KEY.strip())


def complete_openai(system: str, user: str) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        max_tokens=4096,
    )
    return (resp.choices[0].message.content or "").strip()


def complete_ollama(system: str, user: str) -> str:
    url = f"{OLLAMA_BASE.rstrip('/')}/api/generate"
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": f"{system}\n\n{user}",
        "stream": False,
    }
    r = requests.post(url, json=payload, timeout=600)
    r.raise_for_status()
    data = r.json()
    return (data.get("response") or "").strip()


def complete(system: str, user: str) -> str:
    if use_openai():
        return complete_openai(system, user)
    return complete_ollama(system, user)


def generate_outline() -> list[dict]:
    system = (
        "You are a professional fiction writer. Output only valid JSON, no markdown or extra text."
    )
    user = (
        f"Create a detailed outline for a {GENRE} novel with exactly {TARGET_CHAPTERS} chapters. "
        f"Each chapter should be about {TARGET_WORDS_PER_CHAPTER} words. "
        "Include: title, setting, main characters (suspects and victim), central mystery, and red herrings. "
        "Output a JSON array of objects, each with keys: \"chapter_number\" (1-based), \"title\", \"summary\" (2-4 sentences)."
    )
    raw = complete(system, user)
    raw = re.sub(r"^```\w*\n?", "", raw)
    raw = re.sub(r"\n?```\s*$", "", raw)
    try:
        outline = json.loads(raw)
    except json.JSONDecodeError:
        outline = _fallback_outline()
    if not isinstance(outline, list) or len(outline) < 10:
        outline = _fallback_outline()
    return outline[:TARGET_CHAPTERS]


def _fallback_outline() -> list[dict]:
    return [
        {"chapter_number": i, "title": f"Chapter {i}", "summary": f"Key events for chapter {i}."}
        for i in range(1, TARGET_CHAPTERS + 1)
    ]


def build_story_state_summary(state: dict) -> str:
    parts = []
    if state.get("characters"):
        parts.append("Characters: " + "; ".join(state["characters"]))
    if state.get("locations"):
        parts.append("Locations: " + "; ".join(state["locations"]))
    if state.get("clues"):
        parts.append("Clues/events: " + "; ".join(state["clues"]))
    if state.get("recent_summaries"):
        parts.append("Recent chapter summaries:\n" + "\n".join(state["recent_summaries"][-3:]))
    return "\n\n".join(parts) if parts else "No prior story state."


def generate_chapter(
    chapter_spec: dict,
    full_outline: list[dict],
    story_state: dict,
    chapter_index: int,
) -> str:
    outline_text = "\n".join(
        f"Ch{n.get('chapter_number', i)}: {n.get('title', '')} – {n.get('summary', '')}"
        for i, n in enumerate(full_outline, 1)
    )
    state_summary = build_story_state_summary(story_state)

    system = (
        f"You are a professional writer of {GENRE} fiction. "
        "Write in third person past tense. Maintain continuity with the given outline and story state. "
        f"Aim for approximately {TARGET_WORDS_PER_CHAPTER} words for this chapter. "
        "Output only the chapter prose, no title or chapter number."
    )
    user = (
        f"Outline:\n{outline_text}\n\n"
        f"Story state so far:\n{state_summary}\n\n"
        f"Write chapter {chapter_index}: {chapter_spec.get('title', 'Chapter ' + str(chapter_index))}. "
        f"Summary to follow: {chapter_spec.get('summary', '')}"
    )
    return complete(system, user)


def extract_state_updates(text: str, existing: dict) -> dict:
    """Heuristic: ask model for a one-line continuity note or use existing state."""
    existing = dict(existing)
    if "characters" not in existing:
        existing["characters"] = []
    if "locations" not in existing:
        existing["locations"] = []
    if "clues" not in existing:
        existing["clues"] = []
    if "recent_summaries" not in existing:
        existing["recent_summaries"] = []
    return existing


def summarize_chapter(chapter_text: str, story_state: dict) -> str:
    system = "You are an editor. Output only a short summary (2-4 sentences) of the given chapter for continuity. No preamble."
    user = f"Summarize this chapter for continuity:\n\n{chapter_text[:3000]}"
    return complete(system, user)


def export_docx(chapters: list[tuple[str, str]], output_path: Path, title: str = "Murder Mystery"):
    doc = Document()
    doc.add_heading(title, 0)
    doc.add_paragraph("Generated manuscript – murder mystery.")
    for chapter_title, body in chapters:
        doc.add_heading(chapter_title, level=1)
        for para in body.split("\n\n"):
            para = para.strip()
            if not para:
                continue
            p = doc.add_paragraph(para)
            p.paragraph_format.space_after = Pt(12)
    doc.save(output_path)


def main():
    print("AI Book Generator – murder mystery (local script)")
    if use_openai():
        print("Using OpenAI API.")
    else:
        print(f"Using Ollama at {OLLAMA_BASE} (model: {OLLAMA_MODEL}).")
    print("Generating outline...")
    outline = generate_outline()
    print(f"Outline: {len(outline)} chapters.")

    story_state = {
        "characters": [],
        "locations": [],
        "clues": [],
        "recent_summaries": [],
    }
    chapters_out = []

    for i, spec in enumerate(outline):
        ch_num = i + 1
        print(f"Writing chapter {ch_num}/{len(outline)}...")
        text = generate_chapter(spec, outline, story_state, ch_num)
        chapters_out.append((spec.get("title", f"Chapter {ch_num}"), text))
        summary = summarize_chapter(text, story_state)
        story_state["recent_summaries"].append(f"Ch{ch_num}: {summary}")
        story_state = extract_state_updates(text, story_state)

    out_path = Path(__file__).resolve().parent / "manuscript.docx"
    export_docx(chapters_out, out_path)
    word_count = sum(len(b.split()) for _, b in chapters_out)
    print(f"Done. Manuscript saved to: {out_path}")
    print(f"Approximate word count: {word_count}")


if __name__ == "__main__":
    main()
    sys.exit(0)
