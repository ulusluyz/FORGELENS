# ForgeLens Security Policy

## Security Model & Principles

ForgeLens is designed as a local-first, privacy-preserving AI dataset and model auditor.

### Key Management & Storage
1. **Redaction & Masking:** API Keys (OpenAI, Hugging Face Tokens, etc.) are masked in the UI (`sk-...1234`) and NEVER logged, exported to reports, or printed in CLI output/exception stack traces.
2. **Local Database Security:** Keys and configuration settings are stored in a local SQLite database file in the user's home directory (`~/.forgelens/forgelens.db`).
3. **No File Downloads:** Large dataset files and model weights (`.safetensors`, `.bin`, `.gguf`, `.pt`, `.parquet`) are NEVER downloaded to local storage automatically.
4. **Data Transmission Transparency:** When AI Provider evaluation is enabled, ForgeLens sends ONLY the sampled text records and non-sensitive metadata required for semantic evaluation. The exact sample count and payload size are reported to the user.

## Reporting Vulnerabilities
If you discover a security issue or potential vulnerability in ForgeLens, please open an issue in the project repository or notify the maintainers.
