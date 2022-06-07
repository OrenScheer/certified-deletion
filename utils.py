import numpy as np


def random_bit_string(length: int) -> str:
    """Generates a random bit string of the specific length."""
    return "".join([str(random_bit())
                    for _ in range(length)])


def random_bit_matrix(m: int, n: int) -> np.ndarray:
    """Generates a random mxn bit matrix of the specific dimensions."""
    return np.random.randint(0, 2, size=(m, n))


def random_bit() -> int:
    """Generates a single random bit."""
    return random_int(0, 1)


def random_int(lower_bound_inclusive: int, upper_bound_inclusive: int) -> int:
    """Generates a random integer.

    Args:
        lower_bound_inclusive: The integer lower bound.
        upper_bound_inclusive: The integer upper bound.

    Returns:
        A random integer in the range [lower_bound_inclusive, upper_bound_inclusive].
    """
    return np.random.randint(lower_bound_inclusive, upper_bound_inclusive + 1)


def xor(*bit_strings: str) -> str:
    """Calculates the xor of a variable number of bit strings."""
    # Calculate the xor of a variable amount of bit strings
    res = []
    for i in range(len(bit_strings[0])):
        bit = 0
        for bit_string in bit_strings:
            bit ^= int(bit_string[i])
        res.append(str(bit))
    return "".join(res)


def hamming_weight(s: str) -> int:
    """Calculates the Hamming weight of a given string."""
    return s.count("1")
