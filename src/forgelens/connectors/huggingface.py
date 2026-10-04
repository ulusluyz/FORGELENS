"""Hugging Face REST and Dataset Viewer API Connector."""

import logging
from typing import Any, Dict, List, Optional
import httpx

from forgelens.connectors.base import BaseConnector, DatasetMeta, ModelMeta, RepoFileMeta

logger = logging.getLogger(__name__)

HF_HUB_URL = "https://huggingface.co"
HF_DATASETS_SERVER_URL = "https://datasets-server.huggingface.co"


class HuggingFaceConnectorError(Exception):
    """Custom exception for Hugging Face connector errors."""
    pass


class HuggingFaceConnector(BaseConnector):
    """Connector for Hugging FaceHub REST API & Datasets Server.

    Strictly queries remote metadata, dataset server row endpoints, and config files
    without downloading large model binaries or full dataset dumps.
    """

    def __init__(self, token: Optional[str] = None, timeout: float = 30.0, max_retries: int = 3):
        self.token = token
        self.timeout = timeout
        self.max_retries = max_retries

    def _get_headers(self) -> Dict[str, str]:
        headers = {"User-Agent": "ForgeLens-Auditor/0.1.0"}
        if self.token and self.token.strip():
            headers["Authorization"] = f"Bearer {self.token.strip()}"
        return headers

    async def _request(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        method: str = "GET"
    ) -> httpx.Response:
        headers = self._get_headers()
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            for attempt in range(1, self.max_retries + 1):
                try:
                    res = await client.request(method, url, params=params, headers=headers)
                    if res.status_code == 401:
                        raise HuggingFaceConnectorError(
                            "Unauthorized access (401). Verify HF token or repository permissions."
                        )
                    if res.status_code == 404:
                        raise HuggingFaceConnectorError(
                            f"Repository or resource not found (404): {url}"
                        )
                    if res.status_code == 403:
                        raise HuggingFaceConnectorError(
                            "Access forbidden (403). Repository may be private or gated."
                        )
                    res.raise_for_status()
                    return res
                except (httpx.TimeoutException, httpx.NetworkError) as err:
                    if attempt == self.max_retries:
                        raise HuggingFaceConnectorError(f"Network error accessing {url}: {err}")
                except httpx.HTTPStatusError as err:
                    if attempt == self.max_retries:
                        raise HuggingFaceConnectorError(f"HTTP error {res.status_code} for {url}: {err}")

        raise HuggingFaceConnectorError(f"Failed to fetch {url} after {self.max_retries} attempts.")

    async def validate_token(self) -> bool:
        """Validates current HF Token if set."""
        if not self.token:
            return False
        try:
            res = await self._request(f"{HF_HUB_URL}/api/whoami-v2")
            data = res.json()
            return "name" in data or "id" in data
        except Exception:
            return False

    async def get_dataset_metadata(self, repo_id: str, revision: str = "main") -> DatasetMeta:
        # 1. Fetch API info from Hugging Face Hub
        repo_url = f"{HF_HUB_URL}/api/datasets/{repo_id}"
        res = await self._request(repo_url)
        data = res.json()

        author = data.get("author") or repo_id.split("/")[0] if "/" in repo_id else None
        sha = data.get("sha")
        private = data.get("private", False)
        gated = data.get("gated", False)
        tags = data.get("tags", [])

        # Extract license from tags if available
        license_str = None
        for tag in tags:
            if tag.startswith("license:"):
                license_str = tag.replace("license:", "")
                break

        # 2. Fetch README / Dataset Card
        readme_content = None
        try:
            readme_res = await self._request(f"{HF_HUB_URL}/{repo_id}/raw/{revision}/README.md")
            readme_content = readme_res.text
        except Exception:
            logger.debug(f"README not found for dataset {repo_id}")

        # 3. Fetch file list metadata
        files: List[RepoFileMeta] = []
        try:
            files_res = await self._request(f"{HF_HUB_URL}/api/datasets/{repo_id}/tree/{revision}")
            files_data = files_res.json()
            for f in files_data:
                files.append(
                    RepoFileMeta(
                        path=f.get("path", ""),
                        size=f.get("size"),
                        lfs=f.get("lfs")
                    )
                )
        except Exception:
            logger.debug(f"Failed to fetch file tree for {repo_id}")

        # 4. Fetch Configs & Splits from Datasets Server if available
        configs: List[str] = []
        splits: Dict[str, List[str]] = {}
        total_size: Optional[int] = None
        total_rows: Optional[int] = None

        try:
            config_res = await self._request(f"{HF_DATASETS_SERVER_URL}/info", params={"dataset": repo_id})
            info_data = config_res.json().get("dataset_info", {})
            for cfg_name, cfg_info in info_data.items():
                configs.append(cfg_name)
                cfg_splits = list(cfg_info.get("splits", {}).keys())
                splits[cfg_name] = cfg_splits

                # Accrue row count and size if available
                download_size = cfg_info.get("download_size", 0)
                dataset_size = cfg_info.get("dataset_size", 0)
                if download_size or dataset_size:
                    total_size = (total_size or 0) + max(download_size, dataset_size)

                for s_name, s_info in cfg_info.get("splits", {}).items():
                    if "num_examples" in s_info:
                        total_rows = (total_rows or 0) + s_info["num_examples"]
        except Exception:
            logger.debug(f"Datasets Server info endpoint unavailable for {repo_id}")

        return DatasetMeta(
            repo_id=repo_id,
            author=author,
            sha=sha,
            description=data.get("description"),
            license=license_str,
            tags=tags,
            configs=configs,
            splits=splits,
            size_bytes=total_size,
            row_count=total_rows,
            readme_content=readme_content,
            files=files,
            private=private,
            gated=gated,
        )

    async def get_dataset_rows(
        self,
        repo_id: str,
        config: str = "default",
        split: str = "train",
        offset: int = 0,
        limit: int = 100,
        revision: str = "main",
    ) -> List[Dict[str, Any]]:
        """Fetch small window of sample dataset rows via Hugging Face Datasets Viewer API."""
        url = f"{HF_DATASETS_SERVER_URL}/rows"
        params = {
            "dataset": repo_id,
            "config": config,
            "split": split,
            "offset": offset,
            "length": min(limit, 100),
        }
        res = await self._request(url, params=params)
        data = res.json()
        rows_data = data.get("rows", [])
        return [r.get("row", {}) for r in rows_data]

    async def get_model_metadata(self, repo_id: str, revision: str = "main") -> ModelMeta:
        repo_url = f"{HF_HUB_URL}/api/models/{repo_id}"
        res = await self._request(repo_url)
        data = res.json()

        author = data.get("author") or repo_id.split("/")[0] if "/" in repo_id else None
        sha = data.get("sha")
        private = data.get("private", False)
        gated = data.get("gated", False)
        tags = data.get("tags", [])
        pipeline_tag = data.get("pipeline_tag")

        license_str = None
        languages: List[str] = []
        for tag in tags:
            if tag.startswith("license:"):
                license_str = tag.replace("license:", "")
            elif tag.startswith("language:") or (len(tag) == 2 and tag.isalpha()):
                languages.append(tag.replace("language:", ""))

        # Fetch README / Model Card
        readme_content = None
        try:
            readme_res = await self._request(f"{HF_HUB_URL}/{repo_id}/raw/{revision}/README.md")
            readme_content = readme_res.text
        except Exception:
            logger.debug(f"README not found for model {repo_id}")

        # Fetch config.json if available
        config_json: Optional[Dict[str, Any]] = None
        architecture: Optional[str] = None
        parameter_count: Optional[int] = None
        context_length: Optional[int] = None
        vocab_size: Optional[int] = None
        base_model: Optional[str] = None

        try:
            cfg_res = await self._request(f"{HF_HUB_URL}/{repo_id}/raw/{revision}/config.json")
            config_json = cfg_res.json()
            if config_json:
                architectures = config_json.get("architectures")
                if architectures and isinstance(architectures, list):
                    architecture = architectures[0]
                context_length = (
                    config_json.get("max_position_embeddings")
                    or config_json.get("max_sequence_length")
                    or config_json.get("seq_len")
                )
                vocab_size = config_json.get("vocab_size")
                base_model = config_json.get("_name_or_path")
        except Exception:
            logger.debug(f"config.json not found or invalid for model {repo_id}")

        # Fetch tokenizer_config.json if available
        tokenizer_config_json: Optional[Dict[str, Any]] = None
        try:
            tok_res = await self._request(f"{HF_HUB_URL}/{repo_id}/raw/{revision}/tokenizer_config.json")
            tokenizer_config_json = tok_res.json()
        except Exception:
            logger.debug(f"tokenizer_config.json not found for model {repo_id}")

        # Fetch file tree
        files: List[RepoFileMeta] = []
        try:
            files_res = await self._request(f"{HF_HUB_URL}/api/models/{repo_id}/tree/{revision}")
            files_data = files_res.json()
            for f in files_data:
                files.append(
                    RepoFileMeta(
                        path=f.get("path", ""),
                        size=f.get("size"),
                        lfs=f.get("lfs")
                    )
                )
        except Exception:
            logger.debug(f"Failed to fetch file tree for {repo_id}")

        return ModelMeta(
            repo_id=repo_id,
            author=author,
            sha=sha,
            description=data.get("description"),
            license=license_str,
            tags=tags,
            pipeline_tag=pipeline_tag,
            architecture=architecture,
            parameter_count=parameter_count,
            context_length=context_length,
            vocab_size=vocab_size,
            base_model=base_model,
            languages=languages,
            readme_content=readme_content,
            config_json=config_json,
            tokenizer_config_json=tokenizer_config_json,
            files=files,
            private=private,
            gated=gated,
        )
