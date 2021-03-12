# wschor, Spring 2021
"""
This file contains the cryptography API. You should **not** modify this file.
"""

from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, hmac, serialization, constant_time
from cryptography.hazmat.primitives import padding as sym_padding
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from .util import *

import base64
import os



def check_type(arg, corr_type, param_name, func_name):
    """
    A helper function for argument type checking.
    """
    if not isinstance(arg, corr_type):
        print(f"\nParameter \"{param_name}\" to {func_name} must of type {corr_type}!")
        print(f"Instead, it is: {type(arg)}\n")
        raise TypeError



class AsmPublicKey:
    """
    A wrapper around a public key. Allows for marshalling to and from bytes.
    """
    def __init__(self, libPubKey):
        self.libPubKey = libPubKey

    @classmethod
    def from_bytes(cls, byte_repr):
        pub_key = serialization.load_pem_public_key(byte_repr)
        return cls(pub_key)

    def __str__(self):
        pem = self.libPubKey.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        return pem.decode('utf-8')

    def __bytes__(self):
        pem = self.libPubKey.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        return pem


class AsmPrivateKey:
    """
    A wrapper around a private key.
    """
    def __init__(self, libPrivKey):
        self.libPrivKey = libPrivKey

    @classmethod
    def from_bytes(cls, byte_repr):
        private_key = serialization.load_pem_private_key(byte_repr, password=None)
        return cls(private_key)

    def __str__(self):
        pem = self.libPrivKey.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        return pem.decode('utf-8')

    def __bytes__(self):
        pem = self.libPrivKey.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        return pem



def AsymmetricKeyGen():
    """
     Generates a public-key pair for asymmetric encryption purposes.

     Params: None
     Returns: Public Key, Private Key
    """
    private_key = rsa.generate_private_key(public_exponent=65537,key_size=2048)
    public_key = private_key.public_key()

    return AsmPublicKey(public_key), AsmPrivateKey(private_key)



def AsymmetricEncrypt(PublicKey, plaintext):
    """
     Using the public key, encrypt the plaintext
     Params:
        > PublicKey - AsmPublicKey
        > plaintext - bytes
     Returns: Ciphertext object
    """
    check_type(PublicKey, AsmPublicKey, "PublicKey", "AsymmetricEncrypt")
    check_type(plaintext, bytes, "plaintext", "AsymmetricEncrypt")

    c_bytes = PublicKey.libPubKey.encrypt(plaintext, padding.OAEP(
                 mgf=padding.MGF1(algorithm=hashes.SHA512()),
                 algorithm=hashes.SHA512(),
                 label=None
             )
        )
    return c_bytes



def AsymmetricDecrypt(PrivateKey, ciphertext):
    """
     Using the private key, decrypt the ciphertext
     Params:
        > PrivateKey - AsmPrivateKey
        > ciphertext - bytes
     Returns: Public Key, Private Key
    """
    check_type(PrivateKey, AsmPrivateKey, "PrivateKey", "AsymmetricDecrypt")
    check_type(ciphertext, bytes, "ciphertext", "AsymmetricDecrypt")

    plaintext = PrivateKey.libPrivKey.decrypt(
        ciphertext,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA512()),
            algorithm=hashes.SHA512(),
            label=None
        )
    )

    return plaintext




def SignatureKeyGen():
    """
    Generates a public-key pair for digital signature purposes.
    Params: None
    Returns: Public Key, Private Key
    """
    return AsymmetricKeyGen()



def SignatureSign(PrivateKey, data):
    """
    Uses the private key key to sign the data. Note: if the message is too long, it should be
    prehashed and the hash digest should be passed in as data.
    Params:
        > PrivateKey - AsmPrivateKey
        > data       - bytes

    Returns: signature (bytes)
    """
    check_type(PrivateKey, AsmPrivateKey, "PrivateKey", "SignatureSign")
    check_type(data, bytes, "data", "SignatureSign")

    signature = PrivateKey.libPrivKey.sign(
        data,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA512()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA512()
    )
    return signature



