from qiskit import QuantumCircuit
from states import Basis, Key, Ciphertext
from encryption_circuit import calculate_error_correction_hash, calculate_privacy_amplification_hash, synd
from utils import xor, hamming_distance


def create_decryption_circuit(key: Key, ciphertext: Ciphertext) -> QuantumCircuit:
    """Creates and returns the decryption circuit, given a Ciphertext and an associated Key."""
    decryption_circuit = ciphertext.circuit.copy()
    decryption_circuit.barrier()
    decryption_circuit.h(
        [i for i in range(decryption_circuit.num_qubits) if key.theta[i] is Basis.HADAMARD])
    decryption_circuit.measure_all()
    return decryption_circuit


def generate_all_binary_strings(n: int):
    from collections import deque
    ans = deque(["0", "1"])
    while len(ans) < 2 ** n:
        bin_string = ans.popleft()
        ans.append(bin_string + "0")
        ans.append(bin_string + "1")
    return list(ans)


def corr(inp: str, syndrome: str) -> str:
    """Corrects a candidate input string to match the syndromes generated by the original string."""
    min_hamming_distance = float("inf")
    ans = ""
    for binary_string in generate_all_binary_strings(len(inp)):
        if synd(binary_string) == syndrome:
            if (this_hamming_distance := hamming_distance(inp, binary_string)) < min_hamming_distance:
                min_hamming_distance = this_hamming_distance
                ans = binary_string
    return ans


def decrypt_results(measurements: dict[str, int], key: Key, ciphertext: Ciphertext, message: str, error_correct: bool = False) -> None:
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
    """
    correct_decryption_count = 0
    incorrect_decryption_count = 0
    errored_decryption_count = 0
    I_set = set(i for i, basis in enumerate(key.theta)
                if basis is Basis.COMPUTATIONAL)
    for measurement, count in measurements.items():
        relevant_bits = "".join(
            [ch for i, ch in enumerate(measurement) if i in I_set])
        if error_correct:
            r_prime = corr(relevant_bits, xor(ciphertext.q, key.e))
            relevant_bits = r_prime
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
    total_count = correct_decryption_count + incorrect_decryption_count
    print(
        f"Correct message decrypted: {correct_decryption_count}/{total_count} ({(correct_decryption_count / total_count)*100}%)")
    print(
        f"Incorrect message decrypted: {incorrect_decryption_count}/{total_count} ({(incorrect_decryption_count / total_count)*100}%)")
    print(
        f"Error detected during decryption process (hashes didn't match): {errored_decryption_count}/{total_count} ({(errored_decryption_count / total_count)*100}%)")
