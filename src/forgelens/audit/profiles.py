"""Audit profile configuration definitions and weightings."""

from typing import Dict
from pydantic import BaseModel, Field


class AuditProfile(BaseModel):
    name: str
    description: str
    weights: Dict[str, float] = Field(
        default_factory=lambda: {
            "language": 0.20,
            "quality": 0.25,
            "structure": 0.15,
            "duplicates": 0.15,
            "documentation": 0.10,
            "safety": 0.15,
        }
    )


# Pre-configured Audit Profiles
BUILTIN_PROFILES: Dict[str, AuditProfile] = {
    "General Dataset": AuditProfile(
        name="General Dataset",
        description="Balanced audit profile for general AI dataset evaluation.",
        weights={
            "language": 0.15,
            "quality": 0.25,
            "structure": 0.20,
            "duplicates": 0.15,
            "documentation": 0.15,
            "safety": 0.10,
        },
    ),
    "Turkish LLM Training": AuditProfile(
        name="Turkish LLM Training",
        description="Profile tailored for evaluating Turkish language corpora and instruct datasets.",
        weights={
            "language": 0.30,
            "quality": 0.25,
            "structure": 0.15,
            "duplicates": 0.15,
            "documentation": 0.10,
            "safety": 0.05,
        },
    ),
    "Instruction Dataset": AuditProfile(
        name="Instruction Dataset",
        description="Focused on instruction quality, format consistency, and semantic alignment.",
        weights={
            "language": 0.10,
            "quality": 0.35,
            "structure": 0.20,
            "duplicates": 0.15,
            "documentation": 0.10,
            "safety": 0.10,
        },
    ),
    "Conversation Dataset": AuditProfile(
        name="Conversation Dataset",
        description="Evaluates dialogue flow, multi-turn consistency, and chat quality.",
        weights={
            "language": 0.15,
            "quality": 0.30,
            "structure": 0.20,
            "duplicates": 0.15,
            "documentation": 0.10,
            "safety": 0.10,
        },
    ),
    "General Model Audit": AuditProfile(
        name="General Model Audit",
        description="Profile for inspecting model cards, architecture, tokenizer, and license.",
        weights={
            "architecture": 0.25,
            "license": 0.20,
            "documentation": 0.25,
            "quantization": 0.15,
            "fine_tuning": 0.15,
        },
    ),
}
