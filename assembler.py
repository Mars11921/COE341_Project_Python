# assembler.py: Implements the Two-Pass Assembler

import re
from typing import Optional, Dict

# Defining opcodes and register-reference codes
OPCODES = {
    'AND': 0x0, 'ADD': 0x1, 'LDA': 0x2, 'STA': 0x3,
    'BUN': 0x4, 'BSA': 0x5, 'ISZ': 0x6
}

RR_CODES = {
    'CLA': 0x800, 'CLE': 0x400, 'CMA': 0x200, 'CME': 0x100,
    'CIR': 0x080, 'CIL': 0x040, 'INC': 0x020, 'SPA': 0x010,
    'SNA': 0x008, 'SZA': 0x004, 'SZE': 0x002, 'HLT': 0x001
}

#main function to perform the two-pass assembly process
def assemble_program(assembly_file: str, output_file: str) -> bool:
    
    # First Pass: Build Symbol Table (LC) so we know label addresses
    symbol_table = pass_one(assembly_file)
    
    if symbol_table is None:
        print("ASSEMBLER ERROR: Could not complete Pass 1.")
        return False
        
    # Second Pass: Generate Hex Code to output file
    pass_two(assembly_file, output_file, symbol_table)
    
    return True


# Scans the file to build the Symbol Table (Label: Address).
def pass_one(assembly_file: str) -> Optional[Dict[str, int]]:
 
    symbol_table = {}
    lc = 0  # Location Counter starts at 0. Location counter is the address of the current instruction/data.

    # Read through the assembly file line by line to build the symbol table
    try:
        with open(assembly_file, 'r') as f:
            for line_number, line in enumerate(f, 1):
                # Clean and parse the line: LABELS INSTRUCTIONS OPERANDS
                parts = re.split(r'[ \t,]+', line.strip())
                parts = [p for p in parts if p and not p.startswith('/')] # Filter comments and empty strings

                if not parts: continue

                token = parts[0]

                # Check for ORG instruction immediately
                if token == 'ORG' and len(parts) > 1:
                    lc = int(parts[1], 16) # Set LC to specified address
                    continue
                
                if token == 'END':
                    break

                # 1. Check for Label (ends with a colon)
                if token.endswith(':'):
                    label = token[:-1] # Remove colon
                    symbol_table[label] = lc # Map label to current LC
                    
                    # Shift parts to process instruction
                    parts = parts[1:]

                    if not parts:
                        lc += 1 # Reserve space for standalone label.
                        continue
                    
                    # Token must be reset to the instruction (LDA, DEC, etc.)
                    token = parts[0]
                
                # Update Location Counter for Instruction or Data
                # This ensures labeled lines correctly increment LC
                if token in OPCODES or token in RR_CODES:
                    lc += 1 
                elif token in ['HEX', 'DEC']:
                    lc += 1 
                
            return symbol_table # Successfully built symbol table

    # Handle file not found or format errors
    except FileNotFoundError:
        print(f"ASSEMBLER ERROR: Assembly file '{assembly_file}' not found.")
        return None
    except ValueError:
        print(f"ASSEMBLER ERROR: Invalid address or value format in assembly file on line {line_number}. Make sure labels are followed by a colon (:).")
        return None

# Translates instructions into hex machine code.
# Takes the symbol table from Pass 1 to resolve labels.
def pass_two(assembly_file: str, output_file: str, symbol_table: Dict[str, int]) -> None:
    
    lc = 0 # Location Counter starts at 0

    # Read through the assembly file again to generate machine code.
    with open(assembly_file, 'r') as f_asm, open(output_file, 'w') as f_hex:
        for line_number, line in enumerate(f_asm, 1):
            parts = re.split(r'[ \t,]+', line.strip())
            parts = [p for p in parts if p and not p.startswith('/')]

            if not parts: continue # Skip empty/comment lines

            token = parts[0] # First token in the line
            instruction_word = 0 # Default instruction word. This will be set below.
            
            # Handle ORG and END again to maintain LC and stop file write
            if token == 'ORG' and len(parts) > 1:
                lc = int(parts[1], 16)
                continue
            if token == 'END':
                break

            # Prepare tokens for labeled lines

            if token.endswith(':'):
                parts = parts[1:]
                if not parts:
                    # Case: Standalone label (LC was incremented in Pass 1)
                    lc += 1
                    continue
                token = parts[0]

            # Handle Machine Instructions
            # --- 1. Handle Machine Instructions ---
            if token in OPCODES:
                # Memory-Reference Instruction (LDA, ADD, etc.)
                
                I = 0
                opcode = OPCODES[token]
                
                # Check if the operand exists
                operand = parts[1] if len(parts) > 1 else '0' 
                
                # Check for the Indirect Flag: Look at the 3rd token (parts[2])
                # Note: The assembly line is [Instruction] [Operand] [I]
                # Check for Indirect Flag: Consolidate the logic
                if operand.endswith('I'): 
                    operand = operand[:-1] # Remove 'I' suffix
                    I = 1
                
                # Check for 3rd token 'I'
                elif len(parts) > 2 and parts[2] == 'I':
                    I = 1
                
                # Note: If the logic is correct, the final I-bit is correctly set to 1.
                
                # Determine Address: Look up in symbol table or parse as hex
                if operand in symbol_table:
                    address = symbol_table[operand]
                else:
                    # Assume direct hex address if not a label
                    address = int(operand, 16) 

                # Assemble the word: [I | Opcode | Address]
                instruction_word = (I << 15) | (opcode << 12) | address
                  
            elif token in RR_CODES:
                # Register-Reference Instruction (CLA, HLT, etc.)
                
                rr_code = 0
                for code_name in parts: # Check all parts for RR codes
                    if code_name in RR_CODES:
                        rr_code |= RR_CODES[code_name] # Combine codes using bitwise OR

                instruction_word = (0x7 << 12) | rr_code
                
            # Handle Pseudo-Instructions (Data)
            elif token == 'HEX' and len(parts) > 1:
                instruction_word = int(parts[1], 16)
            elif token == 'DEC' and len(parts) > 1:
                # DEC: convert decimal value to 16-bit two's complement hex
                value = int(parts[1])
                instruction_word = value & 0xFFFF
            
            
            # Write Output and Increment LC 
            
            # Write the current LC value (address)
            f_hex.write(f"{lc:04X} {instruction_word:04X}\n")
            
            # Only increment LC if an instruction/data was present
            if token in OPCODES or token in RR_CODES or token in ['HEX', 'DEC']:
                 lc += 1