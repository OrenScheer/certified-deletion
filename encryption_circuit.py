import numpy as np
from utils import random_bit_string
from global_parameters import GlobalParameters
from states import Key, Ciphertext
from qiskit import QuantumCircuit


def encrypt(msg: str, key: Key, global_params: GlobalParameters) -> Ciphertext:
    # Step 1 - sample r_restricted_i
    # assuming theta is a bit string
    comp_basis_index_set = [i for i in range(
        len(key.theta)) if key.theta[i] == "0"]
    # there will be s qubits encoded in the computational basis
    # r_restricted_i is now a bit string of length s corresponding to the positions in the index set
    r_restricted_i = random_bit_string(global_params.s)
    print(r_restricted_i)
    # Step 2 - compute x
    x = calculate_privacy_amplification_hash(
        key.privacy_amplification_matrix, r_restricted_i)
    print(f"x={x}")

    # Step 3 - compute p
    # p = xor(calculate_error_correction_hash(key.error_correction_matrix, r_restricted_i), key.d)
    p = "0" * len(msg)
    # print(p)

    # Step 4 - compute q
    # q = xor(synd(r_restricted_i), key.e)
    q = "0" * len(msg)

    # Step 5 - prepare qubits
    qubits = prepare_qubits(key.theta, r_restricted_i, key.r_restricted_i_bar)

    return Ciphertext(qubits, xor(msg, x, key.u), p, q)


def prepare_qubits(theta: str, computational_qubit_states: str, hadamard_qubit_states: str) -> QuantumCircuit:
    computational_iterator = iter(computational_qubit_states)
    hadamard_iterator = iter(hadamard_qubit_states)
    circuit = QuantumCircuit(len(theta))
    for i, basis in enumerate(theta):
        if basis == "0":
            # computational basis
            state = next(computational_iterator)
            if state == "0":
                # |0>
                pass
            elif state == "1":
                # |1>
                circuit.x(i)
        elif basis == "1":
            # Hadamard basis
            state = next(hadamard_iterator)
            if state == "0":
                # |+>
                circuit.h(i)
            elif state == "1":
                # |->
                circuit.x(i)
                circuit.h(i)
    return circuit


def calculate_privacy_amplification_hash(matrix: np.ndarray, inp: str) -> str:
    # inp is of length s, returns truning of length n
    return xor_multiply_matrix_with_bit_string(matrix, inp)


def calculate_error_correction_hash(matrix: np.ndarray, inp: str) -> str:
    # inp is of length s, returns string of length tau
    return xor_multiply_matrix_with_bit_string(matrix, inp)


def synd(inp: str) -> None:
    pass


def xor_multiply_matrix_with_bit_string(matrix: np.ndarray, bit_string: str) -> str:
    list_to_xor = ["0" * len(matrix)]
    for i in range(len(bit_string)):
        if bit_string[i] == "1":
            list_to_xor.append("".join(str(digit) for digit in matrix[:, i]))
    return xor(*list_to_xor)


def xor(*bit_strings: str) -> str:
    res = []
    for i in range(len(bit_strings[0])):
        bit = 0
        for bit_string in bit_strings:
            bit ^= int(bit_string[i])
        res.append(str(bit))
    return "".join(res)
