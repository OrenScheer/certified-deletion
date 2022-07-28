"""The circuit and associated methods that are used to decrypt a given ciphertext."""

from typing import Iterator, List, Tuple, Dict
from qiskit import QuantumCircuit
from states import Basis, Key, Ciphertext
from encryption_circuit import calculate_error_correction_hash, calculate_privacy_amplification_hash
from utils import xor
from scheme_parameters import corr_hamming
import itertools


def create_decryption_circuit(key: Key, ciphertext: Ciphertext) -> List[QuantumCircuit]:
    """Creates and returns the decryption circuit, given a Ciphertext and an associated Key."""
    decryption_circuits = [circuit.copy() for circuit in ciphertext.circuits]
    qubit_count = 0
    for circuit in decryption_circuits:
        circuit.barrier()
        h_indices = [i for i in range(
            circuit.num_qubits) if key.theta[qubit_count + i] is Basis.HADAMARD]
        if h_indices:
            circuit.h(h_indices)
        circuit.measure_all()
        qubit_count += circuit.num_qubits
    return decryption_circuits


def decrypt_results(measurements: Dict[str, int], key: Key, ciphertext: Ciphertext, message: str, error_correct: bool = False) -> Tuple[int, int, int]:
    """Processes and decrypts the candidate decryption measurements for a sequence of experimental tests.

    Outputs relevant statistics.

    Args:
        measurements: A dictionary whose keys are the measurements of all the qubits by the receiving
            party once the key is revealed, and whose values are the number of times that each measurement
            string has occurred experimentally.
        key: The key to be used in the decryption circuit.
        ciphertext: The ciphertext that the receiving party possesses.
        message: The original plaintext, to compare with the candidate decryption.
        error_correct: Whether or not to apply the error correction procedure.

    Returns:
        A tuple (correct_count, incorrect_count, error_count) where correct_count is the number of
        correctly-decrypted messages, incorrect_count is the number of incorrectly-decrypted messages,
        and error_count is the number of times the decryption circuit raised an error flag.
    """
    correct_decryption_count = 0
    incorrect_decryption_count = 0
    errored_decryption_count = 0
    for measurement, count in measurements.items():
        if len(measurement) == key.theta.count(Basis.COMPUTATIONAL):
            # Only the computational basis qubits were measured
            relevant_bits = measurement
        else:
            # All the qubits were measured
            relevant_bits = "".join(
                [ch for i, ch in enumerate(measurement) if key.theta[i] is Basis.COMPUTATIONAL])
        if error_correct:
            relevant_bits = corr_hamming(
                relevant_bits, xor(ciphertext.q, key.e))
            # relevant_bits = corr_with_hash(relevant_bits, xor(
            #     ciphertext.q, key.e), key.error_correction_matrix, xor(ciphertext.p, key.d))
        error_corretion_hash = xor(calculate_error_correction_hash(
            key.error_correction_matrix, relevant_bits), key.d)
        if error_corretion_hash != ciphertext.p:
            errored_decryption_count += 1
        x_prime = calculate_privacy_amplification_hash(
            key.privacy_amplification_matrix, relevant_bits)
        decrypted_string = xor(ciphertext.c, x_prime, key.u)
        if decrypted_string == message:
            correct_decryption_count += count
        else:
            incorrect_decryption_count += count
    return correct_decryption_count, incorrect_decryption_count, errored_decryption_count
