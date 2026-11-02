# Attack 6: Arbitrary CPI

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
the PDA's signature to whatever program the caller named.

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
| gpt-oss-120b | 100 / 100 | 50 / 100 | 0 / 100 | 76 / 100 | 23 / 100 |
| DeepSeek-V3.2 | 100 / 100 | 100 / 100 | 1 / 100 | 100 / 100 | 100 / 100 |
| Llama-3.3-70B | 83 / 100 | 100 / 100 | 0 / 100 | 4 / 100 | 100 / 100 |
| Nemotron-3-Super-120B | 71 / 100 | 99 / 100 | 1 / 100 | 12 / 100 | 87 / 100 |

### Graded by Gemini 3.8 Flash

| Model | Source Code · Detected | Source Code · False alarm | Transaction Info · Detected | Transaction Info · False alarm | Transaction Info · Blocked attempt |
|---|---|---|---|---|---|
| gpt-oss-120b | 100 / 100 | 50 / 100 | 0 / 100 | 76 / 100 | 23 / 100 |
| DeepSeek-V3.2 | 100 / 100 | 100 / 100 | 1 / 100 | 100 / 100 | 100 / 100 |
| Llama-3.3-70B | 70 / 100 | 100 / 100 | 0 / 100 | 4 / 100 | 100 / 100 |
| Nemotron-3-Super-120B | 71 / 100 | 99 / 100 | 0 / 100 | 12 / 100 | 87 / 100 |

The two graders agreed on 784 of 800 answers for this attack: 385 of 400 on the Source Code
(Cohen's kappa 0.84) and 399 of 400 on the Transaction Information (kappa 0.67, from a single
answer). The Llama Source Code gap (83 vs 70) comes from answers headed "reentrancy" that name
the missing `token_program` check (see Reading); Gemini split near-identical answers of this kind
both ways. I adjudicated the 16 disagreements; the adjudicated labels match the Claude table, so
Llama's Source Code Detected is 83.

### Timing ablation (Transaction Information, timing hidden vs. shown)

The traces above have every timing field removed. Here the same three sessions were run again,
100 times each, with the step times (submitted, confirmed, slot) left in. "Timing hidden"
repeats the numbers from the tables above. "Detected" is scored by each grader as above; "False
alarm" and "Blocked attempt" are the models' own yes/no, so they are the same in both tables.

#### Graded by Claude Opus 5.5

| Model | Timing hidden · Detected | Timing shown · Detected | Timing hidden · False alarm | Timing shown · False alarm | Timing hidden · Blocked attempt | Timing shown · Blocked attempt |
|---|---|---|---|---|---|---|
| gpt-oss-120b | 0 / 100 | 0 / 100 | 76 / 100 | 0 / 100 | 23 / 100 | 98 / 100 |
| DeepSeek-V3.2 | 1 / 100 | 0 / 100 | 100 / 100 | 100 / 100 | 100 / 100 | 100 / 100 |
| Llama-3.3-70B | 0 / 100 | 0 / 100 | 4 / 100 | 0 / 100 | 100 / 100 | 100 / 100 |
| Nemotron-3-Super-120B | 1 / 100 | 1 / 100 | 12 / 100 | 6 / 100 | 87 / 100 | 86 / 100 |

#### Graded by Gemini 3.8 Flash

| Model | Timing hidden · Detected | Timing shown · Detected | Timing hidden · False alarm | Timing shown · False alarm | Timing hidden · Blocked attempt | Timing shown · Blocked attempt |
|---|---|---|---|---|---|---|
| gpt-oss-120b | 0 / 100 | 0 / 100 | 76 / 100 | 0 / 100 | 23 / 100 | 98 / 100 |
| DeepSeek-V3.2 | 1 / 100 | 0 / 100 | 100 / 100 | 100 / 100 | 100 / 100 | 100 / 100 |
| Llama-3.3-70B | 0 / 100 | 0 / 100 | 4 / 100 | 0 / 100 | 100 / 100 | 100 / 100 |
| Nemotron-3-Super-120B | 0 / 100 | 1 / 100 | 12 / 100 | 6 / 100 | 87 / 100 | 86 / 100 |

The graders agreed on all 400 timing-shown attack answers (kappa 1.00).

## Reading

Attack 6 separates noticing an attack from understanding it. The exploit leaves a blatant
on-chain footprint: the vault's entire balance (100,000,001) goes to 0 while the attacker's
account rises by the same amount, all from redeeming a single wrapped token. Every model notices
that — gpt-oss says "attack" 99 of 100, DeepSeek 100, Llama 100 (the only attack trace Llama ever
flags) and Nemotron 99. But almost none of them say why. The cause is visible in the logs — during
`redeem`, a program that is not SPL Token is invoked and moves the vault's funds — yet the models
name it at most once in 100 runs. Instead they call it a mint/burn accounting mismatch, an
integer overflow, a missing access-control or authorization check, or reentrancy. So the drain is
seen, but the substituted token program behind it is not.

On the Source Code the picture is the reverse: the bug is found readily. gpt-oss and DeepSeek
found the unpinned, forwarded token-program id 100 of 100, both naming the `redeem` CPI that
trusts a caller-supplied program. Llama found it 83 of 100 — it usually labels the class
"reentrancy," but the missing check it points to is exactly that `token_program` is never
verified to be SPL Token before `invoke_signed`, so the mechanism is right even when the label is
not. Nemotron found it 71 of 100. This is the attack DeepSeek and Llama read best in source — both
miss the mint-confusion and missing-signer bugs — so source skill is bug-specific even among the
models that audit at all.

The false-alarm columns show how much a trace "yes" is worth. Llama (4 of 100) and Nemotron (12)
barely flag the honest redeem, because it has no disproportion to react to; gpt-oss flags it 76 of
100 and DeepSeek 100. On the blocked attempt gpt-oss stays low (23 of 100) while the others flag
it 87 to 100.

The pattern across the study: on Source Code, which bug a model catches varies by attack, and only
gpt-oss stays quiet on clean code any of the time. On Transaction Information, models react to
visible state changes — a drained vault or a swapped admin key — and miss attacks that succeed
without one (a forged sysvar, an unbacked mint). But reacting is not diagnosing: only on Attack 5,
where the visible change is itself the attack, does noticing turn into naming the mechanism.

With the step times shown, detection stays at 0 or 1 for every model. gpt-oss changes its calls
sharply: false alarms on the honest session drop from 76 to 0 and it flags the blocked attempt 98
times instead of 23, so it behaves more like a monitor reacting to failed transactions, without
coming any closer to naming the substituted token program.

## Files

- Vulnerable copy: `programs/variants/v6-arbitrary-cpi/`
- Attacker's substituted program: `attacker-program/`
- Attack script: `client/src/exploits/exploit-v6.ts`
- Run everything: `scripts/run-attack-v6.sh`
- Records: `traces/v6-arbitrary-cpi/`
- Detection harness: `detection/run_study.py`; grading rubric `detection/judge_prompt.md`, blinding and merge `detection/judge.py`
- Raw answers: `detection/results/v6-arbitrary-cpi-*.json` (scored copies per grader in `results/graded/claude-opus-5-5/` and `results/graded/gemini-3.8-flash/`; answers the graders disagree on in `detection/judging/disagreements-claude-opus-5-5-vs-gemini-3.8-flash.md`)
- Timing-shown runs: `detection/results/v6-arbitrary-cpi-timing-*.json` (scored copies in the same grader folders; answers the graders disagree on in `detection/judging/disagreements-timing-claude-opus-5-5-vs-gemini-3.8-flash.md`)
