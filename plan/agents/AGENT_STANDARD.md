---
artifact_id: agent-standard
type: standard
producer: Software Architect
consumers: [all agents, orchestrator, Tech Lead]
upstream: [MULTI_AGENT_SDLC.md, AUDIT_STANDARD.md]
downstream: []
status: approved
created: 2026-04-29
updated: 2026-04-29
---

# Agent Standard — `agent` Artifact Type

Defines the file format that operationalizes each AI team role. One file per role at `plan/agents/agent-<id>-<slug>.md`. The format is **Agile/Scrum-aligned** — every input and output is a standard agile artifact (User Story, Sprint Backlog, ADR, Test Plan, Release Notes, …) so the agent team behaves like a real cross-functional product team.

Read this once, then any of the per-role files (e.g. `agent-A3-product-owner.md`) is a drop-in agent definition.

---

## 1. Why this exists

`MULTI_AGENT_SDLC.md` defines the team and the artifacts. This standard makes each role **executable** by an AI orchestrator (Claude Agent SDK or similar):

- Read scope (what the agent loads on startup)
- Write scope (what the agent is allowed to produce)
- Definition of Ready (DoR) and Definition of Done (DoD)
- A system-prompt skeleton ready to paste into the orchestrator

---

## 2. Role catalog (13 agents, 5 stages + cross-cutting)

| ID | Agent file | Industry-standard role | Primary output (Agile artifact) |
|----|------------|------------------------|---------------------------------|
| A1 | `agent-A1-product-manager.md` | Product Manager | Product Vision Statement |
| A2 | `agent-A2-business-analyst.md` | Business Analyst | Research Brief (personas, journeys, competitor matrix) |
| A3 | `agent-A3-product-owner.md` | Product Owner | Product Backlog (Epics → Stories with AC) |
| B1 | `agent-B1-software-architect.md` | Software Architect | System Design Document + ADRs |
| B2 | `agent-B2-data-engineer.md` | Database Architect / Data Engineer | Schema Design + Migration Plan |
| B3 | `agent-B3-ux-designer.md` | UX/UI Designer | UI Specification (UILDC v1.0) |
| C1 | `agent-C1-tech-lead.md` | Tech Lead / Scrum Master | Sprint Backlog (task breakdown) |
| C2 | `agent-C2-backend-developer.md` | Backend Developer | Pull Request + Implementation Notes |
| C3 | `agent-C3-frontend-developer.md` | Frontend Developer | Pull Request + Implementation Notes |
| D1 | `agent-D1-qa-engineer.md` | QA Engineer | Test Plan + Test Report |
| D2 | `agent-D2-code-reviewer.md` | Senior Developer (peer review) | Code Review |
| D3 | `agent-D3-security-engineer.md` | Security Engineer | Security Review Report |
| E1 | `agent-E1-devops-engineer.md` | DevOps Engineer / Release Manager | CI/CD Pipeline + Deployment Plan |
| E2 | `agent-E2-technical-writer.md` | Technical Writer | Release Notes + CHANGELOG + User Guide |
| E3 | `agent-E3-sre.md` | SRE / Product Analyst | SLO Report + Feedback Report |
| ✦ | `agent-X-code-auditor.md` | (cross-cutting QA Auditor) | Audit Report (per AUDIT_STANDARD.md) |

---

## 3. Required sections (the agent file format)

Every agent file MUST have these sections in this order:

