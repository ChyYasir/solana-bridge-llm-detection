use solana_program::program_error::ProgramError;

pub struct VerifiedAttestation {
    pub signer: [u8; 32],
    pub message: Vec<u8>,
}

pub fn parse_single_signature(data: &[u8]) -> Result<VerifiedAttestation, ProgramError> {
    const HEADER_LEN: usize = 14;
    if data.len() < 2 + HEADER_LEN {
        return Err(ProgramError::InvalidInstructionData);
    }
    if data[0] != 1 {
        return Err(ProgramError::InvalidInstructionData);
    }
    let header = &data[2..2 + HEADER_LEN];
    let public_key_offset = u16::from_le_bytes([header[4], header[5]]) as usize;
    let message_data_offset = u16::from_le_bytes([header[8], header[9]]) as usize;
    let message_data_size = u16::from_le_bytes([header[10], header[11]]) as usize;

    let pubkey_bytes = data
        .get(public_key_offset..public_key_offset + 32)
        .ok_or(ProgramError::InvalidInstructionData)?;
    let message_bytes = data
        .get(message_data_offset..message_data_offset + message_data_size)
        .ok_or(ProgramError::InvalidInstructionData)?;

    let mut signer = [0u8; 32];
    signer.copy_from_slice(pubkey_bytes);

    Ok(VerifiedAttestation {
        signer,
        message: message_bytes.to_vec(),
    })
}
