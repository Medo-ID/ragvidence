# Third-party notices

This inventory covers direct runtime dependencies selected for RAGvidence v0.1.0. Exact resolved versions are recorded in `uv.lock`. Each dependency remains governed by its own license; consult the installed distribution and upstream project for the complete text.

| Component | Role | License identified by upstream/package metadata |
| --- | --- | --- |
| BM25S | Local lexical retrieval | MIT |
| Jinja2 | Escaped HTML templating | BSD-3-Clause |
| NumPy | Vector operations | BSD-3-Clause and bundled component licenses |
| Pydantic | Data validation | MIT |
| Pydantic Settings | Reserved configuration boundary | MIT |
| Rich | Terminal presentation | MIT |
| Typer | CLI framework | MIT |
| FastEmbed (optional) | Local ONNX embedding runtime | Apache-2.0 |
| BAAI/bge-small-en-v1.5 (downloaded optionally) | Default English embedding model | MIT |

FastEmbed installs transitive runtime dependencies whose versions and licenses may change when `uv.lock` is updated. The resolved inventory for this release is recorded in `THIRD_PARTY_LICENSES.md`. The `py-rust-stemmers` 0.1.8 package metadata does not declare a machine-readable license; its upstream repository license file must be checked manually before each commercial release.

The default model is downloaded separately on first semantic use and is not redistributed inside the core archive.

## Embedded report fonts

Geist Sans and Geist Mono variable WOFF2 files are copied from geist 1.7.2 and
embedded as data URLs in generated HTML. Copyright (c) 2023 Vercel, in
collaboration with basement.studio. Licensed under the SIL Open Font License 1.1;
the complete license is packaged in `src/ragvidence/reporting/fonts/LICENSE.txt`
and included in the report's font-license disclosure. Reports request no fonts
over the network.
