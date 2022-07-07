"""A class and associated methods representing a series of five tests and their execution on a quantum backend."""

from __future__ import annotations
from dataclasses import dataclass, field
import json
import os
import pandas as pd
from typing import Tuple, Dict
from states import Ciphertext, Key
from scheme_parameters import SchemeParameters
from datetime import datetime
from decryption_circuit import decrypt_results
from verification_circuit import verify_deletion_counts
from qiskit.circuit import qpy_serialization


@dataclass
class Experiment:
    """The representation of a single experiment, comprised of several tests, executed on a quantum backend.

    Attributes:
        experiment_id: A unique string to reference this experiment.
        execution_datetime: The time when this experiment was run.
        execution_shots: The number of times each test was run on the backend.
        backend_system: A string representing, in a suitable format, which backend system was used.
        microsecond_delay: The time, in microseconds, between the preparation of the qubits and the first measurement.
        folder_path: The complete path to the local folder where this experiment is or will be stored.
        parameters: The parameters describing this instance of the certified deletion scheme.
        key: The key used for encryption.
        ciphertext: The encrypted state.
        message: The plaintext message.
        deletion_counts_test1: The measurements of the deletion in test1.
        decryption_counts_test2: The measurements of the decryption in test2.
        raw_counts_test3: The combined measurements of test3.
        deletion_counts_test3: The measurements of the deletion in test3.
        decryption_counts_test3: The measurements of the decryption in test3.
        raw_counts_test4: The combined measurements of test4.
        deletion_counts_test4: The measurements of the deletion in test4.
        decryption_counts_test4: The measurements of the decryption in test4.
        raw_counts_test5: The combined measurements of test5.
        decryption_counts_test5: The measurements of the decryption in test5.
        deletion_counts_test5: The measurements of the deletion in test5.
    """
    experiment_id: str
    execution_datetime: datetime
    execution_shots: int
    backend_system: str
    microsecond_delay: int
    folder_path: str
    parameters: SchemeParameters
    key: Key
    ciphertext: Ciphertext
    message: str
    deletion_counts_test1: Dict[str, int]
    decryption_counts_test2: Dict[str, int]
    raw_counts_test3: Dict[str, int]
    deletion_counts_test3: Dict[str, int] = field(init=False)
    decryption_counts_test3: Dict[str, int] = field(init=False)
    raw_counts_test4: Dict[str, int]
    deletion_counts_test4: Dict[str, int] = field(init=False)
    decryption_counts_test4: Dict[str, int] = field(init=False)
    raw_counts_test5: Dict[str, int]
    decryption_counts_test5: Dict[str, int] = field(init=False)
    deletion_counts_test5: Dict[str, int] = field(init=False)

    def __post_init__(self):
        """Splits and saves the counts for the tests with two measurements."""
        self.deletion_counts_test3, self.decryption_counts_test3 = split_counts(
            self.raw_counts_test3)
        self.deletion_counts_test4, self.decryption_counts_test4 = split_counts(
            self.raw_counts_test4)
        self.decryption_counts_test5, self.deletion_counts_test5 = split_counts(
            self.raw_counts_test5)

    def __str__(self) -> str:
        """Returns a readable representation of this Experiment."""
        output_string = self.get_experiment_info() + "\n\n"
        output_string += self.run_test_1() + "\n\n"
        output_string += self.run_test_2() + "\n\n"
        output_string += self.run_test_3() + "\n\n"
        output_string += self.run_test_4() + "\n\n"
        output_string += self.run_test_5()
        return output_string

    def get_experiment_info(self) -> str:
        """Returns the basic information of this Experiment."""
        output_string = f"System: {self.backend_system}\n"
        output_string += f"Message length: {self.parameters.n}\n"
        output_string += f"Total number of qubits: {self.parameters.m}\n"
        output_string += f"Qubits for deletion: {self.parameters.k}\n"
        output_string += f"Qubits used for message encryption: {self.parameters.s}\n"
        output_string += f"Delay between qubit preparation and first measurement: {self.microsecond_delay} us"
        return output_string

    def get_test1_success_rate(self) -> float:
        """Returns the percentage of successful deletions for test1."""
        accepted_count, _, _, _ = verify_deletion_counts(
            self.deletion_counts_test1,
            self.key,
            self.parameters
        )
        return (accepted_count / self.execution_shots) * 100

    def get_test2_success_rate(self) -> float:
        """Returns the percentage of successful decryptions for test2."""
        decryption_count, _, _ = decrypt_results(
            self.decryption_counts_test2, self.key, self.ciphertext, self.message)
        return (decryption_count / self.execution_shots) * 100

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

    def run_test_5(self) -> str:
        """Runs a test of tamper detection."""
        output_string = "-----TEST 5: TAMPER DETECTION-----\n"
        output_string += self.run_combined_flipped_test(
            self.decryption_counts_test5, self.deletion_counts_test5)
        return output_string

    def run_deletion_test(self, deletion_counts: Dict[str, int]) -> str:
        """Runs the verification circuit for a series of measurements.

        Args:
            deletion_counts: A dictionary where each key is a measurement result for a deletion
                certificate, and each value is the number of times that this measurement occurred.

        Returns:
            A string containing the results of this test.
        """
        accepted_count, rejected_count, rejected_distances, _ = verify_deletion_counts(
            deletion_counts,
            self.key,
            self.parameters
        )
        return build_deletion_stats(accepted_count, rejected_count, rejected_distances, self.execution_shots)

    def run_decryption_test(self, decryption_counts: Dict[str, int]) -> str:
        """Runs the decryption circuit for a series of measurements.

        Args:
            decryption_counts: A dictionary where each key is a decryption measurement
                and each value is the number of times that this measurement occurred.

        Returns:
            A string containing the results of this test.
        """
        correct_count, incorrect_count, error_count = decrypt_results(
            decryption_counts,
            self.key,
            self.ciphertext,
            self.message
        )
        return build_decryption_stats(correct_count, incorrect_count, error_count, self.execution_shots)

    def run_combined_test(self, raw_combined_counts: Dict[str, int], deletion_counts: Dict[str, int], decryption_counts: Dict[str, int]) -> str:
        """Runs the deletion circuit followed by the decryption circuit for a series of two successive measurements.

        Args:
            raw_combined_counts: A dictionary where each key is a space-separated string of the two
                successive measurements.
            deletion_counts: A dictionary where each key is a measurement result for a deletion
                certificate, and each value is the number of times that this measurement occurred.
            decryption_counts: A dictionary where each key is a decryption measurement,
                and each value is the number of times that this measurement occurred.

        Returns:
            A string containing the combined results of the deletion and decryption, as well as the results
                of the decryption restricted only to the cases where the deletion certificate was accepted.
        """
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

    def run_combined_flipped_test(self, decryption_counts: Dict[str, int], deletion_counts: Dict[str, int]) -> str:
        """Runs the decryption circuit followed by the deletion circuit for a series of two successive measurements.

        The deletion results are interpreted as checking for tampering. If the deletion certificate
        passes the verification circuit, the ciphertext is judged as tamper-free.

        Args:
            decryption_counts: A dictionary where each key is a decryption measurement,
                and each value is the number of times that this measurement occurred.
            deletion_counts: A dictionary where each key is a measurement result for a deletion
                certificate, and each value is the number of times that this measurement occurred.

        Returns:
            A string containing the combined results of the decryption and deletion.
        """
        output_string = ""
        correct_count, incorrect_count, error_count = decrypt_results(
            decryption_counts,
            self.key,
            self.ciphertext,
            self.message
        )
        output_string += build_decryption_stats(
            correct_count, incorrect_count, error_count, self.execution_shots)

        accepted_count, rejected_count, rejected_distances, _ = verify_deletion_counts(
            deletion_counts,
            self.key,
            self.parameters
        )
        output_string += "\n\n" + build_deletion_stats(
            accepted_count, rejected_count, rejected_distances, self.execution_shots)

        return output_string

    def export_to_folder(self) -> None:
        """Exports the values and results of this Experiment to a folder."""
        os.makedirs(self.folder_path, exist_ok=True)
        with open(f"{self.folder_path}/{experiment_attributes_filename}", "w") as f:
            f.write(json.dumps({
                "experiment_id": self.experiment_id,
                "execution_datetime": self.execution_datetime.isoformat(),
                "execution_shots": self.execution_shots,
                "backend_system": self.backend_system,
                "folder_path": self.folder_path,
                "microsecond_delay": self.microsecond_delay,
            }))

        with open(f"{self.folder_path}/{parameters_filename}", "w") as f:
            f.write(self.parameters.to_json())

        with open(f"{self.folder_path}/{key_filename}", "w") as f:
            f.write(self.key.to_json())

        with open(f"{self.folder_path}/{ciphertext_filename}", "w") as f:
            f.write(self.ciphertext.to_json())

        with open(f"{self.folder_path}/{message_filename}", "w") as f:
            f.write(self.message)

        with open(f"{self.folder_path}/{circuit_filename}", "wb") as f:
            # We assume that the ciphertext circuit is always reset before calling this method
            qpy_serialization.dump(self.ciphertext.circuit, f)

        export_counts(self.deletion_counts_test1,
                      csv_filename=f"{self.folder_path}/{test1_filename}", key_label="Deletion measurement")
        export_counts(self.decryption_counts_test2,
                      csv_filename=f"{self.folder_path}/{test2_filename}", key_label="Decryption measurement")
        export_counts(self.raw_counts_test3,
                      csv_filename=f"{self.folder_path}/{test3_filename}", key_label="Measurement")
        export_counts(self.raw_counts_test4,
                      csv_filename=f"{self.folder_path}/{test4_filename}", key_label="Measurement")
        export_counts(self.raw_counts_test5,
                      csv_filename=f"{self.folder_path}/{test5_filename}", key_label="Measurement")

        with open(f"{self.folder_path}/{results_filename}", "w") as f:
            f.write(str(self))

    @classmethod
    def reconstruct_experiment_from_folder(cls, folder_path: str) -> Experiment:
        """Returns an Experiment based on the files stored in the folder folder_path."""
        with open(f"{folder_path}/{experiment_attributes_filename}", "r") as attributes_file:
            attributes_dict = json.loads(attributes_file.read())
            experiment_id = attributes_dict["experiment_id"]
            execution_datetime = datetime.fromisoformat(
                attributes_dict["execution_datetime"])
            execution_shots = attributes_dict["execution_shots"]
            backend_system = attributes_dict["backend_system"]
            microsecond_delay = attributes_dict["microsecond_delay"]
        with open(f"{folder_path}/{parameters_filename}", "r") as params_file:
            parameters = SchemeParameters.from_json(params_file.read())
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
        raw_counts_test5 = import_counts(f"{folder_path}/{test5_filename}")

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
            raw_counts_test4=raw_counts_test4,
            raw_counts_test5=raw_counts_test5,
            execution_datetime=execution_datetime,
            execution_shots=execution_shots,
            microsecond_delay=microsecond_delay,
        )


