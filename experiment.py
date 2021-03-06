"""A class and associated methods representing a series of five tests and their execution on a quantum backend."""

from __future__ import annotations
from dataclasses import dataclass, field
import json
import os
import pandas as pd
from typing import List, Optional, Dict, cast
from qiskit import QuantumCircuit
from states import Ciphertext, Key
from scheme_parameters import SchemeParameters
from datetime import datetime
from decryption_circuit import decrypt_results
from verification_circuit import verify_deletion_counts
from qiskit.circuit import qpy_serialization
from qiskit.providers.models.backendproperties import Nduv


@dataclass
class Experiment:
    """The representation of a single experiment, comprised of several tests, executed on a quantum backend.

    Attributes:
        experiment_id: A unique string to reference this experiment.
        execution_datetime: The time when this experiment was run.
        execution_shots: The number of times each test was run on the backend.
        backend_system: A string representing, in a suitable format, which backend system was used.
        qubits_per_circuit: The maximum number of qubits encoded in each QuantumCircuit.
        optimization_level: The optimization level chosen to run the circuits on the backend.
        microsecond_delay: The time, in microseconds, between the preparation of the qubits and the first measurement.
        folder_path: The complete path to the local folder where this experiment is or will be stored.
        parameters: The parameters describing this instance of the certified deletion scheme.
        key: The key used for encryption.
        ciphertext: The encrypted state.
        message: The plaintext message.
        deletion_counts_test1: The measurements of the deletion in test1.
        decryption_counts_test2: The measurements of the decryption in test2.
        combined_counts_test3: The combined measurements of test3.
        combined_counts_test4: The combined measurements of test4.
        raw_counts_test5: The combined measurements of test5.
        decryption_counts_test5: The measurements of the decryption in test5.
        deletion_counts_test5: The measurements of the deletion in test5.
        circuits: A list of lists of QuantumCircuits, where the following is each list:
            - The list of circuits to prepare the qubits.
            - The list of circuits for the deletion test.
            - The list of transpiled circuits for the deletion test.
            - The list of circuits for the decryption test.
            - The list of transpiled circuits for the decryption test.
            - The list of circuits for the Breidbart test.
            - The list of transpiled circuits for the Breidbart test.
    """
    experiment_id: str
    execution_datetime: datetime
    execution_shots: int
    backend_system: str
    qubits_per_circuit: int
    optimization_level: int
    microsecond_delay: int
    folder_path: str
    parameters: SchemeParameters
    key: Key
    ciphertext: Ciphertext
    message: str
    deletion_counts_test1: Dict[str, int]
    decryption_counts_test2: Dict[str, int]
    circuits: List[List[QuantumCircuit]]
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
        output_string = f"System: {self.backend_system}\n"
        output_string += f"Message length: {self.parameters.n}\n"
        output_string += f"Total number of qubits: {self.parameters.m}\n"
        output_string += f"Qubits for deletion: {self.parameters.k}\n"
        output_string += f"Qubits used for message encryption: {self.parameters.s}\n"
        output_string += f"Delay between qubit preparation and first measurement: {self.microsecond_delay} us\n"
        output_string += f"Optimization level: {self.optimization_level}"
        return output_string

    def get_test1_success_rate(self) -> float:
        """Returns the percentage of successful deletions for test1."""
        accepted_count, _, _, _ = verify_deletion_counts(
            self.deletion_counts_test1,
            self.key,
            self.parameters
        )
        return (accepted_count / self.execution_shots) * 100

    def get_test2_success_rate(self, error_correct=False) -> float:
        """Returns the percentage of successful decryptions for test2."""
        decryption_count, _, _ = decrypt_results(
            self.decryption_counts_test2, self.key, self.ciphertext, self.message, error_correct)
        return (decryption_count / self.execution_shots) * 100

    def run_test_1(self) -> str:
        """Runs a test of honest deletion."""
        output_string = "-----TEST 1: HONEST DELETION-----\n"
        output_string += self.run_deletion_test(self.deletion_counts_test1)
        output_string += f"\n\nExpected success rate: {self.parameters.get_expected_test1_success_rate()}"
        return output_string

    def run_test_2(self) -> str:
        """Runs a test of decryption."""
        output_string = "-----TEST 2: DECRYPTION-----\n"
        output_string += self.run_decryption_test(self.decryption_counts_test2)
        output_string += f"\n\nExpected success rate: {self.parameters.get_expected_test2_success_rate()}"
        return output_string

    def run_test_3(self) -> str:
        """Runs a test of honest deletion, then attempted decryption."""
        output_string = "-----TEST 3: HONEST DELETION, THEN DECRYPTION-----\n"
        output_string += self.run_combined_test(self.combined_counts_test3)
        output_string += f"\n\nExpected success rate: {self.parameters.get_expected_test3_success_rate()}"
        return output_string

    def run_test_4(self) -> str:
        """Runs a test of malicious deletion, then attempted decryption."""
        output_string = "-----TEST 4: MALICIOUS DELETION, THEN DECRYPTION-----\n"
        output_string += self.run_combined_test(self.combined_counts_test4)
        output_string += f"\n\nExpected success rate: {self.parameters.get_expected_test4_success_rate()}"
        return output_string

    def run_test_5(self) -> str:
        """Runs a test of tamper detection."""
        output_string = "-----TEST 5: TAMPER DETECTION-----\n"
        output_string += self.run_combined_flipped_test(
            self.combined_counts_test5)
        output_string += f"\n\nExpected success rate: {self.parameters.get_expected_test5_success_rate()}"
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
            self.parameters
        )
        output_string += build_deletion_stats(
            accepted_count, rejected_count, rejected_distances, self.execution_shots)

        correct_count, incorrect_count, error_count = decrypt_results(
            combined_counts,
            self.key,
            self.ciphertext,
            self.message
        )
        output_string += "\n\n" + build_decryption_stats(
            correct_count, incorrect_count, error_count, self.execution_shots)

        if accepted_count:
            output_string += "\n\nOf the measurements where the proof of deletion was accepted, the following are the decryption statistics:\n"

            accepted_deletion_decryption_counts = {
                key: val for key, val in combined_counts.items() if key in accepted_certificates}
            doubly_correct_count, incorrect_decrypt_only_count, error_decrypt_only_count = decrypt_results(
                accepted_deletion_decryption_counts,
                self.key,
                self.ciphertext,
                self.message
            )
            output_string += build_decryption_stats(doubly_correct_count, incorrect_decrypt_only_count,
                                                    error_decrypt_only_count, sum(accepted_deletion_decryption_counts.values()))
        return output_string

    def run_combined_flipped_test(self, combined_counts: Dict[str, int]) -> str:
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
        correct_count, incorrect_count, error_count = decrypt_results(
            combined_counts,
            self.key,
            self.ciphertext,
            self.message
        )
        output_string += build_decryption_stats(
            correct_count, incorrect_count, error_count, self.execution_shots)

        accepted_count, rejected_count, rejected_distances, _ = verify_deletion_counts(
            combined_counts,
            self.key,
            self.parameters
        )
        output_string += "\n\n" + build_deletion_stats(
            accepted_count, rejected_count, rejected_distances, self.execution_shots)

        return output_string

    def export_to_folder(self, qubit_list: Optional[List[List[Nduv]]]) -> None:
        """Exports the values and results of this Experiment to a folder."""
        os.makedirs(self.folder_path, exist_ok=True)
        os.makedirs(f"{self.folder_path}/{circuits_folder}", exist_ok=True)
        with open(f"{self.folder_path}/{experiment_attributes_filename}", "w") as f:
            f.write(json.dumps({
                "experiment_id": self.experiment_id,
                "execution_datetime": self.execution_datetime.isoformat(),
                "execution_shots": self.execution_shots,
                "backend_system": self.backend_system,
                "folder_path": self.folder_path,
                "microsecond_delay": self.microsecond_delay,
                "optimization_level": self.optimization_level,
                "qubits_per_circuit": self.qubits_per_circuit,
            }))

        with open(f"{self.folder_path}/{parameters_filename}", "w") as f:
            f.write(self.parameters.to_json())

        with open(f"{self.folder_path}/{key_filename}", "w") as f:
            f.write(self.key.to_json())

        with open(f"{self.folder_path}/{ciphertext_filename}", "w") as f:
            f.write(self.ciphertext.to_json())

        with open(f"{self.folder_path}/{message_filename}", "w") as f:
            f.write(self.message)

        for i, filename in enumerate(circuit_filenames):
            with open(f"{self.folder_path}/{circuits_folder}/{filename}", "wb") as f:
                qpy_serialization.dump(self.circuits[i], f)  # type: ignore

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
            optimization_level = attributes_dict["optimization_level"]
            qubits_per_circuit = attributes_dict["qubits_per_circuit"]
        with open(f"{folder_path}/{parameters_filename}", "r") as params_file:
            parameters = SchemeParameters.from_json(params_file.read())
        with open(f"{folder_path}/{key_filename}", "r") as key_file:
            key = Key.from_json(key_file.read())
        with open(f"{folder_path}/{ciphertext_filename}", "r") as ciphertext_file:
            ciphertext = Ciphertext.from_json(
                ciphertext_file.read(), qpy_filename=f"{folder_path}/{circuits_folder}/{base_circuits_filename}")
        with open(f"{folder_path}/{message_filename}", "r") as message_file:
            message = message_file.read()

        circuits = []
        for filename in circuit_filenames:
            with open(f"{folder_path}/{circuits_folder}/{filename}", "rb") as f:
                circuits.append(qpy_serialization.load(f))

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
            experiment_id=experiment_id,
            folder_path=folder_path,
            backend_system=backend_system,
            parameters=parameters,
            key=key,
            ciphertext=ciphertext,
            message=message,
            deletion_counts_test1=deletion_counts_test1,
            decryption_counts_test2=decryption_counts_test2,
            combined_counts_test3=combined_counts_test3,
            combined_counts_test4=combined_counts_test4,
            combined_counts_test5=combined_counts_test5,
            execution_datetime=execution_datetime,
            execution_shots=execution_shots,
            microsecond_delay=microsecond_delay,
            circuits=circuits,
            optimization_level=optimization_level,
            qubits_per_circuit=qubits_per_circuit,
        )


experiment_attributes_filename = "experiment_attributes.txt"
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

circuits_folder = "circuits"
base_circuits_filename = "base_circuits.qpy"
deletion_circuits_filename = "deletion_circuits.qpy"
transpiled_deletion_circuits_filename = "transpiled_deletion_circuits.qpy"
decryption_circuits_filename = "decryption_circuits.qpy"
transpiled_decryption_circuits_filename = "transpiled_decryption_circuits.qpy"
breidbart_circuits_filename = "breidbart_circuits.qpy"
transpiled_breidbart_circuits_filename = "transpiled_breidbard_circuits.qpy"
circuit_filenames = [base_circuits_filename, deletion_circuits_filename, transpiled_deletion_circuits_filename,
                     decryption_circuits_filename, transpiled_decryption_circuits_filename, breidbart_circuits_filename, transpiled_breidbart_circuits_filename]


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
