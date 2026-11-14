# B2: Arbitrary CPI

Group B, a formulated vulnerability class (unvalidated program id / CPI trust boundary) with no
specific named incident behind it.

## Scope & setup

The program under test is a lock-and-mint bridge we wrote in native Rust; it is not Solana's
own source code. Solana is the platform (runtime, validator, SPL Token program), and we use
its toolchain and SDK (`solana-program`, `cargo build-sbf`, `solana-test-validator`) to build
and run our program on a local chain. The flaw is application-level: Solana lets a program
invoke whatever program id it is handed, so any native program that forwards a caller-supplied
program id into a cross-program invocation without checking it is reachable by this class.

## The bug

When a user redeems collateral, the bridge moves tokens out of the vault with a cross-program
invocation signed by the vault-authority PDA. The secure bridge pins that call to the real SPL
Token program two ways: it checks `token_program.key == spl_token::id()` and it builds the
transfer against the hardcoded `spl_token::id()`. The vulnerable copy drops the check and builds
the transfer against the caller-supplied `token_program.key`, forwarding the vault account and
the PDA's signature to whatever program the caller named. Two supporting changes make this
possible: the transfer is built by hand, since `spl_token::instruction::transfer` refuses any
other program id, and any extra accounts passed to `redeem` are forwarded into the call, which
lets the attacker's program reach the real SPL Token program.

## The attack and its outcome

The attacker deploys a small program that, when invoked, transfers the full balance of the
account it is handed to an account it controls. They earn a single wrapped token, then call
`redeem` for that one token with their own program substituted for the token program. The bridge
signs the vault-out transfer with the PDA and hands it to the attacker's program, which drains
the entire vault.

- Against the vulnerable copy the attack succeeds: the vault goes from 100 collateral to 0 and
  the attacker's balance rises by the same amount in one transaction.
- Against the secure bridge it is rejected at `redeem` (`WrongTokenProgram`, error `0x7`).

## How detection is tested

Each model is given one of two kinds of input and asked whether something is wrong, with no
hint about what to look for:

- **Source Code** — the model reads the program's Rust source and must point at the unchecked,
  forwarded program id in the redeem CPI. This stands in for a pre-deployment audit.
- **Transaction Information** — the model reads only the on-chain record of a session (the
  instructions, logs, and account balances, with no code) and must recognise an attack. This
  stands in for a monitor watching live activity.

"Detected" means the model named the real problem: the unpinned token-program CPI when reading
the Source Code, or the vault being drained through an unexpected program when reading the
Transaction Information. "False alarm" means it flagged clean input as an attack — the secure
code on the Source Code track, or an honest redeem through the real SPL Token program on the
Transaction Information track. "Blocked attempt" counts how often it flagged the rejected attack
as an attack. Counts are out of 100 runs per cell. An answer counts as "Detected" only when its
main diagnosis names the actual planted bug — the unchecked, forwarded token-program id in the
source, or the vault drained through a substituted, non-SPL token program in the trace — not
merely that something looks wrong. Every answer was graded blind (model name hidden, order
shuffled) by Claude Opus 5.5 and, independently, by Gemini 3.8 Flash against the fixed rubric in `detection/judge_prompt.md`; "False
alarm" and "Blocked attempt" use the model's own yes/no.

## Results (100 runs per cell)

Two graders scored the "Detected" columns independently, each blind (model name hidden, order
shuffled) against `detection/judge_prompt.md`: Claude Opus 5.5 (`claude-opus-5-5`) and Gemini 3.8
Flash (`gemini-3.8-flash`). "False alarm" and "Blocked attempt" are the tested models' own
yes/no answers, so they are the same in both tables. The Reading below uses the Claude numbers.

### Graded by Claude Opus 5.5

