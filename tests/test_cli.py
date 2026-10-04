"""End-to-end tests for Application Layer and CLI commands."""

from typer.testing import CliRunner
from unittest.mock import patch, MagicMock

from forgelens.cli.main import app
from forgelens.connectors.huggingface import DatasetMeta, ModelMeta

runner = CliRunner()


def test_cli_provider_configure_and_list():
    # Configure provider
    res_cfg = runner.invoke(app, ["provider", "configure", "openai", "--key", "sk-test12345678901234567890"])
    assert res_cfg.exit_code == 0
    assert "Configured provider" in res_cfg.stdout

    # List providers
    res_list = runner.invoke(app, ["provider", "list"])
    assert res_list.exit_code == 0
    assert "openai" in res_list.stdout


def test_cli_dataset_audit():
    mock_ds_meta = DatasetMeta(
        repo_id="mock/cli-ds",
        configs=["default"],
        splits={"default": ["train"]},
        license="mit",
        readme_content="# Readme",
    )

    with patch("forgelens.connectors.huggingface.HuggingFaceConnector.get_dataset_metadata", return_value=mock_ds_meta), \
         patch("forgelens.connectors.huggingface.HuggingFaceConnector.get_dataset_rows", return_value=[{"text": "Sample"}]):

        res = runner.invoke(app, ["dataset", "audit", "mock/cli-ds", "--output", "json"])
        assert res.exit_code == 0
        assert "mock/cli-ds" in res.stdout
        assert "SUITABLE" in res.stdout or "REVIEW_REQUIRED" in res.stdout


def test_cli_model_audit():
    mock_model_meta = ModelMeta(
        repo_id="mock/cli-model",
        architecture="LlamaForCausalLM",
        license="apache-2.0",
        readme_content="# Model Card",
    )

    with patch("forgelens.connectors.huggingface.HuggingFaceConnector.get_model_metadata", return_value=mock_model_meta):
        res = runner.invoke(app, ["model", "audit", "mock/cli-model", "--output", "json"])
        assert res.exit_code == 0
        assert "mock/cli-model" in res.stdout


def test_cli_audit_list():
    res = runner.invoke(app, ["audit", "list"])
    assert res.exit_code == 0
    assert "Audit History" in res.stdout
