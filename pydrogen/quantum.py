from analysis import Complexity, constant, linear, exponential

# given a function from n bits to 1 bit, determine if it is constant (0 or 1 on
# all inputs) or balanced.
@Complexity(n='n', functions = {'all_binary_strings': exponential, 'oracle': constant})
def deutsch_classical(oracle, n):
    outs_zero = False
    outs_one = False
    for sequence in all_binary_strings(n):
        out = oracle(sequence)
        if out == 0:
            outs_zero = True
            if outs_one:
                # not constant
                return False
        else:
            outs_one = True
            if outs_zero:
                return False
    return True

# quantum version relies on a hadamard transform (nlogn classically, n in the
# quantum case) to create a superposition of a n-bit state that we pass to the
# quantum oracle.
@Complexity(n='n', functions = {'quantum_hadamard': linear, 'quantum_oracle': constant, 'measure': constant})
def deutsch_quantum(quantum_oracle, n):
    superpos_input = quantum_hadamard(n)
    result = quantum_oracle(superpos_input)
    # qubit becomes sharp when measured, evaluating to 1 if constant and 0 if not.
    return measure(result)