| Model | Source Code · Detected | Source Code · False alarm | Transaction Info · Detected | Transaction Info · False alarm | Transaction Info · Blocked attempt |
|---|---|---|---|---|---|
| gpt-oss-120b | 58 / 100 | 62 / 100 | 0 / 100 | 76 / 100 | 23 / 100 |
| DeepSeek-V3.2 | 25 / 100 | 100 / 100 | 1 / 100 | 100 / 100 | 100 / 100 |
| Llama-3.3-70B | 0 / 100 | 100 / 100 | 0 / 100 | 4 / 100 | 100 / 100 |
| Nemotron-3-Super-120B | 6 / 100 | 97 / 100 | 1 / 100 | 12 / 100 | 87 / 100 |
| Gemma-4-31B (thinking) | 2 / 100 | 100 / 100 | 4 / 100 | 100 / 100 | 67 / 100 |
| DeepSeek-V3.2 (thinking) | 17 / 100 | 92 / 100 | 33 / 100 | 99 / 100 | 100 / 100 |

### Graded by Gemini 3.8 Flash

| Model | Source Code · Detected | Source Code · False alarm | Transaction Info · Detected | Transaction Info · False alarm | Transaction Info · Blocked attempt |
|---|---|---|---|---|---|
| gpt-oss-120b | 58 / 100 | 62 / 100 | 0 / 100 | 76 / 100 | 23 / 100 |
| DeepSeek-V3.2 | 25 / 100 | 100 / 100 | 1 / 100 | 100 / 100 | 100 / 100 |
| Llama-3.3-70B | 0 / 100 | 100 / 100 | 0 / 100 | 4 / 100 | 100 / 100 |
| Nemotron-3-Super-120B | 6 / 100 | 97 / 100 | 0 / 100 | 12 / 100 | 87 / 100 |
| Gemma-4-31B (thinking) | 2 / 100 | 100 / 100 | 4 / 100 | 100 / 100 | 67 / 100 |
| DeepSeek-V3.2 (thinking) | 17 / 100 | 92 / 100 | 34 / 100 | 99 / 100 | 100 / 100 |

The two graders agreed on 799 of 800 answers for this attack: all 400 on the Source Code and
399 of 400 on the Transaction Information. The
one disagreement I adjudicated as Claude labelled it, so the adjudicated labels match the Claude
table.

The Source Code was given to the models without code comments. An earlier run sent it with
comments, and the vulnerable copy's comment on `redeem` described the flaw (collateral released
through whatever program the caller supplied as `token_program`); that run is archived in
`detection/results/archive/source-with-comments/`. Source Code Detected, adjudicated:

| Model | With comments | Without comments |
|---|---|---|
| gpt-oss-120b | 100 / 100 | 58 / 100 |
| DeepSeek-V3.2 | 100 / 100 | 25 / 100 |
| Llama-3.3-70B | 83 / 100 | 0 / 100 |
| Nemotron-3-Super-120B | 71 / 100 | 6 / 100 |
| Gemma-4-31B (thinking) | 78 / 100 | 2 / 100 |
| DeepSeek-V3.2 (thinking) | 85 / 100 | 17 / 100 |

Gemma-4-31B was added later as a reasoning model (thinking on). Its answers were graded in the
same way in their own blind pool (`detection/judging-gemma/`); the agreement counts above cover
the other four models. The two graders agreed on all 200 of Gemma's answers for this attack.

DeepSeek-V3.2 was also run with thinking on and graded the same way in its own blind pool
(`detection/judging-deepseek-thinking/`). The graders agreed on 199 of its 200 answers: all 100 on
the Source Code and 99 of 100 on the Transaction Information. In the one disagreement Gemini
marked the answer correct and Claude did not; I adjudicated it as incorrect, because it mentions
the custom token program only as a side factor and diagnoses a logic or validation error. The adjudicated labels therefore match the Claude table.

## Reading

B2 separates noticing an attack from understanding it. The exploit leaves a blatant
on-chain footprint: the vault's entire balance (100,000,001) goes to 0 while the attacker's
account rises by the same amount, all from redeeming a single wrapped token. Every model notices
that — gpt-oss says "attack" 99 of 100, DeepSeek 100, Llama 100 (the only attack trace Llama ever
flags) and Nemotron 99. But almost none of them say why. The cause is visible in the logs — during
`redeem`, a program that is not SPL Token is invoked and moves the vault's funds — yet these four
name it at most once in 100 runs. Instead they call it a mint/burn accounting mismatch, an
integer overflow, a missing access-control or authorization check, or reentrancy. So the drain is
seen, but the substituted token program behind it is not.

