# Security policy

## Supported versions

Security fixes are provided for the latest released CLI version. Upgrade before reporting behavior from an older release.

## Report a vulnerability privately

Do not publish exploitable details in a public issue or discussion. Use GitHub’s private vulnerability reporting for Medo-ID/ragvidence if enabled, or the maintainer’s private security contact listed on the project page. If neither is available, request a private contact without posting exploit details. Include:

- affected version and operating system;
- minimal reproduction steps;
- expected and observed behavior;
- potential impact;
- whether real credentials or private data were exposed.

Do not include live API keys, customer documents, or unrelated personal information. Use synthetic data whenever possible.

## Security boundaries

- BM25 is offline and does not transmit data.
- FastEmbed downloads model files and then runs locally.
- Ollama and OpenAI-compatible endpoints are selected by the user.
- Remote providers receive the text required for the requested operation.
- `.env` values are not written to manifests or reports.
- Exported reports may contain full source passages, questions, prompts and model outputs and must be reviewed before sharing.
- The CLI is not a sandbox. Only run trusted releases and trusted custom templates.

## Release integrity

Official releases should publish SHA-256 checksums. Verify the downloaded artifact before installation and never install a package from an unofficial mirror or unexpected URL.
