"""The circuit used by the receiving party to delete a ciphertext and provide a proof of deletion."""

from states import Ciphertext
from qiskit import QuantumCircuit


def delete(ciphertext: Ciphertext) -> QuantumCircuit:
    """Creates the deletion circuit for a given ciphertext.

    Args:
        ciphertext: A ciphertext containing a QuantumCircuit with the prepared qubits.

    Returns:
        A new QuantumCircuit that includes the deletion measurements.
    """
    deletion_circuit = ciphertext.circuit.copy()
    deletion_circuit.barrier()
    deletion_circuit.h(range(deletion_circuit.num_qubits))
    deletion_circuit.measure_all()
    return deletion_circuit
