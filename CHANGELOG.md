# Changelog

All notable changes to ForgeLens will be documented in this file.

## [0.1.0] - 2025-10-04
### Added
- Initial release of ForgeLens AI Dataset & Model Auditor.
- Hugging Face Connector supporting metadata, dataset viewer sampling, configs, splits, and file metadata without binary downloads.
- Rule, Statistics, Sampling, and Local Deterministic Language Detection engines.
- AI Provider Layer with OpenAI and OpenAI-Compatible endpoints, token/cost budget enforcement, and AI-disabled fallback mode.
- Category scoring engine, evidence system, and audit profile framework.
- Local SQLite database storage and size-capped metadata/sample cache manager.
- Report Engine supporting JSON, Markdown, and HTML output with automatic credential redaction.
- Command-line interface (`forgelens`) and local Web Dashboard (FastAPI).
