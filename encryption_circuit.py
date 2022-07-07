"""The circuit and associated methods used by the sending party to encrypt a plaintext."""

from typing import List, Tuple
from utils import random_bit_string, xor
from scheme_parameters import SchemeParameters
from states import Basis, Key, Ciphertext
from qiskit import QuantumCircuit


def encrypt(message: str, key: Key, scheme_parmas: SchemeParameters, microsecond_delay: int = 0) -> Ciphertext:
    """Encrypts a message according to the values specified by a Key, producing a resulting Ciphertext."""

    # Step 1 - sample the values for the qubits to be encoded in the computational basis
    r_restricted_i = random_bit_string(scheme_parmas.s)

    # Step 2 - compute the privacy-amplified one-time pad
    x = calculate_privacy_amplification_hash(
        key.privacy_amplification_matrix, r_restricted_i)

    # Step 3 - compute the hash of r_restricted_i, for error correction verification
    p = xor(calculate_error_correction_hash(
        key.error_correction_matrix, r_restricted_i), key.d)

    # Step 4 - compute the error syndrome of r_restricted_i
    # q = xor(synd(r_restricted_i), key.e)
    q = "0" * scheme_parmas.mu

    # Step 5 - prepare qubits
    circuit = prepare_qubits(key.theta, r_restricted_i, key.r_restricted_i_bar)
    if microsecond_delay > 0:
        circuit.delay(microsecond_delay, range(circuit.num_qubits), unit="us")
    return Ciphertext(circuit, xor(message, x, key.u), p, q)


def prepare_qubits(theta: Tuple[Basis], computational_qubit_states: str, hadamard_qubit_states: str) -> QuantumCircuit:
    """Prepares the circuit that encodes all the qubits of a Ciphertext.

    Args:
        theta: A tuple of Basis enum values that encode the chosen basis for each qubit.
        computational_qubit_states: A string that encodes the choice of values for the qubits to be prepared,
            where a 0 represents the state |0> and a 1 represents the state |1>. The ith index corresponds
            to the ith 0 in theta.
        hadamard_qubit_states: A string that encodes the chocie of values for the qubits to be prepared,
            where a 0 represents the state |+> and a 1 represents the state |->. The ith index corresponds
            to the ith 1 in theta.

    Returns:
        A QuantumCircuit containing the initialized and prepared qubits. Qubit q_i corresponds to index i
        in theta.
    """
    computational_iterator = iter(computational_qubit_states)
    hadamard_iterator = iter(hadamard_qubit_states)
    circuit = QuantumCircuit(len(theta))
    for i, basis in enumerate(theta):
        if basis is Basis.COMPUTATIONAL:
            state = next(computational_iterator)
            if state == "0":
                # |0>
                pass
            elif state == "1":
                # |1>
                circuit.x(i)
        elif basis is Basis.HADAMARD:
            state = next(hadamard_iterator)
            if state == "0":
                # |+>
                circuit.h(i)
            elif state == "1":
                # |->
                circuit.x(i)
                circuit.h(i)
    return circuit


def calculate_privacy_amplification_hash(matrix: List[List[int]], inp: str) -> str:
    """Calculates the privacy amplification of a given input string.

    Args:
        matrix: An ndarray containing the matrix values for the specific hash function used in privacy amplification.
        inp: A string to be privacy amplified, of length s.

    Returns:
        A privacy-amplified string of length n.
    """
    return xor_multiply_matrix_with_bit_string(matrix, inp)


def calculate_error_correction_hash(matrix: List[List[int]], inp: str) -> str:
    """Calculates the error correction hash of a given input string.

    Args:
        matrix: An ndarray containing the matrix values for the specific hash function used to verify
            the correctness of the error correction scheme.
        inp: A string to be hashed, of length s.

    Returns:
        A string of length tau, the hash of the input string.
    """
    # inp is of length s, returns string of length tau
    return xor_multiply_matrix_with_bit_string(matrix, inp)


def synd(inp: str) -> str:
    """Calculates the error syndromes of a given input string."""
    parity_check_matrix = [
        [1, 0, 1, 0, 1, 0, 1],
        [0, 1, 1, 0, 0, 1, 1],
        [0, 0, 0, 1, 1, 1, 1]
    ]
    return xor_multiply_matrix_with_bit_string(parity_check_matrix, inp)


def xor_multiply_matrix_with_bit_string(matrix: List[List[int]], bit_string: str) -> str:
    """Multiplies a matrix (mod 2) with a bit string, returning a string, as described in family H_3 identified in CW79."""
    list_to_xor = ["0" * len(matrix)]
    for i in range(len(bit_string)):
        if bit_string[i] == "1":
            list_to_xor.append("".join(str(digit)
                               for digit in [row[i] for row in matrix]))
    return xor(*list_to_xor)
