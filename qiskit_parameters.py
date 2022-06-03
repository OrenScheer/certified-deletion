from qiskit.providers.aer import AerSimulator
from qiskit.test.mock import FakeMontreal

# Qiskit parameters
noise_model = FakeMontreal()
backend = AerSimulator.from_backend(noise_model)
optimization_level = 1