experiment_attributes_filename = "experiment_attributes.txt"
parameters_filename = "scheme_parameters.txt"
key_filename = "key.txt"
ciphertext_filename = "ciphertext.txt"
message_filename = "message.txt"
circuit_filename = "base_circuit.qpy"
test1_filename = "test1-deletion-counts.csv"
test2_filename = "test2-decryption-counts.csv"
test3_filename = "test3-raw-counts.csv"
test4_filename = "test4-raw-counts.csv"
test5_filename = "test5-raw-counts.csv"
results_filename = "results.txt"


def split_counts(raw_counts: Dict[str, int]) -> Tuple[dict[str, int], dict[str, int]]:
    """Splits the measurement counts of a consecutive deletion and decryption test into two dictionaries.

    Args:
        raw_counts: A dictionary whose keys are two concatenated strings separated by a space, where
            the first string is a deletion measurement and the second string is a decryption measurement,
            and whose values are the number of occurrences of each concatenated string result.

    Returns:
        A tuple of two dictionaries, where the first dictionary is the counts of each unique first measurement string,
        and the second dictionary is the counts of each unique second measurement string.
    """
    first_measurement_counts = {}
    second_measurement_counts = {}
    for measurement, count in raw_counts.items():
        # Qiskit will return a space-separated string of the two measurements.
        # run_and_measure will reverse the string so that the first substring is the first measurement.
        first_measurement, second_measurement = measurement.split(
            " ")
        first_measurement_counts[first_measurement] = first_measurement_counts.get(
            first_measurement, 0) + count
        second_measurement_counts[second_measurement] = second_measurement_counts.get(
            second_measurement, 0) + count
    return first_measurement_counts, second_measurement_counts


