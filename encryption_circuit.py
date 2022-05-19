import numpy as np
from typing import Optional
from utils import random_bit_string
from global_parameters import GlobalParameters
from key import Key


def encrypt(msg: str, key: Key, global_params: GlobalParameters):
    # Step 1 - sample r_restricted_i
    # assuming theta is a bit string
    comp_basis_index_set = [i for i in range(
        len(key.theta)) if key.theta[i] == "0"]
    # there will be s qubits encoded in the computational basis
    # r_restricted_i is now a bit string of length s corresponding to the positions in the index set
    r_restricted_i = random_bit_string(global_params.s)
    print(r_restricted_i)
    # Step 2 - compute x
    x = calculate_privacy_amplification_hash(
        key.privacy_amplification_matrix, r_restricted_i)
    print(f"x={x}")

    # Step 3 - compute p
    # p = xor(calculate_error_correction_hash(key.error_correction_matrix, r_restricted_i), key.d)
    # print(p)

    # Step 4 - compute q
    # q = xor(synd(r_restricted_i), key.e)


def calculate_privacy_amplification_hash(matrix: np.ndarray, inp: str) -> Optional[str]:
    # inp is of length s, returns truning of length n
    return xor_multiply_matrix_with_bit_string(matrix, inp)


def calculate_error_correction_hash(matrix: np.ndarray, inp: str) -> Optional[str]:
    # inp is of length s, returns string of length tau
    return xor_multiply_matrix_with_bit_string(matrix, inp)


def synd(inp: str) -> None:
    pass


def xor_multiply_matrix_with_bit_string(matrix: np.ndarray, bit_string: str) -> Optional[str]:
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

key = Key.generate_key(global_params)
encrypt("0111010011", key, global_params)
