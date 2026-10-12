use borsh::{BorshDeserialize, BorshSerialize};
use solana_program::{
    account_info::{next_account_info, AccountInfo},
    entrypoint,
    entrypoint::ProgramResult,
    program_error::ProgramError,
    pubkey::Pubkey,
    sysvar::{clock::Clock, Sysvar},
};

entrypoint!(process_instruction);

#[derive(BorshSerialize, BorshDeserialize)]
pub struct OraclePrice {
    pub price: u64,
    pub last_update_slot: u64,
}

fn process_instruction(program_id: &Pubkey, accounts: &[AccountInfo], instruction_data: &[u8]) -> ProgramResult {
    let iter = &mut accounts.iter();
    let authority = next_account_info(iter)?;
    let price_account = next_account_info(iter)?;

    if !authority.is_signer {
        return Err(ProgramError::MissingRequiredSignature);
    }
    if price_account.owner != program_id {
        return Err(ProgramError::IncorrectProgramId);
    }

    let price = u64::from_le_bytes(
        instruction_data
            .get(0..8)
            .and_then(|b| b.try_into().ok())
            .ok_or(ProgramError::InvalidInstructionData)?,
    );

    let data = OraclePrice {
        price,
        last_update_slot: Clock::get()?.slot,
    };
    data.serialize(&mut &mut price_account.data.borrow_mut()[..])?;

    Ok(())
}
