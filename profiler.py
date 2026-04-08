import os 

class Profiler:
    """
    Tracks performance metrics for the Mano Computer simulation.
    This class is instantiated once and passed to the other modules.
    """
    def __init__(self):
        # Start all our counters at zero when the simulator boots up
        self.total_cycles = 0
        self.total_instructions = 0
        self.mem_reads = 0
        self.mem_writes = 0
        # RMV print("Profiler initialized.")


    def log_cycle(self):
        """Called by the Simulation Engine for every single clock cycle."""
        # Just adds 1 to the total clock tick count
        self.total_cycles += 1


    def log_instruction(self):
        """Called by the Control Unit at the start of a new fetch."""
        # We finished one full instruction, so count it
        self.total_instructions += 1


    def log_mem_read(self):
        """Called by the Hardware in memory_read()."""
        # Tracks how many times we had to look something up in memory
        self.mem_reads += 1


    def log_mem_write(self):
        """Called by the Hardware in memory_write()."""
        # Tracks how many times we saved something to memory
        self.mem_writes += 1


    def reset(self):
        """Resets all counters to zero. Useful for re-running a program."""
        # Wipe the scoreboard clean so we can run a new program
        self.total_cycles = 0
        self.total_instructions = 0
        self.mem_reads = 0
        self.mem_writes = 0

    def get_metrics(self):
        """
        Calculates and returns a dictionary of raw metrics for the CLI.
        Called by CLIManager.
        """
        # Package up all our stats into a dictionary so the CLI can print them nicely
        return {
            'Total_Cycles': self.total_cycles,
            'Instructions_Executed': self.total_instructions,
            'Memory_Reads': self.mem_reads,
            'Memory_Writes': self.mem_writes
        }

# --- File I/O Function ---

def load_files_into_memory(computer, program_file, data_file):
    """
    Reads program.txt and data.txt and loads them into the computer's memory.
    """
    # RMV print(f"Loading files...")
    
    # This little helper function handles opening the file and reading lines
    def _parse_and_load(filename, computer_obj):
        # First, check if the file actually exists so the program doesn't crash
        if not os.path.exists(filename):
            print(f"WARNING: File '{filename}' not found. Skipping.")
            return

        # RMV print(f"  Parsing '{filename}'...")
        
        # Open the text file and go through it one line at a time
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip() # Remove any weird spaces or enter keys at the end
                if not line:
                    continue  # If the line is empty, just skip to the next one

                # The file looks like: "100 2200" (Address Value)
                # So we split it by the space in the middle
                parts = line.split()
                
                # Make sure we actually have two parts (Address and Data)
                if len(parts) == 2:
                    try:
                        # Convert the text (which is in Hex) into actual numbers
                        # int(x, 16) means "treat this string as a base-16 hex number"
                        address = int(parts[0], 16)
                        value = int(parts[1], 16)
                        
                        # Save the value into the computer's memory at that address
                        computer_obj.memory_write(address, value)
                    except ValueError:
                        # This happens if there's a typo in the file (like "100 XYZ")
                        print(f"    WARNING: Skipping invalid line: '{line}'")
                else:
                    # This happens if a line is missing data
                    print(f"    WARNING: Skipping malformed line: '{line}'")


    # actually run the loader for both the program code and the data variables
    _parse_and_load(program_file, computer)
    _parse_and_load(data_file, computer)

