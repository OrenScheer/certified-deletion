from utils import random_bit_string, random_bit_matrix, random_int
from global_parameters import GlobalParameters


class Key:
    def __init__(self, theta, r_restricted_i_bar, u, d, e, privacy_amplification_matrix, error_correction_matrix):
        self.theta = theta
        self.r_restricted_i_bar = r_restricted_i_bar
        self.u = u
        self.d = d
        self.e = e
        self.privacy_amplification_matrix = privacy_amplification_matrix
        self.error_correction_matrix = error_correction_matrix

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
        u = random_bit_string(global_params.n)
        d = random_bit_string(global_params.mu)
        e = random_bit_string(global_params.tau)

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


class Ciphertext:
    def __init__(self, circuit, c, p, q):
        self.circuit = circuit
        self.c = c
        self.p = p
        self.q = q
