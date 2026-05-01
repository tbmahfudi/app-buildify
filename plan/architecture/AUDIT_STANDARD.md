---
artifact_id: audit-standard
type: standard
producer: Software Architect
consumers: [Code Auditor, Tech Lead, Product Owner, QA Engineer]
upstream: [MULTI_AGENT_SDLC.md, arch-platform.md]
downstream: []
status: approved
created: 2026-04-29
updated: 2026-04-29
---

# Audit Standard — `audit` Artifact Type

Defines a reproducible contract for **gap-analysis audits** that compare an epic's stories against the actual codebase. An AI agent (or human) following this standard produces an `audit-XX-<slug>.md` file that is machine-parseable, evidence-grounded, and deterministic enough to be re-run as the codebase evolves.

This artifact extends the SDLC framework in `/plan/MULTI_AGENT_SDLC.md`. The new artifact `type: audit` is added to the §2.1 enum.

---

## 1. When to use

- Refresh stale `[DONE] [IN-PROGRESS] [OPEN] [PLANNED]` tags in `BACKLOG.md` and individual epic files.
- Produce input for the Tech Lead agent (C1) to prioritize gaps as new tasks.
- Generate a release-candidate verification report.
- Validate that an epic was actually shipped before flipping its status.

---

## 2. Frontmatter

Extends the SDLC envelope from `MULTI_AGENT_SDLC.md` §2.1. Required fields:

```yaml
---
artifact_id: audit-XX-<slug>      # XX = epic number, slug = epic short name
type: audit
producer: <agent role or human>
consumers: [Tech Lead, Product Owner]
upstream:
  - epic-XX-<slug>                # the epic being audited
  - arch-platform                 # for architectural context
downstream: []
status: draft | review | approved | superseded
created: YYYY-MM-DD
updated: YYYY-MM-DD
audit_target: epic-XX-<slug>      # the epic id being audited
auditor: <agent or human name>
commit_sha: <short SHA>           # the codebase point-in-time
coverage_pct: <0-100>             # share of stories with verified_status set
decisions: [...]
open_questions: [...]
---
```

`commit_sha` makes the audit reproducible: anyone can `git checkout <sha>` and re-run.

---

## 3. Verified-status taxonomy

Every story gets exactly one `verified_status`:

| Value | Meaning |
|-------|---------|
| `DONE` | Every AC bullet has cited evidence in code; behavior matches. |
| `PARTIAL` | ≥ 1 AC bullet has cited evidence, ≥ 1 does not. Story partially shipped. |
| `MISSING` | No evidence found despite a `[DONE]` claim. Critical drift. |
| `DRIFT` | Evidence exists but contradicts the AC (wrong path, wrong signature, wrong behavior). |

