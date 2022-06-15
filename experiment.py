from dataclasses import dataclass
from states import Ciphertext, Key
from global_parameters import GlobalParameters


@dataclass
class Experiment:
    params: GlobalParameters
    key: Key
    ciphertext: Ciphertext
    message: str
    measurement_counts: dict[str, int]
    deletion_counts: dict[str, int]
    deletion_acceptance_rate: float
    deletion_hamming_weight_counts: dict[int, int]
    decryption_counts: dict[str, int]
    decryption_success_rate: float
    dec_success_rate_after_del_acc: int