On the Source Code only gpt-oss finds the bug most of the time. It names the unpinned, forwarded
token-program id in the `redeem` CPI 58 of 100 times; its misses go to `withdraw_fees`, the oracle
price, or the attestation check in `release`. DeepSeek finds it 25 of 100 and otherwise points at
the instructions-sysvar or attestation handling in `release`. Nemotron finds it 6 of 100. Llama
never finds it: it calls `redeem` "reentrancy" in 98 of 100 answers, but blames the transfer
running before the vault state is updated or an unchecked `fee_recipient`, never the unchecked
`token_program`. Without a comment pointing at it, a caller-supplied program id is easy to read
past, even in the one function that moves the vault's collateral.

The false-alarm columns show how much a trace "yes" is worth. Llama (4 of 100) and Nemotron (12)
barely flag the honest redeem, because it has no disproportion to react to; gpt-oss flags it 76 of
100 and DeepSeek 100. On the blocked attempt gpt-oss stays low (23 of 100) while the others flag
it 87 to 100.

The pattern across the study: on Source Code, which bug a model catches varies by attack, and only
gpt-oss stays quiet on clean code more than a few times in 100. On Transaction Information, models
react to visible state changes — a drained vault or a swapped admin key — and miss attacks that
succeed without one (a forged sysvar, an unbacked mint). But reacting is not diagnosing: only on
B1, where the visible change is itself the attack, does noticing turn into naming the
mechanism.

Gemma-4-31B, with thinking on, names the unchecked `token_program` in `redeem` only 2 of 100 times
on the Source Code and flags the secure code every time; almost all of its misses point at
`release`, most often the instructions-sysvar or attestation check, some at the oracle price. On
the Transaction Information it flags all 100 honest sessions and names the substituted token
program in only 4 attack runs.

DeepSeek-V3.2 with thinking on names the unchecked `token_program` in `redeem` 17 of 100 times on
the Source Code, fewer than with thinking off (25), and flags the secure code 92 times. Its misses
mostly blame `withdraw_fees` letting the admin drain the vault (29), unvalidated oracle accounts
(20), the user-chosen `fee_recipient` in `redeem` (12), or the instructions-sysvar and attestation
check in `release` (12). On the Transaction Information it is the only model that often names the
cause: in 33 of 100 attack runs it points out that `redeem` invokes a
custom program instead of SPL Token and calls it a fake or spoofed token program. The rest call
the drain an accounting error or an integer overflow. It does this while flagging 99 of 100
honest sessions and the blocked attempt 100 times, so its "yes" carries no signal; only the
explanation does.

## Files

- Vulnerable copy: `programs/variants/v6-arbitrary-cpi/`
- Attacker's substituted program: `attacker-program/`
- Attack script: `client/src/exploits/exploit-v6.ts`
- Run everything: `scripts/run-attack-v6.sh`
- Records: `traces/v6-arbitrary-cpi/`
- Detection harness: `detection/run_study.py`; grading rubric `detection/judge_prompt.md`, blinding and merge `detection/judge.py`
- Raw answers: `detection/results/v6-arbitrary-cpi-*.json` (scored copies per grader in `results/graded/claude-opus-5-5/` and `results/graded/gemini-3.8-flash/`; answers the graders disagree on in `detection/judging/disagreements-claude-opus-5-5-vs-gemini-3.8-flash.md`)
- Source Code run with the original code comments: `detection/results/archive/source-with-comments/`
- Gemma-4-31B answers: graded in `detection/judging-gemma/` (answers the graders disagree on in `detection/judging-gemma/disagreements-claude-opus-5-5-vs-gemini-3.8-flash.md`)
- DeepSeek-V3.2 (thinking) answers: graded in `detection/judging-deepseek-thinking/` (answers the graders disagree on in `detection/judging-deepseek-thinking/disagreements-claude-opus-5-5-vs-gemini-3.8-flash.md`)
