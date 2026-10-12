# Attack 1: Mint Confusion

**Group A** — real-world incident: Cashio, March 2022, ~$52.8M.
**Model tested:** `openai/gpt-oss-120b` (via DeepInfra), temperature 0.

## Short answer

**Yes, mostly.** The LLM detected the attack from the transaction records every time and
found the bug in the code 2 out of 3 times. It raised no false alarms on normal
transactions. Adding timing data did not help it catch the attack.

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
| Buggy code | "Yes, bug in `lock`" | Found the real bug **2 / 3** times; 1 run pointed at the wrong function | ✅ **Mostly detected** |
| Secure code | "No bug" | Flagged a problem **3 / 3** times — but **2 of these found a real bug we had missed** (see note) | ⚠️ See note |

### Test 2 — reading the transaction records, no code (6 runs each)

| Case | Correct answer | LLM result | Verdict |
|---|---|---|---|
| Successful attack | "Attack" | Flagged **6 / 6**, correctly explained that tokens were minted with no real collateral behind them | ✅ **Detected** |
| Honest user, no attacker | "No attack" | Said "no attack" **6 / 6** | ✅ **No false alarms** |
| Attack attempt that was blocked | "Attempted, failed" | Flagged **1 / 6** | ❌ **Mostly missed** |

### Test 3 — does timing help? (same records, timing shown vs. hidden, 3 runs each)

Normal relay delay from 40 honest runs: average **2.78s**, "suspicious" cut-off **3.60s**.
The attack's delay was **2.90s** — the same as an honest user's (2.90s). On timing alone,
the attack looks normal.

| Case | Without timing | With timing | Verdict |
|---|---|---|---|
| Successful attack | Detected 3 / 3 | Detected 3 / 3 | ➖ **No change** |
| Honest user | No false alarm 3 / 3 | No false alarm 3 / 3 | ➖ **No change** |
| Blocked attempt | Flagged 1 / 3 | Flagged 3 / 3 (cited rapid back-to-back transactions) | ⬆️ **More flags** |

## Note: the LLM found a real bug in our secure bridge

On the secure code, 2 of 3 runs reported that `release` never checks that the account
receiving the wrapped tokens belongs to the recipient in the relay's signed message. This
is correct — the check was missing. Anyone who sees the relay's signed approval on-chain
can reuse it and send the minted tokens to their own account.

This means our "secure" baseline was not fully secure, and the vulnerable copy contained
this bug in addition to the planted one. **The fix and a re-run of these results are
pending.** The numbers above should be treated as preliminary until then.

## Takeaways

1. **Transaction records work best** — the attack was detected every time, with no false
   alarms on normal activity.
2. **Reading the code works most of the time** (2 of 3), and the model also caught a real
   flaw we missed.
3. **Blocked attempts are mostly missed** — the model only looks for damage that happened.
4. **Timing doesn't help catch this attack.** Expected: this attack never has to wait.
   Attack 4 (oracle) is where timing should matter.
5. **Caveat:** Cashio is a well-known hack the model may have read about. Group B
   attacks (5, 6, 7) will show whether results hold without that advantage.

## Files

- Vulnerable copy: `programs/variants/v1-mint-confusion/`
- Attack script: `client/src/exploits/exploit-v1.ts`
- Run everything: `scripts/run-attack-v1.sh`
- Records: `traces/v1-mint-confusion/`, normal-delay baseline in `traces/recon/`
- LLM tests: `detection/source_task.py`, `detection/trace_task.py`, `detection/ablation.py`
- Raw LLM answers: `detection/results/v1-mint-confusion-*-gpt-oss-120b.json`
