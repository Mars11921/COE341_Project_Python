class Computer: 

    def __init__(self, profiler):

        # reference profiler instance for logging memory accesses
        self.profiler = profiler

        # Initialize memory (4096 words, each 16 bits) with a List
        self.memory = [0] * 4096

        # Initialize all registers to 0 using a dictionary
        self.registers = {
            'AC': 0,  # 16-bit Accumulator
            'DR': 0,  # 16-bit Data Register
            'IR': 0,  # 16-bit Instruction Register
            'TR': 0,  # 16-bit Temporary Register
            'AR': 0,  # 12-bit Address Register
            'PC': 0,  # 12-bit Program Counter
            'E': 0,   # 1-bit Extend flip-flop
            'I': 0,   # 1-bit Indirect flip-flop
            'SC': 0   # 8-bit Sequence Counter (can be 0-7)
        }
    
    # allows retrieval of a register's value by name.
    def get_register(self, name):
        return self.registers[name]
    
    #Sets the value of a register and ensures it fits within its bit-width.
    def set_register(self, name, value):

        if name in ['AR', 'PC']:
            self.registers[name] = value & 0xFFF  # Make's sure it is 12-bit

        elif name in ['AC', 'DR', 'IR', 'TR']:
            self.registers[name] = value & 0xFFFF # Make's sure it is 12-bit

        elif name in ['E', 'I']:
            self.registers[name] = value & 0x1    # Make's sure it is 1-bit

        else:
            # For SC or other registers
            self.registers[name] = value

    #   Reads a 16-bit word from a memory address.
    def memory_read(self, address):
        
        # Calls profiler method to log memory read
        self.profiler.log_mem_read()
        
        # Ensure address is valid (12-bit)
        address = address & 0xFFF 
        return self.memory[address]

    # Writes a 16-bit word to a memory address.
    def memory_write(self, address, value):
        
        # Calls profiler method to log memory write
        self.profiler.log_mem_write()
        
        # Ensure address (12-bit) and value (16-bit)
        address = address & 0xFFF
        value = value & 0xFFFF
        self.memory[address] = value

    # Returns a formatted string of all registers for 'show all'.
    def get_all_state(self):
        state = ""

        for name, value in self.registers.items():

            if name in ['AR', 'PC']:
                state += f"{name}=0x{value:03X} " # 3 hex digits

            elif name in ['E', 'I']:
                state += f"{name}={value} "

            elif name == 'SC':
                 state += f"{name}={value} "

            else:
                state += f"{name}=0x{value:04X} " # 4 hex digits

        return state.strip() # Remove trailing space

    # Resets all registers and memory to 0.
    def reset(self):
        
        for name in self.registers:
            self.registers[name] = 0
        
        # Re-initialize memory
        self.memory = [0] * 4096

