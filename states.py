from dataclasses import dataclass
from enum import IntEnum
from typing import BinaryIO, List, Optional, Tuple
from xxlimited import Str
from qiskit import QuantumCircuit
from qiskit.circuit import qpy_serialization
from utils import random_bit_string, random_bit_matrix, random_int
from global_parameters import GlobalParameters
import json


class Basis(IntEnum):
    COMPUTATIONAL = 0
    HADAMARD = 1


@dataclass
class Key:
    """A key used for encrypting messages.

    Attributes:
        theta: A tuple of Basis enum values that encode the chosen basis for each qubit.
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
    theta: Tuple[Basis]
    r_restricted_i_bar: str
    u: str
    d: str
    e: str
    privacy_amplification_matrix: List[List[int]]
    error_correction_matrix: List[List[int]]

    @classmethod
    def generate_key(cls, global_params: GlobalParameters):
        """Generates a key according to the global paramaters global_params."""
        def generate_basis() -> Tuple[Basis]:
            """Generates the basis with which to encode each qubit."""
            total_length = global_params.m
            hamming_weight = global_params.k
            indices_of_ones = set()
            while len(indices_of_ones) < hamming_weight:
                indices_of_ones.add(random_int(0, total_length - 1))
            return tuple(Basis.HADAMARD if i in indices_of_ones else Basis.COMPUTATIONAL for i in range(total_length))

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

    def to_json(self) -> str:
        """Returns a JSON string representing this object."""
        return json.dumps(vars(self))

    @classmethod
    def from_json(cls, json_string: str):
        """Returns a Key based on the encoded JSON string."""
        dictionary = json.loads(json_string)
        return cls(
            theta=tuple(Basis(bit) for bit in dictionary["theta"]),
            r_restricted_i_bar=dictionary["r_restricted_i_bar"],
            u=dictionary["u"],
            d=dictionary["d"],
            e=dictionary["e"],
            privacy_amplification_matrix=dictionary["privacy_amplification_matrix"],
            error_correction_matrix=dictionary["error_correction_matrix"]
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

    def to_json(self) -> str:
        """Returns a JSON string representing this object."""
        dictionary = vars(self)
        dictionary.pop("circuit")
        return json.dumps(dictionary)

    @classmethod
    def from_json(cls, json_string: str, qpy_filename: Optional[str] = None):
        """Returns a Ciphertext based on the encoded JSON string."""
        dictionary = json.loads(json_string)
        # Placeholder circuit since it may not be needed, for example for decryption verification purposes
        circuit = QuantumCircuit()
        if qpy_filename:
            with open(qpy_filename, "rb") as f:
                circuit = qpy_serialization.load(f)[0]
        return cls(
            circuit=circuit,
            c=dictionary["c"],
            p=dictionary["p"],
            q=dictionary["q"],
        )
