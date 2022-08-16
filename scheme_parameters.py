"""The parameters of a given certified deletion scheme, including the chosen error correction scheme. This module also contains preset parameter sets."""

from __future__ import annotations
from dataclasses import dataclass, field
import json
from math import sin, pi
from typing import Dict, List, Tuple, cast
from scipy.stats import binom
from utils import multiply_bit_string_with_matrix, xor


@dataclass
class SchemeParameters:
    """A set of parameters for the BI20 scheme, defined for a specific experiment.

    Attributes:
        security_parameter_lambda: The security parameter.
        n: The length of the messages that will be encrypted.
        m: The total number of qubits to be encoded.
        k: The number of qubits that will be used for deletion.
        s: The number of qubits that will be used as a one-time pad.
        tau: The length of the error-correction hash.
        mu: The length of the error syndromes.
    """
    security_parameter_lambda: float
    n: int
    m: int = field(init=False)
    k: int
    s: int
    tau: int
    mu: int
    delta: float
    error_correcting_code_name: str
    parity_check_matrix: List[List[int]] = field(init=False)
    syndrome_table: Dict[str, str] = field(init=False)
    H_transpose: List[List[int]] = field(init=False)

    def __post_init__(self):
        self.m = self.k + self.s
        with open(f"error_correcting_codes/{self.error_correcting_code_name}_parity_check_matrix.txt", "r") as f:
            self.parity_check_matrix = json.load(f)
        with open(f"error_correcting_codes/{self.error_correcting_code_name}_table.txt", "r") as f:
            self.syndrome_table = json.load(f)
        self.H_transpose = [[row[j] for row in self.parity_check_matrix]
                            for j in range(len(self.parity_check_matrix[0]))]

    def get_expected_test1_success_rate(self, error_rate: float = 0) -> float:
        """Returns the expected (noise-free) success percentage for test1."""
        minimum_correct_qubits = self.k - \
            max(i for i in range(self.k) if i < self.k * self.delta)
        return (1 - cast(float, binom.cdf(minimum_correct_qubits - 1, self.k, 1 - error_rate))) * 100

    def get_expected_test2_success_rate(self, error_rate: float = 0) -> Tuple[float, float]:
        """Returns a tuple of the expected (noise-free) success percentage range for test2."""
        lower_bound = cast(
            float, binom.pmf(self.s, self.s, 1 - error_rate))
        upper_bound = lower_bound + \
            (cast(float, binom.cdf(self.s - 1, self.s, 1 - error_rate))/(2**self.n)
             )  # Account for the possibility of collision in the privacy amplification
        return lower_bound * 100, upper_bound * 100

    def get_expected_test3_success_rate(self) -> Tuple[float, Tuple[float, float]]:
        """Returns a tuple of two values. The first value is the expected success percentage for the deletion part of test3,
        and the second is a tuple of the expected success percentage range for the decryption part of test3."""
        expected_deletion_success = self.get_expected_test1_success_rate()
        expected_decryption_range = self.get_expected_test2_success_rate(
            error_rate=0.5)
        return expected_deletion_success, expected_decryption_range

    def get_expected_test4_success_rate(self) -> Tuple[float, Tuple[float, float]]:
        """Returns a tuple of two values. The first value is the expected success percentage for the deletion part of test4,
        and the second is a tuple of the expected percentage range for the decryption part of test4."""
        breidbart_error_rate = sin(pi/8) ** 2
        expected_deletion_success = self.get_expected_test1_success_rate(
            error_rate=breidbart_error_rate)
        expected_decryption_range = self.get_expected_test2_success_rate(
            error_rate=breidbart_error_rate)
        return expected_deletion_success, expected_decryption_range

    def get_expected_test5_success_rate(self) -> Tuple[Tuple[float, float], float]:
        """Returns a tuple of two values. The first value is a tuple representing the expected success range for the decryption part
        of test5, and the second value is the expected success percentage for the deletion part of test5."""
        expected_decryption_range = self.get_expected_test2_success_rate()
        expected_deletion_success = self.get_expected_test1_success_rate()
        return expected_decryption_range, expected_deletion_success

    def synd(self, inp: str) -> str:
        codeword_length = len(self.H_transpose)
        ans = ""
        for i in range(0, len(inp), codeword_length):
            ans += multiply_bit_string_with_matrix(
                inp[i:i+codeword_length], self.H_transpose)
        return ans

    def corr(self, inp: str, syndrome: str) -> str:
        codeword_length = len(self.H_transpose)
        syndrome_length = len(self.H_transpose[0])
        ans = ""
        codeword_indices = [i for i in range(
            codeword_length, len(inp) + 1, codeword_length)]
        syndrome_indices = [i for i in range(
            syndrome_length, len(syndrome) + 1, syndrome_length)]
        codeword_start = syndrome_start = 0
        for codeword_end, syndrome_end in zip(codeword_indices, syndrome_indices):
            ans += self.corr_single_block(inp[codeword_start:codeword_end],
                                          syndrome[syndrome_start:syndrome_end])
            codeword_start = codeword_end
            syndrome_start = syndrome_end
        return ans

    def corr_single_block(self, inp: str, syndrome: str) -> str:
        new_syndrome = xor(multiply_bit_string_with_matrix(
            inp, self.H_transpose), syndrome)
        if new_syndrome in self.syndrome_table:
            error_vector = self.syndrome_table[new_syndrome]
            return xor(inp, error_vector)
        else:
            # Correction failed, return original string
            return inp

    def to_json(self) -> str:
        """Returns a JSON string representing this object."""
        dictionary = vars(self).copy()
        dictionary.pop("parity_check_matrix", None)
        dictionary.pop("syndrome_table", None)
        dictionary.pop("H_transpose", None)
        return json.dumps(dictionary)

    @classmethod
    def from_json(cls, json_string: str) -> SchemeParameters:
        """Returns a SchemeParameters object based on the encoded JSON string."""
        dictionary = json.loads(json_string)
        return cls(
            security_parameter_lambda=dictionary["security_parameter_lambda"],
            n=dictionary["n"],
            k=dictionary["k"],
            s=dictionary["s"],
            tau=dictionary["tau"],
            mu=dictionary["mu"],
            delta=dictionary["delta"],
            error_correcting_code_name=dictionary["error_correcting_code_name"],
        )


byte_hamming_4 = SchemeParameters(
    security_parameter_lambda=1,
    n=8,
    k=714,
    s=150,
    tau=0,
    mu=40,
    delta=0.05,
    error_correcting_code_name="hamming_4",
)

byte_rm_4_7 = SchemeParameters(
    security_parameter_lambda=1,
    n=8,
    k=736,
    s=128,
    tau=0,
    mu=29,
    delta=0.05,
    error_correcting_code_name="reed_muller_4_7"
)
