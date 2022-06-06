from qiskit import QuantumCircuit
from states import Key, Ciphertext
from encryption_circuit import calculate_privacy_amplification_hash
from utils import xor


def create_decryption_circuit(key: Key, ciphertext: Ciphertext) -> QuantumCircuit:
    decryption_circuit = ciphertext.circuit.copy()
    decryption_circuit.barrier()
    decryption_circuit.h(
        [i for i in range(decryption_circuit.num_qubits) if key.theta[i] == "1"])
    decryption_circuit.measure_all()
    return decryption_circuit


def corr(inp: str, syndrome: str) -> None:
    pass


def decrypt_results(measurements: dict[str, int], key: Key, ciphertext: Ciphertext, message: str) -> None:
    correct_decryption_count = 0
    incorrect_decryption_count = 0
    I_set = set(i for i, basis in enumerate(key.theta) if basis == "0")
    for measurement, count in measurements.items():
        relevant_bits = "".join(
            [ch for i, ch in enumerate(measurement) if i in I_set])
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
