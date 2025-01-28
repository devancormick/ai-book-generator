#!/usr/bin/env python3
"""
AI Book Generator – local script to generate a murder mystery novel (20k–30k words)
using OpenAI API or local Llama via Ollama. Outputs .md (default) or .docx.
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

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

TEST_RUN = os.environ.get("TEST_RUN", "").strip() in ("1", "true", "yes")


def _parse_format() -> str:
    parser = argparse.ArgumentParser(description="Generate a murder mystery novel.")
    parser.add_argument(
        "--format", "-f",
        choices=["md", "docx"],
        default=None,
        help="Output format: md (default) or docx",
    )
    args, _ = parser.parse_known_args()
    if args.format:
        return args.format
    raw = (os.environ.get("OUTPUT_FORMAT", "md") or "md").strip().lower()
    return "docx" if raw == "docx" else "md"


OUTPUT_FORMAT = _parse_format()
TARGET_CHAPTERS = 2 if TEST_RUN else 11
TARGET_WORDS_PER_CHAPTER = 800 if TEST_RUN else 2500
GENRE = "murder mystery"


_OPENAI_VALID: Optional[bool] = None


def _validate_openai_key() -> bool:
    """Validate OPENAI_API_KEY: format check + API ping. Cached after first call."""
    global _OPENAI_VALID
    if _OPENAI_VALID is not None:
        return _OPENAI_VALID
    key = (OPENAI_API_KEY or "").strip()
    if not key or not key.startswith("sk-") or len(key) < 32:
        _OPENAI_VALID = False
        return False
    try:
        from openai import OpenAI
        client = OpenAI(api_key=key)
        client.models.list(limit=1)
        _OPENAI_VALID = True
        return True
    except Exception:
        _OPENAI_VALID = False
        return False


def use_openai() -> bool:
    return _validate_openai_key()


def check_backend():
    """Verify we can reach the chosen backend before generating."""
    if use_openai():
        return
    try:
        r = requests.get(f"{OLLAMA_BASE.rstrip('/')}/api/tags", timeout=5)
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        print("Ollama is not running or not reachable.", file=sys.stderr)
        print(f"  {e}", file=sys.stderr)
        print(
            "  Start Ollama (e.g. run 'ollama serve' or start the Ollama app), then run this script again.",
            file=sys.stderr,
        )
        print(
            "  Or set OPENAI_API_KEY in .env to use OpenAI instead.",
            file=sys.stderr,
        )
        sys.exit(1)


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
        "Output a JSON array of objects. First object MUST include \"novel_title\": a unique, specific book title "
        "(e.g. \"The Ashford Manor Affair\", \"Death at the Winter Ball\")—never generic like \"Murder Mystery\". "
        "Each object: \"chapter_number\" (1-based), \"title\", \"summary\" (2-4 sentences)."
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
    items = [
        {"chapter_number": i, "title": f"Chapter {i}", "summary": f"Key events for chapter {i}."}
        for i in range(1, TARGET_CHAPTERS + 1)
    ]
    if items:
        items[0]["novel_title"] = "The Shadow at Thornwood Hall"
    return items


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


def export_md(chapters: list[tuple[str, str]], output_path: Path, title: str = "Murder Mystery"):
    lines = [f"# {title}\n", "*Generated manuscript – murder mystery.*\n"]
    for chapter_title, body in chapters:
        lines.append(f"\n## {chapter_title}\n\n")
        lines.append(body.strip())
        lines.append("\n\n")
    output_path.write_text("".join(lines), encoding="utf-8")


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
    if TEST_RUN:
        print("Test run: 2 short chapters (~800 words each).")
    print(f"Output format: {OUTPUT_FORMAT}")
    if use_openai():
        print("Using OpenAI API (valid key).")
    else:
        key_present = bool((OPENAI_API_KEY or "").strip())
        if key_present:
            print("OpenAI key invalid or unreachable, using Llama (Ollama).")
        else:
            print("No OpenAI key provided, using Llama (Ollama).")
        print(f"Ollama at {OLLAMA_BASE} (model: {OLLAMA_MODEL}).")
    check_backend()
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

    ext = "docx" if OUTPUT_FORMAT == "docx" else "md"
    base = "manuscript_test" if TEST_RUN else "manuscript"
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    novel_title = ""
    title_slug = ""
    for item in (outline or []):
        if isinstance(item, dict):
            raw = str(item.get("novel_title", "")).strip()
            if raw:
                novel_title = raw
                title_slug = "_" + re.sub(r"[^\w\s-]", "", raw).strip().replace(" ", "_")[:50]
            elif not novel_title and item.get("title"):
                novel_title = str(item["title"]).strip()
                title_slug = "_" + re.sub(r"[^\w\s-]", "", novel_title).strip().replace(" ", "_")[:50] if novel_title else ""
            break
    if not novel_title:
        novel_title = outline[0].get("title", "Untitled") if outline and isinstance(outline[0], dict) else "Untitled"
        title_slug = "_" + re.sub(r"[^\w\s-]", "", novel_title).strip().replace(" ", "_")[:50] if novel_title else ""
    out_name = f"{base}{title_slug}_{ts}.{ext}"
    out_dir = Path(__file__).resolve().parent / "output"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / out_name
    if OUTPUT_FORMAT == "docx":
        export_docx(chapters_out, out_path, title=novel_title)
    else:
        export_md(chapters_out, out_path, title=novel_title)
    word_count = sum(len(b.split()) for _, b in chapters_out)
    print(f"Done. Manuscript saved to: {out_path}")
    print(f"Approximate word count: {word_count}")


if __name__ == "__main__":
    main()
    sys.exit(0)
