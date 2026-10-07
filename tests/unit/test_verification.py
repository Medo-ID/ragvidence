from raglab.verification import run_verification


def test_verification_passes_finished_non_owner_fixtures() -> None:
    results = {item.name: item for item in run_verification()}
    for name in ("Asset hashes", "Dataset", "Tokenizer", "BM25 fixture", "Recovery"):
        assert results[name].status == "PASS"
    assert results["Metrics"].status == "PASS"
    assert results["HTML template"].status == "BLOCKED"
