use borsh::{BorshDeserialize, BorshSerialize};
use solana_program::pubkey::Pubkey;

#[derive(BorshSerialize, BorshDeserialize, Debug, Clone)]
pub enum BridgeInstruction {
    /// 0. `[signer, writable]` admin
    /// 1. `[writable]` config (PDA)
    /// 2. `[writable]` vault (PDA, becomes an SPL token account)
    /// 3. `[writable]` wrapped_mint (PDA, becomes an SPL mint)
    /// 4. `[]` approved_collateral_mint
    /// 5. `[]` oracle_feed
    /// 6. `[]` relay_authority
    /// 7. `[]` token_program
    /// 8. `[]` system_program
    Initialize {
        fee_bps: u16,
    },

    /// 0. `[signer]` user
    /// 1. `[writable]` user_token_account
    /// 2. `[writable]` vault
    /// 3. `[writable]` config
    /// 4. `[writable]` message (PDA for `config.next_nonce`)
    /// 5. `[]` token_program
    /// 6. `[]` system_program
    Lock {
        amount: u64,
        recipient: Pubkey,
    },

    /// 0. `[signer]` relay (fee payer only; authorization comes from the Ed25519 ix below)
    /// 1. `[writable]` config
    /// 2. `[writable]` message
    /// 3. `[]` instructions_sysvar — must carry an Ed25519 verify ix immediately before this one
    /// 4. `[]` oracle_feed
    /// 5. `[writable]` wrapped_mint
    /// 6. `[writable]` recipient_wrapped_account
    /// 7. `[]` token_program
    Release {
        nonce: u64,
    },

    /// 0. `[signer]` user
    /// 1. `[writable]` user_wrapped_account
    /// 2. `[writable]` wrapped_mint
    /// 3. `[writable]` vault
    /// 4. `[writable]` user_collateral_account
    /// 5. `[writable]` fee_recipient
    /// 6. `[]` config
    /// 7. `[]` token_program
    Redeem {
        amount: u64,
    },

    /// 0. `[signer]` admin
    /// 1. `[writable]` config
    SetFee {
        fee_bps: u16,
    },

    /// 0. `[signer]` admin
    /// 1. `[writable]` config
    SetPaused {
        paused: bool,
    },

    /// 0. `[signer]` admin
    /// 1. `[writable]` config
    SetAdmin {
        new_admin: Pubkey,
    },

    /// 0. `[signer]` admin
    /// 1. `[]` config
    /// 2. `[writable]` vault
    /// 3. `[writable]` admin_token_account
    /// 4. `[]` token_program
    WithdrawFees {
        amount: u64,
    },
}
