# Attack 1: Mint Confusion — Analysis

**Group:** A (already-documented real-world incident — Cashio, March 2022, ~$52.8M)
**Status:** complete (build → exploit → evidence → LLM detection → analysis)

## 1. The vulnerability

The bridge's `lock` instruction accepts a deposit and records it for later crediting.
The secure version requires the deposited token's mint to match the one approved
collateral type (`collateral_mint.key() == config.approved_collateral_mint`). The
vulnerable variant (`v1-mint-confusion`) has exactly this one check removed — nothing
else differs from the secure baseline.

Without it, the bridge still correctly derives a valid, well-formed "vault" account for
whatever mint is claimed (our vault design uses one associated token account per mint,
owned by a program PDA) — so the deposit is not rejected at the token-transfer level.
The program simply never asks *whether that mint was supposed to be accepted in the
first place*.

## 2. The exploit

An attacker:
1. Creates a brand-new SPL token mint they fully control — worth nothing, backed by
   nothing.
2. Mints themselves an arbitrary amount of it.
3. Creates the (permissionless) vault account for that mint.
4. Calls `lock`, claiming this worthless token as the approved collateral, depositing
   500,000 units of it.
5. The off-chain relay — acting entirely honestly, with no way to independently verify
   collateral authenticity from on-chain state alone — signs off on the resulting message
   and calls `release`.
6. The bridge mints 500,000 real wrapped tokens to the attacker.

**Result, run against the vulnerable variant:** the attacker received 500,000 wrapped
tokens; the bridge's real vault (holding genuine users' collateral) was never touched.
Value was created from nothing.

**Negative control, run against the secure baseline:** the identical script was rejected
at the `lock` step with `custom program error: 0x3` — confirmed to be exactly
`BridgeError::WrongMint`, not an unrelated failure.

Both runs' full transaction logs, signatures, and balances are saved in
`traces/v1-mint-confusion/vulnerable.json` and `baseline.json`.

## 3. LLM detection results

Model: `deepseek-ai/DeepSeek-V3.2` (via DeepInfra), temperature 0, 3 runs per item.
Two independent tracks were tested — the model never saw both at once, and never saw
which item was which.

### Source-code track (given only the Rust source, no transaction data)

| Item | Runs correct (no false claim / correct bug found) |
|---|---|
| Secure baseline (no bug) | **0 / 3** — every run invented an unrelated, non-exploitable concern about the oracle account's data format |
| Vulnerable variant (planted bug) | **1 / 3** — only one run named the actual missing check (`lock`, `collateral_mint == approved_collateral_mint`); the other two runs pointed at different, unrelated functions |

### Trace track (given only transaction logs, signatures, and balances — no source code)

| Item | Attack correctly flagged | Vulnerability class correctly named |
|---|---|---|
| Benign (ordinary user, no attacker) | **0 / 3** — every run hallucinated a problem from the normal, correct end-state of a completed redemption | — |
| Blocked attempt (attacker tries the strike, rejected by the baseline) | **3 / 3** correctly flagged something was attempted | **0 / 3** — guessed "reentrancy," "replay," "state corruption"; never mint/collateral-related |
| Vulnerable (exploit succeeds) | **3 / 3** correctly flagged as an attack | **3 / 3** reasonably on-target ("vault impersonation / fake vault attack" — captures the real mechanism without our exact wording |

## 4. What this means

- **The model is good at noticing that *something* happened, bad at explaining *what*.**
  Every run against real attack activity (trace track) correctly said "yes, this is an
  attack" — but correctly naming the vulnerability class only happened when the attack
  actually succeeded, not when it was blocked.
- **False positives are a real, first-order problem, not a footnote.** Both tracks produced
  confident, detailed, wrong answers on their true negatives — fabricating an oracle
  concern in source code that isn't there, and misreading a normal, successful redemption's
  zero balances as evidence of theft in the trace. A detection system this confidently
  wrong on clean activity would generate constant false alarms in practice.
- **Source-code detection was inconsistent even at temperature 0**, finding the actual
  planted bug in only 1 of 3 identical runs. This suggests code-review-style detection
  needs multiple samples/votes, not a single pass, before it can be trusted.
- **Caveat on Group A framing:** Attack 1 is a well-documented, widely-written-about
  incident (Cashio). The model's awareness of "a fake-token deposit pattern" in the trace
  track may be helped by exposure to this kind of writeup during training — this is part
  of why Group B (attacks 5, 6, 7 — not tied to one famous incident) will be tested
  separately for comparison.

## 5. Artifacts

- Vulnerable variant: `programs/variants/v1-mint-confusion/`
- Exploit script: `client/src/exploits/exploit-v1.ts`
- Automated test runner: `scripts/run-attack-v1.sh`
- Evidence: `traces/v1-mint-confusion/{benign,vulnerable,baseline}.json`
- Detection harness: `detection/source_task.py`, `detection/trace_task.py`
- Raw model outputs: `detection/results/v1-mint-confusion-{source,trace}.json`
