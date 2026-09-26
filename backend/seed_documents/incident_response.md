# Production Incident Response Runbook

A production incident must be declared when customer impact, data integrity, security, or a critical service objective is at risk.

## First response
1. Stabilize the affected service before attempting non-essential optimization.
2. Open an incident record and assign a severity and owning team.
3. For SEV-1 or security incidents, page the on-call incident commander immediately.
4. Record a timeline of material decisions and mitigations.
5. Never paste secrets, personal data, or credentials into the incident chat.

## Security incidents
If a credential may be exposed, revoke or rotate it immediately, preserve relevant logs, notify the Security team, and avoid destroying evidence. Security owns disclosure and forensic coordination.

## Closure
An incident may be closed after customer impact is resolved, follow-up owners are assigned, and the incident commander confirms that monitoring has returned to normal. SEV-1 and SEV-2 incidents require a post-incident review within five working days.
