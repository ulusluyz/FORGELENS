# Contributing to ForgeLens

Thank you for contributing to ForgeLens!

## Development Guidelines

1. **Python Environment:** Requires Python 3.12+.
2. **Setup:**
   ```bash
   pip install -e ".[dev]"
   ```
3. **Core Principles:**
   - **No Large Downloads:** Connectors must strictly query metadata/API endpoints (such as HF Dataset Viewer).
   - **Deterministic Logic First:** Heavy statistical, language, missing-value, and duplicate checks must be executed deterministically before calling AI Providers.
   - **Key Privacy:** Never log or export raw API keys or tokens.

4. **Testing:**
   Run tests using pytest:
   ```bash
   pytest
   ```
