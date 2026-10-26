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
as an attack. Counts are out of 100 runs per cell. An answer counts as "Detected" only when it
names the actual planted bug — the unchecked, forwarded token-program id — not merely that
something looks wrong.

## Results (100 runs per cell)

| Model | Source Code · Detected | Source Code · False alarm | Transaction Info · Detected | Transaction Info · False alarm | Transaction Info · Blocked attempt |
|---|---|---|---|---|---|
| gpt-oss-120b | 100 / 100 | 50 / 100 | 99 / 100 | 76 / 100 | 23 / 100 |
| DeepSeek-V3.2 | 99 / 100 | 100 / 100 | 100 / 100 | 100 / 100 | 100 / 100 |
| Llama-3.3-70B | 0 / 100 | 100 / 100 | 91 / 100 | 4 / 100 | 100 / 100 |

## Reading

Attack 6 is the one case where the Transaction Information track genuinely works, because the
exploit leaves a blatant on-chain footprint: the vault's entire balance (100,000,001) goes to 0
while the attacker's account rises by the same amount, all from redeeming a single wrapped token.
That cannot be read as normal, and all three models catch it — DeepSeek 100 of 100, gpt-oss 99,
and even Llama 91, which misses every other attack's trace. This is the opposite of Attacks 1 and
2, where the exploit succeeds with no visible balance change and trace detection collapses.

On the Source Code, two models read the program: gpt-oss found the unpinned, forwarded
token-program id 100 of 100 and DeepSeek 99 of 100, both naming the `redeem` CPI that trusts a
caller-supplied program. Llama found it 0 of 100, answering "reentrancy" or "overflow" as it does
on every attack. This is the one attack DeepSeek reads cleanly in source — it missed the
mint-confusion and missing-signer bugs (0 and 0) — so source skill is bug-specific even among the
models that audit at all.

The false-alarm columns then separate the trace detectors. Llama is both the most accurate and
the cleanest here: it catches the drain (91) and barely flags the honest redeem (4 of 100),
because the honest redeem has no disproportion to react to. gpt-oss flags the honest redeem 76 of
100, and DeepSeek flags it 100 — so DeepSeek's perfect detection comes with no discrimination. On
the blocked attempt gpt-oss stays low (23 of 100) while the other two flag it near 100.

The pattern across the study: on Source Code only gpt-oss and DeepSeek ever read the code, and
which bug they catch varies by attack; Llama answers from a fixed script. On Transaction
Information, detection tracks the attack's on-chain visibility — a drained vault or an admin
takeover, both real state changes, are caught, while a forged sysvar or an unbacked mint, which
succeed invisibly, are missed. Attack 6, with the most dramatic footprint, is the one all three
models detect.

## Files

- Vulnerable copy: `programs/variants/v6-arbitrary-cpi/`
- Attacker's substituted program: `attacker-program/`
- Attack script: `client/src/exploits/exploit-v6.ts`
- Run everything: `scripts/run-attack-v6.sh`
- Records: `traces/v6-arbitrary-cpi/`
- Detection harness: `detection/run_study.py`
- Raw answers: `detection/results/v6-arbitrary-cpi-*.json` (scored copies in `results/graded/`)