def SignatureVerify(PublicKey, data, signature):
    """
    Uses the public key key to verify that signature is a valid signature for message.
    Params:
        > PublicKey - AsmPublicKey
        > data      - bytes
        > signature - bytes

    Returns: boolean conditional on signature matches
    """
    check_type(PublicKey, AsmPublicKey, "PublicKey", "SignatureVerify")
    check_type(data, bytes, "data", "SignatureVerify")

    try:
        PublicKey.libPubKey.verify(
            signature,
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA512()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA512()
        )
    except Exception as e:
        return False

    return True



def Hash(data):
    """
    Computes a cryptographically secure hash of data.
    Params:
        > data - bytes

    Returns: the SHA512 hash of the input data (bytes)
    """
    check_type(data, bytes, "data", "Hash")

    digest = hashes.Hash(hashes.SHA512())
    digest.update(data)
    return digest.finalize()


def HMAC(key, data):
    """
    Compute a SHA-512 hash-based message authentication code (HMAC) of data.
    Returns an error if key is not 128 bits (16 bytes).

    You should use this function if you want a “keyed hash” instead of simply calling Hash
    on the concatenation of key and data, since in practical applications,
    doing a simple concatenation can allow the adversary to retrieve the full key.

    Params:
        > key  - bytes
        > data - bytes

    Returns: SHA-512 hash-based message authentication code (HMAC) of data (bytes)
    """
    check_type(data, bytes, "data", "Hash")
    check_type(key, bytes, "key", "Hash")

    h = hmac.HMAC(key, hashes.SHA512())
    h.update(data)
    return h.finalize()

def HMAC_Verify(key, data, hmac):
    """
    Check if an HMAC is correct in constant time wrt the number of matching bytes.
    This is important to avoid timing attacks.

    Params:
        > key  - bytes
        > data - bytes
        > hmac - bytes

    Returns: Boolean conditional on if hmacs match
    """
    return constant_time.bytes_eq(HMAC(key, data), hmac)



def HashKDF(key, purpose):
    """
    Takes a key and a purpose and returns a new key.
    HashKDF is a keyed hash function that can generate multiple keys from a single key.
    This can simplify your key management schemes.

    Note that the "purpose" adds another input the the hash function such that the same password can produce
    more than one key.

    Params:
        > key - bytes
        > purpose - string

    Returns: new key (bytes)
    """

    check_type(key, bytes, "key", "HashKDF")
    check_type(purpose, str, "purpose", "HashKDF")

    hkdf = HKDF(
        algorithm=hashes.SHA512(),
        length=len(key),
        salt=None,
        info=None,
    )
    key = hkdf.derive(key + purpose.encode())
    return key




def PasswordKDF(password, salt, keyLen):
    """
    Output some bytes that can be used as a symmetric key. The size of the output equals keyLen.
    A password-based key derivation function can be used to deterministically generate a cryptographic key
    from a password or passphrase.

    A password-based key derivation function is an appropriate way to derive a key from a password,
    if the password has at least a medium level of entropy (40 bits or so).

    Ideally, the salt should be different for each user or use of the function.
    Avoid using the same constant salt for everyone,
    as that may enable an attacker to create a single lookup table for reversing this function.

    Params:
        > password - string
        > salt - bytes
        > keyLen - int

    Returns: A key of length keyLen (bytes)
    """
    check_type(password, str, "password", "PasswordKDF")
    check_type(salt, bytes, "salt", "PasswordKDF")
    check_type(keyLen, int, "keyLen", "PasswordKDF")

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=keyLen,
        salt=salt,
        iterations=100000,
    )
    key = kdf.derive(password.encode())
    return key



