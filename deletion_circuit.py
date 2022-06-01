import numpy as np
from typing import Optional
from global_parameters import GlobalParameters
from states import Ciphertext
from qiskit import QuantumCircuit


def delete(cipher: Ciphertext):
    delete_circuit = cipher.circuit.copy()
    delete_circuit.h(range(delete_circuit.num_qubits))
    delete_circuit.measure_all()
