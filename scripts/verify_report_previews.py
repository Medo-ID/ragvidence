"""Check unchanged synthetic evidence and actual PDF disclosure contents."""

import argparse
import json
import re
from pathlib import Path

from pypdf import PdfReader


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def verify(root: Path, after: str) -> dict:
    comparisons = []
    for name in ("source-only", "retrieval", "reviewed", "comparison", "unscored", "failure"):
        left = read(next((root / "before" / name).rglob("report.json")))
        right = read(next((root / after / name).rglob("report.json")))
        if left.get("kind") == "comparison":
            for key in ("state", "evaluation_level", "phase", "baseline", "policy", "comparisons"):
                assert left[key] == right[key], (name, key)
            pairs = zip(left["participants"], right["participants"], strict=True)
            reports = []
            for a, b in pairs:
                assert a["state"] == b["state"] and a.get("error") == b.get("error")
                if a["state"] != "complete":
                    continue
                for key in ("summaries", "evidence_scope", "usage", "criteria"):
                    assert a[key] == b[key], (name, a["name"], key)
                for key in ("context_characters", "context_units", "context_unit"):
                    assert a["resources"][key] == b["resources"][key]
                reports.append((a["report"], b["report"]))
        else:
            reports = [(left, right)]
        for a, b in reports:
            for key in ("input", "preparation", "evaluation", "observations", "limitations"):
                assert a[key] == b[key], (name, key)
            assert a["manifest"]["config"] == b["manifest"]["config"]
            for x, y in zip(a["questions"], b["questions"], strict=True):
                for key in (
                    "question_id",
                    "question",
                    "hits",
                    "metrics",
                    "context_hash",
                    "context_characters",
                    "context_measurement",
                    "observations",
                ):
                    assert x[key] == y[key], (name, x["question_id"], key)
        comparisons.append(name)
    for filename in ("bm25-body.json", "bm25-heading_context.json"):
        a, b = [
            read(root / phase / "tutorial/first-run/evaluations" / filename)
            for phase in ("before", after)
        ]
        assert a["summary"] == b["summary"]
        for x, y in zip(a["questions"], b["questions"], strict=True):
            assert {k: v for k, v in x.items() if k != "query_time_ms"} == {
                k: v for k, v in y.items() if k != "query_time_ms"
            }
    pdfs = []

    # PDF extraction reorders Arabic glyphs; compare every ASCII character in each
    # complete preformatted block, then inspect the Unicode rendering separately.
    def normalized(value):
        return re.sub(r"[^\x21-\x7e]", "", value)

    for pdf in sorted((root / "browser" / after).glob("*.pdf")):
        reader = PdfReader(pdf)
        text = "\n".join(page.extract_text() for page in reader.pages)
        expected = read(pdf.with_name(pdf.stem + "-print-content.json"))
        for index, content in enumerate(expected["pre"]):
            assert normalized(content) in normalized(text), (pdf.name, index)
        assert "SIL OPEN FONT LICENSE" in text
        pdf.with_suffix(".txt").write_text(text, encoding="utf-8")
        pdfs.append(
            {
                "report": pdf.stem,
                "pages": len(reader.pages),
                "verified_blocks": len(expected["pre"]),
                "closed_disclosures": expected["closed"],
            }
        )
    assert len(pdfs) == 7
    record = {"unchanged_evidence": comparisons + ["tutorial"], "pdfs": pdfs}
    (root / "evidence-checks.json").write_text(json.dumps(record, indent=2) + "\n")
    print("PASS: unchanged evidence in all seven journeys; every PDF preformatted block present")
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--after", default="accepted")
    args = parser.parse_args()
    verify(args.root, args.after)
