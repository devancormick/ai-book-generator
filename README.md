# AI Book Generator

Local Python script that generates a 20,000–30,000 word murder mystery novel. Supports **OpenAI**, **Groq** (free), **OpenRouter** (free), or **Ollama** (local). No SaaS, no web app, no database.

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
- One of these backends (first valid key wins):

| Backend | Cost | Setup |
|---------|------|-------|
| **Groq** | Free | [console.groq.com](https://console.groq.com) → API Keys → set `GROQ_API_KEY` |
| **OpenRouter** | Free models available | [openrouter.ai](https://openrouter.ai) → Keys → set `OPENROUTER_API_KEY` |
| **OpenAI** | Paid | [platform.openai.com](https://platform.openai.com) → set `OPENAI_API_KEY` |
| **Ollama** | Free (local CPU) | [ollama.com](https://ollama.com) → `ollama pull llama3.2` |

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

4. **Set a backend key** (copy `.env.example` to `.env`, uncomment one):
   ```bash
   # Groq — free, recommended
   GROQ_API_KEY=gsk_your-key-here

   # OpenRouter — free models available
   # OPENROUTER_API_KEY=sk-or-your-key-here

   # OpenAI — paid
   # OPENAI_API_KEY=sk-your-key-here
   ```
   If no key is set, the script falls back to Ollama (local, CPU-intensive).

5. **Run the generator:**
   ```bash
   python generate_novel.py
   ```
   Options:
   | Flag | Description |
   |------|-------------|
   | `--chapters 10\|11\|12` | Number of chapters (default: 11) |
   | `--format md\|docx` | Output format (default: md) |
   | `--output DIR` | Custom output directory (default: `./output/`) |
   | `--author NAME` | Author name shown on the manuscript byline |
   | `--model MODEL` | Override the LLM model name (e.g. `gpt-4o`, `llama3.1`) |
   | `--pov first\|third` | Narrative point of view (default: first) |
   | `--test` | Quick 2-chapter test run (~800 words each) |

6. **Output:** `output/manuscript_<Title>_<timestamp>.md` (default). Use `--format docx` for Word.

## Environment variables

| Variable              | Purpose |
|-----------------------|---------|
| `GROQ_API_KEY`        | Groq cloud key — **free**, fast (priority 1 after OpenAI) |
| `GROQ_MODEL`          | Groq model (default: `llama-3.3-70b-versatile`) |
| `OPENROUTER_API_KEY`  | OpenRouter key — free models available (priority 2) |
| `OPENROUTER_MODEL`    | OpenRouter model (default: `meta-llama/llama-3.1-8b-instruct:free`) |
| `OPENAI_API_KEY`      | OpenAI key — paid, highest priority if set |
| `OPENAI_MODEL`        | OpenAI model (default: `gpt-4o-mini`) |
| `OLLAMA_HOST`         | Ollama base URL (default: `http://localhost:11434`) |
| `OLLAMA_MODEL`        | Ollama model (default: `llama3.2`) |
| `OUTPUT_FORMAT`       | `md` (default) or `docx` |
| `TARGET_CHAPTERS`     | 10, 11, or 12 (default: 11) |
| `TEST_RUN`            | Set to `1` for a quick 2-chapter test (same as `--test`) |

## Project status

**Private.** This is a local script for personal use.

---

## License

All rights reserved. Private use only. No redistribution or commercial use without permission.
