# ForgeLens — System Architecture

ForgeLens is an open-source, independent AI dataset and model auditor. Its core principle is **remote-audit-first**: it inspects Hugging Face datasets and models without downloading large binary weight files or full dataset dumps.

## Architecture Layers

```text
                  +-----------------------------------+
                  |           UI Layer                |
                  |  (Web GUI: FastAPI / Dashboard)   |
                  |  (CLI: Typer / Terminal App)      |
                  +-----------------+-----------------+
                                    |
                                    v
                  +-----------------------------------+
                  |        Application Layer          |
                  |  - Dataset Audit Flow             |
                  |  - Model Audit Flow               |
                  |  - API & Key Management           |
                  |  - Audit Profiles Management      |
                  +-------+-----------------+---------+
                          |                 |
         +----------------+                 +----------------+
         |                                                   |
         v                                                   v
+-----------------------+                         +-----------------------+
|   Connector Layer     |                         |   AI Provider Layer   |
| - HF REST Connector   |                         | - OpenAI Provider     |
| - HF Dataset Viewer   |                         | - OpenAI-Compatible   |
| - Future Connectors   |                         |   (Ollama, vLLM, etc) |
+-----------+-----------+                         +-----------+-----------+
            |                                                 |
            v                                                 v
+-------------------------------------------------------------------------+
|                            Analysis Engine                              |
| - Rule Engine (Deterministic checks: language, structure, duplicates)   |
| - Statistics Engine (Row counts, null ratios, size metrics)            |
| - Sampling Engine (Random, Uniform, Stratified, First/Last)              |
+------------------------------------+------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                            Audit Engine                                 |
| - Evaluates profile weights, rules, and optional AI qualitative review  |
| - Calculates Category Scores & Overall Suitability Status               |
+------------------------------------+------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                            Evidence Engine                              |
| - Links every finding to concrete measurements, samples, or AI notes    |
+------------------------------------+------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                            Report Engine                                |
| - Generates structured JSON, Markdown, and HTML reports                 |
| - Redacts sensitive tokens/keys                                         |
+------------------------------------+------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                       Local Storage & Cache Layer                       |
| - SQLite database for audit history, profiles, settings, API tokens    |
| - Metadata and sample cache (size-capped, no binary weights stored)     |
+-------------------------------------------------------------------------+
```

## Modular Structure

- `forgelens/connectors/`: Abstract base connectors and Hugging Face implementation.
- `forgelens/analysis/`: Rule Engine, Statistics, Sampling, Local Language Detection.
- `forgelens/providers/`: AI Provider abstraction, OpenAI & OpenAI-compatible providers, budget controller.
- `forgelens/audit/`: Audit Engine, Evidence Engine, Scoring Engine, Profiles.
- `forgelens/reports/`: Exporters for JSON, Markdown, HTML.
- `forgelens/storage/`: SQLite database client and Cache Manager.
- `forgelens/app/`: Application layer orchestrating operations shared by GUI & CLI.
- `forgelens/cli/`: Terminal command-line tool interface.
- `forgelens/web/`: FastAPI server and Web Dashboard frontend.
