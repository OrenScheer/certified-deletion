from global_parameters import GlobalParameters
from states import Ciphertext
from qiskit import QuantumCircuit
from utils import run_and_measure


def delete(ciphertext: Ciphertext):
    deletion_circuit = ciphertext.circuit.copy()
    deletion_circuit.barrier()
    deletion_circuit.h(range(deletion_circuit.num_qubits))
    deletion_circuit.measure_all()
    proof_of_deletion = run_and_measure(deletion_circuit)
    return proof_of_deletion
