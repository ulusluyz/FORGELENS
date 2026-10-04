"""Statistics Engine for computing row metrics, field presence, and size measurements."""

import json
from typing import Any, Dict, List
from pydantic import BaseModel


class FieldStats(BaseModel):
    name: str
    dtype: str
    null_count: int
    null_ratio: float
    empty_str_count: int
    avg_length: float


class DatasetStatistics(BaseModel):
    total_sampled: int
    column_count: int
    field_stats: List[FieldStats]
    avg_row_char_length: float


class StatisticsEngine:
    """Computes field-level and row-level statistical measurements."""

    @staticmethod
    def calculate_dataset_statistics(rows: List[Dict[str, Any]]) -> DatasetStatistics:
        if not rows:
            return DatasetStatistics(
                total_sampled=0,
                column_count=0,
                field_stats=[],
                avg_row_char_length=0.0,
            )

        sampled_count = len(rows)
        columns = list(rows[0].keys()) if rows else []

        field_stats_list: List[FieldStats] = []
        total_chars_all_rows = 0

        for col in columns:
            null_cnt = 0
            empty_str_cnt = 0
            char_len_sum = 0
            sample_dtype = "unknown"

            for row in rows:
                val = row.get(col)
                if val is None:
                    null_cnt += 1
                elif isinstance(val, str):
                    sample_dtype = "str"
                    s_len = len(val)
                    char_len_sum += s_len
                    if s_len == 0:
                        empty_str_cnt += 1
                elif isinstance(val, (int, float)):
                    sample_dtype = "number"
                    char_len_sum += len(str(val))
                elif isinstance(val, (list, dict)):
                    sample_dtype = "json/nested"
                    char_len_sum += len(json.dumps(val))
                else:
                    char_len_sum += len(str(val))

            avg_len = round(char_len_sum / sampled_count, 2)
            null_ratio = round((null_cnt / sampled_count) * 100.0, 2)

            field_stats_list.append(
                FieldStats(
                    name=col,
                    dtype=sample_dtype,
                    null_count=null_cnt,
                    null_ratio=null_ratio,
                    empty_str_count=empty_str_cnt,
                    avg_length=avg_len,
                )
            )

            total_chars_all_rows += char_len_sum

        avg_row_len = round(total_chars_all_rows / sampled_count, 2)

        return DatasetStatistics(
            total_sampled=sampled_count,
            column_count=len(columns),
            field_stats=field_stats_list,
            avg_row_char_length=avg_row_len,
        )
