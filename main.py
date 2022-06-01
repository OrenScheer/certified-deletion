from global_parameters import GlobalParameters
from states import Key
from encryption_circuit import encrypt


def main():
    global_params = GlobalParameters(5)
    key = Key.generate_key(global_params)
    encrypt("0111010011", key, global_params)


if __name__ == "__main__":
    main()
