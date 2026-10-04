"""Unit tests for Hugging Face Connector using mock HTTP client."""

import pytest
from unittest.mock import patch, MagicMock
import httpx

from forgelens.connectors.huggingface import HuggingFaceConnector, HuggingFaceConnectorError


@pytest.mark.asyncio
async def test_validate_token_valid():
    connector = HuggingFaceConnector(token="hf_mock_token_123")

    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = {"name": "test-user", "id": "12345"}

    with patch("httpx.AsyncClient.request", return_value=mock_res):
        assert await connector.validate_token() is True


@pytest.mark.asyncio
async def test_get_dataset_metadata_success():
    connector = HuggingFaceConnector()

    mock_repo_res = MagicMock()
    mock_repo_res.status_code = 200
    mock_repo_res.json.return_value = {
        "author": "mockauthor",
        "sha": "abc123sha",
        "tags": ["license:mit", "turkic"],
        "description": "Mock dataset description"
    }

    mock_readme_res = MagicMock()
    mock_readme_res.status_code = 200
    mock_readme_res.text = "# Mock Dataset Readme"

    mock_tree_res = MagicMock()
    mock_tree_res.status_code = 200
    mock_tree_res.json.return_value = [
        {"path": "data/train.parquet", "size": 1048576, "lfs": {}}
    ]

    mock_info_res = MagicMock()
    mock_info_res.status_code = 200
    mock_info_res.json.return_value = {
        "dataset_info": {
            "default": {
                "splits": {"train": {"num_examples": 5000}},
                "download_size": 200000
            }
        }
    }

    async def mock_request(method, url, **kwargs):
        if "/api/datasets/mockauthor/mockds/tree/" in url:
            return mock_tree_res
        elif "/api/datasets/mockauthor/mockds" in url:
            return mock_repo_res
        elif "/raw/main/README.md" in url:
            return mock_readme_res
        elif "/info" in url:
            return mock_info_res
        return mock_repo_res

    with patch("httpx.AsyncClient.request", side_effect=mock_request):
        meta = await connector.get_dataset_metadata("mockauthor/mockds")
        assert meta.repo_id == "mockauthor/mockds"
        assert meta.author == "mockauthor"
        assert meta.license == "mit"
        assert meta.row_count == 5000
        assert meta.readme_content == "# Mock Dataset Readme"
        assert len(meta.files) == 1
        assert meta.files[0].path == "data/train.parquet"


@pytest.mark.asyncio
async def test_get_dataset_rows():
    connector = HuggingFaceConnector()

    mock_rows_res = MagicMock()
    mock_rows_res.status_code = 200
    mock_rows_res.json.return_value = {
        "rows": [
            {"row": {"id": 1, "text": "Merhaba dunya"}},
            {"row": {"id": 2, "text": "Hello world"}}
        ]
    }

    with patch("httpx.AsyncClient.request", return_value=mock_rows_res):
        rows = await connector.get_dataset_rows("mock/ds", limit=2)
        assert len(rows) == 2
        assert rows[0]["text"] == "Merhaba dunya"


@pytest.mark.asyncio
async def test_get_model_metadata_success():
    connector = HuggingFaceConnector()

    mock_repo_res = MagicMock()
    mock_repo_res.status_code = 200
    mock_repo_res.json.return_value = {
        "author": "modelauthor",
        "sha": "modelsha123",
        "tags": ["license:apache-2.0", "tr"],
        "pipeline_tag": "text-generation"
    }

    mock_cfg_res = MagicMock()
    mock_cfg_res.status_code = 200
    mock_cfg_res.json.return_value = {
        "architectures": ["LlamaForCausalLM"],
        "max_position_embeddings": 4096,
        "vocab_size": 32000
    }

    mock_tree_res = MagicMock()
    mock_tree_res.status_code = 200
    mock_tree_res.json.return_value = [
        {"path": "model.safetensors", "size": 7000000000}
    ]

    async def mock_request(method, url, **kwargs):
        if "config.json" in url:
            return mock_cfg_res
        elif "/tree/" in url:
            return mock_tree_res
        elif "/api/models/" in url:
            return mock_repo_res
        res = MagicMock()
        res.status_code = 404
        return res

    with patch("httpx.AsyncClient.request", side_effect=mock_request):
        meta = await connector.get_model_metadata("modelauthor/llm")
        assert meta.repo_id == "modelauthor/llm"
        assert meta.architecture == "LlamaForCausalLM"
        assert meta.context_length == 4096
        assert meta.vocab_size == 32000
        assert meta.license == "apache-2.0"
        assert len(meta.files) == 1


@pytest.mark.asyncio
async def test_connector_http_error():
    connector = HuggingFaceConnector()
    mock_err_res = MagicMock()
    mock_err_res.status_code = 404

    with patch("httpx.AsyncClient.request", return_value=mock_err_res):
        with pytest.raises(HuggingFaceConnectorError):
            await connector.get_dataset_metadata("nonexistent/dataset")
