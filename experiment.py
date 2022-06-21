from dataclasses import dataclass
import json
from typing import Optional, Tuple
from states import Ciphertext, Key
from global_parameters import GlobalParameters
from datetime import datetime
from decryption_circuit import decrypt_results
from utils import import_counts
from verification_circuit import verify_deletion_counts


@dataclass
class Experiment:
    experiment_id: str
    folder_path: str
    backend_system: str
    parameters: GlobalParameters
    key: Key
    ciphertext: Ciphertext
    message: str
    deletion_counts_test1: dict[str, int]
    decryption_counts_test2: dict[str, int]
    raw_counts_test3: dict[str, int]
    deletion_counts_test3: dict[str, int]
    decryption_counts_test3: dict[str, int]
    raw_counts_test4: dict[str, int]
    deletion_counts_test4: dict[str, int]
    decryption_counts_test4: dict[str, int]
    execution_datetime: Optional[datetime] = None
    execution_shots: int = 1000

    def __post_init__(self):
        if self.execution_datetime is None:
            self.execution_datetime = datetime.now()

    def __str__(self) -> str:
        string_to_return = ""
        string_to_return += f"{self.backend_system}\n\n"
        string_to_return += f"Message length: {self.parameters.n}\n"
        string_to_return += f"Total number of qubits: {self.parameters.m}\n"
        string_to_return += f"Qubits for deletion: {self.parameters.s}\n"
        string_to_return += f"Qubits used for message encryption: {self.parameters.k}"

        string_to_return += "-----TEST 1: HONEST DELETION-----"
        # Print Test 1 stats
        string_to_return += "-----TEST 2: DECRYPTION-----"
        # Print Test 2 stats
        string_to_return += "-----TEST 3: HONEST DELETION, THEN DECRYPTION-----"
        # Print Test 3 stats
        string_to_return += "-----TEST 4: MALICIOUS DELETION, THEN DECRYPTION-----"
        # Print Test 4 stats
        return string_to_return

    def run_test_1(self) -> None:
        """Runs a test of honest deletion."""
        print("-----TEST 1: HONEST DELETION-----")
        self.run_deletion_test(self.deletion_counts_test1)

    def run_test_2(self) -> None:
        """Runs a test of decryption."""
        print("-----TEST 2: DECRYPTION-----")
        self.run_decryption_test(self.decryption_counts_test2)

    def run_test_3(self) -> None:
        """Runs a test of honest deletion, then attempted decryption."""
        print("-----TEST 3: HONEST DELETION, THEN DECRYPTION-----")
        self.run_combined_test(
            self.raw_counts_test3, self.deletion_counts_test3, self.decryption_counts_test3)

    def run_test_4(self) -> None:
        """Runs a test of malicious deletion, then attempted decryption."""
        print("-----TEST 4: MALICIOUS DELETION, THEN DECRYPTION-----")
        self.run_combined_test(
            self.raw_counts_test4, self.deletion_counts_test4, self.decryption_counts_test4)

    def run_deletion_test(self, deletion_counts: dict[str, int]) -> None:
        accepted_count, rejected_count, rejected_distances, _ = verify_deletion_counts(
            deletion_counts,
            self.key,
            self.parameters
        )
        self.output_deletion_stats(
            accepted_count, rejected_count, rejected_distances)

    def run_decryption_test(self, decryption_counts: dict[str, int]) -> None:
        correct_count, incorrect_count, error_count = decrypt_results(
            decryption_counts,
            self.key,
            self.ciphertext,
            self.message
        )
        self.output_decryption_stats(
            correct_count, incorrect_count, error_count)

    def run_combined_test(self, raw_combined_counts: dict[str, int], deletion_counts: dict[str, int], decryption_counts: dict[str, int]) -> None:
        accepted_count, rejected_count, rejected_distances, accepted_certificates = verify_deletion_counts(
            deletion_counts,
            self.key,
            self.parameters
        )
        self.output_deletion_stats(
            accepted_count, rejected_count, rejected_distances)

        print()
        correct_count, incorrect_count, error_count = decrypt_results(
            decryption_counts,
            self.key,
            self.ciphertext,
            self.message
        )
        self.output_decryption_stats(
            correct_count, incorrect_count, error_count)

        print("\nOf the measurements where the proof of deletion was accepted, the following are the decryption statistics:")

        accepted_deletion_decryption_counts = {}
        for measurement, count in raw_combined_counts.items():
            deletion_measurement, decryption_measurement = measurement.split(
                " ")
            if deletion_measurement in accepted_certificates:
                accepted_deletion_decryption_counts[decryption_measurement] = accepted_deletion_decryption_counts.get(
                    decryption_measurement, 0) + count
        doubly_correct_count, incorrect_decrypt_only_count, error_decrypt_only_count = decrypt_results(
            accepted_deletion_decryption_counts,
            self.key,
            self.ciphertext,
            self.message
        )
        self.output_decryption_stats(
            doubly_correct_count, incorrect_decrypt_only_count, error_decrypt_only_count)

    def output_deletion_stats(self, accepted_count: int, rejected_count: int, rejected_distances: dict[int, int]) -> None:
        print(
            f"Accepted proof of deletion: {accepted_count}/{self.execution_shots} ({(accepted_count / self.execution_shots)*100}%)")
        print(
            f"Rejected proof of deletion: {rejected_count}/{self.execution_shots} ({(rejected_count / self.execution_shots)*100}%)")
        if rejected_distances:
            print(f"Out of the {rejected_count} rejected certificates, the following are the counts of the Hamming distances between the received certificate and the expected certificate:")
            for distance, count in sorted(rejected_distances.items()):
                print(f"Hamming distance {distance}: {count}")

    def output_decryption_stats(self, correct_count: int, incorrect_count: int, error_count: int) -> None:
        print(
            f"Correct message decrypted: {correct_count}/{self.execution_shots} ({(correct_count / self.execution_shots)*100}%)")
        print(
            f"Incorrect message decrypted: {incorrect_count}/{self.execution_shots} ({(incorrect_count / self.execution_shots)*100}%)")
        print(
            f"Error detected during decryption process (hashes didn't match): {error_count}/{self.execution_shots} ({(error_count / self.execution_shots)*100}%)")

    @classmethod
    def reconstruct_experiment_from_folder(cls, folder_path: str):
        with open(f"{folder_path}/experiment_attributes.txt", "r") as attributes_file:
            attributes_dict = json.loads(attributes_file.read())
            experiment_id = attributes_dict["experiment_id"]
            execution_datetime = datetime.fromisoformat(
                attributes_dict["execution_datetime"])
            execution_shots = attributes_dict["execution_shots"]
            backend_system = attributes_dict["backend_system"]
        with open(f"{folder_path}/global_parameters.txt", "r") as params_file:
            parameters = GlobalParameters.from_json(params_file.read())
        with open(f"{folder_path}/key.txt", "r") as key_file:
            key = Key.from_json(key_file.read())
        with open(f"{folder_path}/ciphertext.txt", "r") as ciphertext_file:
            ciphertext = Ciphertext.from_json(ciphertext_file.read())
        with open(f"{folder_path}/message.txt", "r") as message_file:
            message = message_file.read()

        deletion_counts_test1 = import_counts(
            f"{folder_path}/{test1_filename}")
        decryption_counts_test2 = import_counts(
            f"{folder_path}/{test2_filename}")
        raw_counts_test3 = import_counts(f"{folder_path}/{test3_filename}")
        raw_counts_test4 = import_counts(f"{folder_path}/{test4_filename}")

        deletion_counts_test3, decryption_counts_test3 = split_counts(
            raw_counts_test3)
        deletion_counts_test4, decryption_counts_test4 = split_counts(
            raw_counts_test4)

        return cls(
            experiment_id=experiment_id,
            folder_path=folder_path,
            backend_system=backend_system,
            parameters=parameters,
            key=key,
            ciphertext=ciphertext,
            message=message,
            deletion_counts_test1=deletion_counts_test1,
            decryption_counts_test2=decryption_counts_test2,
            raw_counts_test3=raw_counts_test3,
            deletion_counts_test3=deletion_counts_test3,
            decryption_counts_test3=decryption_counts_test3,
            raw_counts_test4=raw_counts_test4,
            deletion_counts_test4=deletion_counts_test4,
            decryption_counts_test4=decryption_counts_test4,
            execution_datetime=execution_datetime,
            execution_shots=execution_shots,
        )


