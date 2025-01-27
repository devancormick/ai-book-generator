# AI Book Generator

Local Python script that generates a 20,000–30,000 word murder mystery novel. Uses **OpenAI API** when `OPENAI_API_KEY` is set, otherwise **Llama** via **Ollama** on your machine. No SaaS, no web app, no database.

## What it does

- Generates a structured outline (10–12 chapters)
- Writes each chapter with a simple memory/summary system for continuity
- Exports the manuscript as `manuscript.docx` in the project folder

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

6. **Output:** `manuscript.docx` appears in the same folder as the script.

## Environment variables

| Variable          | Purpose |
|-------------------|--------|
| `OPENAI_API_KEY`  | If set, use OpenAI instead of Ollama |
| `OPENAI_MODEL`    | OpenAI model (default: `gpt-4o-mini`) |
| `OLLAMA_HOST`     | Ollama base URL (default: `http://localhost:11434`) |
| `OLLAMA_MODEL`    | Ollama model (default: `llama3.2`) |

## Project status

**Private.** This is a local script for personal use.

---

## License

All rights reserved. Private use only. No redistribution or commercial use without permission.