def build_deletion_stats(accepted_count: int, rejected_count: int, rejected_distances: Dict[int, int], total_count: int) -> str:
    """Returns the relevant statistics of a deletion test.

    Args:
        accepted_count: The number of deletion certificates that were accepted by the verification circuit.
        rejected_count: The number of deletion certificates that were rejected by the verification circuit.
        rejected_distances: A dictionary where each key is the Hamming distance between the rejected
            candidate certificate and the expected certificate, and each value is the number of times this
            Hamming distance was observed for this test.
        total_count: The number of total verification attempts for this test.

    Returns:
        A string containing the percentage of accepted and rejected certificates, and the counts of the
            Hamming distances for the rejected certificates.
    """
    output_string = ""
    output_string += f"Accepted proof of deletion: {accepted_count}/{total_count} ({(accepted_count / total_count)*100}%)\n"
    output_string += f"Rejected proof of deletion: {rejected_count}/{total_count} ({(rejected_count / total_count)*100}%)\n"
    if rejected_distances:
        output_string += f"Of the {rejected_count} rejected certificates, the following are the counts of the Hamming distances between the received certificate and the expected certificate:\n"
        for distance, count in sorted(rejected_distances.items()):
            output_string += f"  Hamming distance {distance}: {count}\n"
    return output_string.strip()