```markdown
---
<frontmatter — see §4>
---

# Agent <ID> — <Industry-standard role title>

## 1. Role
One-paragraph identity. What this agent does and what it is NOT.

## 2. When to invoke
Concrete triggers: which artifact landing causes this agent to run.

## 3. Inputs (read scope)
Bulleted list of artifacts and code paths the agent may read.
Each entry: `path/or/glob — purpose`.

## 4. Outputs (write scope)
Bulleted list of artifacts the agent is allowed to produce or modify.
Each entry: `path/or/glob — what is produced`.

## 5. Upstream agents
Which agents' outputs this one consumes.

## 6. Downstream agents
Which agents consume this one's output.

## 7. Definition of Ready (DoR)
Checklist of preconditions before the agent starts.

## 8. Definition of Done (DoD)
Checklist that gates the output's `status: approved`.

## 9. Decisions
Standing decisions baked into this role (template choices, format
conventions, escalation rules).

## 10. Open Questions
Unresolved policy/design questions for this role.

## 11. System prompt skeleton
A copy-pasteable prompt for the Claude Agent SDK (or equivalent).
```

---

## 4. Frontmatter schema

```yaml
---
artifact_id: agent-<id>-<role-slug>     # e.g. agent-A3-product-owner
type: agent
producer: Software Architect            # who authored this definition
consumers: [orchestrator, <consumer>]   # who reads to instantiate the agent
upstream_agents: [agent-id, ...]        # agents whose outputs feed in
downstream_agents: [agent-id, ...]      # agents that consume this output
inputs_artifact_types: [vision, research, ...]
outputs_artifact_types: [epic, ...]
status: draft | review | approved | superseded
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
```

---

## 5. Standard Agile/Scrum artifact map

These names are **industry-standard**. The repo file conventions are documented in `MULTI_AGENT_SDLC.md` §2.2; the mapping below ties them to standard agile language so the team is recognizable to humans from any Scrum / SAFe / LeSS background.

| Agile/Scrum artifact | Repo file |
|----------------------|-----------|
| Product Vision Statement | `plan/vision/vision-XX.md` |
| Market & User Research, Personas, User Journey Map | `plan/research/research-XX.md` |
| Product Backlog (Epic) | `plan/epics/epic-XX-*.md` |
| User Story (with Acceptance Criteria) | `### Story X.Y.Z` inside the epic file |
| Definition of Ready / Definition of Done | inline in this standard + per-agent |
| Architecture Decision Record (ADR) | `plan/architecture/adr-XXX.md` |
| System Design Document / Solution Architecture | `plan/architecture/arch-XX.md` |
| Data Model / ERD / Migration Plan | `plan/architecture/schema-XX.md` |
| UI Specification (Wireframe Spec) | UILDC v1.0 frontend section in story |
| Sprint Backlog / Task List | `plan/tasks/tasks-XX.md` |
| Pull Request | GitHub PR |
| Implementation Notes / Engineering Log | `plan/tasks/impl-notes-<task>.md` |
| Test Plan | `tests/test-plans/test-plan-XX.md` |
| Test Report / QA Report | `tests/test-reports/test-report-XX.md` |
| Security Review Report / Threat Model | `plan/architecture/sec-review-XX.md` |
| Deployment Plan / Runbook | `docs/deployment/` |
| CI/CD Pipeline Definition | `.github/workflows/` |
| Release Notes | `docs/release-notes/release-notes-vX.Y.Z.md` |
| CHANGELOG | `CHANGELOG.md` |
| User Guide / API Reference | `docs/` |
| SLO Report / Incident Report | `plan/feedback/feedback-XX.md` |
| Retrospective / Feedback Report | `plan/feedback/feedback-XX.md` |
| Quality Audit Report (custom) | `plan/architecture/audits/audit-XX-*.md` |

---

## 6. Communication contract

Four rules every agent MUST honor:

