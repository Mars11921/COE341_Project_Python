from typing import List, Optional   # import typing helpers
from mano_computer import Computer  # import hardware module 
from profiler import Profiler       # import profiler module 


class ControlUnit:
    """
    Implements the sequential and combinational logic for Mano's Basic Computer.
    """

    def __init__(self, computer, profiler=None):
        # store links to hardware and profiler
        self.computer = computer 
        self.profiler = profiler

        # cached state for current instruction
        self.ir: int = 0         
        self.opcode: int = 0     
        self.I: int = 0          
        self.halted: bool = False
        # list used to log memory accesses per cycle
        self.memory_access_log = []

        # info used by maryam's cli
        self._last_micro_op: str = ""
        self._last_changed: List[str] = []

    # main public api called by cli each clock
    def next_cycle(self) -> dict:
        """
        Executes exactly ONE clock cycle (T0, T1, ..., Tn).
        Returns a dictionary containing the state report for the CLI.
        """
        # if already halted, return status without doing anything
        if self.halted:
            return {'instruction': self.ir, 'micro_operation': "HLT: Machine already halted", 'changed': [], 'halted': True}

        self._last_changed = [] # reset changed elements list
        instruction_complete = False # track if full instruction finished this cycle
        
        current_sc = self.computer.get_register('SC')  # read sequence counter from hardware

        # choose micro-operation based on sc
        if current_sc == 0:
            self._t0_fetch()
        elif current_sc == 1:
            self._t1_fetch()
        elif current_sc == 2:
            self._t2_decode()
        elif current_sc == 3:
            instruction_complete = self._t3_decode_or_register_reference()
        else:
            # execution phase t4, t5, ...
            instruction_complete = self._execute_memory_reference()

        # tell profiler that one cycle has passed
        if self.profiler is not None:
            self.profiler.log_cycle()

        # update sequence counter in hardware
        if instruction_complete:
            self.computer.set_register('SC', 0)  # reset sc when instruction done
        elif not self.halted:
            self.computer.set_register('SC', current_sc + 1)  # move to next t-state

        # return snapshot of current state for cli
        return {
            'instruction': self.ir,
            'micro_operation': self._last_micro_op,
            'changed': list(self._last_changed),
            'halted': self.halted,
        }
        

    # small helpers for register access
    def _get(self, reg: str) -> int:
        """Helper to get a register value."""
        return self.computer.get_register(reg) 

    def _set(self, reg: str, value: int) -> None:
        """Helper to set a register value and log the change."""
        self.computer.set_register(reg, value)
        self._last_changed.append(reg)

    def _set_E(self, value: int) -> None:
        """Helper for the E flip-flop."""
        self.computer.set_register("E", value & 0x1)  # keep 1 bit
        self._last_changed.append("E")

    # memory read/write helpers
    def _mem_read(self, address: int) -> int:
        """Read memory. The profiler logging is handled by Amira's function."""
        
        addr = address & 0x0FFF # mask to 12-bit address
        val = self.computer.memory_read(addr) & 0xFFFF  # read 16-bit word

        # log this memory read for profiler/report
        self.memory_access_log.append({
            'T_Cycle': self.computer.get_register('SC'),
            'Instruction': self.ir,
            'Type': 'READ',
            'Address': addr
        })

        return val
    

    def _mem_write(self, address: int, value: int) -> None:
        """Write memory. The profiler logging is handled by Amira's function."""
    
        addr = address & 0x0FFF  # mask to 12-bit address
        self.computer.memory_write(addr, value & 0xFFFF) # write 16-bit word
        self._last_changed.append(f"M[{addr:03X}]") # mark memory cell as changed

        # log this memory write for profiler/report
        self.memory_access_log.append({
            'T_Cycle': self.computer.get_register('SC'),
            'Instruction': self.ir,
            'Type': 'WRITE',
            'Address': addr
        })

    # fetch / decode t0–t3

    def _t0_fetch(self) -> None:
        # t0: ar <- pc
        pc = self._get("PC") # read program counter
        self._set("AR", pc) # send pc into address register

        self._last_micro_op = "T0: AR <- PC"

    def _t1_fetch(self) -> None:
        # t1: ir <- m[ar]; pc <- pc + 1
        ar = self._get("AR") # read address register
        word = self._mem_read(ar) # fetch instruction from memory

        self._set("IR", word) # load instruction register

        pc = self._get("PC") # read pc
        self._set("PC", pc + 1) # increment pc

        # cache fields for fast use during execution
        self.ir = word & 0xFFFF
        self.I = (self.ir >> 15) & 0x1
        self.opcode = (self.ir >> 12) & 0x7

        self._last_micro_op = "T1: IR <- M[AR]; PC <- PC + 1"

    def _t2_decode(self) -> None:
        # t2: ar <- ir(0–11)
        ea = self.ir & 0x0FFF # extract 12-bit address
        self._set("AR", ea)  # send effective address to ar

        self._last_micro_op = "T2: AR <- IR(0–11)"

    def _t3_decode_or_register_reference(self) -> bool:
        """Handles T3: Indirect addressing or Register-Reference execution."""
    
        if self.opcode != 7 and self.I == 1:
            # indirect memory reference: ar <- m[ar]
            ar = self._get("AR") # read address register
            ea = self._mem_read(ar) # read memory to get final address
            self._set("AR", ea & 0x0FFF) # keep 12-bit effective address

            self._last_micro_op = "T3: AR <- M[AR] (indirect addressing)"
            return False  # continue at t4
            
        elif self.opcode == 7 and self.I == 0:
            # register-reference instruction executes fully at t3
            self._execute_register_reference()
            return True
            
        elif self.opcode != 7 and self.I == 0:  # direct memory reference
            # direct memory-reference instruction, address already in ar
            self._last_micro_op = "T3: Address determined (Direct)"
            return False  # move on to execution at t4
            
        else:
            # i/o instruction (opcode 7, i = 1) or invalid -> treat as nop
            self._last_micro_op = "T3: NOP (Instruction not required or invalid)"
            if self.profiler is not None:
                self.profiler.log_instruction()
            return True

    # register-reference instructions (opcode = 7, i = 0)

    def _execute_register_reference(self) -> None:
        """Implements all register-reference instructions (HLT, CLA, INC, etc.)."""
        
        ac = self._get("AC") # read accumulator
        e = self._get("E") & 0x1 # read e bit
        pc = self._get("PC") # read program counter

        r = self.ir & 0x0FFF # function bits (low 12 bits)
        actions = [] # accumulate names of actions for display

        # cla (7800): clear ac
        if r & 0x0800:
            ac = 0
            self._set("AC", ac)
            actions.append("CLA")

        # cle (7400): clear e
        if r & 0x0400:
            e = 0
            self._set_E(e)
            actions.append("CLE")
            
        # cma (7200): complement ac
        if r & 0x0200:
            ac = (~ac) & 0xFFFF
            self._set("AC", ac)
            actions.append("CMA")

        # cme (7100): complement e
        if r & 0x0100:
            e ^= 0x1
            self._set_E(e)
            actions.append("CME")

        # cir (7080): rotate right {ac,e}
        if r & 0x0080:
            new_E = ac & 0x1 # lsb of ac to e
            new_AC = ((ac >> 1) | (e << 15)) & 0xFFFF # e into msb of ac
            ac, e = new_AC, new_E
            self._set("AC", ac)
            self._set_E(e)
            actions.append("CIR")

        # cil (7040): rotate left {ac,e}
        if r & 0x0040:
            new_E = (ac >> 15) & 0x1 # msb of ac to e
            new_AC = ((ac << 1) & 0xFFFF) | (e & 0x1)   # e into lsb of ac
            ac, e = new_AC, new_E
            self._set("AC", ac)
            self._set_E(e)
            actions.append("CIL")

        # inc (7020): increment ac
        if r & 0x0020:
            ac = (ac + 1) & 0xFFFF
            self._set("AC", ac)
            actions.append("INC")

        # spa (7010): skip if ac positive
        if r & 0x0010:
            if (ac & 0x8000) == 0:  # sign bit is 0 -> positive
                pc = (pc + 1) & 0xFFFF
                self._set("PC", pc)
                actions.append("SPA (skip)")
            else:
                actions.append("SPA (no skip)")

        # sna (7008): skip if ac negative
        if r & 0x0008:
            if ac & 0x8000:  # sign bit is 1 -> negative
                pc = (pc + 1) & 0xFFFF
                self._set("PC", pc)
                actions.append("SNA (skip)")
            else:
                actions.append("SNA (no skip)")

        # sza (7004): skip if ac zero
        if r & 0x0004:
            if ac == 0:
                pc = (pc + 1) & 0xFFFF
                self._set("PC", pc)
                actions.append("SZA (skip)")
            else:
                actions.append("SZA (no skip)")

        # sze (7002): skip if e zero
        if r & 0x0002:
            if e == 0:
                pc = (pc + 1) & 0xFFFF
                self._set("PC", pc)
                actions.append("SZE (skip)")
            else:
                actions.append("SZE (no skip)")

        # hlt (7001): halt machine
        if r & 0x0001:
            self.halted = True
            actions.append("HLT")

        # if no bits matched, treat as nop
        if not actions:
            actions.append("NOP")

        # save combined description for cli
        self._last_micro_op = "T3: " + "; ".join(actions)
        
        # count completed instruction in profiler
        if self.profiler is not None:
            self.profiler.log_instruction()

    # memory-reference instructions

    def _execute_memory_reference(self) -> bool:
        """Execute one micro-operation based on opcode."""
        
        if self.opcode == 0:  # and
            return self._instr_AND()
        elif self.opcode == 1:  # add
            return self._instr_ADD()
        elif self.opcode == 2:  # lda
            return self._instr_LDA()
        elif self.opcode == 3:  # sta
            return self._instr_STA()
        elif self.opcode == 4:  # bun
            return self._instr_BUN()
        elif self.opcode == 5:  # bsa
            return self._instr_BSA()
        elif self.opcode == 6:  # isz
            return self._instr_ISZ()
        else:
            self._last_micro_op = "Execution: Unknown opcode (NOP); SC <- 0"
            if self.profiler is not None:
                self.profiler.log_instruction()
            return True

    # memory-reference: and

    def _instr_AND(self) -> bool:
        # t4: dr <- m[ar]; t5: ac <- ac & dr; sc <- 0
        if self.computer.get_register('SC') == 4:
            ar = self._get("AR")          # read effective address
            data = self._mem_read(ar)     # read memory
            self._set("DR", data)         # store into dr
            self._last_micro_op = "T4 (AND): DR <- M[AR]"
            return False                  # need next micro-step
        elif self.computer.get_register('SC') == 5:
            ac = self._get("AC")          # read ac
            dr = self._get("DR")          # read dr
            ac = ac & dr                  # bitwise and
            self._set("AC", ac)           # update ac
            self._last_micro_op = "T5 (AND): AC <- AC & DR; SC <- 0"
            if self.profiler is not None:
                self.profiler.log_instruction()
            return True                   # instruction complete
        return True 

    # memory-reference: add

    def _instr_ADD(self) -> bool:
        # t4: dr <- m[ar]; t5: ac <- ac + dr; e <- carry; sc <- 0
        if self.computer.get_register('SC') == 4:
            ar = self._get("AR")          # read address
            data = self._mem_read(ar)     # read memory
            self._set("DR", data)         # store in dr
            self._last_micro_op = "T4 (ADD): DR <- M[AR]"
            return False
        elif self.computer.get_register('SC') == 5:
            ac = self._get("AC")          # read ac
            dr = self._get("DR")          # read dr
            total = ac + dr               # compute sum
            new_ac = total & 0xFFFF       # lower 16 bits
            new_e = (total >> 16) & 0x1   # carry out to e
            self._set("AC", new_ac)       # write new ac
            self._set_E(new_e)            # write new e
            self._last_micro_op = "T5 (ADD): {AC,E} <- AC + DR; SC <- 0"
            if self.profiler is not None:
                self.profiler.log_instruction()
            return True
        return True 

    # memory-reference: lda

    def _instr_LDA(self) -> bool:
        # t4: dr <- m[ar]; t5: ac <- dr; sc <- 0
        if self.computer.get_register('SC') == 4:
            ar = self._get("AR")          # read effective address
            data = self._mem_read(ar)     # read memory
            self._set("DR", data)         # store in dr
            self._last_micro_op = "T4 (LDA): DR <- M[AR]"
            return False
        elif self.computer.get_register('SC') == 5:
            dr = self._get("DR")          # read dr
            self._set("AC", dr)           # load ac from dr
            self._last_micro_op = "T5 (LDA): AC <- DR; SC <- 0"
            if self.profiler is not None:
                self.profiler.log_instruction()
            return True
        return True 

    # memory-reference: sta 

    def _instr_STA(self) -> bool:
        # t4: m[ar] <- ac; sc <- 0
        if self.computer.get_register('SC') == 4:
            ar = self._get("AR")          # read address
            ac = self._get("AC")          # read ac
            self._mem_write(ar, ac)       # store ac to memory
            self._last_micro_op = "T4 (STA): M[AR] <- AC; SC <- 0"
            if self.profiler is not None:
                self.profiler.log_instruction()
            return True
        return True 

    # memory-reference: bun 

    def _instr_BUN(self) -> bool:
        # t4: pc <- ar; sc <- 0
        if self.computer.get_register('SC') == 4:
            ar = self._get("AR")          # read branch target
            self._set("PC", ar)           # jump to ar
            self._last_micro_op = "T4 (BUN): PC <- AR; SC <- 0"
            if self.profiler is not None:
                self.profiler.log_instruction()
            return True
        return True 

    # memory-reference: bsa 

    def _instr_BSA(self) -> bool:
        # t4: m[ar] <- pc; t5: pc <- ar + 1; sc <- 0
        if self.computer.get_register('SC') == 4:
            ar = self._get("AR")          # read base address
            pc = self._get("PC")          # read current pc
            self._mem_write(ar, pc)       # store return address
            self._last_micro_op = "T4 (BSA): M[AR] <- PC"
            return False
        elif self.computer.get_register('SC') == 5:
            ar = self._get("AR")          # read same base address
            self._set("PC", ar + 1)       # branch to ar + 1
            self._last_micro_op = "T5 (BSA): PC <- AR + 1; SC <- 0"
            if self.profiler is not None:
                self.profiler.log_instruction()
            return True
        return True 

    # memory-reference: isz

    def _instr_ISZ(self) -> bool:
        # t4: dr <- m[ar]; t5: dr <- dr + 1; m[ar] <- dr; t6: if dr == 0 then pc <- pc + 1; sc <- 0
        if self.computer.get_register('SC') == 4:
            ar = self._get("AR")          # read address
            data = self._mem_read(ar)     # read memory
            self._set("DR", data)         # store in dr
            self._last_micro_op = "T4 (ISZ): DR <- M[AR]"
            return False
        elif self.computer.get_register('SC') == 5:
            dr = self._get("DR")          # read dr
            dr = (dr + 1) & 0xFFFF        # increment with wrap
            self._set("DR", dr)           # update dr
            ar = self._get("AR")          # read address again
            self._mem_write(ar, dr)       # write back to memory
            self._last_micro_op = "T5 (ISZ): DR <- DR + 1; M[AR] <- DR"
            return False
        elif self.computer.get_register('SC') == 6:
            dr = self._get("DR")          # read final dr
            if dr == 0:
                pc = self._get("PC")      # read pc
                self._set("PC", pc + 1)   # skip next instruction
                self._last_micro_op = "T6 (ISZ): DR == 0 -> PC <- PC + 1; SC <- 0"
            else:
                self._last_micro_op = "T6 (ISZ): DR != 0 (no skip); SC <- 0"
            if self.profiler is not None:
                self.profiler.log_instruction()
            return True
        return True
