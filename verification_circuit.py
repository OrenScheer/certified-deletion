from typing import Tuple
from states import Key
from utils import xor, hamming_weight


def verify(key: Key, certificate: str) -> Tuple[bool, int]:
    certificate_restricted_i_bar = "".join(
        [certificate[i] for i, ch in enumerate(key.theta) if ch == "1"])
    # print(f"Expected certificate of deletion: {key.r_restricted_i_bar}")
    # print(f"Received certificate of deletion: {certificate_restricted_i_bar}")
    # TODO: accept the certificate even if it's off by some bits, dependent on a parameter delta
    hamming_distance = hamming_weight(
        xor(key.r_restricted_i_bar, certificate_restricted_i_bar))
    return hamming_distance == 0, hamming_distance


def verify_deletion_counts(certificates: dict[str, int], key: Key) -> None:
    accepted_count = 0
    rejected_count = 0
    rejected_string_distances = {}
    for certificate, count in certificates.items():
        is_exact_match, distance = verify(key, certificate)
        if is_exact_match:
            accepted_count += count
        else:
            rejected_count += count
            rejected_string_distances[distance] = rejected_string_distances.get(
                distance, 0) + count
    total_count = accepted_count + rejected_count
    print(
        f"Accepted proof of deletion: {accepted_count}/{total_count} ({(accepted_count / total_count)*100}%)")
    print(
        f"Rejected proof of deletion: {rejected_count}/{total_count} ({(rejected_count / total_count)*100}%)")
    if rejected_string_distances:
        print(f"Out of the {rejected_count} rejected certificates, the following are the counts of the Hamming distances between the received certificate and the expected certificate:")
        for distance, count in sorted(rejected_string_distances.items()):
            print(f"Hamming distance {distance}: {count}")
