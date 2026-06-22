import pytest
from cryptography.fernet import Fernet

from app.auth.security import TokenCipher, TokenEncryptionError


def test_token_cipher_encrypts_and_decrypts_access_token() -> None:
    cipher = TokenCipher(Fernet.generate_key().decode("utf-8"))
    encrypted = cipher.encrypt("github-access-token")

    assert encrypted != b"github-access-token"
    assert cipher.decrypt(encrypted) == "github-access-token"


def test_token_cipher_rejects_invalid_key() -> None:
    with pytest.raises(TokenEncryptionError):
        TokenCipher("invalid-key")