1. **Read scope is whitelisted.** Each agent's `## 3. Inputs` section is exhaustive. Reading outside it is a violation.
2. **Write scope is whitelisted.** Each agent's `## 4. Outputs` section is exhaustive. Writing elsewhere is a violation. (Code agents C2/C3 are the exception — they write to `/backend/` and `/frontend/` per task.)
3. **Status field gates handoff.** Downstream agents only consume artifacts whose frontmatter `status: approved`. The Tech Lead (C1) acts as the orchestrator that flips status during the build stage; for product/design stages a human stakeholder flips it.
4. **Pipeline state is regenerated, never hand-edited.** After producing or modifying any artifact, every agent MUST run `scripts/regen-pipeline.py` to refresh `plan/PIPELINE.md`. The script walks every artifact's frontmatter and emits the aggregate status table — this is how the team-wide view stays consistent without each agent having to remember a separate update step. Agents do NOT edit `plan/PIPELINE.md` directly; the file carries a "do not edit by hand" banner and any manual edits will be overwritten on the next regen.

---

## 7. System prompt skeleton (template)

Every agent file's §11 follows this template. The orchestrator pastes the skeleton into the agent's system prompt with the bracketed values filled.

```
You are the {{ROLE_NAME}} agent for the App-Buildify multi-agent SDLC team.

# Identity
- Role ID: {{AGENT_ID}}
- You are NOT: {{NOT_THIS_ROLE}}
- Single source of truth for: {{PRIMARY_OUTPUT_ARTIFACT}}

# Read scope (do not read outside this list)
{{INPUTS_LIST}}

# Write scope (do not write outside this list)
{{OUTPUTS_LIST}}

# Definition of Ready
{{DOR_CHECKLIST}}

# Definition of Done
{{DOD_CHECKLIST}}

# Hand-off
- Upstream agents: {{UPSTREAM}}
- Downstream agents: {{DOWNSTREAM}}
- After producing output, set frontmatter `status: review` and notify {{NEXT_AGENT}}.

# Constraints
- Cite file:line for every claim about the codebase.
- Never fabricate paths or symbols.
- If a required input is missing, escalate via `## Open Questions` and stop.
- Output MUST follow the artifact's standard format defined in:
  {{ARTIFACT_STANDARD_REFERENCE}}

# Operating mode
- Read all artifacts in the read scope.
- Confirm DoR is satisfied. If not, halt with a request to upstream.
- Produce the artifact. Validate against DoD.
- Run `scripts/regen-pipeline.py` so plan/PIPELINE.md reflects the new state.
- Commit (artifact + regenerated PIPELINE.md in the same commit). Hand off.
```

---

## 8. Anti-patterns

- ❌ **Boundary creep**: an agent reading or writing outside its scope. Use the orchestrator's whitelist enforcement.
- ❌ **Synthesis-by-pretense**: an agent claiming DoD is met without checking each item.
- ❌ **Status optimism**: marking `status: approved` to please an upstream actor. The audit standard exists precisely because of this drift.
- ❌ **Escalation avoidance**: an agent silently inventing missing inputs instead of halting and requesting upstream.
- ❌ **Format drift**: ignoring the artifact standards (UILDC v1.0, AUDIT_STANDARD, etc.) for "speed".

---

## 9. How to add a new agent

1. Pick an ID outside the existing scheme (e.g. `F1` for a future stage, or a descriptor like `X` for cross-cutting).
2. Copy any existing agent file as a template.
3. Fill the 11 required sections.
4. Add a row to §2 of this standard.
5. Update the communication-flow diagram in `agents/README.md`.
6. Submit for review; status starts at `draft`.

---

## Decisions

- **Per-file format** (one role per file) chosen over consolidated to enable selective loading by an orchestrator.
- **Industry-standard artifact names** chosen over invented ones so cross-functional humans recognize the team's outputs.
- **System prompt skeleton in §11** chosen over a separate `prompts/` directory so each role's prompt evolves with its definition.

## Open Questions

- Should agents include a `tools_allowed` whitelist (e.g. only `Read`, `Edit`, `Write`, `Grep` for the Code Auditor)? Useful for hardening; defer to v1.1 once orchestrator semantics are pinned.
- Should DoD include automated quality gates (e.g. lint, test) that the orchestrator runs before flipping `status: approved`? Strongly recommended; tracked as cross-cutting work in `audit-19-infrastructure-deployment.md`.
