from dataclasses import dataclass
import numpy as np
from qiskit import QuantumCircuit
from utils import random_bit_string, random_bit_matrix, random_int
from global_parameters import GlobalParameters


@dataclass
class Key:
    """A key used for encrypting messages.

    Attributes:
        theta: A string that encodes the chosen basis, where a 0 represents a qubit to be encoded
            in the computational basis, and a 1 represents a qubit to be encoded in the Hadamard basis.
        r_restricted_i_bar: A string that encodes the choice of values for the qubits to be prepared
            in the computational basis, where a 0 represents the state |0> and a 1 represents the state |1>. 
            The ith index corresponds to the ith 0 in theta.
        u: A one-time pad for the message.
        d: A one-time pad for the error correction hash.
        e: A one-time pad for the error syndrome.
        privacy_amplification_matrix: An ndarray containing the matrix values for the specific hash function
            used in privacy amplification.
        error_correction_matrix: An ndarray containing the matrix values for the specific hash function
            used to verify the correctness of the error correction scheme.
    """
    theta: str
    r_restricted_i_bar: str
    u: str
    d: str
    e: str
    privacy_amplification_matrix: np.ndarray
    error_correction_matrix: np.ndarray

    @classmethod
    def generate_key(cls, global_params: GlobalParameters):
        """Generates a key according to the global paramaters global_params."""
        def generate_basis() -> str:
            total_length = global_params.m
            hamming_weight = global_params.k
            indices_of_ones = set()
            while len(indices_of_ones) < hamming_weight:
                indices_of_ones.add(random_int(0, total_length - 1))
            return "".join(["1" if i in indices_of_ones else "0" for i in range(total_length)])

        theta = generate_basis()
        r_restricted_i_bar = random_bit_string(global_params.k)
        u = random_bit_string(global_params.n)
        d = random_bit_string(global_params.tau)
        e = random_bit_string(global_params.mu)

        privacy_amplification_matrix = random_bit_matrix(
            global_params.n, global_params.s)
        error_correction_matrix = random_bit_matrix(
            global_params.tau, global_params.n)

        return cls(
            theta=theta,
            r_restricted_i_bar=r_restricted_i_bar,
            u=u,
            d=d,
            e=e,
            privacy_amplification_matrix=privacy_amplification_matrix,
            error_correction_matrix=error_correction_matrix,
        )


@dataclass
class Ciphertext:
    """A representation of an encrypted state.

    Attributes:
        circuit: A QuantumCircuit containing the prepared qubits.
        c: A doubly one-time padded message.
        p: A one-time padded error correction hash.
        q: A one-time padded error syndrome string.
    """
    circuit: QuantumCircuit
    c: str
    p: str
    q: str
