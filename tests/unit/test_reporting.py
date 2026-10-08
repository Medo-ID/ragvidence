from pathlib import Path

from raglab.reporting.html import render_html
from raglab.reporting.markdown import render_markdown
from raglab.reporting.payload import build_report


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
    template = Path(__file__).parents[2] / "src/raglab/reporting/templates/report.html.j2"
    baseline = _complete_evaluation("baseline", success=False)
    intervention = _complete_evaluation("intervention", success=True)

    rendered = render_html(build_report(baseline, intervention), template)

    assert "RAG Debugging Lab" in rendered
    assert "Fail To Pass" in rendered
    assert "run-baseline" in rendered
    assert "run-intervention" in rendered
    assert "SRC-1" in rendered
    assert "<script>alert" not in rendered
    assert "&lt;script&gt;alert" in rendered


def test_product_html_template_renders_baseline_only() -> None:
    template = Path(__file__).parents[2] / "src/raglab/reporting/templates/report.html.j2"

    rendered = render_html(build_report(_complete_evaluation("baseline", success=True)), template)

    assert "Baseline question results" in rendered
    assert "Intervention summary" not in rendered
    assert "Change analysis" not in rendered
