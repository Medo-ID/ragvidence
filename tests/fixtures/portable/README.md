# Reviewed extraction fixtures

These small source files have deliberately specified contents independent of the
loaders. Tests assert the resulting text and original locations, not only successful
parsing or a value copied from the implementation.

- HTML: three heading sections, with paragraph boundaries separated by blank lines.
  Title/style/script/hidden/aria-hidden text must be absent. Entity decoding yields
  `Device & power`; the second heading contains `α`.
- JSON: two records; only `text` becomes searchable. Nested metadata and tags remain
  metadata. Record 1 contains a newline before `Then release.`
- JSONL: two records on physical lines 1 and 3; only `content` is searchable.
- CSV: a header, then two data rows. The first quoted body spans physical lines 2–3;
  the second row starts at line 4. Only `body` is searchable.
- PDF: manually authored PDF 1.4 objects with a standard Helvetica font. Page 1 says
  `Hold reset for eight seconds.`; page 2 is an image without a text layer; page 3
  says `Use USB-C power.`. It must retain page numbers 1 and 3 and report page 2 as
  having no extracted text. This fixture checks simple page extraction, not layout,
  tables, font encodings, OCR quality or arbitrary production PDFs.
