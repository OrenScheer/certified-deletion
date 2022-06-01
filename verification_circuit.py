from states import Key


def verify(key: Key, certificate: str) -> bool:
    certificate_restricted_i_bar = "".join(
        [certificate[i] for i, ch in enumerate(key.theta) if ch == "1"])
    # TODO: accept the certificate even if it's off by some bits, dependent on a parameter delta
    return certificate_restricted_i_bar == key.r_restricted_i_bar
