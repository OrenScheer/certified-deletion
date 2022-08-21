"""A class and associated methods representing a series of five tests and their execution on a quantum backend."""

from __future__ import annotations
from dataclasses import dataclass, field
import os
import pandas as pd
from typing import List, Optional, Dict, Tuple, cast
from qiskit import QuantumCircuit
from experiment_properties import ExperimentProperties
from states import Ciphertext, Key, Basis
from scheme_parameters import SchemeParameters
from decryption_circuit import decrypt_results
from verification_circuit import verify_deletion_counts
from utils import hamming_distance
from qiskit.circuit import qpy_serialization
from qiskit.providers.models.backendproperties import Nduv
from math import ceil


@dataclass
class Experiment:
    """The representation of a single experiment, comprised of several tests, executed on a quantum backend.

    Attributes:
        experiment_id: A unique string to reference this experiment.
        experiment_properties: The Qiskit-related properties of this experiment.
        folder_path: The complete path to the local folder where this experiment is or will be stored.
        scheme_parameters: The parameters describing this instance of the certified deletion scheme.
        key: The key used for encryption.
        ciphertext: The encrypted state.
        message: The plaintext message.
        encoded_in_qubits: The bit string encoded in the quantum part of the circuit (regardless of basis).
        base_circuits: A list of QuantumCircuits with just the qubit preparation for the ciphertext.
        full_circuits: A list of lists of QuantumCircuits, where the following is each list:
            - The list of circuits for the deletion test.
            - The list of circuits for the decryption test.
            - The list of circuits for the Breidbart test.
        transpiled_circuits: A list of lists of QuantumCircuits, where the following is each list:
            - The list of transpiled circuits for the deletion test.
            - The list of transpiled circuits for the decryption test.
            - The list of transpiled circuits for the Breidbart test.
        deletion_counts_test1: The measurements of the deletion in test1.
        decryption_counts_test2: The measurements of the decryption in test2.
        combined_counts_test3: The combined measurements of test3.
        combined_counts_test4: The combined measurements of test4.
        combined_counts_test5: The combined measurements of test5.
    """
    experiment_id: str
    experiment_properties: ExperimentProperties
    number_of_circuits: int
    folder_path: str
    scheme_parameters: SchemeParameters
    key: Key
    ciphertext: Ciphertext
    message: str
    encoded_in_qubits: str
    base_circuits: List[QuantumCircuit]
    full_circuits: List[List[QuantumCircuit]] = field(default_factory=list)
    transpiled_circuits: List[List[QuantumCircuit]
                              ] = field(default_factory=list)
    deletion_counts_test1: Dict[str, int] = field(default_factory=dict)
    decryption_counts_test2: Dict[str, int] = field(default_factory=dict)
    combined_counts_test3: Dict[str, int] = field(default_factory=dict)
    combined_counts_test4: Dict[str, int] = field(default_factory=dict)
    combined_counts_test5: Dict[str, int] = field(default_factory=dict)

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
        output_string = f"System: {self.experiment_properties.system}\n"
        output_string += f"Message length: {self.scheme_parameters.n}\n"
        output_string += f"Total number of qubits: {self.scheme_parameters.m}\n"
        output_string += f"Qubits for deletion: {self.scheme_parameters.k}\n"
        output_string += f"Qubits used for message encryption: {self.scheme_parameters.s}\n"
        output_string += f"Error syndrome length: {self.scheme_parameters.mu}\n"
        output_string += f"Error-correcting code: {self.scheme_parameters.error_correcting_code_name}\n"
        output_string += f"Delay between qubit preparation and first measurement: {self.experiment_properties.microsecond_delay} us\n"
        output_string += f"Optimization level: {self.experiment_properties.optimization_level}"
        return output_string

    def get_test1_success_rate(self) -> float:
        """Returns the percentage of successful deletions for test1."""
        accepted_count, _, _, _ = verify_deletion_counts(
            self.deletion_counts_test1,
            self.key,
            self.scheme_parameters
        )
        return (accepted_count / self.experiment_properties.shots) * 100

    def get_test2_success_rate(self, error_correct=True) -> float:
        """Returns the percentage of successful decryptions for test2."""
        success_with_flag, success_no_flag, _, _ = self.get_full_test2_reuslts(
            error_correct=error_correct)
        correct_decryption_count = success_no_flag + success_with_flag
        return (correct_decryption_count / self.experiment_properties.shots) * 100

    def get_full_test2_reuslts(self, error_correct=True) -> Tuple[int, int, int, int]:
        """Returns the four counts from test 2."""
        return decrypt_results(self.decryption_counts_test2, self.key, self.ciphertext, self.message, self.scheme_parameters, error_correct)

    def run_test_1(self) -> str:
        """Runs a test of honest deletion."""
        output_string = "-----TEST 1: HONEST DELETION-----\n"
        output_string += self.run_deletion_test(self.deletion_counts_test1)
        output_string += f"\n\nExpected success rate: {self.scheme_parameters.get_expected_test1_success_rate()}"
        return output_string

    def run_test_2(self) -> str:
        """Runs a test of decryption."""
        output_string = "-----TEST 2: DECRYPTION-----\n"
        output_string += self.run_decryption_test(self.decryption_counts_test2)
        output_string += f"\n\nExpected success rate: {self.scheme_parameters.get_expected_test2_success_rate()}"
        return output_string

    def run_test_3(self) -> str:
        """Runs a test of honest deletion, then attempted decryption."""
        output_string = "-----TEST 3: HONEST DELETION, THEN DECRYPTION-----\n"
        output_string += self.run_combined_test(self.combined_counts_test3)
        output_string += f"\n\nExpected success rate: {self.scheme_parameters.get_expected_test3_success_rate()}"
        return output_string

    def run_test_4(self) -> str:
        """Runs a test of malicious deletion, then attempted decryption."""
        output_string = "-----TEST 4: MALICIOUS DELETION, THEN DECRYPTION-----\n"
        output_string += self.run_combined_test(self.combined_counts_test4)
        output_string += f"\n\nExpected success rate: {self.scheme_parameters.get_expected_test4_success_rate()}"
        return output_string

    def run_test_5(self) -> str:
        """Runs a test of tamper-evident decryption."""
        output_string = "-----TEST 5: TAMPER-EVIDENT DECRYPTION-----\n"
        output_string += self.run_tamper_evidence_test(
            self.combined_counts_test5)
        output_string += f"\n\nExpected success rate: {self.scheme_parameters.get_expected_test5_success_rate()}"
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
            self.scheme_parameters
        )
        return build_deletion_stats(accepted_count, rejected_count, rejected_distances, self.experiment_properties.shots)

    def run_decryption_test(self, decryption_counts: Dict[str, int]) -> str:
        """Runs the decryption circuit for a series of measurements.

        Args:
            decryption_counts: A dictionary where each key is a decryption measurement
                and each value is the number of times that this measurement occurred.

        Returns:
            A string containing the results of this test.
        """
        correct_with_flag, correct_no_flag, incorrect_with_flag, incorrect_no_flag = decrypt_results(
            decryption_counts,
            self.key,
            self.ciphertext,
            self.message,
            self.scheme_parameters
        )
        return build_decryption_stats(correct_with_flag, correct_no_flag, incorrect_with_flag, incorrect_no_flag, self.experiment_properties.shots)

    def run_combined_test(self, combined_counts: Dict[str, int]) -> str:
        """Runs the deletion circuit followed by the decryption circuit for a series of two successive measurements.

        Args:
            combined_counts: A dictionary where each key is a single measurement result for both
                the deletion certificate and the decryption attempt, and each value is the number
                of times this measurement occurred.

        Returns:
            A string containing the combined results of the deletion and decryption, as well as the results
                of the decryption restricted only to the cases where the deletion certificate was accepted.
        """
        output_string = ""
        accepted_count, rejected_count, rejected_distances, accepted_certificates = verify_deletion_counts(
            combined_counts,
            self.key,
            self.scheme_parameters
        )
        output_string += build_deletion_stats(
            accepted_count, rejected_count, rejected_distances, self.experiment_properties.shots)

        correct_with_flag, correct_no_flag, incorrect_with_flag, incorrect_no_flag = decrypt_results(
            combined_counts,
            self.key,
            self.ciphertext,
            self.message,
            self.scheme_parameters
        )
        output_string += "\n\n" + build_decryption_stats(
            correct_with_flag, correct_no_flag, incorrect_with_flag, incorrect_no_flag, self.experiment_properties.shots)

        if accepted_count:
            output_string += "\n\nOf the measurements where the proof of deletion was accepted, the following are the decryption statistics:\n"

            accepted_deletion_decryption_counts = {
                key: val for key, val in combined_counts.items() if key in accepted_certificates}
            d_correct_with_flag, d_correct_no_flag, d_incorrect_with_flag, d_incorrect_no_flag = decrypt_results(
                accepted_deletion_decryption_counts,
                self.key,
                self.ciphertext,
                self.message,
                self.scheme_parameters
            )
            output_string += build_decryption_stats(d_correct_with_flag, d_correct_no_flag, d_incorrect_with_flag,
                                                    d_incorrect_no_flag, sum(accepted_deletion_decryption_counts.values()))
        return output_string

    def run_tamper_evidence_test(self, combined_counts: Dict[str, int]) -> str:
        """Runs the decryption circuit followed by the deletion circuit for a series of two successive measurements.

        The deletion results are interpreted as checking for tampering. If the deletion certificate
        passes the verification circuit, the ciphertext is judged as tamper-free.

        Args:
            combined_counts: A dictionary where each key is a single measurement result for both
                the deletion certificate and the decryption attempt, and each value is the number
                of times this measurement occurred.

        Returns:
            A string containing the combined results of the decryption and deletion.
        """
        output_string = ""

        # Run deletion first, since we get the accepted certificates
        _, _, _, accepted_certificates = verify_deletion_counts(
            combined_counts,
            self.key,
            self.scheme_parameters
        )

        accepted_deletion_decryption_counts = {
            key: val for key, val in combined_counts.items() if key in accepted_certificates}
        d_correct_with_flag, d_correct_no_flag, _, _ = decrypt_results(
            accepted_deletion_decryption_counts,
            self.key,
            self.ciphertext,
            self.message,
            self.scheme_parameters
        )
        doubly_correct_count = d_correct_with_flag + d_correct_no_flag
        doubly_correct_string = f"{doubly_correct_count}/{self.experiment_properties.shots}"
        percent_string = f"{(doubly_correct_count / self.experiment_properties.shots)*100}%"
        output_string += f"Correct message decrypted (regardless of error flag during decryption), and verification of deletion certificate passed : {doubly_correct_string} ({percent_string})"
        return output_string

    def get_average_error_rate(self, basis: Basis) -> float:
        """Returns the average error rate of a chosen basis for this experiment."""
        index_set = set(i for i in range(len(self.encoded_in_qubits))
                        if self.key.theta[i] is basis)
        total_error_rate = 0
        expected_qubits = "".join(
            [self.encoded_in_qubits[i] for i in range(len(self.encoded_in_qubits)) if i in index_set])
        if basis is Basis.COMPUTATIONAL:
            counts = self.decryption_counts_test2
        else:
            counts = self.deletion_counts_test1
        for meas, count in counts.items():
            for _ in range(count):
                total_error_rate += hamming_distance("".join([meas[i] for i in range(
                    len(meas)) if i in index_set]), expected_qubits)/len(index_set)
        return total_error_rate/self.experiment_properties.shots

    def export_to_folder(self, qubit_list: Optional[List[List[Nduv]]]) -> None:
        """Exports the values and results of this Experiment to a folder."""
        os.makedirs(self.folder_path, exist_ok=True)
        os.makedirs(f"{self.folder_path}/{circuits_folder}", exist_ok=True)
        with open(f"{self.folder_path}/{experiment_properties_filename}", "w") as f:
            f.write(self.experiment_properties.to_json())

        with open(f"{self.folder_path}/{parameters_filename}", "w") as f:
            f.write(self.scheme_parameters.to_json())

        with open(f"{self.folder_path}/{key_filename}", "w") as f:
            f.write(self.key.to_json())

        with open(f"{self.folder_path}/{ciphertext_filename}", "w") as f:
            f.write(self.ciphertext.to_json())

        with open(f"{self.folder_path}/{message_filename}", "w") as f:
            f.write(self.message)

        with open(f"{self.folder_path}/{encoded_filename}", "w") as f:
            f.write(self.encoded_in_qubits)

        with open(f"{self.folder_path}/{circuits_folder}/{base_circuits_filename}", "wb") as f:
            qpy_serialization.dump(self.base_circuits, f)  # type: ignore

        for i, filename in enumerate(full_circuit_filenames):
            with open(f"{self.folder_path}/{circuits_folder}/{filename}", "wb") as f:
                qpy_serialization.dump(
                    self.full_circuits[i], f)  # type: ignore

        for i, filename in enumerate(transpiled_circuit_filenames):
            with open(f"{self.folder_path}/{circuits_folder}/{filename}", "wb") as f:
                qpy_serialization.dump(
                    self.transpiled_circuits[i], f)  # type: ignore

        export_counts(self.deletion_counts_test1,
                      csv_filename=f"{self.folder_path}/{test1_filename}", key_label="Deletion measurement")
        export_counts(self.decryption_counts_test2,
                      csv_filename=f"{self.folder_path}/{test2_filename}", key_label="Decryption measurement")
        export_counts(self.combined_counts_test3,
                      csv_filename=f"{self.folder_path}/{test3_filename}", key_label="Measurement")
        export_counts(self.combined_counts_test4,
                      csv_filename=f"{self.folder_path}/{test4_filename}", key_label="Measurement")
        export_counts(self.combined_counts_test5,
                      csv_filename=f"{self.folder_path}/{test5_filename}", key_label="Measurement")

        with open(f"{self.folder_path}/{results_filename}", "w") as f:
            f.write(str(self))

        if qubit_list:
            export_qubits_info(
                qubit_list, f"{self.folder_path}/{qubit_properties_filename}")

    @classmethod
    def reconstruct_experiment_from_folder(cls, folder_path: str, include_circuits: bool = True) -> Experiment:
        """Returns an Experiment based on the files stored in the folder folder_path."""
        with open(f"{folder_path}/{experiment_properties_filename}", "r") as properties_file:
            experiment_properties = ExperimentProperties.from_json(
                properties_file.read())
        with open(f"{folder_path}/{parameters_filename}", "r") as params_file:
            scheme_parameters = SchemeParameters.from_json(params_file.read())
        with open(f"{folder_path}/{key_filename}", "r") as key_file:
            key = Key.from_json(key_file.read())
        with open(f"{folder_path}/{ciphertext_filename}", "r") as ciphertext_file:
            ciphertext = Ciphertext.from_json(
                ciphertext_file.read(), qpy_filename=f"{folder_path}/{circuits_folder}/{base_circuits_filename}" if include_circuits else None)
        with open(f"{folder_path}/{message_filename}", "r") as message_file:
            message = message_file.read()
        with open(f"{folder_path}/{encoded_filename}", "r") as encoded_file:
            encoded_in_qubits = encoded_file.read()

        base_circuits = []
        if include_circuits:
            with open(f"{folder_path}/{circuits_folder}/{base_circuits_filename}", "rb") as f:
                base_circuits = cast(List[QuantumCircuit],
                                     qpy_serialization.load(f))

        full_circuits = []
        if include_circuits:
            for i, filename in enumerate(full_circuit_filenames):
                with open(f"{folder_path}/{circuits_folder}/{filename}", "rb") as f:
                    full_circuits.append(qpy_serialization.load(f))

        transpiled_circuits = []
        if include_circuits:
            for i, filename in enumerate(transpiled_circuit_filenames):
                with open(f"{folder_path}/{circuits_folder}/{filename}", "rb") as f:
                    transpiled_circuits.append(qpy_serialization.load(f))

        deletion_counts_test1 = import_counts(
            f"{folder_path}/{test1_filename}")
        decryption_counts_test2 = import_counts(
            f"{folder_path}/{test2_filename}")
        combined_counts_test3 = import_counts(
            f"{folder_path}/{test3_filename}")
        combined_counts_test4 = import_counts(
            f"{folder_path}/{test4_filename}")
        combined_counts_test5 = import_counts(
            f"{folder_path}/{test5_filename}")

        return cls(
            experiment_id=experiment_properties.experiment_id,
            folder_path=folder_path,
            experiment_properties=experiment_properties,
            scheme_parameters=scheme_parameters,
            key=key,
            ciphertext=ciphertext,
            message=message,
            deletion_counts_test1=deletion_counts_test1,
            decryption_counts_test2=decryption_counts_test2,
            combined_counts_test3=combined_counts_test3,
            combined_counts_test4=combined_counts_test4,
            combined_counts_test5=combined_counts_test5,
            base_circuits=base_circuits,
            full_circuits=full_circuits,
            transpiled_circuits=transpiled_circuits,
            number_of_circuits=ceil(
                scheme_parameters.m / experiment_properties.qubits_per_circuit),
            encoded_in_qubits=encoded_in_qubits,
        )