def build_decryption_stats(correct_count: int, incorrect_count: int, error_count: int, total_count: int) -> str:
    """Returns the relevant statistics of a decryption test.
    Args:
        correct_count: The number of times the plaintext was correctly decrypted.
        incorrect_count: The number of times the plaintext resulting from the decryption circuit did 
            not match the plaintext originally encrypted.
        error_count: The number of times the decryption circuit raised a flag that an error had been
            detected in the decryption process.
        total_count: The number of total decryption attempts for this test.

    Returns:
        A string containing the percentage of successful, unsuccessful, and error-detected decryption attempts.
    """
    output_string = ""
    output_string += f"Correct message decrypted: {correct_count}/{total_count} ({(correct_count / total_count)*100}%)\n"
    output_string += f"Incorrect message decrypted: {incorrect_count}/{total_count} ({(incorrect_count / total_count)*100}%)\n"
    output_string += f"Error detected during decryption process (hashes didn't match): {error_count}/{total_count} ({(error_count / total_count)*100}%)\n"
    return output_string.strip()


def export_counts(counts: Dict[str, int], csv_filename: str, key_label: str) -> None:
    """Exports a dictionary of counts to a CSV, where the first column is the keys and the second column is the values."""
    df = pd.DataFrame.from_dict(data=counts, orient='index', columns=["Count"]).sort_values(
        by="Count", ascending=False)
    df.index.rename(key_label, inplace=True)
    df.to_csv(csv_filename)


def import_counts(csv_filename: str) -> Dict[str, int]:
    """Imports a dictionary of counts from a CSV file, where the first column is the keys and the second column is the values."""
    try:
        df = pd.read_csv(csv_filename, dtype=str)
        key_label, value_label = df.columns
        df.set_index(key_label, inplace=True)
        df[value_label] = df[value_label].astype(int)
        return df.to_dict()[value_label]
    except FileNotFoundError:
        return {}
