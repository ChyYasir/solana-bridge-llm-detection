# Attack 1: Mint Confusion

**Group A** — real-world incident: Cashio, March 2022, ~$52.8M.
**Model tested:** `deepseek-ai/DeepSeek-V3.2` (via DeepInfra), temperature 0.

## Scope & setup

The vulnerable program is a lock-and-mint bridge **we wrote ourselves** in native Rust; it
is not Solana's source code. *Solana* is the platform (runtime, validator, SPL Token
program); we only use its toolchain and SDK (`solana-program`, `cargo build-sbf`,
`solana-test-validator`) to build and run our own program on a local chain. The bug is an
**application-level** flaw — Solana does not prevent it automatically — so this class remains
exploitable in current native programs that omit the check. The specific Cashio instance was
patched (the protocol was drained and shut down); the class is what we reproduce and test.

## Short answer

**From the transaction records, yes. From the source code, no.** The model caught the
successful attack every time it read the on-chain records, but it also raised false alarms
on normal activity. Reading the source code, it called almost everything vulnerable and
never pointed at the actual bug. Timing data did not help.

## The bug

`lock` accepts a deposit. The secure bridge checks that the deposited token is the
approved one. The vulnerable copy removes only that check.

## The attack

The attacker created a worthless token of their own, deposited 500,000 of it, and the
bridge minted them **500,000 real wrapped tokens** in return.

- Against the vulnerable copy: **attack succeeded.**
- Against the secure bridge: **attack blocked** (`WrongMint`, error `0x3`).

## Did the LLM detect it?

### Test 1 — reading the source code (3 runs each)

| Case | Correct answer | LLM result | Verdict |
|---|---|---|---|
| Buggy code | "Yes, bug in `lock`" | Said "vulnerable" 3 / 3, but **0 / 3** named the missing `lock` check — each run pointed at a different, unrelated function | ❌ **Missed the planted bug** |
| Secure code | "No bug" | Said "vulnerable" **3 / 3** | ❌ **False alarm every time** |

The model does not distinguish the vulnerable copy from the secure one: it labels both
"vulnerable" and offers a different guessed flaw on each run, none of which is the planted
mint-confusion bug.

### Test 2 — reading the transaction records, no code (3 runs each)

| Case | Correct answer | LLM result | Verdict |
|---|---|---|---|
| Successful attack | "Attack" | Flagged **3 / 3**, correctly explained that the attacker got 500,000 wrapped tokens while the real vault held none and a fake vault held the deposit | ✅ **Detected** |
| Honest user, no attacker | "No attack" | Flagged **3 / 3** | ❌ **False alarm every time** |
| Attack attempt that was blocked | "Attempted, failed" | Flagged **3 / 3** (read the failed step as an exploit attempt) | ➖ |

On the records the model clearly identifies the real attack and even describes the
mint-confusion mechanics, but it treats nearly any session as suspicious, so its
precision is low.

### Test 3 — does timing help? (same records, timing shown vs. hidden, 3 runs each)

Normal relay delay from 40 honest runs: average **2.80s**, "suspicious" cut-off **3.88s**
(mean + 3σ). The attack's delay was **2.89s** — inside the normal band. On timing alone,
the attack looks normal.

| Case | Without timing | With timing | Verdict |
|---|---|---|---|
| Successful attack | Flagged 3 / 3 | Flagged 3 / 3 | ➖ **No change** |
| Honest user | Flagged 3 / 3 | Flagged 3 / 3 | ➖ **No change** |
| Blocked attempt | Flagged 1 / 3 | Flagged 3 / 3 (cited the timing of the failed step) | ⬆️ **More flags** |

## Takeaways

1. **Records beat code for this model.** It caught the actual attack every time from the
   on-chain evidence; from the source it found neither the planted bug nor any real one.
2. **Low precision on records.** It flagged normal activity as an attack just as often as a
   real attack, so a "yes" alone is not trustworthy — the *explanation* is what carries the
   signal (only the real-attack explanation matches the mint-confusion pattern).
3. **Source review is noise here.** "Vulnerable 3 / 3" on both the buggy and the secure
   copy, with a different guess each run, means no real discrimination.
4. **Timing doesn't help catch this attack.** Expected: this attack never has to wait. The
   attack delay (2.89s) is indistinguishable from an honest user's. Attack 4 (oracle) is
   where timing should matter.
5. **Caveat:** Cashio is a well-known hack the model may have read about. Group B attacks
   (5, 6, 7) test whether results hold without that advantage.

## Files

- Vulnerable copy: `programs/variants/v1-mint-confusion/`
- Attack script: `client/src/exploits/exploit-v1.ts`
- Run everything: `scripts/run-attack-v1.sh`
- Records: `traces/v1-mint-confusion/`, normal-delay baseline in `traces/recon/`
- LLM tests: `detection/source_task.py`, `detection/trace_task.py`, `detection/ablation.py`
- Raw LLM answers: `detection/results/v1-mint-confusion-*-deepseek-v3.2.json`
