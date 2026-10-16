use solana_program::{
    account_info::{next_account_info, AccountInfo},
    entrypoint,
    entrypoint::ProgramResult,
    program_error::ProgramError,
    pubkey::Pubkey,
};

entrypoint!(process_instruction);

// Test helper: copies the instruction data verbatim into the first account's data. Used by the
// Attack 2 exploit to stage a fabricated instructions-sysvar account on the local validator;
// not part of the bridge.
fn process_instruction(program_id: &Pubkey, accounts: &[AccountInfo], data: &[u8]) -> ProgramResult {
    let target = next_account_info(&mut accounts.iter())?;
    if target.owner != program_id {
        return Err(ProgramError::IllegalOwner);
    }
    let mut buf = target.data.borrow_mut();
    if data.len() > buf.len() {
        return Err(ProgramError::AccountDataTooSmall);
    }
    buf[..data.len()].copy_from_slice(data);
    Ok(())
}
