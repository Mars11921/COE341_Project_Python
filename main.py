# main.py

import os
from mano_computer import Computer
from control_unit import ControlUnit
from profiler import Profiler, load_files_into_memory
from assembler import assemble_program
from CLI import CLIManager


if __name__ == "__main__":

    print("\n***************************************")
    print("*** COE 341: MANO SIMULATOR PROJECT ***")
    print("***************************************")
    print("Original Simulator Made by: Amira Azim, Farah Tawalbeh, Mariam Moghazi, Dana Khalil")
    print("Spring 2026 Appendum For The COE 341 Project Done By: Hasan Morobeid, x, x, x")
    print("Instructor: Dr. Ihab Amer")
    print("Original Program: Fall 2025")
    print("Spring 2026")
    print("--------------------------------------\n")
    
    # CONFIGURATION AND INITIALIZATION
    ASSEMBLY_FILE = "program.asm"
    HEX_FILE = "program.txt"
    DATA_FILE = "data.txt"

    profiler = Profiler()
    computer = Computer(profiler)
    control_unit = ControlUnit(computer, profiler)

    # ASSEMBLY & FILE LOAD LOGIC
    if os.path.exists(ASSEMBLY_FILE):
        assemble_program(ASSEMBLY_FILE, HEX_FILE)
    
    try:
        load_files_into_memory(computer, HEX_FILE, DATA_FILE)
    except Exception as e:
        print(f"Error: {e}. Starting with default memory state.")

    # Final setup before launch
    computer.set_register('PC', 0x100)
    profiler.reset()
        
    cli_manager = CLIManager(computer, control_unit, profiler)
    computer.set_register('PC', 0x100)
    cli_manager.start_cli()