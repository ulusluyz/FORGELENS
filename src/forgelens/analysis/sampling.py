"""Sampling Engine module supporting multiple sampling algorithms on record sequences."""

import random
from enum import Enum
from typing import Any, Dict, List, Optional


class SamplingStrategy(str, Enum):
    RANDOM = "random"
    UNIFORM = "uniform"
    FIRST_LAST = "first_last"
    STRATIFIED = "stratified"


class SamplingEngine:
    """Provides methods to sample subset of rows from dataset collections."""

    @staticmethod
    def sample_rows(
        rows: List[Dict[str, Any]],
        sample_size: int = 1000,
        strategy: SamplingStrategy = SamplingStrategy.RANDOM,
        stratify_key: Optional[str] = None,
        seed: int = 42,
    ) -> List[Dict[str, Any]]:
        """Samples rows based on the requested strategy and limit."""
        if not rows or sample_size <= 0:
            return []

        total = len(rows)
        if total <= sample_size:
            return list(rows)

        rng = random.Random(seed)

        if strategy == SamplingStrategy.RANDOM:
            indices = rng.sample(range(total), sample_size)
            indices.sort()
            return [rows[i] for i in indices]

        elif strategy == SamplingStrategy.UNIFORM:
            step = total / sample_size
            indices = [int(i * step) for i in range(sample_size)]
            indices = [min(i, total - 1) for i in indices]
            return [rows[i] for i in indices]

        elif strategy == SamplingStrategy.FIRST_LAST:
            half = sample_size // 2
            first_half = rows[:half]
            second_half = rows[-(sample_size - half):]
            return first_half + second_half

        elif strategy == SamplingStrategy.STRATIFIED and stratify_key:
            groups: Dict[Any, List[Dict[str, Any]]] = {}
            for row in rows:
                val = row.get(stratify_key, "unknown")
                groups.setdefault(val, []).append(row)

            sampled: List[Dict[str, Any]] = []
            for key, group in groups.items():
                group_sample_count = max(1, int(round((len(group) / total) * sample_size)))
                if len(group) <= group_sample_count:
                    sampled.extend(group)
                else:
                    indices = rng.sample(range(len(group)), group_sample_count)
                    sampled.extend([group[i] for i in indices])

            return sampled[:sample_size]

        # Fallback to random
        indices = rng.sample(range(total), sample_size)
        indices.sort()
        return [rows[i] for i in indices]
