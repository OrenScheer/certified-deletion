from typing import Tuple
from states import Basis, Key
from utils import xor, hamming_weight


def verify(key: Key, certificate: str) -> Tuple[bool, int]:
    """Verifies an individual certificate agains the expected value according to the key.

    Args:
        key: The key to be used in the verification circuit.
        certificate: The candidate proof of deletion as provided by the receiving party.

    Returns:
        A tuple (verification_passed, hamming_distance) where verification_passed is a bool indicating whether 
        the candidate certificate has been accepted as a proof of deletion, and hamming_distance is the
        Hamming distance between the expected deletion certificate and the candidate received.
    """

    certificate_restricted_i_bar = "".join(
        [certificate[i] for i, basis in enumerate(key.theta) if basis is Basis.HADAMARD])
    # TODO: accept the certificate even if it's off by some bits, dependent on a parameter delta
    hamming_distance = hamming_weight(
        xor(key.r_restricted_i_bar, certificate_restricted_i_bar))
    return hamming_distance == 0, hamming_distance


def verify_deletion_counts(certificates: dict[str, int], key: Key) -> None:
    """Processes the candidate proof of deletion certificates for a sequence of experimental tests.

    Outputs relevant statistics.

    Args:
        certificates: A dictionary whose keys are the candidate certificates as provided by
            the receiving party, and whose values are the number of times that each candidate string
            has occurred experimentally.
        key: The key to be used in the verification circuit.
    """
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
