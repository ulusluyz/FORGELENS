"""Unit tests for Report Exporter and key redaction."""

from forgelens.audit.evidence import EvidenceReport
from forgelens.audit.scoring import ScoreBreakdown, FinalStatus
from forgelens.audit.engine import AuditResult
from forgelens.reports.exporter import ReportExporter, redact_sensitive_keys


def test_redact_sensitive_keys():
    raw_data = {
        "api_key": "sk-proj-123456789012345678901234",
        "hf_token": "hf_123456789012345678901234",
        "nested": {
            "user_token": "secret_token_val",
            "normal_field": "public_text",
        },
    }
    sanitized = redact_sensitive_keys(raw_data)
    assert sanitized["api_key"] == "***REDACTED***"
    assert sanitized["hf_token"] == "***REDACTED***"
    assert sanitized["nested"]["user_token"] == "***REDACTED***"
    assert sanitized["nested"]["normal_field"] == "public_text"


def test_report_exporters():
    evidence = EvidenceReport()
    evidence.add_evidence("Language Check", {"tr": 90.0}, ai_interpretation="High Turkish ratio")

    scores = ScoreBreakdown(
        category_scores={"language": 90.0, "quality": 85.0},
        weighted_total_score=87.5,
        final_status=FinalStatus.SUITABLE,
        status_reasons=["High quality dataset."],
    )

    audit_result = AuditResult(
        audit_type="dataset",
        repo_id="mock/report-dataset",
        revision="main",
        profile_name="General Dataset",
        ai_enabled=False,
        scores=scores,
        evidence=evidence,
        rule_summary={"exact_duplicate_ratio": 0.0},
    )

    # 1. Test JSON export
    json_out = ReportExporter.export_json(audit_result)
    assert "mock/report-dataset" in json_out
    assert "SUITABLE" in json_out

    # 2. Test Markdown export
    md_out = ReportExporter.export_markdown(audit_result)
    assert "# ForgeLens Audit Report: mock/report-dataset" in md_out
    assert "SUITABLE" in md_out

    # 3. Test HTML export
    html_out = ReportExporter.export_html(audit_result)
    assert "<title>ForgeLens Report - mock/report-dataset</title>" in html_out
    assert "SUITABLE" in html_out
