# ForgeLens — AI Dataset & Model Auditor

**ForgeLens** is an open-source, independent audit application designed to inspect and evaluate Hugging Face AI models and datasets remotely — **without downloading large binary weight files or full dataset dumps**.

ForgeLens operates with absolute independence: it does not depend on any proprietary model family, company, or specific AI infrastructure.

---

## Key Principle — Remote Audit First (No Large File Downloads)

ForgeLens strictly enforces a **Remote-Audit-First** philosophy:

- **NO** downloading full dataset dumps (`.parquet`, `.jsonl`, ZIP/TAR archives).
- **NO** downloading model weight binaries (`.safetensors`, `.bin`, `.gguf`, `.pt`, `.pth`).
- **NO** full repository cloning.

Instead, ForgeLens uses Hugging Face's REST and Datasets Viewer APIs to inspect:
- Repository metadata, Model Cards, Dataset Cards, READMEs
- Config files (`config.json`, `tokenizer_config.json`)
- Split lists, dataset statistics, and small sampled records via API streaming endpoints
- License, tags, revisions, and commit SHAs

---

## Features & Capabilities

- **Dataset Audit:**
  - Structural metadata, column types, missing/null value analysis.
  - Deterministic duplicate check (exact & pattern duplicates).
  - Local deterministic language distribution ratios (e.g. Turkish ratio, English ratio).
  - Text quality, HTML artifacts, short/long text checks.
  - Optional AI semantic evaluation (consistency, instruction quality, synthetic data indicators).
- **Model Audit:**
  - Remote architecture inspection (`LlamaForCausalLM`, context length, vocab size).
  - Model card completeness, license identification, quantization tag detection.
  - Information categorization: `Known`, `Unknown`, `Not Available`, `Inferred`.
- **API & Token Management:**
  - Support for OpenAI and OpenAI-Compatible custom base URLs (e.g., Ollama, vLLM, LM Studio).
  - Support for optional Hugging Face tokens to audit private/gated repositories without unauthenticated rate limits.
  - Token and Cost Budget Controller (strictly stops before exceeding max tokens/cost limits).
  - Pure deterministic mode when AI providers are disabled.
  - Sensitive API key masking and automatic redaction from reports and logs.
- **Evidence Engine & Audit Profiles:**
  - Clear separation between **Measurement**, **Evidence**, and **AI Interpretation**.
  - Built-in customizable weighted audit profiles (`General Dataset`, `Turkish LLM Training`, `Instruction Dataset`, `Conversation Dataset`, `General Model Audit`).
- **Interfaces:**
  - **Local Web Dashboard:** Modern, responsive FastAPI Web GUI.
  - **Command-Line Interface (CLI):** Full CLI support via `forgelens`.
- **Report Exporters:** Export reports in JSON, Markdown, and HTML with masked API keys.

---

## Minimum System Requirements

- **Python:** 3.12 or newer
- **OS:** Linux, macOS, or Windows
- **CPU:** Standard 2-core CPU (No GPU required)
- **RAM:** 2 GB RAM minimum
- **Disk Space:** ~50 MB (No large dataset storage needed)

---

## Installation

```bash
git clone https://github.com/forgelens/forgelens.git
cd forgelens
pip install -e .
```

For development and running tests:
```bash
pip install -e ".[dev]"
```

---

## CLI Usage

### 1. Configure Provider Tokens / API Keys

```bash
# Configure Hugging Face Token (Optional - for private/gated repos)
forgelens provider configure huggingface --key hf_xxx...

# Configure OpenAI Provider API Key
forgelens provider configure openai --key sk-xxx... --model gpt-4o-mini

# List configured providers
forgelens provider list
```

### 2. Dataset Audit

```bash
# Run Dataset Audit with default profile and JSON output
forgelens dataset audit databricks/databricks-dolly-15k

# Run Dataset Audit with Turkish LLM Training profile and Markdown output
forgelens dataset audit myuser/turkish-instructions --profile "Turkish LLM Training" --output markdown
```

### 3. Model Audit

```bash
forgelens model audit meta-llama/Llama-2-7b-hf --output html
```

### 4. Audit History

```bash
forgelens audit list
```

---

## Web Dashboard Usage

Start the local Web GUI dashboard:

```bash
uvicorn forgelens.web.app:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000` in your web browser.

---

## Testing

Run the automated test suite using pytest:

```bash
pytest
```

---

## Security & Privacy

- API keys and tokens are stored in a local SQLite database (`~/.forgelens/forgelens.db`).
- Raw keys and tokens are **NEVER** written to log files, exported reports, or displayed in plain text in the UI.
- Local metadata and sample cache is size-capped and stored in `~/.forgelens/cache`.

---

## License

This project is licensed under the [MIT License](LICENSE).
