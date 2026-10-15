"""Optional page text extraction. No OCR, passwords or downloads."""

from io import BytesIO

from ragvidence.ingestion.extraction import ExtractedText, Extraction, ExtractionLimitError


def extract_pdf(raw: bytes, *, max_records: int, max_characters: int) -> Extraction:
    try:
        import pypdf
    except ImportError as exc:
        raise ValueError(
            "PDF support requires the optional extra: install 'ragvidence[pdf]'"
        ) from exc
    try:
        reader = pypdf.PdfReader(BytesIO(raw), strict=True)
        if reader.is_encrypted:
            raise ValueError("Encrypted PDFs are unsupported; provide a decrypted text-bearing PDF")
        if len(reader.pages) > max_records:
            raise ValueError(f"PDF exceeds the {max_records}-page limit")
        units, warnings = [], []
        total = 0
        for number, page in enumerate(reader.pages, 1):
            text = page.extract_text() or ""
            total += len(text)
            if total > max_characters:
                raise ExtractionLimitError(
                    f"PDF exceeds the {max_characters}-character extraction limit"
                )
            if text.strip():
                units.append(ExtractedText(text, {"page": number}))
            else:
                warnings.append(f"PDF page {number} has no extracted text; OCR is not performed")
        if not units:
            raise ValueError("PDF has no extractable text (empty or scanned); OCR is not performed")
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"Cannot extract PDF: {exc}") from exc
    return Extraction(
        units,
        f"pypdf-{pypdf.__version__}-plain-v1",
        [
            "PDF text follows parser order; columns, tables and OCR accuracy are not validated.",
            *warnings,
        ],
    )
