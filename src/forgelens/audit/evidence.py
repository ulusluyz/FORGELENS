"""Evidence Engine model separating Measurement, Evidence, and AI Interpretation."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class EvidenceItem(BaseModel):
    claim: str
    measurement: Dict[str, Any]  # Measured numeric/exact data (e.g. ratio: 93.4%)
    evidence_sample: Optional[List[Any]] = None  # Sample rows or metrics supporting claim
    ai_interpretation: Optional[str] = None  # Qualitative assessment from AI or rule


class EvidenceReport(BaseModel):
    items: List[EvidenceItem] = []

    def add_evidence(
        self,
        claim: str,
        measurement: Dict[str, Any],
        evidence_sample: Optional[List[Any]] = None,
        ai_interpretation: Optional[str] = None,
    ):
        self.items.append(
            EvidenceItem(
                claim=claim,
                measurement=measurement,
                evidence_sample=evidence_sample,
                ai_interpretation=ai_interpretation,
            )
        )
