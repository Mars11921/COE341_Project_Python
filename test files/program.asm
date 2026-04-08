        ORG 100
START:  LDA ADS1
        STA PTR1
        LDA ADS2
        STA PTR2
        LDA NMB
        STA CNTR

LOOP:   LDA PTR1 I
        SZA
        BUN CHECK
        ISZ CTR 

CONT:   ISZ PTR1
        ISZ CNTR
        BUN LOOP
        HLT

CHECK:  SNA
        BUN CONT
        STA PTR2 I
        ISZ PTR2
        BUN CONT

NMB:    DEC -10
CNTR:   HEX 0
ADS1:   HEX 200
PTR1:   HEX 0
ADS2:   HEX 300
PTR2:   HEX 0
CTR:    HEX 0

        ORG 200
        DEC 5
        DEC 0
        DEC 4
        DEC -2
        DEC 3
        DEC -1
        DEC 0
        DEC -4
        DEC 5
        DEC 10
        END