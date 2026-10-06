# Interpreting results

## Sufficient evidence at k

A question passes only when every required evidence ID appears somewhere in the top `k`. This is the primary result because a partially retrieved multi-part answer is still incomplete.

## Evidence coverage

Coverage shows the fraction of required evidence found. A value of `0.5` can reveal progress on a two-evidence question, but it is not a pass.

## First relevant rank and reciprocal rank

These describe how early the first required evidence appears. They do not prove that all evidence was retrieved.

## Precision at k

Precision describes how many of the `k` positions contain required evidence. It can punish harmless supporting context and should not replace evidence sufficiency.

## Change classes

- `fail_to_pass`: improvement worth inspecting.
- `pass_to_fail`: regression; investigate before adoption.
- `pass_to_pass`: preserved success.
- `fail_to_fail`: the intervention did not solve this case.

Never accept an aggregate improvement without opening the changed queries. Confirm that success came from authentic source context rather than label leakage, duplicated answers or a changed evaluation depth.

## Diagnosis language

The built-in diagnosis describes observable patterns and proposes a next experiment. It does not claim certainty about the cause. Confidence and limitations belong beside every recommendation.