def SymmetricEncrypt(key, iv, plaintext):
    """
    Encrypt the plaintext using AES-CBC mode with the provided key and IV.
    Pads plaintext using 128 bit blocks. Requires a valid size key.
    The ciphertext at the end will inlcude the IV as the last 16 bytes.

    Params:
        > key - bytes (128, 192, or 256 bits)
        > iv  - bytes (128 bits)
        > plaintext - bytes

    Returns: A ciphertext using AES-CBC mode with the provided key and IV (bytes)
    """
    check_type(key, bytes, "key", "SymmetricEncrypt")
    check_type(iv, bytes, "iv", "SymmetricEncrypt")
    check_type(plaintext, bytes, "plaintext", "SymmetricEncrypt")

    padder = sym_padding.PKCS7(128).padder()
    padded_data = padder.update(plaintext)
    padded_data += padder.finalize()

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()

    return ciphertext + iv

def SymmetricDecrypt(key, ciphertext):
    """
    Decrypt the ciphertext using the key. The last 16 bytes of the ciphertext should be the IV.

    Params:
        > key        - bytes
        > iv         - bytes
        > ciphertext - bytes

    Returns: A plaintext, decrypted from the given ciphertext, key and iv (bytes)
    """
    check_type(key, bytes, "key", "symmetricDecrypt")
    check_type(ciphertext, bytes, "ciphertext", "symmetricDecrypt")

    iv = ciphertext[-16:]
    ciphertext = ciphertext[:-16]

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    decryptor = cipher.decryptor()
    plaintext = decryptor.update(ciphertext) + decryptor.finalize()

    unpadder = sym_padding.PKCS7(128).unpadder()
    plaintext = unpadder.update(plaintext)
    plaintext += unpadder.finalize()

    return plaintext



def SecureRandom(num_bytes):
    """
    Given a length, return that many randomly generated bytes. Can be used for an IV or symmetric key.

    Params:
        > num_bytes - int

    Returns: num_bytes random bytes
    """
    return os.urandom(num_bytes)




if __name__ == '__main__':
    # generate keys
    pk, sk = AsymmetricKeyGen()

    # marshall keys to byte
    pk_bytes = bytes(pk)
    sk_bytes = bytes(sk)

    # generate key copies from bytes
    pk2 = AsmPublicKey.from_bytes(pk_bytes)
    sk2 = AsmPrivateKey.from_bytes(sk_bytes)

    # encrypt the same message with the pub key and its copy
    cipher = AsymmetricEncrypt(pk, "CS166".encode())
    cipher2 = AsymmetricEncrypt(pk2, "CS166".encode())

    # decrypt with the non-matching sk to show they are the same
    plain = AsymmetricDecrypt(sk, cipher2)
    plain2 = AsymmetricDecrypt(sk2, cipher)

    assert(plain == plain2)

    # compute a signature
    verify_key, signing_key = SignatureKeyGen()
    data = "CS166".encode()
    signature = SignatureSign(signing_key, data)
    verification = SignatureVerify(verify_key, data, signature)

    assert(verification == True)

    # compute a hash (SHA512)
    hash = Hash("CS166".encode())
    assert(len(hash) == 64)

    # check HMACs
    hmac1 = HMAC("key".encode(), "data".encode())
    hmac2 = HMAC("key".encode(), "data".encode())
    assert(hmac1 == hmac2)

    # check HashKDF
    hkdf1 = HashKDF("key".encode(), "CS166")
    hkdf2 = HashKDF("key".encode(), "CS166")
    assert(hkdf1 == hkdf2)

    # check PasswordKDF
    password = "this is a long and secure password. Here are some symbols: @#$%^&^*%^%&"
    pkey = PasswordKDF(password, SecureRandom(16), 32)
    assert(len(pkey) == 32)

    # check symmetric encryption
    key = SecureRandom(32)
    iv = SecureRandom(16)
    plaintext = "CS166 is the best class".encode()

    ciphertext = SymmetricEncrypt(key, iv, plaintext)
    plaintext2 = SymmetricDecrypt(key, ciphertext)
    assert(plaintext == plaintext2)
