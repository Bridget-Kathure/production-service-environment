# Gate 1 design pack — index

Group 10's peer review flagged that `docs/gate1-iac/` only has files `00`, `01`, `04`, `08`, and `10` — the other required sections aren't missing from the submission, they live in `docs/gate1-design.md` instead (which is a single, complete document covering the whole Gate 1 pack). This index maps every required section to exactly where it lives, so nothing gets missed on review.

We're pointing to `gate1-design.md` rather than backfilling six new numbered files that would just duplicate content already there. We just fixed a real bug caused by exactly that kind of duplication (a cluster name that drifted out of sync between two docs saying the same thing) — one source of truth per topic is the safer choice going forward.

| # | Required section | Where to find it |
|---|---|---|
| 00 | Kickoff / tooling decisions | [`00-kickoff-decisions.md`](./00-kickoff-decisions.md) |
| 01 | Dependency graph | [`01-dependencygraph.md`](./01-dependencygraph.md) |
| 02 | Ownership map | [`gate1-design.md`](../gate1-design.md), section 1, "Ownership Rotation (2-Person Adaptation)" |
| 03 | CIDR / subnet-capacity table | [`gate1-design.md`](../gate1-design.md), section 2, "CIDR and Subnet Capacity Table" |
| 04 | Route-table and egress design | [`04-routes-egress.md`](./04-routes-egress.md) |
| 05 | Security-group matrix and traffic contract | [`gate1-design.md`](../gate1-design.md), section 4, "Security Group Matrix and Traffic Contract" |
| 06 | Expected resource names and tags | [`gate1-design.md`](../gate1-design.md), section 5, "Expected Resource Names and Tags" |
| 07 | Three predicted broken dependency edges | [`gate1-design.md`](../gate1-design.md), section 6, "Three Predicted Broken Dependency Edges" |
| 08 | State-backend design | [`08-state-backend.md`](./08-state-backend.md) |
| 09 | Application-release ownership | [`gate1-design.md`](../gate1-design.md), section 8, "Application Release Ownership" |
| 10 | Five architecture decision cards | [`10-decision-cards.md`](./10-decision-cards.md) |

## Related, but not part of the numbered pack

- Repository shape — `gate1-design.md`, section 10
- Scar log (evidence-driven failure diagnoses) — [`../gate1/06-scar-log.md`](../gate1/06-scar-log.md)
- Platform resource reference (real IDs/ARNs, for Service B/C build) — [`../gate1/platform-resources.md`](../gate1/platform-resources.md)
- Cost sweep evidence — [`../gate1/phase6-cost-sweep.md`](../gate1/phase6-cost-sweep.md)
- Full submission summary — [`../gate1/gate1-submission.md`](../gate1/gate1-submission.md)
