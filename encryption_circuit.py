from utils import random_bit_string, xor
from global_parameters import GlobalParameters
from states import Key, Ciphertext
from qiskit import QuantumCircuit


def encrypt(msg: str, key: Key, global_params: GlobalParameters) -> Ciphertext:
    # Step 1 - sample r_restricted_i
    # Portion of the one-time pad that is encoded in the qubits
    r_restricted_i = random_bit_string(global_params.s)

    # Step 2 - encode the message in the error correction scheme
    x = global_params.encode_error_correction(msg)

    # Step 3 - prepare qubits
    qubits = prepare_qubits(key.theta, r_restricted_i, key.r_restricted_i_bar)
    return Ciphertext(qubits, c=xor(x, r_restricted_i, key.u))


def prepare_qubits(theta: str, computational_qubit_states: str, hadamard_qubit_states: str) -> QuantumCircuit:
    # Prepare a circuit with len(theta) qubits, according to the bases in theta and the values specified in the other two strings
    computational_iterator = iter(computational_qubit_states)
    hadamard_iterator = iter(hadamard_qubit_states)
    circuit = QuantumCircuit(len(theta))
    for i, basis in enumerate(theta):
        if basis == "0":
            # computational basis
            state = next(computational_iterator)
            if state == "0":
                # |0>
                pass
            elif state == "1":
                # |1>
                circuit.x(i)
        elif basis == "1":
            # Hadamard basis
            state = next(hadamard_iterator)
            if state == "0":
                # |+>
                circuit.h(i)
            elif state == "1":
                # |->
                circuit.x(i)
                circuit.h(i)
    return circuit
