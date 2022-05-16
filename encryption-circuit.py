import random
import numpy as np
from typing import List, Optional


class Key:
    def __init__(self, r_restricted_i_bar, theta, u, d, e, H_pa_matrix, H_ec_matrix):
        self.r_restricted_i_bar = r_restricted_i_bar
        self.theta = theta
        self.u = u
        self.d = d
        self.e = e
        self.H_pa_matrix = H_pa_matrix
        self.H_ec_matrix = H_ec_matrix


class GlobalParameters:
    def __init__(self, security_parameter_lambda):
        self.security_parameter_lambda = security_parameter_lambda
        self.n = self.calculate_n()
        self.m = self.calculate_m()
        self.k = self.calculate_k()
        self.s = self.calculate_s()
        self.tau = self.calculate_tau()
        self.mu = self.calculate_mu()

    def calculate_n(self):
        return 10

    def calculate_m(self):
        return 20

    def calculate_k(self):
        return 10

    def calculate_s(self):
        return 10

    def calculate_tau(self):
        return 5

    def calculate_mu(self):
        return 5


def generate_key(global_params: GlobalParameters) -> Key:
    H_pa_matrix = np.random.randint(
        0, 2, size=(global_params.n, global_params.s))
    H_ec_matrix = np.random.randint(
        0, 2, size=(global_params.tau, global_params.n))
    return Key(
        r_restricted_i_bar="01",
        theta="1001011010",
        u="110",
        d="01101",
        e="",
        H_pa_matrix=H_pa_matrix,
        H_ec_matrix=H_ec_matrix,
    )


def encrypt(msg: str, key: Key, global_params: GlobalParameters):
    # Step 1 - sample r_restricted_i
    # assuming theta is a bit string
    comp_basis_index_set = [i for i in range(
        len(key.theta)) if key.theta[i] == "0"]
    # there will be s qubits encoded in the computational basis
    # r_restricted_i is now a bit string of length s corresponding to the positions in the index set
    r_restricted_i = "".join([str(random.randint(0, 1))
                              for _ in range(global_params.s)])
    print(r_restricted_i)
    # Step 2 - compute x
    x = hash_pa(key.H_pa_matrix, r_restricted_i)
    print(f"x={x}")

    # Step 3 - compute p
    # p = xor(hash_ec(key.H_ec_matrix, r_restricted_i), key.d)
    # print(p)

    # Step 4 - compute q
    # q = xor(synd(r_restricted_i), key.e)


def hash_pa(matrix: List[List[int]], inp: str) -> str:
    # inp is of length s, returns truning of length n
    return xor_multiply_matrix_with_bitstring(matrix, inp)


def hash_ec(matrix: List[List[int]], inp: str) -> str:
    # inp is of length s, returns string of length tau
    return xor_multiply_matrix_with_bitstring(matrix, inp)


def synd(inp: str) -> str:
    pass


def xor_multiply_matrix_with_bitstring(matrix: List[List[int]], bit_string: str) -> str:
    list_to_xor = ["0" * len(matrix)]
    for i in range(len(bit_string)):
        if bit_string[i] == "1":
            list_to_xor.append("".join(str(digit) for digit in matrix[:, i]))
    return xor(*list_to_xor)


def xor(*bit_strings: str) -> Optional[str]:
    if not bit_strings or len(bit_strings) < 2 or not all([len(bit_string) == len(bit_strings[0]) for bit_string in bit_strings]):
        return None
    res = []
    for i in range(len(bit_strings[0])):
        bit = 0
        for bit_string in bit_strings:
            bit ^= int(bit_string[i])
        res.append(str(bit))
    return "".join(res)


global_params = GlobalParameters(5)

key = generate_key(global_params)
encrypt("0111010011", key, global_params)
