# Resolved dependency license inventory

Generated from the locked core and semantic runtime environment for version 0.2.0;
extended with the optional PDF runtime in development. Package metadata is
informational; upstream license files remain authoritative.

| Name               | Version   | License                                            | URL                                                                  |
|--------------------|-----------|----------------------------------------------------|----------------------------------------------------------------------|
| Jinja2             | 3.1.6     | BSD License                                        | https://github.com/pallets/jinja/                                    |
| MarkupSafe         | 3.0.4     | BSD-3-Clause                                       | https://github.com/pallets/markupsafe/                               |
| PyYAML             | 6.0.3     | MIT License                                        | https://pyyaml.org/                                                  |
| Pygments           | 2.21.0    | BSD-2-Clause                                       | https://pygments.org                                                 |
| annotated-doc      | 0.0.5     | MIT                                                | https://github.com/fastapi/annotated-doc                             |
| annotated-types    | 0.8.0     | MIT                                                | https://github.com/annotated-types/annotated-types                   |
| anyio              | 4.15.1    | MIT                                                | https://anyio.readthedocs.io/en/stable/versionhistory.html           |
| bm25s              | 0.2.14    | MIT License                                        | https://github.com/xhluca/bm25s                                      |
| certifi            | 2026.7.22 | Mozilla Public License 2.0 (MPL 2.0)               | https://github.com/certifi/python-certifi                            |
| charset-normalizer | 3.5.2     | MIT                                                | https://github.com/jawah/charset_normalizer/blob/master/CHANGELOG.md |
| click              | 8.5.0     | BSD-3-Clause                                       | https://github.com/pallets/click/                                    |
| fastembed          | 0.9.0     | Apache Software License                            | https://github.com/qdrant/fastembed                                  |
| filelock           | 4.1.1     | MIT                                                | https://github.com/tox-dev/py-filelock                               |
| flatbuffers        | 25.12.19  | Apache Software License                            | https://google.github.io/flatbuffers/                                |
| fsspec             | 2026.9.0  | BSD-3-Clause                                       | https://github.com/fsspec/filesystem_spec                            |
| h11                | 0.16.0    | MIT License                                        | https://github.com/python-hyper/h11                                  |
| hf-xet             | 1.7.0     | Apache-2.0                                         | https://github.com/huggingface/xet-core                              |
| httpcore           | 1.0.9     | BSD-3-Clause                                       | https://www.encode.io/httpcore/                                      |
| httpx              | 0.28.1    | BSD License                                        | https://github.com/encode/httpx                                      |
| huggingface_hub    | 1.33.0    | Apache Software License                            | https://github.com/huggingface/huggingface_hub                       |
| idna               | 3.20      | BSD-3-Clause                                       | https://github.com/kjd/idna                                          |
| loguru             | 0.7.3     | MIT License                                        | https://github.com/Delgan/loguru                                     |
| markdown-it-py     | 4.2.0     | MIT License                                        | https://github.com/executablebooks/markdown-it-py                    |
| mdurl              | 0.1.2     | MIT License                                        | https://github.com/executablebooks/mdurl                             |
| mmh3               | 5.3.1     | MIT License                                        | https://pypi.org/project/mmh3/                                       |
| numpy              | 2.5.4     | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 | https://numpy.org                                                    |
| onnxruntime        | 1.23.2    | MIT License                                        | https://onnxruntime.ai                                               |
| packaging          | 26.3      | Apache-2.0 OR BSD-2-Clause                         | https://github.com/pypa/packaging                                    |
| pillow             | 12.3.0    | MIT-CMU                                            | https://python-pillow.github.io                                      |
| protobuf           | 7.36.2    | 3-Clause BSD License                               | https://developers.google.com/protocol-buffers/                      |
| py_rust_stemmers   | 0.1.8     | MIT (wheel LICENSE; metadata UNKNOWN)               | https://pypi.org/project/py-rust-stemmers/                             |
| pydantic           | 2.14.1    | MIT                                                | https://github.com/pydantic/pydantic                                 |
| pydantic-settings  | 2.15.0    | MIT                                                | https://github.com/pydantic/pydantic-settings                        |
| pydantic_core      | 2.50.1    | MIT                                                | https://github.com/pydantic                                          |
| python-dotenv      | 1.2.4     | BSD-3-Clause                                       | https://github.com/theskumar/python-dotenv                           |
| pypdf (optional)   | 6.20.1    | BSD-3-Clause                                       | https://github.com/py-pdf/pypdf                                     |
| requests           | 2.34.2    | Apache Software License                            | https://github.com/psf/requests                                      |
| rich               | 14.3.4    | MIT License                                        | https://github.com/Textualize/rich                                   |
| scipy              | 1.18.1    | BSD License                                        | https://scipy.org/                                                   |
| shellingham        | 1.5.4     | ISC License (ISCL)                                 | https://github.com/sarugaku/shellingham                              |
| tokenizers         | 0.23.3    | Apache Software License                            | https://github.com/huggingface/tokenizers                            |
| tqdm               | 4.70.1    | MPL-2.0 AND MIT                                    | https://tqdm.github.io                                               |
| typer              | 0.27.3    | MIT                                                | https://github.com/fastapi/typer                                     |
| typing-inspection  | 0.4.4     | MIT                                                | https://github.com/pydantic/typing-inspection                        |
| typing_extensions  | 4.16.0    | PSF-2.0                                            | https://github.com/python/typing_extensions                          |
| urllib3            | 2.8.0     | MIT                                                | https://github.com/urllib3/urllib3/blob/main/CHANGES.rst             |

The installed `py-rust-stemmers` 0.1.8 wheel includes an MIT LICENSE (copyright 2024 qdrant), despite UNKNOWN metadata. The portability audit constrains ONNX Runtime below 1.24 for Intel macOS; the universal lock now selects 1.23.2 on all four CI targets. This adds coloredlogs, humanfriendly, mpmath and sympy, plus pyreadline3 on Windows. Other runtime versions are unchanged.

## Additional portability dependencies

| Component | Locked version | Identified license | Scope |
| --- | --- | --- | --- |
| coloredlogs | 15.0.1 | MIT | ONNX Runtime logging |
| humanfriendly | 10.0 | MIT | coloredlogs |
| mpmath | 1.3.0 | BSD (package metadata; preserve bundled license) | sympy |
| sympy | 1.14.0 | BSD (package metadata; preserve bundled license) | ONNX Runtime |
| pyreadline3 | 3.5.6 | BSD-3-Clause | Windows humanfriendly |
| colorama | 0.4.6 | BSD-3-Clause | Windows terminal adapters |
| win32-setctime | 1.2.0 | MIT | Windows loguru |

The inventory includes Windows-only runtime dependencies not installed in the Linux
verification environment. Each locked wheel retains its own upstream license.
