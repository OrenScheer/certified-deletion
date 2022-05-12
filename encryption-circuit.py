import random
import numpy as np
from typing import List


class Key:
    def __init__(self, r_restricted_i_bar, theta, u, d, e, H_pa_matrix, H_ec_matrix):
        self.r_restricted_i_bar = r_restricted_i_bar
        self.theta = theta
        self.u = u
        self.d = d
        self.e = e
        self.H_pa_matrix = H_pa_matrix
        self.H_ec_matrix = H_ec_matrix


def generate_key(global_params: dict) -> Key:
    H_pa_matrix = np.random.randint(
        0, 2, size=(global_params["n"], global_params["s"]))
    H_ec_matrix = np.random.randint(
        0, 2, size=(global_params["tau"], global_params["n"]))
    return Key(
        r_restricted_i_bar="01",
        theta="1001011010",
        u="110",
        d="01101",
        e="",
        H_pa_matrix=H_pa_matrix,
        H_ec_matrix=H_ec_matrix,
    )


def encrypt(msg: str, key: Key, global_params: dict):
    # Step 1 - sample r_restricted_i
    # assuming theta is a bit string
    comp_basis_index_set = [i for i in range(
        len(key.theta)) if key.theta[i] == "0"]
    # there will be s qubits encoded in the computational basis
    # r_restricted_i is now a bit string of length s corresponding to the positions in the index set
    r_restricted_i = "".join([str(random.randint(0, 1))
                              for _ in range(global_params["s"])])
    print(r_restricted_i)
    # Step 2 - compute x
    x = hash_pa(key.H_pa_matrix, r_restricted_i)
    print(x)

    # Step 3 - compute p
    p = xor(hash_ec(key.H_ec_matrix, r_restricted_i), key.d)
    print(p)

    # Step 4 - compute q
    q = xor(synd(r_restricted_i), key.e)


def hash_pa(matrix: List[List[int]], inp: str) -> str:
    # inp is of length s, returns truning of length n
    hashResultList = multiply_matrices_mod_2(matrix, [int(ch) for ch in inp])
    return "".join([str(bit) for bit in hashResultList])


def hash_ec(matrix: List[List[int]], inp: str) -> str:
    # inp is of length s, returns string of length tau
    hashResultList = multiply_matrices_mod_2(matrix, [int(ch) for ch in inp])
    return "".join([str(bit) for bit in hashResultList])


def synd(inp: str) -> str:
    pass


def multiply_matrices_mod_2(A: List[List[int]], B: List[int]) -> List[int]:
    # A is a x b
    # B is b x 1
    # C is a x 1
    C = np.matmul(A, B)
    return [x % 2 for x in C]


def xor(a: str, b: str) -> None:
    if not a or not b:
        return None
    res = []
    for chA, chB in zip(a, b):
        res.append(str(int(chA) ^ int(chB)))
    return "".join(res)


global_params = {
    "n": 10,  	# length of the message
    "m": 20,    # number of qubits sent, == k + s
    "k": 10,     # length of string used for deletion
    "s": 10,     # length of string used for extracting randomness
    "tau": 5,   # length of error correction hash
    "mu": 5,    # length of error syndrome
}

key = generate_key(global_params)
encrypt("0111010011", key, global_params)
