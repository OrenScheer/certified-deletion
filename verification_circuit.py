"""The circuit used by the sending party to verify whether to accept a certificate of deletion produced by the receiving party."""

from typing import Set, Tuple, Dict
from scheme_parameters import SchemeParameters
from states import Basis, Key
from utils import xor, hamming_weight


def verify(key: Key, certificate: str, delta: float) -> Tuple[bool, int]:
    """Verifies an individual certificate agains the expected value according to the key.

    Args:
        key: The key to be used in the verification circuit.
        certificate: The candidate proof of deletion as provided by the receiving party.
        delta: The threshold rate for the verification check.

    Returns:
        A tuple (verification_passed, hamming_distance) where verification_passed is a bool indicating whether 
        the candidate certificate has been accepted as a proof of deletion, and hamming_distance is the
        Hamming distance between the expected deletion certificate and the candidate received.
    """

    certificate_restricted_i_bar = "".join(
        [certificate[i] for i, basis in enumerate(key.theta) if basis is Basis.HADAMARD])
    hamming_distance = hamming_weight(
        xor(key.r_restricted_i_bar, certificate_restricted_i_bar))
    k = len(certificate_restricted_i_bar)
    return hamming_distance < delta*k, hamming_distance


def verify_deletion_counts(certificates: Dict[str, int], key: Key, scheme_params: SchemeParameters) -> Tuple[int, int, Dict[int, int], Set[str]]:
    """Processes the candidate proof of deletion certificates for a sequence of experimental tests.

    Outputs relevant statistics.

    Args:
        certificates: A dictionary whose keys are the candidate certificates as provided by
            the receiving party, and whose values are the number of times that each candidate string
            has occurred experimentally.
        key: The key to be used in the verification circuit.
        scheme_params: The SchemeParameters of this experiment.

    Returns:
        A tuple (accepted_count, rejected_count, rejected_distances, accepted_certificates) where
        accepted_count is the number of accepted certificates; rejected_count is the number of
        rejected certificates; rejected_distances is a dictionary where each key is the Hamming
        distance between a rejected candidate certificate and the expected certificate, and each value is
        the number of times this Hamming distance was seen; and accepted_certificates is a set of the
        certificates which were accepted.
    """
    accepted_count = 0
    rejected_count = 0
    rejected_string_distances = {}
    accepted_certificates = set()
    for certificate, count in certificates.items():
        is_exact_match, distance = verify(
            key, certificate, scheme_params.delta)
        if is_exact_match:
            accepted_count += count
            accepted_certificates.add(certificate)
        else:
            rejected_count += count
            rejected_string_distances[distance] = rejected_string_distances.get(
                distance, 0) + count
    return accepted_count, rejected_count, rejected_string_distances, accepted_certificates
