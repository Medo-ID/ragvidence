"""Generate synthetic HTML review fixtures through the real CLI; never edit outputs."""

import argparse
import hashlib
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

from ragvidence.ingestion import load_corpus


def generate(root: Path, phase: str) -> None:
    output = root / phase
    if output.exists():
        raise ValueError(f"Keep existing evidence unchanged; choose a new phase: {output}")
    fixtures = root / "fixtures"
    fixtures.mkdir(parents=True, exist_ok=True)
    source = fixtures / ("manual café 日本語 " + "long-path-" * 12 + ".md")
    text = (
        "# Reset · Réinitialisation 日本語\n\nreset button\n\n"
        "Hold the reset button for eight seconds. Café — مرحبا — 日本語.\n\n"
        "# Power\n\npower connector\n\nUse USB-C supply.\n\n"
        "# Safety\n\n"
        + "Synthetic handling notes: keep dry; inspect the cable. " * 35
        + '\nLiteral source text: <script>alert("escaped")</script> & <example>.\n'
    )
    source.write_text(text, encoding="utf-8")
    (fixtures / "unsupported.bin").write_bytes(b"synthetic unsupported input")
    (fixtures / "plain.txt").write_text("Reset the button for eight seconds.\n", encoding="utf-8")
    (fixtures / "empty.txt").write_text("", encoding="utf-8")
    snapshot = load_corpus(source, exclude=[])
    original = snapshot.documents[0]
    evidence = []
    for name, quote in [("RESET", "eight seconds"), ("POWER", "USB-C")]:
        start = text.index(quote)
        evidence.append(
            {
                "evidence_id": name,
                "spans": [
                    {
                        "source_id": original.source_unit_id,
                        "start": start,
                        "end": start + len(quote),
                        "text": quote,
                    }
                ],
            }
        )
    questions = [
        {
            "question_id": "RESET",
            "question": "reset button",
            "split": "dev",
            "answerable": True,
            "required_evidence_ids": ["RESET"],
        },
        {
            "question_id": "POWER",
            "question": "power connector",
            "split": "dev",
            "answerable": True,
            "required_evidence_ids": ["POWER"],
        },
        {
            "question_id": "NA",
            "question": "Battery capacity? Café 日本語 مرحبا " + "long " * 80,
            "split": "dev",
            "answerable": False,
        },
        {
            "question_id": "HELD",
            "question": "power supply",
            "split": "heldout",
            "answerable": True,
            "required_evidence_ids": ["POWER"],
        },
    ]

    def write(name, value):
        (fixtures / name).write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    write(
        "reviewed.json",
        {"corpus_hash": snapshot.corpus_hash, "evidence": evidence, "questions": questions},
    )
    write(
        "questions.json",
        [{"question_id": q["question_id"], "question": q["question"]} for q in questions],
    )
    imported = fixtures / "imported.jsonl"
    imported.write_text(
        "\n".join(
            json.dumps(
                {
                    "question_id": q["question_id"],
                    "hits": [
                        {
                            "source_id": original.source_unit_id,
                            "start": 0,
                            "end": len(text),
                            "text": text,
                        }
                    ]
                    if q["question_id"] == "RESET"
                    else [],
                },
                ensure_ascii=False,
            )
            for q in questions
        )
        + "\n",
        encoding="utf-8",
    )
    write(
        "suite.json",
        {
            "baseline": "existing",
            "bootstrap_samples": 100,
            "variants": [
                {"name": "existing", "technique": "import-data", "results_file": "imported.jsonl"},
                {"name": "lexical", "technique": "bm25"},
                {"name": "parents", "technique": "parent-child"},
            ],
            "slices": {"empty-slice": ["absent"]},
        },
    )
    output.mkdir(parents=True, exist_ok=True)
    commands = []
    env = {
        **os.environ,
        "HF_HUB_OFFLINE": "1",
        "PYTHONUTF8": "1",
        "XDG_CONFIG_HOME": str(root / "config"),
    }

    def run(name, args, expected=0):
        destination = output / name
        command = [
            str(Path(sys.executable).with_name("ragvi.exe" if os.name == "nt" else "ragvi")),
            *map(str, args),
            "--output",
            str(destination),
            "--format",
            "html",
            "--format",
            "json",
            "--no-input",
        ]
        result = subprocess.run(command, env=env, capture_output=True, text=True)
        (output / f"{name}.log").write_text(result.stdout + result.stderr, encoding="utf-8")
        if result.returncode != expected:
            raise RuntimeError(f"{name}: {result.stdout}\n{result.stderr}")
        commands.append(shlex.join(command))

    common = ["--k", "1", "--chunk-size", "36", "--chunk-overlap", "0"]
    run(
        "source-only",
        ["bm25", fixtures, "--include", "*.md", "--include", "*.txt", "--include", "*.bin"],
    )
    run("retrieval", ["bm25", source, "--questions", fixtures / "questions.json", *common])
    run("reviewed", ["bm25", source, "--reviewed", fixtures / "reviewed.json", *common])
    run(
        "comparison",
        [
            "compare-data",
            source,
            "--reviewed",
            fixtures / "reviewed.json",
            "--suite",
            fixtures / "suite.json",
            *common,
        ],
    )
    run(
        "unscored",
        [
            "compare-data",
            source,
            "--questions",
            fixtures / "questions.json",
            "--techniques",
            "bm25,parent-child",
            *common,
        ],
    )
    run(
        "failure",
        [
            "compare-data",
            fixtures / "plain.txt",
            "--query",
            "reset",
            "--techniques",
            "bm25,heading-context",
        ],
        expected=1,
    )
    command = [
        str(Path(sys.executable).with_name("ragvi.exe" if os.name == "nt" else "ragvi")),
        "tutorial",
        "--root",
        str(output / "tutorial"),
    ]
    result = subprocess.run(command, env=env, capture_output=True, text=True, check=True)
    (output / "tutorial.log").write_text(result.stdout, encoding="utf-8")
    commands.append(shlex.join(command))
    reports = sorted(output.rglob("*.html"))
    manifest = {
        str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in reports
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (output / "commands.txt").write_text("\n".join(commands) + "\n")
    print(f"Generated {len(reports)} reports in {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--phase", required=True)
    args = parser.parse_args()
    generate(args.root.resolve(), args.phase)
