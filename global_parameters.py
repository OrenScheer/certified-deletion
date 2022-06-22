from dataclasses import dataclass
import json


@dataclass
class GlobalParameters:
    """A set of parameters defined for a specific experiment.

    Attributes:
        security_parameter_lambda: The security parameter.
        n: The length of the messages that will be encrypted.
        m: The total number of qubits to be encoded.
        k: The number of qubits that will be used for deletion.
        s: The number of qubits that will be used as a one-time pad.
        tau: The length of the error-correction hash.
        mu: The length of the error syndromes.
    """
    security_parameter_lambda: float
    n: int
    m: int
    k: int
    s: int
    tau: int
    mu: int
    delta: float

    @classmethod
    def generate_from_lambda(cls, security_parameter_lambda: float):
        """Generates a GlobalParameters object based on a security parameter."""
        def calculate_n() -> int:
            """Returns the length of the message."""
            return 5

        def calculate_m() -> int:
            """Returns the total number of qubits."""
            return 27

        def calculate_k() -> int:
            """Returns the number of qubits used for deletion."""
            return 15

        def calculate_s() -> int:
            """Returns the number of qubits used as a one-time pad for encryption."""
            return calculate_m() - calculate_k()

        def calculate_tau() -> int:
            """Returns the length of the error correction hash."""
            return 3

        def calculate_mu() -> int:
            """Returns the length of the error syndromes."""
            return 3

        def calculate_delta() -> float:
            """Returns the threshold rate for the verification check."""
            return 1/calculate_k()  # Accept no errors

        return cls(
            security_parameter_lambda=security_parameter_lambda,
            n=calculate_n(),
            m=calculate_m(),
            k=calculate_k(),
            s=calculate_s(),
            tau=calculate_tau(),
            mu=calculate_mu(),
            delta=calculate_delta(),
        )

    def to_json(self) -> str:
        """Returns a JSON string representing this object."""
        dictionary = vars(self).copy()
        return json.dumps(dictionary)

    @classmethod
    def from_json(cls, json_string: str):
        """Returns a GlobalParameters object based on the encoded JSON string."""
        dictionary = json.loads(json_string)
        return cls(
            security_parameter_lambda=dictionary["security_parameter_lambda"],
            n=dictionary["n"],
            m=dictionary["m"],
            k=dictionary["k"],
            s=dictionary["s"],
            tau=dictionary["tau"],
            mu=dictionary["mu"],
            delta=dictionary["delta"],
        )
