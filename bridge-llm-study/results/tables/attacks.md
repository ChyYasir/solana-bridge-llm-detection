# The four planted attacks

Each variant removes this check from the secure bridge (B2 also forwards the call to the caller's program). Real-world basis: Cashio and Wormhole are incidents; B1 and B2 are classes from the Ackee Blockchain list of common Solana attack vectors (https://github.com/Ackee-Blockchain/solana-common-attack-vectors).

| Attack | Real-world basis | Function | Check removed | Exploit (attacker) | Secure bridge |
|---|---|---|---|---|---|
| A1 mint confusion | Cashio (2022) | `lock` | deposited mint equals the approved collateral mint | deposits 500,000 of a worthless self-made token and receives 500,000 real wrapped tokens | `WrongMint` |
| A2 sysvar spoof | Wormhole (2022) | `release` | instructions sysvar is the real sysvar address | passes a fake instruction list with a dummy Ed25519 check; wrapped tokens are minted with no relay signature | `UnsupportedSysvar` |
| B1 missing signer | Signer authorization (Solana audit class) | `require_admin` | admin account signed (key match kept) | calls set_admin with the real admin's key but no signature and makes itself admin | `MissingSignature` |
| B2 arbitrary CPI | Arbitrary CPI (Solana audit class) | `redeem` | token program is the real SPL Token program | passes its own program as the token program; redeeming one wrapped token drains the vault | `WrongTokenProgram` |
