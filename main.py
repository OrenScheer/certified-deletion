from global_parameters import GlobalParameters
from states import Key
from encryption_circuit import encrypt
from deletion_circuit import delete
from verification_circuit import verify


def main():
    global_params = GlobalParameters(1)
    key = Key.generate_key(global_params)
    ciphertext = encrypt("1011", key, global_params)
    deletion_certificate = delete(ciphertext)
    if verify(key, deletion_certificate):
        print("Accepted deletion certificate!")
    else:
        print("Did not accept deletion certificate.")


if __name__ == "__main__":
    main()
