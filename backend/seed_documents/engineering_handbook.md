# Engineering Handbook

## Production ownership
Every production service has one owning team. The owner is responsible for service health, on-call coverage, operational documentation, dependency mapping, and remediation of repeated failure modes.

## Changes
High-risk production changes should be reversible, observable, and reviewed by another engineer. Emergency changes are permitted during incidents but must be documented in the incident timeline.

## Service-level objectives
Teams should prioritize customer-impacting SLO breaches above feature work. Repeated SLO misses should result in a reliability plan with measurable corrective actions.
