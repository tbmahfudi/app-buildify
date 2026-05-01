---
artifact_id: audit-16-internationalization
type: audit
producer: Code Auditor
consumers: [Tech Lead, Product Owner]
upstream: [epic-16-internationalization, arch-platform]
downstream: []
status: approved
created: 2026-04-29
updated: 2026-04-29
audit_target: epic-16-internationalization
auditor: Claude (Opus 4.7)
commit_sha: cc47a54
coverage_pct: 100
---

# Audit — Epic 16: Internationalization (audit-16-internationalization)

## 1. Summary

- Stories audited: **5**
- DONE: **2** • PARTIAL: **1** • DRIFT: **0** • MISSING: **2** (PLANNED)
- Tag-drift count: **1** (16.1.3 PARTIAL)
- Recommended `BACKLOG.md` tag: **Feature 16.1 DONE; Feature 16.2 PLANNED** (currently "DONE; Module i18n PLANNED" — accurate)

## 2. Story-by-story

| Story | Title | Claimed | Verified | Backend evidence | Frontend evidence | Gaps | 🚦 |
|-------|-------|---------|----------|------------------|-------------------|------|----|
| 16.1.1 | Language Loading & Runtime Switching | DONE | DONE | `app/routers/metadata.py` Accept-Language-aware labels | `frontend/assets/js/i18n.js`, language selector in settings | — | — |
| 16.1.2 | Translation Namespace Coverage | DONE | DONE | — | `frontend/assets/i18n/{en,de,es,fr,id}/{common,pages,menu}.json` (15 files) | — | — |
| 16.1.3 | Translation Completeness Check | DONE | PARTIAL | — | `frontend/scripts/check-translations.js` not located; no `npm run i18n:check` script | Completeness check tooling missing | 🟡 |
| 16.2.1 | Module i18n Namespace Registration | PLANNED | MISSING | — | — | No module-scoped i18n loading in frontend i18n config | — |
| 16.2.2 | Entity & Field Label i18n | PLANNED | MISSING | `label_i18n` JSONB defined on entity-definition models | — | API does not return localized labels per Accept-Language; entity designer "Translations" UI absent | — |

## 3. Gaps

### 🟡 Medium
- [ ] **16.1.3** Add `frontend/scripts/check-translations.js` plus `npm run i18n:check` to fail CI on missing keys per locale. **Effort**: S.

## 5. Verdict

The base i18n stack works in 5 languages. Module-scoped i18n and entity-level localization remain PLANNED. Single most impactful next action: ship the completeness check (16.1.3) so translation drift can't sneak in.

## Decisions

- 16.2.2 marked MISSING despite a JSONB column existing; the column without serializers and UI is not a usable feature.

## Open Questions

- Should locale fallback chain be configurable per tenant (e.g. `de → en` for Germany), or stay global?
