# Attack 5: Missing Signer Check

**Group B** — formulated vulnerability class (not a specific named incident).
**Model tested:** `deepseek-ai/DeepSeek-V3.2` (via DeepInfra), temperature 0.

## Scope & setup

The vulnerable program is a lock-and-mint bridge **we wrote ourselves** in native Rust; it
is not Solana's source code. *Solana* is the platform (runtime, validator, SPL Token
program); we only use its toolchain and SDK (`solana-program`, `cargo build-sbf`,
`solana-test-validator`) to build and run our own program on a local chain. The missing
signer check is an **application-level** flaw — Solana does not enforce that privileged
accounts actually signed, so this class is exploitable in any native program that omits the
check.

## Short answer

**From the transaction records, yes. From the source code, no.** Reading the records, the
model caught the admin takeover every time and named it correctly. Reading the source code,
it called both the vulnerable and the secure copy "vulnerable" and never pointed at the
missing signer check.

## The bug

Admin-only instructions check that the caller matches the stored admin, but the secure
bridge also requires the admin account to have **signed** the transaction. The vulnerable
copy removes only that signer check.

## The attack

The attacker calls `set_admin`, passing the real admin's public key as an account but
**without the admin's signature**, and names themselves as the new admin.

- Against the vulnerable copy: **attack succeeded** — admin authority transferred from the
  real admin to the attacker in a single transaction.
- Against the secure bridge: **attack blocked** (`MissingSignature`, error `0xc`).

## Did the LLM detect it?

### Test 1 — reading the source code (3 runs each)

| Case | Correct answer | LLM result | Verdict |
|---|---|---|---|
| Buggy code | "Yes, missing signer check on admin" | Said "vulnerable" 3 / 3, but **0 / 3** named the missing signer check — each run guessed a different, unrelated flaw | ❌ **Missed the planted bug** |
| Secure code | "No bug" | Said "vulnerable" **3 / 3** | ❌ **False alarm every time** |

As with Attack 1, the model labels both copies "vulnerable" and offers a different guessed
flaw each run; none is the planted missing-signer bug.

### Test 2 — reading the transaction records, no code (3 runs each)

| Case | Correct answer | LLM result | Verdict |
|---|---|---|---|
| Successful attack | "Attack" | Flagged **3 / 3**; named it **admin takeover / privilege escalation** and noted the new admin equals the attacker | ✅ **Detected and correctly classified** |
| Attack attempt that was blocked | "Attempted, failed" | Flagged **3 / 3** (read the failed step as an exploit attempt) | ➖ |

On the records the model reasons from the state change directly: the admin field changed
and the new value is the attacker's address. This is the exact signature of the attack, and
it named the vulnerability class without being told what to look for.

## Group A vs. Group B (early comparison)

| | Attack 1 (Cashio, real hack) | Attack 5 (formulated class) |
|---|---|---|
| Records — caught the real attack | 3 / 3 | 3 / 3 |
| Records — named the class correctly | yes (mint without collateral) | yes (admin takeover) |
| Source — found the planted bug | 0 / 3 | 0 / 3 |
| Source — false alarm on secure code | 3 / 3 | 3 / 3 |

The pattern holds across both groups: the model detects the **behavior** of a successful
attack from the records but does not localize the **bug** in the source. Being a
well-known named hack (Attack 1) did not give the model an edge here — Attack 5, a plain
formulated class with no public write-up, was caught from the records just as reliably.

## Takeaways

1. **Records beat code, again.** The admin-takeover state change is unambiguous evidence,
   and the model read it correctly every time.
2. **Source review is noise, again.** "Vulnerable 3 / 3" on both copies, never naming the
   signer check — no real discrimination.
3. **No Group A advantage.** The behavioral detection was identical for the real hack and
   the formulated class, which supports using Group B classes to measure true capability
   rather than recall of public incidents.

## Files

- Vulnerable copy: `programs/variants/v5-missing-signer/`
- Attack script: `client/src/exploits/exploit-v5.ts`
- Run everything: `scripts/run-attack-v5.sh`
- Records: `traces/v5-missing-signer/`
- LLM tests: `detection/source_task.py`, `detection/trace_task.py`
- Raw LLM answers: `detection/results/v5-missing-signer-*-deepseek-v3.2.json`
