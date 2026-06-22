from cryptography.fernet import Fernet, InvalidToken


class TokenEncryptionError(Exception):
    """Raised when token encryption configuration or data is invalid."""


class TokenCipher:
    def __init__(self, encryption_key: str) -> None:
        try:
            self.fernet = Fernet(encryption_key.encode("utf-8"))
        except (TypeError, ValueError) as error:
            raise TokenEncryptionError("Token encryption key is invalid") from error

    def encrypt(self, token: str) -> bytes:
        return self.fernet.encrypt(token.encode("utf-8"))

    def decrypt(self, encrypted_token: bytes) -> str:
        try:
            return self.fernet.decrypt(encrypted_token).decode("utf-8")
        except InvalidToken as error:
            raise TokenEncryptionError("Encrypted token could not be decrypted") from error

