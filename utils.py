import numpy as np
from qiskit import QuantumCircuit, execute
from main import backend, optimization_level


def random_bit_string(length: int) -> str:
    return "".join([str(random_bit())
                    for _ in range(length)])


def random_bit_matrix(m: int, n: int) -> np.ndarray:
    return np.random.randint(0, 2, size=(m, n))


def random_bit() -> int:
    return random_int(0, 1)


def random_int(lower_bound_inclusive: int, upper_bound_inclusive: int) -> int:
    # Returns a random number in [lower_bound_inclusive, upper_bound_inclusive]
    return np.random.randint(lower_bound_inclusive, upper_bound_inclusive + 1)


def run_and_measure(circuit: QuantumCircuit) -> str:
    result = execute(circuit, backend=backend,
                     optimization_level=optimization_level, shots=1).result()
    counts = result.get_counts()
    # Reverse the string since the most significant qubit is at the 0th index of the measurement string
    return counts.keys()[0][::-1]
