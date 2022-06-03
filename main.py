from global_parameters import GlobalParameters
from states import Key
from encryption_circuit import encrypt
from qiskit.providers.aer import AerSimulator
from qiskit.test.mock import FakeMontreal

# Qiskit parameters
noise_model = FakeMontreal()
backend = AerSimulator.from_backend(noise_model)
optimization_level = 1


def main():
    global_params = GlobalParameters(5)
    key = Key.generate_key(global_params)
    encrypt("0111010011", key, global_params)


if __name__ == "__main__":
    main()