experiment_properties_filename = "experiment_attributes.txt"
parameters_filename = "scheme_parameters.txt"
key_filename = "key.txt"
ciphertext_filename = "ciphertext.txt"
message_filename = "message.txt"
test1_filename = "test1-deletion-counts.csv"
test2_filename = "test2-decryption-counts.csv"
test3_filename = "test3-raw-counts.csv"
test4_filename = "test4-raw-counts.csv"
test5_filename = "test5-raw-counts.csv"
results_filename = "results.txt"
qubit_properties_filename = "qubits.csv"
encoded_filename = "encoded_in_qubits.txt"

circuits_folder = "circuits"
base_circuits_filename = "base_circuits.qpy"
deletion_circuits_filename = "deletion_circuits.qpy"
transpiled_deletion_circuits_filename = "transpiled_deletion_circuits.qpy"
decryption_circuits_filename = "decryption_circuits.qpy"
transpiled_decryption_circuits_filename = "transpiled_decryption_circuits.qpy"
breidbart_circuits_filename = "breidbart_circuits.qpy"
transpiled_breidbart_circuits_filename = "transpiled_breidbard_circuits.qpy"
full_circuit_filenames = [deletion_circuits_filename,
                          decryption_circuits_filename,  breidbart_circuits_filename]
transpiled_circuit_filenames = [transpiled_deletion_circuits_filename,
                                transpiled_decryption_circuits_filename, transpiled_breidbart_circuits_filename]


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


