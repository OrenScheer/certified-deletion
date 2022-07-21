"""The circuit used by the receiving party to delete a ciphertext and provide a proof of deletion."""

from typing import List
from states import Ciphertext
from qiskit import QuantumCircuit


def delete(ciphertext: Ciphertext) -> List[QuantumCircuit]:
    """Creates the deletion circuit for a given ciphertext.

    Args:
        ciphertext: A ciphertext containing a QuantumCircuit with the prepared qubits.

    Returns:
        A new QuantumCircuit that includes the deletion measurements.
    """
    deletion_circuits = [circuit.copy() for circuit in ciphertext.circuits]
    for circuit in deletion_circuits:
        circuit.barrier()
        circuit.h(range(circuit.num_qubits))
        circuit.measure_all()
    return deletion_circuits
