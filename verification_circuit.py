from states import Key
from utils import xor, hamming_weight


def verify(key: Key, certificate: str) -> bool:
    certificate_restricted_i_bar = "".join(
        [certificate[i] for i, ch in enumerate(key.theta) if ch == "1"])
    print(f"Expected certificate of deletion: {key.r_restricted_i_bar}")
    print(f"Received certificate of deletion: {certificate_restricted_i_bar}")
    # TODO: accept the certificate even if it's off by some bits, dependent on a parameter delta
    return hamming_weight(xor(key.r_restricted_i_bar, certificate_restricted_i_bar)) == 0
