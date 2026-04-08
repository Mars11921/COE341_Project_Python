# COE 341 project: Mano Basic Computer Simulator

This repository contains the complete implementation of a functional simulator for Mano's Basic Computer, designed and executed by the team:
**Amira Azim | Farah Tawalbeh | Mariam Moghazi | Dana Khalil**

The simulator features a fully integrated two-pass assembler and executes the instruction cycle (Fetch-Decode-Execute) to compute performance metrics.

---

## 1. Setup and Execution

### Requirements
* **Python 3.7+**
* **VS Code** (recommended IDE)

* ### Core Files
| File Name | Purpose | Content |
| :--- | :--- | :--- |
| **`program.txt`** | **Instruction Memory** (Used WITHOUT Assembler). | Sequential list of operations in **hexadecimal machine code**. |
| **`data.txt`** | **Data Memory** (Used for all runs). | Initial values for any memory locations (variables) in hexadecimal. |
| **`program.asm`** | **Assembly Source** (Used WITH Assembler). | Assembly language source code (e.g., LDA, ADD, HLT). |

### Core Files
* `main.py` Program Launcher. Handles initialization and presents the CLI/GUI launch option.
* `control_unit.py`: Implements the fetch-decode-execute logic.
* `mano_computer.py`: Implements the registers and memory (Hardware).
* `assembler.py`: Handles assembly-to-hex translation (Bonus Feature).
* `program.txt`: Sequential list of operations the CPU must execute. 
* `program.asm`: Initial values for any memory locations.
* `data.txt`: Data Memory Input (Used for all runs).

##  Execution Instructions

### A. Core Execution (Without Assembler)

This method executes the pre-compiled **hexadecimal machine code (program.txt and data.txt)** directly.

1.  **Preparation:** Ensure your machine code and data are correctly placed in **`program.txt`** and **`data.txt`**.
2.  **Start:** Run the entry point from your terminal:
    ```bash
    python main.py
    ```

### B. Bonus Execution (With Assembler)

This method automatically translates assembly mnemonics into machine code before execution.

1.  **Preparation:** Write your program using assembly mnemonics in the **`program.asm`** file. *NOTE: Make sure no program.txt files exist as it will create a new program.txt file*
2.  **Start:** Run the entry point: `python main.py`
    *(The simulator automatically detects the `.asm` file, runs the assembler, and loads the resulting code into a `program.txt` file)*

---

## Command Line Interface (CLI)

The CLI provides control over execution speed and allows inspection of registers and memory.

### A. Execution Control
| Command | Purpose |
| :--- | :--- |
| **`run`** | Executes the entire program until the HLT instruction is reached. |
| **`next_cycle`** | Executes one single clock cycle (T0, T1, T2, etc.) for detailed tracing. |
| **`fast_cycle N`** | Executes N clock cycles in sequence. |
| **`next_inst`** | Executes one full instruction (Fetch-Decode-Execute). |
| **`fast_inst N`** | Executes N full instructions in sequence. |

### B. Inspection Commands
| Command | Output | Notes |
| :--- | :--- | :--- |
| **`show AC`** | Shows the value of the Accumulator and its grouped binary form. | None |
| **`show mem address [count]`** | Displays the value(s) in memory. | **NOTE:** This counts as a memory read for the profiler. |
| **`show all`** | Displays the state of all major registers (PC, IR, AR, AC, etc.). | None |
| **`show profiler`** | Displays total cycles, CPI, memory reads, and writes. | Verification of performance metrics. |
| **`show trace`** | Displays a sequential log of every memory read and write ($\text{T}$-cycle, Instruction, Address). | Validates $\text{CPI}$ and bandwidth metrics. |

---

## Verification and Metrics

The profiler tracks execution performance and memory utilization.

* **Total Cycles (CPI):** Measures the clock cycles required for the instruction set (e.g., LDA = 6 cycles, HLT = 4 cycles).
* **Memory Bandwidth:** Tracks the total number of memory reads and writes performed by the execution unit (excluding file loading).
