from mano_computer import Computer

class CLIManager:

    # Manages the Command Line Interface, handling user input for inspection
    # and controlling the execution flow (cycle, instruction, program level).
    
    def __init__(self, Computer, control_unit, profiler):
        # Constructor to initialize the CLI with required simulation components.
        # It links the CLI to the hardware model (Computer), the execution logic (ControlUnit),
        # and the performance tracker (Profiler).
        # Instances of the core simulator components
        self.computer = Computer 	    # ManoComputer instance (provides register and memory access)
        self.control_unit = control_unit # ControlUnit instance (handles micro-operations and execution cycles)
        self.profiler = profiler 	    # Profiler instance (collects execution statistics)
        self.running = True             # Boolean flag to keep the main CLI loop active

    def start_cli(self):
        
        # Starts the main interactive command-line loop, which is the user's interface
        # to the Mano Basic Computer simulator.
        
        
       # RMV print("Mano Basic Computer Simulator CLI started.")
        self._display_menu() # Displays the list of available commands to the user


        while self.running:
            try: 	
                # The main loop continuously prompts the user for input.
                #NOTE:here we can try to add a menu of things that the user can ask so that they know what to input
                command = input("> ").strip()
                if not command:
                    continue # Skip processing if the input is empty
                
                parts = command.lower().split() # Tokenizes the command into parts for easy parsing (e.g., "show mem 100")

                # --- Command Dispatch Logic ---
                
                if parts[0] == "help": # Checks if the user requested the command menu.
                    self._display_menu()
                
                # --- Handle Execution Commands (next/fast/run) ---
                # Routes commands related to executing instructions or cycles to the handler.
                elif parts[0] in ["next_cycle", "next_inst", "run"] or parts[0].startswith(("fast_cycle", "fast_inst")):
                    self._handle_execution(command.lower())
                
                # --- Handle Inspection Commands (show) ---
                # Routes commands related to viewing the simulator state (registers, memory, profiler) to the handler.
                elif parts[0] == "show":
                    self._handle_show(command.lower())
                
                # --- Handle Exit Command ---
                elif parts[0] == "exit":
                    self.running = False # Terminates the main loop
                
                # --- Handle Unknown Command ---
                else:
                    print(f"Unknown command: {parts[0]}")
            
            except EOFError:
                # Catches Ctrl+D (end-of-file) to ensure a graceful shutdown.
                self.running = False
            except Exception as e:
                # Generic exception handling for runtime errors.
                print(f"An error occurred: {e}")


    # --- Inspection Command Handlers (Days 2-4) ---
    
    def _handle_show(self, command):
        # Processes 'show' commands: reg_name, mem, all, profiler.
        parts = command.split()
        if len(parts) < 2:
            print("Usage: show [reg_name | mem address [count] | all | profiler | trace]")
            return


        command_type = parts[1]
        
        # 1. show reg_name (e.g., show AC, show PC)
        if command_type in ['ac', 'dr', 'ar', 'pc', 'ir', 'tr', 'e', 'i', 'sc']:
            reg_name = command_type.upper()
            try:
                # Retrieves the current value of the specified register from the Computer instance.
                value = self.computer.get_register(reg_name)
            except KeyError:
                print(f"Error: Register '{reg_name}' not found.")
                return
            
            # Format output based on register size
            if reg_name in ['AR', 'PC']:
                # 12-bit registers (Address Register, Program Counter)
                hex_val = f"0x{value:03X}"
                #bin_val = f"{value:012b}"
                bin_val = self._format_binary(value, 12)
            elif reg_name in ['AC', 'DR', 'IR', 'TR']:
                # 16-bit registers (Accumulator, Data Register, Instruction Register, Temporary Register)
                hex_val = f"0x{value:04X}"
                #bin_val = f"{value:016b}"
                bin_val = self._format_binary(value, 16)
            elif reg_name in ['E', 'I', 'SC']:
                # Control/Flip-flop registers (E-register, Interrupt flip-flop, Sequence Counter)
                print(f"${reg_name}={value}") # Prints the value without hex/binary formatting
                return
            else:
                # Default 16-bit formatting for any other register
                hex_val = f"0x{value:04X}"
                #bin_val = f"{value:016b}"
                bin_val = self._format_binary(value, 16)
                
            # Print standard output format (e.g., $AC=0x0042 (binary: 0000 0000 0100 0010))
            print(f"${reg_name}={hex_val} (binary: {bin_val})")


        # 2. show mem address [count] (e.g., show mem 200 5)
        elif command_type == 'mem' and len(parts) >= 3:
            try:
                # Parses the memory address (accepts hexadecimal input)
                address = int(parts[2], 16)
                # Parses the optional count of memory locations to display, defaults to 1.
                count = int(parts[3]) if len(parts) == 4 else 1
                
                if address < 0 or address + count > 4096:
                    raise ValueError("Address out of bounds (0x000 - 0xFFF).")


                # Loop to read and display requested memory locations
                for i in range(count):
                    current_addr = address + i
                    # Reads the memory value, which also triggers the profiler log for a memory read.
                    value = self.computer.memory_read(current_addr)
                    
                    # Formats and prints the memory content.
                    hex_val = f"0x{value:04X}"
                    #bin_val = f"{value:016b}"
                    bin_val = self._format_binary(value, 16)
                    print(f"M[{current_addr:03X}]={hex_val} (binary: {bin_val})")
                    
            except ValueError as e:
                print(f"Invalid address or count: {e}")
            except IndexError:
                print("Missing memory address.")

        # 3. show trace (Displays memory access history)
        elif command_type == 'trace':
            # Prints a detailed, sequential log of all memory read/write operations recorded by the Control Unit.
            print("\n--- DETAILED MEMORY ACCESS TRACE ---")
            print("  CYCLE | INSTRUCTION | TYPE | ADDRESS")
            print("--------------------------------------")
            
            for entry in self.control_unit.memory_access_log:
                print(f"  T{entry['T_Cycle']:<5} | 0x{entry['Instruction']:04X} | {entry['Type']:<4} | 0x{entry['Address']:04X}")
                
        # 4. show all (Displays all major registers)
        elif command_type == 'all':
            # Calls the Computer object's method to print a full state summary.
            print(self.computer.get_all_state())


        # 5. show profiler (Displays performance metrics)
        elif command_type == 'profiler':
            self._show_profiler_data()
        
        else:
            # Handles 'show' commands with unknown sub-commands.
            print("Invalid show command.")


    # --- Execution Command Handlers ---


    def _handle_execution(self, command):
        # Processes execution commands: next_cycle, next_inst, fast_*, run.
        
        parts = command.split()
        command_type = parts[0]


        if command_type == "next_cycle":
            # Executes one clock cycle (micro-operation level) and logs the output.
            self._execute_cycle(log_output=True)
        
        elif command_type == "next_inst":
            # Executes one full instruction cycle (Fetch, Decode, Execute) and logs the summary.
            self._execute_instruction(log_output=True)
        
        elif command_type == "run":
            # Executes the program continuously until HLT is encountered.
            self._execute_run()
        
        # fast_cycle N or fast_inst N
        elif command_type.startswith(("fast_cycle", "fast_inst")):
            # Handles fast-forward execution for a specified number of steps.
            self._execute_fast(command)
    
    def _execute_cycle(self, log_output=True):
        # Executes one clock cycle (T0, T1, T2...). Calls Farah's ControlUnit.
        
        # 1. Executes one step of the instruction cycle logic.
        state_data = self.control_unit.next_cycle() 
        
        # 2. Display the state only if not in fast-forward mode
        if log_output:
            # Prints details about the micro-operation and components that changed state.
            print(f"Instruction in hand: 0x{state_data['instruction']:04X}")
            print(f"Micro-operation: {state_data['micro_operation']}")
            print(f"Changed: {', '.join(state_data['changed'])}") 
            
        # Returns the halted status, indicating if the HLT state was entered during this cycle.
        return state_data['halted']
    

    def _execute_instruction(self, log_output=True):
        # Executes one full instruction cycle (Fetch-Decode-Execute).
        
        # 1. Execute the current cycle (which starts the instruction execution)
        halted = self._execute_cycle(log_output=log_output)
        
        if halted:
            if log_output:
                print("Program halted.")
            return halted # Stops if HLT was found immediately

        # 2. Loop until the SC (Sequence Counter) resets to 0, signaling instruction completion.
        while self.computer.get_register('SC') != 0:
            # Continue running cycles, but suppress the detailed micro-op output
            halted = self._execute_cycle(log_output=False) 
            
            if halted:
                if log_output:
                    print("Program halted.")
                break

        # 3. Provide summary output (Only if HLT was not encountered)
        if not halted and log_output:
            # Prints the state of the PC and AC registers after instruction completion.
            pc_val = self.computer.get_register('PC')
            ac_val = self.computer.get_register('AC')
            # IR holds the instruction that was just executed
            print(f"Instruction executed: 0x{self.computer.get_register('IR'):04X}")
            print(f"$PC=0x{pc_val:03X} $AC=0x{ac_val:04X}")
        
        return halted


    def _execute_fast(self, command):
        # Executes N cycles or N instructions without logging every step.
        parts = command.split()
        try:
            N = int(parts[1]) # The number of steps (cycles or instructions) to execute.
        except (IndexError, ValueError):
            print("Usage: fast_cycle N or fast_inst N. N must be an integer.")
            return


        is_cycle = parts[0] == "fast_cycle"
        print(f"Executing {N} {'cycles' if is_cycle else 'instructions'}...")
        halted = False
        
        # Loops N times, executing either a cycle or a full instruction.
        for _ in range(N):
            if is_cycle:
                halted = self._execute_cycle(log_output=False) # Executes one cycle silently
            else: # fast_inst N
                halted = self._execute_instruction(log_output=False) # Executes one instruction silently
            
            if halted:
                print(f"Execution halted after reaching HLT instruction before completing {N} steps.")
                break
        
        if not halted:
            print("Fast execution completed.")
        
        # Show the final state/summary
        if not halted:
             if is_cycle:
                 # If executed by cycle, show the detailed output of the final cycle.
                 self._execute_cycle(log_output=True)
             else:
                 # If executed by instruction, show the summary output after the final instruction completes.
                 self._execute_instruction(log_output=True)


    def _execute_run(self):
        # Executes the whole program until it encounters the HLT instruction.
        print("Running program until HLT...")
        halted = False
        
        # Loops, executing instruction by instruction until HLT is reached.
        while not halted:
            # Execute instruction by instruction, suppressing output
            halted = self._execute_instruction(log_output=False)
        
        if halted:
            print("Program successfully completed (HLT encountered).")
        
        # Inspection remains available after HLT 


    # --- Profiler Command Handler (Days 8-10) ---


    def _show_profiler_data(self):
        # Displays all profiler metrics (cycles, instructions, CPI, BW).
        
        # Retrieves metrics from the Profiler instance.
        metrics = self.profiler.get_metrics()
        
        # Extracts specific metrics, using 0 as a default if a key is missing.
        total_cycles = metrics.get('Total_Cycles', 0)
        instructions_executed = metrics.get('Instructions_Executed', 0)
        memory_reads = metrics.get('Memory_Reads', 0)
        memory_writes = metrics.get('Memory_Writes', 0)
        
        # Calculates Cycles Per Instruction (CPI). Avoids division by zero.
        cpi = total_cycles / instructions_executed if instructions_executed > 0 else 0
        
        print("--- Profiler Metrics ---")
        print(f"Total cycles executed: {total_cycles}")
        print(f"Number of instructions executed: {instructions_executed}")
        print(f"Average cycles per instruction (CPI): {cpi:.2f}") 
        # Memory bandwidth is defined as the total number of memory accesses.
        print(f"Memory bandwidth (Total reads + writes): {memory_reads + memory_writes}") 
        print(f"    - Total Reads: {memory_reads}")
        print(f"    - Total Writes: {memory_writes}")


    #Function to format the binary output with spaces (0000 0000 0000 0000)
    def _format_binary(self, value: int, bits: int) -> str:
        """Converts an integer to a spaced binary string (e.g., 0000 0000)."""
        # 1. Generates a binary string padded with leading zeros to the correct bit length.
        bin_str = format(value, f'0{bits}b')
        # 2. Slices the string into 4-bit chunks and joins them with a space for readability.
        return ' '.join([bin_str[i:i+4] for i in range(0, len(bin_str), 4)])
    
    #Function to generate a menu of commands for the user
    def _get_menu_options(self) -> dict:
        """Returns the structured list of commands and descriptions."""
        return {
            # --- Execution Commands ---
            "Execution": [
                ("run", "Executes the program until the HLT instruction is reached."),
                ("next_inst", "Executes one full instruction cycle (Fetch-Decode-Execute)."),
                ("fast_inst N", "Executes N full instructions in sequence."),
                ("next_cycle", "Executes one single clock cycle (T0, T1, T2...)."),
                ("fast_cycle N", "Executes N clock cycles in sequence."),
            ],
            # --- Inspection Commands ---
            "Inspection": [
                ("show reg_name", "Shows the value and binary representation of a register (e.g., show AC)."),
                ("show mem address [count]", "Shows the value(s) in memory. NOTE: This counts as a memory read for the profiler."),
                ("show all", "Shows the current value of all major registers."),
                ("show profiler", "Displays profiler metrics (cycles, CPI, bandwidth)."),
                ("show trace", "Displays a sequential log of every memory read and write (T-cycle, Instruction, Address)."),
            ],
            # --- Control Commands ---
            "Control": [
                ("help", "Displays this list of available commands."),
                ("exit", "Exits the simulator."),
            ]
        }
    
    #Function to display the menu to the user
    def _display_menu(self) -> None:
        """Formats and prints the available commands to the console."""
        print("\n=========================================================")
        print("         Mano Basic Computer Simulator Commands")
        print("=========================================================")
        
        menu_options = self._get_menu_options()
        
        for section, commands in menu_options.items():
            print(f"\n--- {section} ---")
            for command, description in commands:
                # Use left-aligned formatting for clean columns
                print(f"{command:<25}{description}")

        print("\nReady for input. Type 'help' to show this menu.")
