from states import Key
from utils import xor, hamming_weight


def verify(key: Key, certificate: str) -> bool:
    certificate_restricted_i_bar = "".join(
        [certificate[i] for i, ch in enumerate(key.theta) if ch == "1"])
    # print(f"Expected certificate of deletion: {key.r_restricted_i_bar}")
    # print(f"Received certificate of deletion: {certificate_restricted_i_bar}")
    # TODO: accept the certificate even if it's off by some bits, dependent on a parameter delta
    return hamming_weight(xor(key.r_restricted_i_bar, certificate_restricted_i_bar)) == 0


def verify_deletion_counts(certificates: dict[str, int], key: Key) -> None:
    accepted_count = 0
    rejected_count = 0
    for certificate, count in certificates.items():
        if verify(key, certificate):
            accepted_count += count
        else:
            rejected_count += count
    total_count = accepted_count + rejected_count
    print(
        f"Accepted proof of deletion: {accepted_count}/{total_count} ({(accepted_count / total_count)*100}%)")
    print(
        f"Rejected proof of deletion: {rejected_count}/{total_count} ({(rejected_count / total_count)*100}%)")
