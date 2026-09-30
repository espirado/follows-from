# Mislabel classes

A class, here, is the set of inputs on which a method returns `SUPPORTED` and the reference does not. For argument echo and Python `==`, the reference is `check` on the trace as written, and the method is a stand-in. For inferred grounds, the reference is `check` on the written claim, and the method is `check` on a premise copied from the tool-call argument. Each class starts from a control where the two verdicts agree, and changes one factor.

This is a measurement of three stand-ins. It is not a rate, and it is not a claim that any class is new.

## Argument echo

The method is `follows_from.probes.transcript_reader`. It returns `SUPPORTED` when a printed `lookup_mpfs` parameter equals the value the action claims. The printed JSON is the one from the 28 September 2026 goose turn. It does not change.

`follows_from.probes.causal.score_mutations` starts from `examples/supported.json` and applies one edit per row.

| Factor | Checker | Reader | Overclaim |
|---|---|---|---|
| none | `SUPPORTED` | `SUPPORTED` | no |
| drop the tool result | `INSUFFICIENT_EVIDENCE` | `SUPPORTED` | yes |
| set `isError` | `INSUFFICIENT_EVIDENCE` | `SUPPORTED` | yes |
| set the returned code to `99214` | `CONTRADICTED` | `SUPPORTED` | yes |
| change the claim to `99214` | `CONTRADICTED` | `INSUFFICIENT_EVIDENCE` | no |
| edit the descriptor | `SUPPORTED` | `SUPPORTED` | no |

The last row of that table is not an overclaim: the descriptor is not the field the claim uses, and both methods stay `SUPPORTED`.

The overclaim rows are the class. Each one leaves the printed code equal to the claim and removes support from the trace. Dropping the result and marking the call failed are different checker verdicts, and the reader does not distinguish them. Changing the claim takes the input out of the class, because the print no longer echoes it. Editing an unused field does not create the class.

The named traces in `printed_call_pair.md` are the same class, including the captured unexecuted turn and the captured HTTP 504. The mutations above rebuild it from one file.

## Python `==` on a boolean

The method is `follows_from.probes.python_eq`. It compares with Python's `==`, which is what an early version of the checker did. `1 == True` and `0 == False` there. The current checker uses JSON equality and returns `CONTRADICTED` on those pairs. The early bug is fixed in `check`; this module only reconstructs it.

| Observed | Expected | Checker | Python `==` | Overclaim |
|---|---|---|---|---|
| `true` | `true` | `SUPPORTED` | `SUPPORTED` | no |
| `1` | `1` | `SUPPORTED` | `SUPPORTED` | no |
| `20` | `20.0` | `SUPPORTED` | `SUPPORTED` | no |
| `1` | `true` | `CONTRADICTED` | `SUPPORTED` | yes |
| `true` | `1` | `CONTRADICTED` | `SUPPORTED` | yes |
| `0` | `false` | `CONTRADICTED` | `SUPPORTED` | yes |
| `false` | `0` | `CONTRADICTED` | `SUPPORTED` | yes |
| `2` | `true` | `CONTRADICTED` | `CONTRADICTED` | no |

The class is the four bool/int collisions. `20` and `20.0` agree under both methods, so the class is not numeric comparison in general. `2` against `true` disagrees with the claim for both methods, so a mismatch alone is not the class.

## Inferred grounds

The method is `follows_from.probes.infer_grounds`. It copies the `lookup_mpfs` argument into a premise, `results.0.hcpcs_code` equals that argument, and then calls `check`. The action's claim is not an input. The reference is `check` on the trace with its written grounds.

`score_inferred_grounds` starts from `examples/supported.json`. The tool call and the returned code in that file are the executed goose turn. Every other row edits that file. `examples/contradicted.json` is the `claim_99214` edit under another name: the same result, with the grounds written as `99214`.

| Factor | Reference | Inferred | Overclaim |
|---|---|---|---|
| none | `SUPPORTED` | `SUPPORTED` | no |
| claim set to `99214` | `CONTRADICTED` | `SUPPORTED` | yes |
| claim set to `99215` | `CONTRADICTED` | `SUPPORTED` | yes |
| drop the tool result | `INSUFFICIENT_EVIDENCE` | `INSUFFICIENT_EVIDENCE` | no |
| set `isError` | `INSUFFICIENT_EVIDENCE` | `INSUFFICIENT_EVIDENCE` | no |
| set the returned code to `99214` | `CONTRADICTED` | `CONTRADICTED` | no |
| drop the tool call | `SUPPORTED` | `INSUFFICIENT_EVIDENCE` | no |

On the overclaim rows the inferred premise says `99213`, which is the argument, and the server returned `99213`. `check` is right about that premise and returns `SUPPORTED`. The written claim is a different code, so the reference returns `CONTRADICTED`. The confident verdict is about the argument. The action claimed something else.

The unexecuted goose turn is not in this class. That trace has no `lookup_mpfs` call to copy. The inferrer removes the grounds and `check` returns `INSUFFICIENT_EVIDENCE`, which is also the reference. A missing result and a failed call stay `INSUFFICIENT_EVIDENCE` for both, because this method still asks `check` and `check` still requires a result. A returned code of `99214` is `CONTRADICTED` for both, because the copied argument is `99213`.

Dropping the tool call is the other boundary. The result still supports the written claim, so the reference is `SUPPORTED`. With no argument to copy, the inferrer abstains and the verdict is `INSUFFICIENT_EVIDENCE`. The score leaves that row out. The method is not saying `SUPPORTED`.

No row here is a goose turn in which the model quoted a code other than the argument. The two overclaim rows are that claim, written in by the edit.

## What the three have in common

Each stand-in returns a well-formed `SUPPORTED` on a set of inputs where the reference does not. Argument echo never reads the tool result, and it stays `SUPPORTED` across a missing result, a failed call, and a different code. Python `==` reads the result and equates a boolean with `0` or `1`. Inferred grounds reads the result through `check`, and the overclaim is the case where the written claim is not the argument the server returned. The same score picks out each set. The inputs in the sets are different, and so is the factor that leaves the control.

```bash
python -m pytest -q tests/test_causal.py tests/test_python_eq.py tests/test_infer_grounds.py
```