test1_filename = "test1-deletion-counts.csv"
test2_filename = "test2-decryption-counts.csv"
test3_filename = "test3-raw-counts.csv"
test4_filename = "test4-raw-counts.csv"


def split_counts(raw_counts: dict[str, int]) -> Tuple[dict[str, int], dict[str, int]]:
    """Splits the measurement counts of a consecutive deletion and decryption test into two dictionaries.

    Args:
        raw_counts: A dictionary whose keys are two concatenated strings separated by a space, where
            the first string is a deletion measurement and the second string is a decryption measurement,
            and whose values are the number of occurrences of each concatenated string result.

    Returns:
        A tuple of two dictionaries, where the first dictionary is the counts of each unique deletion string,
        and the second dictionary is the counts of each unique decryption string.
    """
    deletion_counts = {}
    decryption_counts = {}
    for measurement, count in raw_counts.items():
        # Qiskit will return a space-separated string of the two measurements.
        # run_and_measure will reverse the string so that the first substring is the first measurement.
        deletion_measurement, decryption_measurement = measurement.split(
            " ")
        deletion_counts[deletion_measurement] = deletion_counts.get(
            deletion_measurement, 0) + count
        decryption_counts[decryption_measurement] = decryption_counts.get(
            decryption_measurement, 0) + count
    return deletion_counts, decryption_counts
