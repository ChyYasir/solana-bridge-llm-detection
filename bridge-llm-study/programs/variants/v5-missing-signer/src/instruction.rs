use borsh::{BorshDeserialize, BorshSerialize};
use solana_program::pubkey::Pubkey;

#[derive(BorshSerialize, BorshDeserialize, Debug, Clone)]
pub enum BridgeInstruction {
    Initialize {
        fee_bps: u16,
    },

    Lock {
        amount: u64,
        recipient: Pubkey,
    },

    Release {
        nonce: u64,
    },

    Redeem {
        amount: u64,
    },

    SetFee {
        fee_bps: u16,
    },

    SetPaused {
        paused: bool,
    },

    SetAdmin {
        new_admin: Pubkey,
    },

    WithdrawFees {
        amount: u64,
    },
}
