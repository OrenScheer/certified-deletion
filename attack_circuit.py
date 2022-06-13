from qiskit import QuantumCircuit
from states import Ciphertext
from math import cos, sin, pi


def breidbart_measurement(ciphertext: Ciphertext) -> QuantumCircuit:
    breidbart_matrix = [
        [cos(pi/8), sin(pi/8)],
        [-sin(pi/8), cos(pi/8)]
    ]
    attack_circuit = ciphertext.circuit.copy()
    attack_circuit.barrier()
    attack_circuit.unitary(                                 # type: ignore
        breidbart_matrix, range(attack_circuit.num_qubits), label='breidbart')
    attack_circuit.measure_all()
    return attack_circuit
