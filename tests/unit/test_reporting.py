from copy import deepcopy
from html.parser import HTMLParser
from pathlib import Path

import pytest

from ragvidence.reporting.html import render_html
from ragvidence.reporting.markdown import render_markdown
from ragvidence.reporting.payload import build_report


def _evaluation(name: str) -> dict:
    return {
        "manifest": {
            "dataset_hash": "abc",
            "config": {"name": name, "strategy": "bm25", "representation": "body", "k": 2},
        },
        "summary": {"successful": 1, "answerable": 1, "sufficient_evidence_rate": 1.0},
        "questions": [
            {
                "question_id": "Q-1",
                "split": "dev",
                "sufficient_evidence": True,
                "evidence_coverage": 1.0,
                "first_relevant_rank": 1,
                "hits": [],
            }
        ],
    }


def test_single_run_markdown_contains_reproducibility_fields() -> None:
    markdown = render_markdown(build_report(_evaluation("baseline")))
    assert "Sufficient evidence: **1/1**" in markdown
    assert "Dataset hash: `abc`" in markdown
    assert "Retrieval evaluation does not prove" in markdown


def test_html_renderer_escapes_dataset_content(tmp_path: Path) -> None:
    template = tmp_path / "test.html.j2"
    template.write_text("<h1>{{ report.baseline.manifest.config.name }}</h1>")
    evaluation = _evaluation("<script>alert(1)</script>")
    rendered = render_html(build_report(evaluation), template)
    assert "<script>" not in rendered
    assert "&lt;script&gt;" in rendered


def _complete_evaluation(name: str, *, success: bool) -> dict:
    return {
        "manifest": {
            "run_id": f"run-{name}",
            "created_at": "2026-10-08T08:00:00+00:00",
            "product_version": "0.1.0",
            "python_version": "3.12.0",
            "platform": "Linux",
            "dataset_hash": "abc",
            "config": {
                "name": name,
                "strategy": "bm25",
                "representation": "heading_context" if success else "body",
                "k": 2,
                "model": None,
                "provider": None,
            },
            "index_time_ms": 2.5,
            "warnings": [],
        },
        "summary": {
            "successful": int(success),
            "answerable": 1,
            "sufficient_evidence_rate": float(success),
        },
        "questions": [
            {
                "question_id": "Q-1",
                "split": "dev",
                "answerable": True,
                "required_evidence_ids": ["E-1"],
                "sufficient_evidence": success,
                "evidence_coverage": float(success),
                "first_relevant_rank": 1 if success else None,
                "reciprocal_rank": 1.0 if success else 0.0,
                "precision_at_k": 0.5 if success else 0.0,
                "hits": [
                    {
                        "source_unit_id": "SRC-1",
                        "rank": 1,
                        "score": 0.75,
                        "evidence_ids": ["E-1"] if success else [],
                        "preview": "<script>alert('unsafe')</script>",
                        "metadata": {},
                    }
                ],
            }
        ],
    }


def test_product_html_template_renders_baseline_and_comparison() -> None:
    template = Path(__file__).parents[2] / "src/ragvidence/reporting/templates/report.html.j2"
    baseline = _complete_evaluation("baseline", success=False)
    intervention = _complete_evaluation("intervention", success=True)

    rendered = render_html(build_report(baseline, intervention), template)

    assert "RAGvidence" in rendered
    assert "Fail → Pass" in rendered
    assert "run-baseline" in rendered
    assert "run-intervention" in rendered
    assert "SRC-1" in rendered
    assert "<script>alert" not in rendered
    assert "&lt;script&gt;alert" in rendered


def test_product_html_template_renders_baseline_only() -> None:
    template = Path(__file__).parents[2] / "src/ragvidence/reporting/templates/report.html.j2"

    rendered = render_html(build_report(_complete_evaluation("baseline", success=True)), template)

    assert "Baseline question results" in rendered
    assert "Intervention summary" not in rendered
    assert "Change analysis" not in rendered


TEMPLATE = Path(__file__).parents[2] / "src/ragvidence/reporting/templates/report.html.j2"


@pytest.mark.parametrize("before,after,label", [
    (False, True, "Fail → Pass"),
    (True, False, "Pass → Fail"),
    (False, False, "Fail → Fail"),
    (True, True, "Pass → Pass"),
])
def test_report_comparison_states_preserve_payload(before, after, label) -> None:
    report = build_report(
        _complete_evaluation("baseline", success=before),
        _complete_evaluation("intervention", success=after),
    )
    original = deepcopy(report)
    rendered = render_html(report, TEMPLATE)
    assert report == original
    assert label in rendered
    assert '<details class="question-card">' in rendered
    assert '<details class="question-card" open' not in rendered
    assert rendered.index('<section id="regressions">') < rendered.index(
        '<section id="unresolved-failures">'
    ) < rendered.index('<section id="improvements">') < rendered.index(
        '<section id="stable-results">'
    )
    assert "Required evidence gained:" in rendered
    assert "Required evidence lost:" in rendered
    assert "Still missing:" in rendered


