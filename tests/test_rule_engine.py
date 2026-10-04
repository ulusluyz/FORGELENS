"""Unit tests for Sampling Engine, Local Language Detector, and Rule Engine."""

from forgelens.analysis.sampling import SamplingEngine, SamplingStrategy
from forgelens.analysis.language import LocalLanguageDetector
from forgelens.analysis.rule_engine import RuleEngine


def test_sampling_engine_random():
    rows = [{"id": i, "text": f"sample text {i}"} for i in range(100)]
    sampled = SamplingEngine.sample_rows(rows, sample_size=10, strategy=SamplingStrategy.RANDOM)
    assert len(sampled) == 10


def test_sampling_engine_stratified():
    rows = [
        {"id": i, "category": "A"} for i in range(50)
    ] + [
        {"id": i, "category": "B"} for i in range(50)
    ]
    sampled = SamplingEngine.sample_rows(
        rows, sample_size=20, strategy=SamplingStrategy.STRATIFIED, stratify_key="category"
    )
    assert len(sampled) == 20
    cat_a = sum(1 for r in sampled if r["category"] == "A")
    cat_b = sum(1 for r in sampled if r["category"] == "B")
    assert cat_a == 10
    assert cat_b == 10


def test_local_language_detector_turkish():
    texts = [
        "Bu dataset Türkçe dil modelini eğitmek için hazırlanmıştır.",
        "Ayrıca içerisinde birçok Türkçe makale ve soru cevap çifti bulunmaktadır.",
        "Geliştiriciler bu veriyi rahatlıkla kullanabilirler."
    ]
    ratios = LocalLanguageDetector.analyze_language_distribution(texts)
    assert "tr" in ratios
    assert ratios["tr"] > 80.0


def test_rule_engine_duplicates_and_empty():
    rows = [
        {"text": "Aynı metin icerigi"},
        {"text": "Aynı metin icerigi"},
        {"text": ""},
        {"text": "Farklı bağımsız bir metin cümlesi."},
    ]
    analysis = RuleEngine.analyze_dataset_sample(rows, text_fields=["text"])
    assert analysis.total_sampled == 4
    assert analysis.exact_duplicate_count == 1
    assert analysis.exact_duplicate_ratio == 25.0
    assert analysis.empty_row_ratio == 25.0
    assert len(analysis.checks) >= 3
