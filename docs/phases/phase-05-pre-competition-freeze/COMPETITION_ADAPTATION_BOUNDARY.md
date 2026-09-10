# Competition Adaptation Boundary

## Allowed after the official brief is published

- Prompt wording and scenario wording
- Demo narrative and business-domain mapping
- Judge Mode explanatory copy
- Runbook and README clarification
- Competition-selected benchmark subset, while preserving the frozen 15-scenario baseline
- Screenshots, video, and presentation packaging
- Submission metadata and project description

## Not allowed without a new review and regression

- Rewriting the ReasonFuse core detector or state ownership
- Introducing a new database, queue, agent runtime or release platform
- Changing approval or authorization semantics
- Changing the Run Contract or outcome semantics casually
- Adding a new benchmark category to improve a headline score
- Upgrading the model, Toolbox, Knowledge Base or SDK for novelty
- Changing APIM routing semantics
- Adding automatic rollback that was not part of the frozen design
- Deleting the canonical release manifest or Phase reports

## Decision rule

If a proposed change can alter tool choice, progress classification, outcome
verification, release routing, trace lineage or recovery behavior, it is a
behavioral change. Record it, rerun the affected regression, and do not treat
the existing RC1 tag as valid until the new result is reviewed.
