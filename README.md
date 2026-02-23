# AI Book Generator

Local Python script that generates a 20,000–30,000 word murder mystery novel. Uses **OpenAI API** when `OPENAI_API_KEY` is set, otherwise **Llama** via **Ollama** on your machine. No SaaS, no web app, no database.

## What it does

- Generates a structured outline (10–12 chapters)
- Writes each chapter with a simple memory/summary system for continuity
- Exports the manuscript as a timestamped `.docx` (default) or `.md` file in `output/`

## Why this approach?

Generating a full 20k–30k novel in **one prompt** is not practical or reliable: context limits and single-shot length lead to drift, contradictions, and cut-offs. This script uses a **multi-step pipeline** instead:

1. **Outline** – High-level concept and a detailed outline (beats per chapter, clue placement).
2. **Chapter-by-chapter generation** – 10–12 chapters, each generated separately.
3. **Memory between chapters** – After each chapter, a summary and story state (characters, clues, timeline) are kept and fed into the next chapter prompt for continuity.
4. **Assembly** – Final manuscript is exported to `.docx`.

Word count is controlled by chapter targets (e.g. 11 chapters × ~2,200 words ≈ 24,200 words). **OpenAI** is strong for structure and style in this workflow; **Llama** (via Ollama) works too but needs enough VRAM/RAM and careful prompting—either way, generation is chunked by chapter, not one prompt.

## Requirements

- Python 3.9+
- Either:
  - **OpenAI:** set `OPENAI_API_KEY` (optional; if set, OpenAI is used), or
  - **Ollama:** [install Ollama](https://ollama.com), pull a model (e.g. `ollama pull llama3.2`), and run with no API key

## How to run

1. **Clone or copy** this folder to your computer.

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```
   On macOS/Linux: `source venv/bin/activate`

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Optional – use OpenAI:**  
   Copy `.env.example` to `.env` and set your key:
   ```bash
   OPENAI_API_KEY=sk-your-key-here
   ```
   If you skip this, the script uses Ollama (local Llama).

5. **Run the generator:**
   ```bash
   python generate_novel.py
   ```
   Options:
   | Flag | Description |
   |------|-------------|
   | `--chapters 10\|11\|12` | Number of chapters (default: 11) |
   | `--format md\|docx` | Output format (default: docx) |
   | `--output DIR` | Custom output directory (default: `./output/`) |
   | `--author NAME` | Author name shown on the manuscript byline |
   | `--model MODEL` | Override the LLM model name (e.g. `gpt-4o`, `llama3.1`) |
   | `--test` | Quick 2-chapter test run (~800 words each) |

6. **Output:** `output/manuscript_<Title>_<timestamp>.docx` (default). Use `--format md` for Markdown.

## Environment variables

| Variable          | Purpose |
|-------------------|--------|
| `OPENAI_API_KEY`  | If set, use OpenAI instead of Ollama |
| `OPENAI_MODEL`    | OpenAI model (default: `gpt-4o-mini`) |
| `OLLAMA_HOST`     | Ollama base URL (default: `http://localhost:11434`) |
| `OLLAMA_MODEL`    | Ollama model (default: `llama3.2`) |
| `OUTPUT_FORMAT`   | `docx` (default) or `md` |
| `TARGET_CHAPTERS` | 10, 11, or 12 (default: 11) |
| `TEST_RUN`        | Set to `1` for a quick 2-chapter test (same as `--test`) |

## Project status

**Private.** This is a local script for personal use.

---

## License

All rights reserved. Private use only. No redistribution or commercial use without permission.