def test_unanswerable_comparison_has_na_without_division_or_false_success() -> None:
    evaluation = _complete_evaluation("unanswerable", success=False)
    evaluation["summary"] = {
        "successful": 0, "answerable": 0, "sufficient_evidence_rate": None,
    }
    question = evaluation["questions"][0]
    question["answerable"] = False
    question["required_evidence_ids"] = []
    for field in ["sufficient_evidence", "evidence_coverage", "first_relevant_rank",
                  "reciprocal_rank", "precision_at_k"]:
        question[field] = None
    rendered = render_html(build_report(evaluation, deepcopy(evaluation)), TEMPLATE)
    assert "N/A · Unanswerable" in rendered
    assert "No answerable success-rate comparison is available." in rendered
    assert "None%" not in rendered


def test_missing_hits_optional_fields_and_diagnosis_render_useful_fallbacks() -> None:
    baseline = _complete_evaluation("baseline", success=False)
    baseline["questions"][0]["hits"] = []
    intervention = deepcopy(baseline)
    report = build_report(baseline, intervention)
    report["diagnosis"] = None
    rendered = render_html(report, TEMPLATE)
    assert "No results were retrieved for this question." in rendered
    assert "Missing required evidence:</strong> E-1" in rendered
    assert "Not configured" in rendered
    assert "No diagnostic interpretation is available." in rendered


def test_long_and_hostile_content_is_escaped_in_real_template() -> None:
    hostile = '<script>alert("x")</script><img src="https://invalid.test/x"> & < > "'
    evaluation = _complete_evaluation(hostile, success=False)
    evaluation["questions"][0]["question"] = hostile * 100
    evaluation["questions"][0]["hits"][0]["preview"] = hostile * 1000
    evaluation["questions"][0]["hits"][0]["source_unit_id"] = hostile
    evaluation["questions"][0]["hits"][0]["metadata"] = {"heading_path": [hostile]}
    rendered = render_html(build_report(evaluation), TEMPLATE)
    tags = []

    class Tags(HTMLParser):
        def handle_starttag(self, tag, attrs):
            tags.append(tag)

    Tags().feed(rendered)
    assert not {"script", "img", "iframe", "link"}.intersection(tags)
    assert "&lt;script&gt;" in rendered
    assert "&amp;" in rendered
    assert rendered.count("data:font/woff2;base64,") == 2
    assert "SIL OPEN FONT LICENSE" in rendered
    assert "Printing includes every question" in rendered


def test_fractional_coverage_keeps_display_precision() -> None:
    evaluation = _complete_evaluation("fractional", success=False)
    evaluation["questions"][0]["evidence_coverage"] = 1 / 3
    rendered = render_html(build_report(evaluation), TEMPLATE)
    assert "33.3%" in rendered


@pytest.mark.parametrize("command", ["source-only", "retrieval", "comparison", "failure"])
def test_portable_html_keeps_facts_offline_assets_and_navigation(tmp_path, command):
    """Real command payloads retain their text, N/A and failure facts in HTML."""
    import json

    from typer.testing import CliRunner

    from ragvidence.cli import app
    from ragvidence.reporting.render import render_report

    source = tmp_path / "manual café.txt"
    text = 'Reset 日本語 مرحبا <script>alert("unsafe")</script> & use USB-C.\n'
    source.write_text(text, encoding="utf-8")
    output = tmp_path / "output"
    args = ["compare-data" if command in {"comparison", "failure"} else "bm25", str(source)]
    if command != "source-only":
        args += ["--query", "Reset"]
    if command in {"comparison", "failure"}:
        args += [
            "--techniques",
            "bm25,heading-context" if command == "failure" else "bm25,parent-child",
        ]
    result = CliRunner().invoke(
        app, [*args, "--output", str(output), "--format", "html", "--format", "json", "--no-input"]
    )
    assert result.exit_code == (1 if command == "failure" else 0), result.output
    pattern = "*/exports/*/report.json" if command in {"comparison", "failure"} else "*/report.json"
    payload = json.loads(next(output.glob(pattern)).read_text(encoding="utf-8"))
    assert payload.get("kind") == (
        "comparison" if command in {"comparison", "failure"} else "inspection"
    )
    original = deepcopy(payload)
    html = render_report(payload, "html")
    assert payload == original
    assert source.read_text(encoding="utf-8") == text
    assert "N/A" in html
    if command == "failure":
        assert "partial failure" in html and "failed" in html
        assert payload["participants"][1]["error"] in html
    elif command != "source-only":
        assert "Reset 日本語 مرحبا &lt;script&gt;alert(&#34;unsafe&#34;)&lt;/script&gt;" in html
    ids, links, assets, tags = [], [], [], []

    class Document(HTMLParser):
        def handle_starttag(self, tag, attrs):
            tags.append(tag)
            for key, value in attrs:
                if key == "id":
                    ids.append(value)
                if key == "href":
                    links.append(value)
                if key in {"src", "srcset"}:
                    assets.append(value)

    Document().feed(html)
    assert len(ids) == len(set(ids))
    assert links and all(link.startswith("#") and link[1:] in ids for link in links)
    assert not assets and not {"script", "link", "iframe", "img"}.intersection(tags)
    assert html.count("data:font/woff2;base64,") == 2
    assert "SIL OPEN FONT LICENSE" in html
