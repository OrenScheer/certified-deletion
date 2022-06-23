from dataclasses import dataclass
import json
from typing import Tuple
from states import Ciphertext, Key
from global_parameters import GlobalParameters
from datetime import datetime
from decryption_circuit import decrypt_results
from utils import import_counts
from verification_circuit import verify_deletion_counts


@dataclass
class Experiment:
    experiment_id: str
    execution_datetime: datetime
    execution_shots: int
    backend_system: str
    microsecond_delay: int
    folder_path: str
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

    def __str__(self) -> str:
        string_to_return = ""
        string_to_return += f"{self.backend_system}\n\n"
        string_to_return += f"Message length: {self.parameters.n}\n"
        string_to_return += f"Total number of qubits: {self.parameters.m}\n"
        string_to_return += f"Qubits for deletion: {self.parameters.s}\n"
        string_to_return += f"Qubits used for message encryption: {self.parameters.k}\n\n"

        string_to_return += self.run_test_1() + "\n\n"
        string_to_return += self.run_test_2() + "\n\n"
        string_to_return += self.run_test_3() + "\n\n"
        string_to_return += self.run_test_4()
        return string_to_return

    def get_test1_success_rate(self) -> float:
        accepted_count, _, _, _ = verify_deletion_counts(
            self.deletion_counts_test1,
            self.key,
            self.parameters
        )
        return accepted_count / self.execution_shots

    def get_test2_success_rate(self) -> float:
        decryption_count, _, _ = decrypt_results(
            self.decryption_counts_test2, self.key, self.ciphertext, self.message)
        return decryption_count / self.execution_shots

    def run_test_1(self) -> str:
        """Runs a test of honest deletion."""
        output_string = "-----TEST 1: HONEST DELETION-----\n"
        output_string += self.run_deletion_test(self.deletion_counts_test1)
        return output_string

    def run_test_2(self) -> str:
        """Runs a test of decryption."""
        output_string = "-----TEST 2: DECRYPTION-----\n"
        output_string += self.run_decryption_test(self.decryption_counts_test2)
        return output_string

    def run_test_3(self) -> str:
        """Runs a test of honest deletion, then attempted decryption."""
        output_string = "-----TEST 3: HONEST DELETION, THEN DECRYPTION-----\n"
        output_string += self.run_combined_test(
            self.raw_counts_test3, self.deletion_counts_test3, self.decryption_counts_test3)
        return output_string

    def run_test_4(self) -> str:
        """Runs a test of malicious deletion, then attempted decryption."""
        output_string = "-----TEST 4: MALICIOUS DELETION, THEN DECRYPTION-----\n"
        output_string += self.run_combined_test(
            self.raw_counts_test4, self.deletion_counts_test4, self.decryption_counts_test4)
        return output_string

    def run_deletion_test(self, deletion_counts: dict[str, int]) -> str:
        accepted_count, rejected_count, rejected_distances, _ = verify_deletion_counts(
            deletion_counts,
            self.key,
            self.parameters
        )
        return build_deletion_stats(accepted_count, rejected_count, rejected_distances, self.execution_shots)

    def run_decryption_test(self, decryption_counts: dict[str, int]) -> str:
        correct_count, incorrect_count, error_count = decrypt_results(
            decryption_counts,
            self.key,
            self.ciphertext,
            self.message
        )
        return build_decryption_stats(correct_count, incorrect_count, error_count, self.execution_shots)

    def run_combined_test(self, raw_combined_counts: dict[str, int], deletion_counts: dict[str, int], decryption_counts: dict[str, int]) -> str:
        output_string = ""
        accepted_count, rejected_count, rejected_distances, accepted_certificates = verify_deletion_counts(
            deletion_counts,
            self.key,
            self.parameters
        )
        output_string += build_deletion_stats(
            accepted_count, rejected_count, rejected_distances, self.execution_shots)

        correct_count, incorrect_count, error_count = decrypt_results(
            decryption_counts,
            self.key,
            self.ciphertext,
            self.message
        )
        output_string += "\n\n" + build_decryption_stats(
            correct_count, incorrect_count, error_count, self.execution_shots)

        if accepted_count:
            output_string += "\n\nOf the measurements where the proof of deletion was accepted, the following are the decryption statistics:\n"

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
            output_string += build_decryption_stats(doubly_correct_count, incorrect_decrypt_only_count,
                                                    error_decrypt_only_count, sum(accepted_deletion_decryption_counts.values()))
        return output_string

    @classmethod
    def reconstruct_experiment_from_folder(cls, folder_path: str):
        with open(f"{folder_path}/{experiment_attributes_filename}", "r") as attributes_file:
            attributes_dict = json.loads(attributes_file.read())
            experiment_id = attributes_dict["experiment_id"]
            execution_datetime = datetime.fromisoformat(
                attributes_dict["execution_datetime"])
            execution_shots = attributes_dict["execution_shots"]
            backend_system = attributes_dict["backend_system"]
            microsecond_delay = attributes_dict["microsecond_delay"]
        with open(f"{folder_path}/{parameters_filename}", "r") as params_file:
            parameters = GlobalParameters.from_json(params_file.read())
        with open(f"{folder_path}/{key_filename}", "r") as key_file:
            key = Key.from_json(key_file.read())
        with open(f"{folder_path}/{ciphertext_filename}", "r") as ciphertext_file:
            ciphertext = Ciphertext.from_json(
                ciphertext_file.read(), qpy_filename=f"{folder_path}/{circuit_filename}")
        with open(f"{folder_path}/{message_filename}", "r") as message_file:
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
            microsecond_delay=microsecond_delay,
        )


experiment_attributes_filename = "experiment_attributes.txt"
parameters_filename = "global_parameters.txt"
key_filename = "key.txt"
ciphertext_filename = "ciphertext.txt"
message_filename = "message.txt"
circuit_filename = "base_circuit.qpy"
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


def build_deletion_stats(accepted_count: int, rejected_count: int, rejected_distances: dict[int, int], total_count: int) -> str:
    output_string = ""
    output_string += f"Accepted proof of deletion: {accepted_count}/{total_count} ({(accepted_count / total_count)*100}%)\n"
    output_string += f"Rejected proof of deletion: {rejected_count}/{total_count} ({(rejected_count / total_count)*100}%)\n"
    if rejected_distances:
        output_string += f"Of the {rejected_count} rejected certificates, the following are the counts of the Hamming distances between the received certificate and the expected certificate:\n"
        for distance, count in sorted(rejected_distances.items()):
            output_string += f"  Hamming distance {distance}: {count}\n"
    return output_string.strip()


def build_decryption_stats(correct_count: int, incorrect_count: int, error_count: int, total_count: int) -> str:
    output_string = ""
    output_string += f"Correct message decrypted: {correct_count}/{total_count} ({(correct_count / total_count)*100}%)\n"
    output_string += f"Incorrect message decrypted: {incorrect_count}/{total_count} ({(incorrect_count / total_count)*100}%)\n"
    output_string += f"Error detected during decryption process (hashes didn't match): {error_count}/{total_count} ({(error_count / total_count)*100}%)\n"
    return output_string.strip()
