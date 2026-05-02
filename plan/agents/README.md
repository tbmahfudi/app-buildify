---
artifact_id: agents-index
type: index
producer: Software Architect
consumers: [orchestrator, all agents, human stakeholders]
upstream: [AGENT_STANDARD.md, MULTI_AGENT_SDLC.md]
downstream: []
status: approved
created: 2026-04-29
updated: 2026-04-29
---

# AI Team — Roles & Communication Flow

Index for the App-Buildify multi-agent SDLC team. Every role is operationalized as a file under this folder per [`AGENT_STANDARD.md`](AGENT_STANDARD.md). Inputs and outputs are **standard Agile/Scrum artifacts**.

## 1. Roster

13 agents in 5 stages plus 1 cross-cutting auditor.

| Stage | ID | File | Industry-standard role | Primary input → Primary output |
|-------|----|------|------------------------|-------------------------------|
| **A. Discovery & Product** | A1 | [agent-A1-product-manager](agent-A1-product-manager.md) | Product Manager | Idea → Product Vision |
|  | A2 | [agent-A2-business-analyst](agent-A2-business-analyst.md) | Business Analyst | Vision → Research Brief (personas, journeys) |
|  | A3 | [agent-A3-product-owner](agent-A3-product-owner.md) | Product Owner | Vision + Research → Product Backlog (Epics → User Stories) |
| **B. Design** | B1 | [agent-B1-software-architect](agent-B1-software-architect.md) | Software Architect | Epic → System Design + ADRs |
|  | B2 | [agent-B2-data-engineer](agent-B2-data-engineer.md) | Database Architect | Epic + ADRs → Schema Design + Migration |
|  | B3 | [agent-B3-ux-designer](agent-B3-ux-designer.md) | UX/UI Designer | Story → UI Specification (UILDC v1.0) |
| **C. Build** | C1 | [agent-C1-tech-lead](agent-C1-tech-lead.md) | Tech Lead / Scrum Master | Design artifacts → Sprint Backlog |
|  | C2 | [agent-C2-backend-developer](agent-C2-backend-developer.md) | Backend Developer | Task → PR + Implementation Notes |
|  | C3 | [agent-C3-frontend-developer](agent-C3-frontend-developer.md) | Frontend Developer | Task + UILDC → PR + Implementation Notes |
| **D. Quality** | D1 | [agent-D1-qa-engineer](agent-D1-qa-engineer.md) | QA Engineer | Story + PR → Test Plan + Test Report |
|  | D2 | [agent-D2-code-reviewer](agent-D2-code-reviewer.md) | Senior Developer (peer review) | PR → Code Review Verdict |
|  | D3 | [agent-D3-security-engineer](agent-D3-security-engineer.md) | Security Engineer | PR + Schema → Security Review Report |
| **E. Release & Operate** | E1 | [agent-E1-devops-engineer](agent-E1-devops-engineer.md) | DevOps / Release Manager | Approved PRs → CI/CD + Deployment Plan |
|  | E2 | [agent-E2-technical-writer](agent-E2-technical-writer.md) | Technical Writer | Merged stories → Release Notes + User Guide |
|  | E3 | [agent-E3-sre](agent-E3-sre.md) | SRE / Product Analyst | Production telemetry → SLO + Feedback Report |
| **Cross-cutting** | ✦ | [agent-X-code-auditor](agent-X-code-auditor.md) | Quality Auditor | Epic + codebase → Audit Report |

---

## 2. Communication Flow (artifact-driven)

Agents do not call each other. They produce artifacts. Other agents consume those artifacts when their `status: approved`. The Tech Lead (C1) plus a human stakeholder gate the status transitions.

```
            ┌──────────────────┐
  human →   │  1-line idea     │
            └────────┬─────────┘
                     ▼
                    A1  ──────► Product Vision (vision-XX.md)
                     │
                     ▼
                    A2  ──────► Research Brief (research-XX.md)
                     │
                     ▼
                    A3  ──────► Epic + User Stories (epic-XX-*.md, BACKLOG.md)
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
       B1           B2           B3
   System Design  Schema +     UILDC frontend
   + ADRs         Migration    section in story
        │            │            │
        └────────────┼────────────┘
                     ▼
                    C1  ──────► Sprint Backlog (tasks-XX.md)
                     │
              ┌──────┴──────┐
              ▼             ▼
             C2            C3
       backend PR    frontend PR
              │             │
              └──────┬──────┘
                     ▼
        ┌────────────┼────────────┐
        ▼            ▼            ▼
       D1           D2           D3
   Test Plan +   Code Review   Security Review
   Test Report   verdict       Report
        │            │            │
        └────────────┼────────────┘
                     ▼
                    E1  ──────► CI/CD pipeline + Deployment
                     │
              ┌──────┴──────┐
              ▼             ▼
             E2            E3
      Release Notes    SLO + Feedback
      + User Guide     Report
                            │
                            ▼
                          (loops back to A1)


  Cross-cutting (any time): ✦ Code Auditor
                            │
                            ▼
              Audit Report (audit-XX-*.md)
              feeds → A3 (retag) and C1 (new tasks)
```

---

