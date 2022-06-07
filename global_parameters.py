from utils import encode_three_repetition, decode_three_repetition


class GlobalParameters:
    def __init__(self, security_parameter_lambda):
        self.security_parameter_lambda = security_parameter_lambda
        self.n = self.calculate_n()
        self.co = self.calculate_co()
        self.m = self.calculate_m()
        self.k = self.calculate_k()
        self.s = self.calculate_s()
        self.encode_error_correction = encode_three_repetition
        self.decode_error_correction = decode_three_repetition

    # TODO: implement the below functions

    def calculate_n(self):
        # Length of the message
        return 3

    def calculate_co(self):
        # Length of the message with error correction encoded
        return 9

    def calculate_m(self):
        # Number of qubits
        return 15

    def calculate_k(self):
        # Number of qubits used for deletion
        return 6

    def calculate_s(self):
        # Number of qubits used for a one-time pad for the message
        return self.m - self.k
