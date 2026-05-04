              /SUM Function
SUM:    HEX 0           
        CLA             / Clear the Accumulator
        STA AC_TMP      / Initialize the running total variable to 0.
        LDA L_SIZE      / Load the number of elements in the array.
        CMA             / Complement and increment to create a negative 
        INC             / counter (2's complement) for the loop.
        STA L_CTR       / Store negative count in the loop counter.
S_LOOP: LDA L_PTR I     / Load value from memory address stored in L_PTR indirectly.
        ADD AC_TMP      / Add the current running total to this value.
        STA AC_TMP      / Save the new total back to temporary storage.
        ISZ L_PTR       / Increment the pointer to point to the next array element.
        ISZ L_CTR       / Increment counter, if it reaches 0, skip the next instruction.
        BUN S_LOOP      / If counter is not 0, branch back to start of loop.
        LDA AC_TMP      / Load final sum into AC for the caller.
        BUN SUM I       / Return to the main program (Indirect branch).

            /MEAN Function
MEAN:   HEX 0           
        BSA SUM         / Branch and Save Address to SUM; result returns in AC.
        STA DIV1        / Store Sum in DIV1 (dividend from the DIV_SW routine).
        LDA L_SIZE      / Load array size.
        STA FNC_IN      / Store size in FNC_IN (divisor).
        BSA DIV_SW      / Call our library's standard division.
        BUN MEAN I      / Return, and the result is already in AC.

            /SAD Function
SAD:    HEX 0           / Return address.
        CLA             / Clear AC.
        STA AC_TMP      / Initialize running sum to 0.
        LDA L_SIZE      / Setup negative loop counter (same as SUM).
        CMA
        INC
        STA L_CTR
SAD_L:  LDA L_PTR I     / Load element from Array A.
        CMA             / Convert A[i] to negative.
        INC
        ADD L_PTR2 I    / Add element from Array B: AC = B[i] - A[i].
        SPA             / Skip next if AC is positive (already absolute).
        BUN ABS_V       / If negative, jump to make it positive.
        BUN SAD_ADD     / If positive, proceed to add to total.
ABS_V:  CMA             / Convert negative result to positive (2's complement).
        INC
SAD_ADD:ADD AC_TMP      / Add this absolute difference to our running total.
        STA AC_TMP      / Save updated total.
        ISZ L_PTR       / Move pointer A to next element.
        ISZ L_PTR2      / Move pointer B to next element.
        ISZ L_CTR       / Increment counter and check if loop finished.
        BUN SAD_L       / Repeat if counter is not 0.
        LDA AC_TMP      / Load final SAD total into AC.
        BUN SAD I       / Return

            /MSE Function
MSE:    HEX 0           / Return Address slot.
        CLA             / Clear AC.
        STA S_MSE       / Initialize the running sum of squares to 0.
        LDA L_SIZE      / Setup negative loop counter.
        CMA
        INC
        STA L_CTR       / L_CTR = -L_SIZE.
MSE_L:  LDA L_PTR I     / Load element A[i] from first array.
        CMA
        INC             / Negate A[i].
        ADD L_PTR2 I    / Add B[i]: AC = B[i] - A[i] (the error).
        STA FNC_IN      / Store error in FNC_IN as the multiplier.
        BSA MUL_SW      / AC = AC * FNC_IN (Squares the error).
        ADD S_MSE       / Add this squared error to the running sum.
        STA S_MSE       / Save updated sum of squares.
        ISZ L_PTR       / Increment pointer for Array A.
        ISZ L_PTR2      / Increment pointer for Array B.
        ISZ L_CTR       / Increment counter; check if loop is done.
        BUN MSE_L       / Repeat if counter is not zero.
        LDA S_MSE       / Load total sum of squares into AC.
        STA DIV1        / Prepare as Dividend for division.
        LDA L_SIZE      / Load total number of elements.
        STA FNC_IN      / Set as Divisor.
        BSA DIV_SW      / AC = SumOfSquares / Size.
        BUN MSE I       / Return to caller with MSE in AC.

            /VAR Function
VAR:    HEX 0           / Return Address.
        BSA MEAN        / First, find the average (Mean) of the array.
        STA AVG_VAL     / Save the Mean for subtraction in the loop.
        CLA
        STA S_MSE       / Reuse variable to store sum of squared differences.
        LDA L_SIZE      / Setup negative loop counter.
        CMA
        INC
        STA L_CTR
V_LOOP: LDA L_PTR I     / Load x[i].
        CMA
        INC             / -x[i].
        ADD AVG_VAL     / AC = Mean - x[i] (the deviation).
        STA FNC_IN      / Store deviation as multiplier.
        BSA MUL_SW      / AC = deviation * deviation (Squares it)[cite: 5, 7].
        ADD S_MSE       / Accumulate squared deviation.
        STA S_MSE
        ISZ L_PTR       / Move to next element.
        ISZ L_CTR       / Loop control.
        BUN V_LOOP
        LDA S_MSE       / Load total sum of squared deviations.
        STA DIV1        / Set as Dividend.
        LDA L_SIZE
        STA FNC_IN      / Set as Divisor.
        BSA DIV_SW      / AC = Sum / Size.
        BUN VAR I       / Return.

            /STDEV Function
STDEV:  HEX 0           / Return Address.
        BSA VAR         / Calculate Variance first; result is in AC.
        BSA SQRT_SW     / Call software square root routine.
        BUN STDEV I     / Return result in AC.

/--- Software Square Root (Integer Approximation) ---
SQRT_SW: HEX 0          / Return Address.
         STA S_VAL      / Store the Variance value.
         CLA
         STA S_RES      / Start guess at 0.
SQ_L:    LDA S_RES
         INC
         STA S_RES      / Increment guess.
         STA FNC_IN
         BSA MUL_SW     / AC = guess * guess.
         CMA
         INC            / -(guess^2).
         ADD S_VAL      / Compare: Variance - guess^2.
         SPA            / If result is still positive, keep going.
         BUN SQ_DONE    / If guess^2 > Variance, we are done.
         BUN SQ_L
SQ_DONE: LDA S_RES
         ADD NEGONE     / Use the previous guess for floor(sqrt).
         BUN SQRT_SW I
