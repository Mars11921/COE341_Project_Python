              /SUM Function
SUM:    HEX 0
        CLA
        STA S_SUM
        LDA L_SIZE
        CMA
        INC
        STA L_CTR       / Create negative counter
S_LOOP: LDA L_PTR I     / Indirect load from pointer
        ADD S_SUM
        STA S_SUM
        ISZ L_PTR       / Increment pointer
        ISZ L_CTR       / Increment counter
        BUN S_LOOP
        LDA S_SUM
        BUN SUM I

            /MEAN Function
MEAN:   HEX 0
        BSA SUM         / Calculate Sum first
        STA AC_TMP
        LDA L_SIZE
        STA FNC_IN      / Set divisor for DIV_SW
        LDA AC_TMP
        BSA DIV_SW      / AC = Sum / Size
        BUN MEAN I

            /SAD Function
SAD:    HEX 0
        CLA
        STA S_SAD
        LDA L_SIZE
        CMA
        INC
        STA L_CTR
SAD_L:  LDA L_PTR2 I
        CMA
        INC
        ADD L_PTR I     / AC = A[i] - B[i]
        SPA             / Skip if result is positive
        BUN SAD_NEG
        BUN SAD_ADD
SAD_NEG:CMA             / Convert negative to positive (Absolute Value)
        INC
SAD_ADD:ADD S_SAD
        STA S_SAD
        ISZ L_PTR
        ISZ L_PTR2
        ISZ L_CTR
        BUN SAD_L
        LDA S_SAD
        BUN SAD I

            /MSE Function
MSE:    HEX 0
        CLA
        STA S_MSE
        LDA L_SIZE
        CMA
        INC
        STA L_CTR
MSE_L:  LDA L_PTR2 I
        CMA
        INC
        ADD L_PTR I     / AC = (A[i] - B[i])
        STA FNC_IN      / Prep for squaring
        BSA MUL_SW      / AC = (A[i] - B[i])^2
        ADD S_MSE
        STA S_MSE
        ISZ L_PTR
        ISZ L_PTR2
        ISZ L_CTR
        BUN MSE_L
        LDA S_MSE
        STA AC_TMP
        LDA L_SIZE
        STA FNC_IN
        LDA AC_TMP
        BSA DIV_SW      / AC = Sum of Squares / Size
        BUN MSE I

            /VAR Function
VAR:    HEX 0
        STA V_PTR_TMP   / Backup pointer
        BSA MEAN
        STA V_AVG       / Calculate Mean (mu)
        CMA
        INC
        STA V_AVG_NEG   / -mu
        LDA V_PTR_TMP
        STA L_PTR       / Restore pointer
        CLA
        STA S_VAR
        LDA L_SIZE
        CMA
        INC
        STA L_CTR
V_LOOP: LDA L_PTR I
        ADD V_AVG_NEG   / (x - mu)
        STA FNC_IN
        BSA MUL_SW      / (x - mu)^2
        ADD S_VAR
        STA S_VAR
        ISZ L_PTR
        ISZ L_CTR
        BUN V_LOOP
        LDA S_VAR
        STA AC_TMP
        LDA L_SIZE
        STA FNC_IN
        LDA AC_TMP
        BSA DIV_SW      / Variance result
        BUN VAR I

            /STDEV Function
STDEV:  HEX 0
        BSA VAR         / Get Variance
        BSA SQRT        / Call SQRT subroutine (approximate)
        BUN STDEV I
