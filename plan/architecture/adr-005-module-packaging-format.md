---
artifact_id: adr-005-module-packaging-format
type: adr
producer: B1 Software Architect
consumers: [C1 Tech Lead, C2 Backend Developer, E1 DevOps]
upstream: [epic-23-module-lifecycle-and-activation, arch-23]
downstream: []
status: accepted
created: 2026-06-18
updated: 2026-06-18
---

# ADR-005 — Module Packaging Format

## Context

Epic 23 requires a reproducible, deployable artifact format for code modules. The developer builds a module in dev, tests it, and must deploy it to production without manual steps. Three formats were considered:

1. **Git repository + branch tag** — production server clones the repo at a tag and runs migrations. Used by Frappe/ERPNext.
2. **Sealed tarball** (`<name>_<version>.tar.gz`) — a self-contained archive produced by `manage.sh module pack`, containing backend service, frontend assets, manifest, migrations, and a SHA256SUMS file.
3. **OCI container image** — the module backend is packaged as a Docker image layer. Used for fully isolated microservice modules.

## Decision

**Use a sealed tarball** produced by `manage.sh module pack`.

Rationale:
- **Dev = prod parity**: a sealed tarball at a point in time cannot drift. Git clone can diverge if the tag is moved or the repo has uncommitted changes in the working tree.
- **No external dependency at deploy time**: installing a tarball requires no internet access, no Git credentials, no registry auth. A production server can install modules air-gapped.
- **Simpler than OCI**: OCI images are appropriate when the module is a fully independent service (the financial module already has its own Docker container). For the `manage.sh install` use case — where the module is loaded into the same FastAPI process — a tarball is the right granularity.
- **SHA256 integrity check**: included in the format; the install script verifies before applying.

OCI images remain the deployment unit for modules running as separate services (e.g. the financial module). Tarballs are the packaging unit for modules installed into the core platform process.

## Status

Proposed

## Consequences

- `manage.sh module pack` must produce a deterministic tarball (file timestamps normalized, directory order stable).
- The tarball format is versioned in the manifest schema (`packaging_format: "tarball-v1"`); future versions can introduce breaking changes without invalidating the install command.
- CI/CD pipelines should archive the tarball as a build artifact (e.g. GitHub Actions artifact or S3 object) before running `manage.sh module install` on the production host.
- Module tarballs should NOT be committed to the Git repository; they are build artifacts.