## 3. Artifact Map (who produces what, who consumes what)

This is the **inter-role contract** in one table. Read it as: "Agent X writes artifact Y; agents Z₁, Z₂… read it."

| Artifact (Agile/Scrum name) | Repo path | Producer | Consumers |
|-----------------------------|-----------|----------|-----------|
| Product Vision Statement | `plan/vision/vision-XX.md` | A1 | A2 |
| Research Brief (personas, journeys, competitor matrix) | `plan/research/research-XX.md` | A2 | A3 |
| Product Backlog (Epic + User Stories) | `plan/epics/epic-XX-*.md`, `plan/BACKLOG.md` | A3 | B1, B2, B3, C1 |
| System Design Document | `plan/architecture/arch-XX.md` | B1 | B2, C1, C2, C3, D3 |
| Architecture Decision Record (ADR) | `plan/architecture/adr-XXX.md` | B1 | all build + quality + ops agents |
| Schema Design + Migration | `plan/architecture/schema-XX.md`, Alembic migrations | B2 | C2, D1, D3 |
| UI Specification (UILDC v1.0) | `#### Frontend` section in epic story | B3 | C3, D1 |
| Sprint Backlog | `plan/tasks/tasks-XX.md` | C1 | C2, C3 |
| Pull Request (code) | GitHub PR | C2, C3 | D1, D2, D3, E1 |
| Implementation Notes | `plan/tasks/impl-notes-<task>.md` | C2, C3 | D2, future maintainers |
| Test Plan + Test Report | `tests/test-plans/`, `tests/test-reports/` | D1 | C1 (signoff), E1 |
| Code Review (PR comments + verdict) | GitHub PR review | D2 | C2, C3 |
| Security Review Report | `plan/architecture/sec-review-XX.md` | D3 | C2, C3, C1 |
| CI/CD Pipeline + Deployment Plan | `.github/workflows/`, `docs/deployment/` | E1 | E2, E3 |
| Release Notes + CHANGELOG + User Guide | `docs/release-notes/`, `CHANGELOG.md`, `docs/` | E2 | end users |
| SLO Report + Incident Report + Feedback Report | `plan/feedback/feedback-XX.md` | E3 | A1 (loops), C1 (priority) |
| Audit Report | `plan/architecture/audits/audit-XX-*.md` | ✦ | A3 (retag), C1 (new tasks) |

---

## 4. Definition of Ready / Done (cross-stage gates)

These gates apply to handoffs across stage boundaries. Per-agent DoR/DoD lives in each agent file.

### Stage A → B (Discovery → Design)
- **Ready**: `epic-XX-*.md` exists, has Backend + Frontend AC for every story, and `BACKLOG.md` has been updated. Status: `approved`.
- **Done**: B1 + B2 + B3 outputs all `status: approved` and reference the same `epic-XX` in their frontmatter `upstream`.

### Stage B → C (Design → Build)
- **Ready**: System Design, Schema (if any), and UILDC sections are `approved`.
- **Done**: `tasks-XX.md` decomposes every story into ordered tasks with owner-role + depends-on + AC link.

### Stage C → D (Build → Quality)
- **Ready**: PR is open, CI green (when CI exists — see `audit-19`), self-review checklist complete.
- **Done**: D1 + D2 + D3 outputs `status: approved` (or changes-requested resolved).

### Stage D → E (Quality → Release)
- **Ready**: All quality gates green; release window scheduled.
- **Done**: Deployment successful, smoke tests green, release notes published.

### Stage E → A (Release → Discovery, feedback loop)
- **Ready**: Deployment live ≥ 24 h.
- **Done**: `feedback-XX.md` produces ≥ 1 item suitable to start a new vision.

---

## 5. How to use this folder (orchestrator)

1. **Boot the orchestrator** with this README and `AGENT_STANDARD.md`.
2. **Instantiate an agent** by reading its file (`agent-XX-*.md`). Use §11 System Prompt as the agent's system message.
3. **Provide the read scope** declared in §3 of the agent's file. Restrict tool access to that scope.
4. **Wait on DoR** before starting. If DoR is unmet, halt and notify upstream.
5. **Run** the agent. It produces artifacts only in §4 write scope.
6. **Validate DoD**. If satisfied, set `status: approved` and notify downstream.
7. **Hand off**. Repeat with the next agent in the flow.

For human-driven simulation (the user's first run), this README is the runbook: pick an idea, walk through A1 → A2 → … → E3, producing the artifacts at each step.

---

## 6. Open Questions

- Should the orchestrator enforce write scope at the filesystem level (chroot-like sandbox), or trust the agent's prompt? Recommend FS-level once the SDK supports it.
- Should there be a `Scrum Master` distinct from `Tech Lead`? Currently merged at C1. Split if facilitation overhead grows.
- How does the team handle multi-tenant work (multiple epics in flight)? Orchestrator queue + per-epic agent instances seems cleanest; pin in v1.1.

## Decisions

- 13 agents, not more. Adding roles dilutes accountability.
- Industry-standard artifact names everywhere; repo file paths are an implementation detail.
- Cross-cutting Code Auditor (✦) is the only agent without a fixed upstream — it can be invoked any time.
