# Attack 1: Mint Confusion

**Group A** — real-world incident: Cashio, March 2022, ~$52.8M.
**Model tested:** `deepseek-ai/DeepSeek-V3.2` (DeepInfra), temperature 0, 3 runs per case.

## Short answer

**Partly.** The LLM reliably caught the attack when it saw the transaction records of a
successful exploit. It did **not** reliably find the bug by reading the code, and it raised
false alarms on clean code and on normal transactions every time. Adding timing data did
not help.

## The bug

`lock` accepts a deposit. The secure bridge checks that the deposited token is the
approved one. The vulnerable copy removes only that check.

## The attack

The attacker created a worthless token of their own, deposited 500,000 of it, and the
bridge minted them **500,000 real wrapped tokens** in return.

- Against the vulnerable copy: **attack succeeded.**
- Against the secure bridge: **attack blocked** (`WrongMint`, error `0x3`).

## Did the LLM detect it?

### Test 1 — reading the source code

| Case | Correct answer | LLM result | Verdict |
|---|---|---|---|
| Buggy code | "Yes, bug in `lock`" | Found the real bug **1 / 3** times; the other 2 pointed at the wrong function | ❌ **Mostly missed** |
| Clean code | "No bug" | Claimed a bug **3 / 3** times (made-up issue) | ❌ **False alarm** |

### Test 2 — reading the transaction records (no code)

| Case | Correct answer | LLM result | Verdict |
|---|---|---|---|
| Successful attack | "Attack" | Flagged **3 / 3**, described it as a fake-vault attack | ✅ **Detected** |
| Honest user, no attacker | "No attack" | Flagged **3 / 3** — misread a normal completed redemption as theft | ❌ **False alarm** |
| Attack attempt that was blocked | "Attempted, failed" | Flagged **1 / 3** | ❌ **Mostly missed** |

### Test 3 — does timing help? (same records, timing shown vs. hidden)

Normal relay delay from 40 honest runs: average **2.78s**, "suspicious" cut-off **3.60s**.
The attack's delay was **2.90s** — the same as an honest user's (2.90s). On timing alone,
the attack looks normal.

| Case | Without timing | With timing | Verdict |
|---|---|---|---|
| Successful attack | Detected 3 / 3 | Detected 3 / 3 | ➖ **No change** |
| Honest user | False alarm 3 / 3 | False alarm 3 / 3, and 2 runs now blamed timing | ❌ **Worse** |
| Blocked attempt | Flagged 1 / 3 | Flagged 3 / 3, 2 runs for wrong timing reasons | ❌ **Wrong reasons** |

## Takeaways

1. **Transaction records work better than code** for catching this attack once it has
   happened.
2. **False alarms are the biggest problem.** The model flagged clean code and honest
   transactions every time, so its "yes" can't be trusted on its own.
3. **Results vary run to run** even at temperature 0, so one run isn't enough.
4. **Timing doesn't help for this attack and can mislead the model.** That's expected:
   this attack never has to wait. Attack 4 (oracle) is where timing should matter.
5. **Caveat:** Cashio is a well-known hack the model may have read about. Group B
   attacks (5, 6, 7) will show whether results hold without that advantage.

## Files

- Vulnerable copy: `programs/variants/v1-mint-confusion/`
- Attack script: `client/src/exploits/exploit-v1.ts`
- Run everything: `scripts/run-attack-v1.sh`
- Records: `traces/v1-mint-confusion/`, normal-delay baseline in `traces/recon/`
- LLM tests: `detection/source_task.py`, `detection/trace_task.py`, `detection/ablation.py`
- Raw LLM answers: `detection/results/v1-mint-confusion-*.json`
