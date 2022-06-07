import numpy as np


def random_bit_string(length: int) -> str:
    return "".join([str(random_bit())
                    for _ in range(length)])


def random_bit_matrix(m: int, n: int) -> np.ndarray:
    return np.random.randint(0, 2, size=(m, n))


def random_bit() -> int:
    return random_int(0, 1)


def random_int(lower_bound_inclusive: int, upper_bound_inclusive: int) -> int:
    # Returns a random number in [lower_bound_inclusive, upper_bound_inclusive]
    return np.random.randint(lower_bound_inclusive, upper_bound_inclusive + 1)


def xor(*bit_strings: str) -> str:
    # Calculate the xor of a variable amount of bit strings
    res = []
    for i in range(len(bit_strings[0])):
        bit = 0
        for bit_string in bit_strings:
            bit ^= int(bit_string[i])
        res.append(str(bit))
    return "".join(res)


def hamming_weight(s: str) -> int:
    return s.count("1")
