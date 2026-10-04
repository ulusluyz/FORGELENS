"""Local language detection engine using langdetect and fallback heuristics."""

import logging
import re
from typing import Dict, List, Optional
from langdetect import detect_langs, DetectorFactory

# Set seed for deterministic language detection results
DetectorFactory.seed = 42

logger = logging.getLogger(__name__)


class LocalLanguageDetector:
    """Detects text languages locally and calculates language distribution ratios."""

    TURKISH_CHARACTERS = re.compile(r"[çğıöşüÇĞİÖŞÜ]")

    @classmethod
    def detect_text_language(cls, text: str) -> Optional[str]:
        if not text or not text.strip():
            return None

        # Clean text slightly
        clean_text = text.strip()
        if len(clean_text) < 3:
            return None

        # Quick heuristic check for Turkish specific characters
        tr_chars_found = cls.TURKISH_CHARACTERS.findall(clean_text)
        if len(tr_chars_found) > 2 and ("ve" in clean_text or "bir" in clean_text or "bu" in clean_text):
            return "tr"

        try:
            langs = detect_langs(clean_text)
            if langs and langs[0].prob > 0.4:
                return langs[0].lang
        except Exception:
            pass

        return "unknown"

    @classmethod
    def analyze_language_distribution(cls, text_samples: List[str]) -> Dict[str, float]:
        """Calculates language ratio percentages from given list of text samples."""
        if not text_samples:
            return {}

        counts: Dict[str, int] = {}
        total_valid = 0

        for text in text_samples:
            lang = cls.detect_text_language(text)
            if lang:
                counts[lang] = counts.get(lang, 0) + 1
                total_valid += 1

        if total_valid == 0:
            return {}

        ratios: Dict[str, float] = {}
        for lang, count in counts.items():
            ratios[lang] = round((count / total_valid) * 100.0, 2)

        return ratios
