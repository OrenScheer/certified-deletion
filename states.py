from dataclasses import dataclass
import numpy as np
from qiskit import QuantumCircuit
from utils import random_bit_string, random_bit_matrix, random_int
from global_parameters import GlobalParameters


@dataclass
class Key:
    theta: str
    r_restricted_i_bar: str
    u: str

    @classmethod
    def generate_key(cls, global_params: GlobalParameters):
        def generate_basis() -> str:
            total_length = global_params.m
            hamming_weight = global_params.k
            indices_of_ones = set()
            while len(indices_of_ones) < hamming_weight:
                indices_of_ones.add(random_int(0, total_length - 1))
            return "".join(["1" if i in indices_of_ones else "0" for i in range(total_length)])

        theta = generate_basis()
        r_restricted_i_bar = random_bit_string(global_params.k)
        u = random_bit_string(global_params.co)

        return cls(
            theta=theta,
            r_restricted_i_bar=r_restricted_i_bar,
            u=u
        )


@dataclass
class Ciphertext:
    circuit: QuantumCircuit
    c: str  # msg ^ r_I ^ u
