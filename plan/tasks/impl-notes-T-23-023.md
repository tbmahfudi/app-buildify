# T-23.023 Implementation Notes — DeactivateModal

## What was done

Replaced the pre-scaffolded showDeactivateModal function (raw DOM, no FlexModal) with a
proper export class DeactivateModal following the same class structure as ActivationModal.

File: frontend/assets/js/modules-page.js

## UILDC spec compliance

| Spec requirement | Status |
|---|---|
| FlexModal, size=sm, backdropDismiss=true | Done — FlexModal constructor options |
| header: "Deactivate [Module Name]?" | Done |
| FlexAlert(warning, ph-shield-warning) safety message | Done |
| dependents-section hidden until 409 caught | Done — _showDependents() reveals it |
| ph-link-break error FlexAlert header | Done |
| ph-cube icon per dependent item | Done |
| Deactivate button disabled when dependents present | Done — stays disabled after 409 |
| deactivating state: spinner + "Deactivating..." label | Done |
| module:deactivated CustomEvent on success | Done — dispatched with {detail:{moduleId}} |
| modules:refresh event on success | Done |
| Error state: "Deactivation failed: [msg]" above footer | Done — _showErrorInZone() |

## Approach for dependents check

Used approach 2 from the task brief: show the safety message immediately, let user hit
Confirm, then catch the 409 dependents_active response and surface the blocking list.
The button remains disabled after the 409 so the user cannot retry until they deactivate
the blocking modules.

Response shape handles both flat {code, dependents:[...]} and nested
{code, detail:{dependents:[...]}} to cover any backend variation.

## Click handler update

The container click handler now calls:
  new DeactivateModal(moduleId, displayName).open()
instead of the old showDeactivateModal() function.

## Files changed

Only frontend/assets/js/modules-page.js was modified.