def build_decryption_stats(correct_with_flag: int, correct_no_flag: int, incorrect_with_flag: int, incorrect_no_flag: int, total_count: int) -> str:
    """Returns the relevant statistics of a decryption test.
    Args:
        correct_with_flag: The number of times the plaintext was correctly decrypted, and the error flag was raised.
        correct_no_flag: The number of times the plaintext was correctly decrypted, with no error flag raised.
        incorrect_with_flag: The number of times the plaintext was unsuccessfully decrypted, and the error flag was raised.
        incorrect_no_flag: The number of times the plaintext was unsuccessfully decrypted, with no error flag raised.
        total_count: The number of total verification attempts for this test.

    Returns:
        A string containing the percentage of successful, unsuccessful, and error-detected decryption attempts.
    """
    correct_count = correct_no_flag + correct_with_flag
    incorrect_count = incorrect_no_flag + incorrect_with_flag
    output_string = ""
    output_string += f"Correct message decrypted: {correct_count}/{total_count} ({(correct_count / total_count)*100}%)\n"
    output_string += f"  - Error detected during decryption process (hashes didn't match): {correct_with_flag}/{total_count} ({(correct_with_flag / total_count)*100}%)\n"
    output_string += f"  - No error detected during decryption process: {correct_no_flag}/{total_count} ({(correct_no_flag / total_count)*100}%)\n"
    output_string += f"Incorrect message decrypted: {incorrect_count}/{total_count} ({(incorrect_count / total_count)*100}%)\n"
    output_string += f"  - Error detected during decryption process (hashes didn't match): {incorrect_with_flag}/{total_count} ({(incorrect_with_flag / total_count)*100}%)\n"
    output_string += f"  - No error detected during decryption process: {incorrect_no_flag}/{total_count} ({(incorrect_no_flag / total_count)*100}%)\n"
    return output_string.strip()


def export_counts(counts: Dict[str, int], csv_filename: str, key_label: str) -> None:
    """Exports a dictionary of counts to a CSV, where the first column is the keys and the second column is the values."""
    df = pd.DataFrame.from_dict(data=counts, orient='index', columns=["Count"]).sort_values(
        by="Count", ascending=False)
    df.index.rename(key_label, inplace=True)
    df.to_csv(csv_filename)


def export_qubits_info(qubits: List[List[Nduv]], csv_filename: str) -> None:
    props = [dict({"qubit": i}, **prop.to_dict())
             for i, qubit in enumerate(qubits) for prop in qubit]
    df = pd.DataFrame.from_records(data=props)
    df.to_csv(csv_filename, index=False)


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