Compare `verified_status` against `claimed_status` (the epic's tag): mismatches feed the BACKLOG-retag side-output (§7).

---

## 4. Per-story canonical schema

Each audited story is one row in the audit's main table. Columns:

| Column | Type | Source |
|--------|------|--------|
| `story_id` | `E.F.S` (e.g. `1.1.1`) | epic markdown |
| `title` | string | epic story heading |
| `claimed_status` | `DONE` \| `IN-PROGRESS` \| `OPEN` \| `PLANNED` | epic status tag |
| `verified_status` | `DONE` \| `PARTIAL` \| `MISSING` \| `DRIFT` | code inspection |
| `backend_evidence` | `path/to/file.py:symbol` (CSV) | actual code |
| `frontend_evidence` | `path/to/file.js:symbol` (CSV) | actual code |
| `gaps` | bullet list | unmet AC bullets |
| `priority` | 🔴 \| 🟡 \| 🟢 \| — | rubric §5 |

Use `—` when the column is N/A (e.g. `frontend_evidence` for a backend-only story; `priority` when there are no gaps).

Markdown rendering:

```markdown
| Story | Title | Claimed | Verified | Backend evidence | Frontend evidence | Gaps | 🚦 |
|-------|-------|---------|----------|------------------|-------------------|------|----|
| 1.1.1 | User Login with JWT | DONE | DONE | `app/routers/auth.py:login`, `app/core/auth.py:create_access_token` | `assets/js/api.js:login` | — | — |
```

---

## 5. Priority rubric (gaps only)

Reuses the convention from `/docs/backend/DYNAMIC_ENTITIES_GAPS.md`:

| Emoji | Meaning |
|-------|---------|
| 🔴 | High — blocks downstream epics, security, or production. |
| 🟡 | Medium — partial functionality; users notice. |
| 🟢 | Low — polish, nice-to-have, observability. |

---

## 6. File layout (per audit)

```markdown
---
<frontmatter>
---

# Audit — Epic XX: <Epic Title> (audit-XX-<slug>)

## 1. Summary

- Stories audited: N
- DONE: a • PARTIAL: b • MISSING: c • DRIFT: d
- Tag-drift count: k (stories whose verified_status != claimed_status)
- Recommended BACKLOG.md tag: <new overall status string>

## 2. Story-by-story

<canonical table from §4>

## 3. Gaps

### 🔴 High
- [ ] <story_id>: short description — **Files**: `path` — **Effort**: S/M/L

### 🟡 Medium
...

### 🟢 Low
...

## 4. Drift notes

(only if any rows are DRIFT) — short paragraph per drifted story explaining how
the code disagrees with the AC.

## 5. Verdict

One paragraph: should the BACKLOG.md row for this epic be retagged? What's the
single most important next action?

## Decisions

- ...

## Open Questions

- ...
```

---

## 7. Reproducibility recipe

A future agent must be able to regenerate any audit deterministically. Steps:

1. **Parse the epic file** at `plan/epics/epic-XX-<slug>.md` (or `plan-mod-<x>/epics/...` for module epics). For each `#### Story <id>` heading, extract:
   - `story_id` (from heading, e.g. `1.1.1`)
   - `title` (rest of the heading)
   - `claimed_status` (the `[DONE]` / `[OPEN]` / etc. tag)
   - AC bullets under `- ` until the next `####` or `---`
   - The frontend section (under `#### Frontend`) if present

2. **For each AC bullet, search the codebase** with one of these patterns:

   | AC pattern | Grep template |
   |------------|---------------|
   | `<METHOD> <path>` (endpoint) | `(@router\|@app)\.(get\|post\|put\|patch\|delete)\(["'].*<path>` over `/backend/app/routers/` and `/modules/*/backend/app/routers/` |
   | Model name | `class <Name>\(.*Base.*\)` over `/backend/app/models/` |
   | Permission string `r:a:s` | literal grep over `/backend/app/seeds/` and `app/routers/rbac.py` |
   | Frontend route `#/foo` | grep over `/frontend/assets/js/router.js` and `frontend/config/menu.json` |
   | Frontend component `Flex<X>` | locate `assets/js/components/flex-<x>.js` |
   | Field/column on a model | `<field_name>\s*=\s*Column` over `/backend/app/models/` |

3. **Resolve evidence** to `path/to/file.py:symbol` form. If multiple files match, take the first 2 (CSV).

4. **Set `verified_status`** per §3 taxonomy:
   - All ACs cited → `DONE`
   - Some ACs cited → `PARTIAL`
   - None cited → `MISSING`
   - Cited path exists but signature/behavior contradicts AC → `DRIFT`

5. **Write the row.** For each unmet AC, add to `gaps` with priority per §5.

6. **Write summary** (§6 §1): counts, drift list, recommended retag.

Pseudocode:
```python
for epic_file in glob("plan/epics/epic-*.md"):
    epic = parse_epic(epic_file)
    audit = AuditDoc(epic.id, commit_sha=git_head())
    for story in epic.stories:
        evidence_be, evidence_fe, missing = [], [], []
        for ac in story.ac_bullets:
            hit = grep_for_ac(ac, scope=["backend", "frontend"])
            if hit.backend: evidence_be.append(hit.backend)
            if hit.frontend: evidence_fe.append(hit.frontend)
            if not hit: missing.append(ac)
        audit.add_row(
            story_id=story.id,
            title=story.title,
            claimed=story.tag,
            verified=classify(evidence_be, evidence_fe, missing, story.ac_bullets),
            backend_evidence=evidence_be,
            frontend_evidence=evidence_fe,
            gaps=missing,
            priority=score(missing, story),
        )
    audit.write(f"plan/architecture/audits/audit-{epic.id}-{epic.slug}.md")
```

---

## 8. Side outputs

Each audit produces two derived artifacts (optional, but encouraged):

- **Tag-drift report** — a short list at the bottom of the audit: `story_id | claimed | verified | suggested_backlog_action`. Feeds Product Owner to retag `BACKLOG.md`.
- **Gap tasks** — every 🔴 gap converts directly into a task row for `tasks-XX.md` (the Tech Lead artifact in MULTI_AGENT_SDLC.md §2.2).

---

## 9. Anti-patterns

- ❌ Citing files that don't exist — verify every `path:symbol` before writing.
- ❌ Marking `DONE` from documentation alone — code is the source of truth.
- ❌ Inflating evidence — one cited symbol per AC is enough; don't pad.
- ❌ Skipping the frontend column when the AC names UI behavior — those are PARTIAL, not DONE.
- ❌ Editorializing in the table — keep notes in §3 Gaps and §4 Drift.

---

## 10. Worked examples

See `audit-04-rbac-permissions.md` and `audit-11-module-system.md` as the
reference implementations of this standard. Both are explicitly used in the
verification step of `MULTI_AGENT_SDLC.md` §6 Verification.

## Decisions

- The audit is **read-only** — it never modifies the epic or BACKLOG; downstream actors do that based on the audit's recommendation.
- `commit_sha` is mandatory so audits are reproducible after the codebase moves.
- Evidence format is `path:symbol` (CSV when multiple) so agents can grep for symbols later.

## Open Questions

- Should `verified_status` distinguish between `MISSING` (no code at all) and `MISSING_BACKEND_ONLY` / `MISSING_FRONTEND_ONLY`? Current taxonomy folds them; revisit if it causes ambiguity.
- Should there be a `tests_evidence` column for the QA Engineer's downstream use? Held back to keep the table narrow; add in v1.1 if needed.
