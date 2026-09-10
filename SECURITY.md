# Security policy

This repository distributes public vocabulary data and offline tooling; the
public release does not process credentials or private reviewer data. Local,
ignored review records may contain reviewer identity, authority, conflicts, or
sensitive community correspondence and must not be packaged or committed
without explicit publication consent. Never include Zenodo tokens, GitHub
tokens, private reviewer details, or unpublished credentials in issues or
public files.

Report vulnerabilities privately through GitHub's private vulnerability-reporting
feature when enabled. Until then, contact the repository owner privately rather
than opening a public issue. Include affected version, reproduction steps, impact,
and suggested mitigation.

Supported security fixes target the current major release. Data-quality reports
and scholarly disagreements are not security issues and should use normal issue
templates.

Release dependencies and GitHub Actions are exactly pinned. Report a suspected
supply-chain compromise, malicious archive content, checksum mismatch, or
credential exposure through the private security channel. The local release
audit rejects common credential patterns, private working paths, unexpected
archive members, and checksum or manifest drift.
