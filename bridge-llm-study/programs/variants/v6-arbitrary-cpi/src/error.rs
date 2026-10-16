use solana_program::program_error::ProgramError;
use thiserror::Error;

#[derive(Error, Debug, Copy, Clone, PartialEq, Eq)]
pub enum BridgeError {
    #[error("config account is already initialized")]
    AlreadyInitialized,
    #[error("config account is not initialized")]
    NotInitialized,
    #[error("signer is not the bridge admin")]
    NotAdmin,
    #[error("deposited mint does not match the approved collateral mint")]
    WrongMint,
    #[error("sysvar account is not the official sysvar address")]
    WrongSysvar,
    #[error("oracle account is not the configured price feed")]
    WrongOracle,
    #[error("oracle price is stale")]
    StalePrice,
    #[error("invoked program is not the real SPL Token program")]
    WrongTokenProgram,
    #[error("source and destination accounts must differ")]
    DuplicateAccount,
    #[error("transfer message has already been released")]
    AlreadyReleased,
    #[error("bridge is paused")]
    BridgePaused,
    #[error("arithmetic overflow")]
    Overflow,
    #[error("account did not sign the instruction")]
    MissingSignature,
    #[error("derived PDA does not match the supplied account")]
    WrongPda,
    #[error("destination account does not belong to the attested recipient")]
    WrongRecipient,
}

impl From<BridgeError> for ProgramError {
    fn from(e: BridgeError) -> Self {
        ProgramError::Custom(e as u32)
    }
}
