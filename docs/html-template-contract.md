# HTML template contribution contract

The template receives one variable named `report`, containing the same dictionary written to the authoritative evaluation JSON.

- Create `src/raglab/reporting/templates/report.html.j2` as one self-contained Jinja2 file with embedded CSS and no remote assets.
- Auto-escaping stays enabled; never use `|safe` for dataset content.
- Show configuration, numerator and denominator, per-question results, ranked evidence/source IDs, limitations and reproducibility metadata.
- Do not embed credentials, undisclosed absolute paths or full source bodies.
- Keep print and narrow-screen layouts readable.
- Do not change the Python renderer contract.
