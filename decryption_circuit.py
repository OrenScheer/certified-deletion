from states import Key, Ciphertext
from utils import run_and_measure


def decrypt(key: Key, ciphertext: Ciphertext):
    decryption_circuit = ciphertext.circuit.copy()
    decryption_circuit.h(
        [i for i in range(decryption_circuit.num_qubits) if key.theta[i] == "1"])
    decryption_circuit.measure_all()
    measurement_result = run_and_measure(decryption_circuit)


def corr(inp: str, syndrome: str) -> None:
    pass
