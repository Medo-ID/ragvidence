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
