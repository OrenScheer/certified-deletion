from states import Ciphertext
from qiskit import QuantumCircuit


def delete(ciphertext: Ciphertext) -> QuantumCircuit:
    deletion_circuit = ciphertext.circuit.copy()
    deletion_circuit.barrier()
    deletion_circuit.h(range(deletion_circuit.num_qubits))
    deletion_circuit.measure_all()
    return deletion_circuit
