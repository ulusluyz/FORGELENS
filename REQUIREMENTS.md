# ForgeLens — Requirements Matrix

| Requirement ID | Module / Feature | Description | Status / Plan |
|---|---|---|---|
| REQ-01 | Remote Audit First | Audit datasets & models without downloading large binary files (`.safetensors`, `.bin`, `.parquet`, `.gguf`, etc.). | Core Principle |
| REQ-02 | HF Connector | Hugging Face Dataset & Model metadata, README, Dataset Viewer rows, configs, splits, statistics. | Connector Layer |
| REQ-03 | HF Auth Management | Optional HF Token management (gated/private repos), masked, non-logging, secure storage. | API Manager |
| REQ-04 | AI Provider Abstraction | Configurable AI Providers (`OpenAI`, `OpenAI-Compatible`), test connection, models list, budget limits. | Provider Layer |
| REQ-05 | Provider Disable Mode | System operates in 100% deterministic mode if AI providers are disabled. | Engine Layer |
| REQ-06 | Budget Controller | Token budget and cost limits (e.g. max 1,000 samples, 100,000 tokens). Halts when exceeded. | Provider Layer |
| REQ-07 | Rule Engine | Deterministic checks: missing values, exact/near duplicate detection, local language ratios. | Analysis Engine |
| REQ-08 | Sampling Engine | Sampling strategies: Random, Uniform, First/Last, Stratified, Custom sample sizes. | Analysis Engine |
| REQ-09 | Local Language Engine | Local deterministic language detection (e.g., `langdetect`) without sending raw data to AI. | Analysis Engine |
| REQ-10 | Evidence System | Separates Measurement, Evidence, and AI Interpretation for every claim. | Audit Engine |
| REQ-11 | Audit Profiles | Weight-based profiles (General Dataset, Turkish LLM, Instruction, Conversation, Model Audit). | Audit Engine |
| REQ-12 | Category Scoring | Category scores (0-100) and final status (`SUITABLE`, `REVIEW_REQUIRED`, `NOT_SUITABLE`, `INSUFFICIENT_DATA`). | Scoring Engine |
| REQ-13 | Reports | Export results to JSON, Markdown, and HTML. Mask all API tokens/keys. | Report Engine |
| REQ-14 | Storage & Cache | Local SQLite database for audit history and local metadata/sample cache (size-capped). | Storage Layer |
| REQ-15 | GUI | FastAPI local Web Dashboard with HTML/CSS/JS frontend. | Interface Layer |
| REQ-16 | CLI | Command-line interface (`forgelens dataset audit`, `model audit`, `provider list`, `export`). | Interface Layer |
| REQ-17 | Quality & Security | Test suite with pytest, mock network calls, sensitive key redactions, full docs. | Quality Assurance |
