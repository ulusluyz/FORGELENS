"""Base Connector module for dataset and model metadata retrieval."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class RepoFileMeta(BaseModel):
    path: str
    size: Optional[int] = None
    lfs: Optional[Dict[str, Any]] = None


class DatasetMeta(BaseModel):
    repo_id: str
    author: Optional[str] = None
    sha: Optional[str] = None
    description: Optional[str] = None
    license: Optional[str] = None
    tags: List[str] = []
    configs: List[str] = []
    splits: Dict[str, List[str]] = {}
    size_bytes: Optional[int] = None
    row_count: Optional[int] = None
    readme_content: Optional[str] = None
    files: List[RepoFileMeta] = []
    private: bool = False
    gated: bool = False


class ModelMeta(BaseModel):
    repo_id: str
    author: Optional[str] = None
    sha: Optional[str] = None
    description: Optional[str] = None
    license: Optional[str] = None
    tags: List[str] = []
    pipeline_tag: Optional[str] = None
    architecture: Optional[str] = None
    parameter_count: Optional[int] = None
    context_length: Optional[int] = None
    vocab_size: Optional[int] = None
    base_model: Optional[str] = None
    languages: List[str] = []
    readme_content: Optional[str] = None
    config_json: Optional[Dict[str, Any]] = None
    tokenizer_config_json: Optional[Dict[str, Any]] = None
    files: List[RepoFileMeta] = []
    private: bool = False
    gated: bool = False


class BaseConnector(ABC):
    """Abstract connector interface for external repositories."""

    @abstractmethod
    async def get_dataset_metadata(self, repo_id: str, revision: str = "main") -> DatasetMeta:
        pass

    @abstractmethod
    async def get_dataset_rows(
        self,
        repo_id: str,
        config: str = "default",
        split: str = "train",
        offset: int = 0,
        limit: int = 100,
        revision: str = "main",
    ) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def get_model_metadata(self, repo_id: str, revision: str = "main") -> ModelMeta:
        pass
