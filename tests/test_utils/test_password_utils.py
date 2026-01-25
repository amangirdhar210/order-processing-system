import pytest
from app.serverful.utils.password_utils import hash_password, verify_password


class TestHashPassword:
    def test_hash_password_success(self):
        password = "SecurePassword123!"
        
        hashed = hash_password(password)
        
        assert hashed is not None
        assert isinstance(hashed, str)
        assert hashed != password
        assert hashed.startswith("$2b$")

    def test_hash_password_different_hashes_for_same_password(self):
        password = "SamePassword123"
        
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        assert hash1 != hash2

    def test_hash_password_empty_string_raises_error(self):
        with pytest.raises(ValueError) as exc_info:
            hash_password("")
        
        assert "Password cannot be empty" in str(exc_info.value)

    def test_hash_password_with_special_characters(self):
        password = "P@ssw0rd!#$%^&*()"
        
        hashed = hash_password(password)
        
        assert hashed is not None
        assert verify_password(hashed, password)

    def test_hash_password_with_unicode(self):
        password = "пароль密码🔐"
        
        hashed = hash_password(password)
        
        assert hashed is not None
        assert verify_password(hashed, password)


class TestVerifyPassword:
    def test_verify_password_correct(self):
        password = "CorrectPassword123"
        hashed = hash_password(password)
        
        result = verify_password(hashed, password)
        
        assert result is True

    def test_verify_password_incorrect(self):
        password = "CorrectPassword123"
        hashed = hash_password(password)
        
        result = verify_password(hashed, "WrongPassword456")
        
        assert result is False

    def test_verify_password_empty_plain_password(self):
        hashed = hash_password("SomePassword")
        
        result = verify_password(hashed, "")
        
        assert result is False

    def test_verify_password_invalid_hash_format(self):
        result = verify_password("not_a_valid_hash", "password")
        
        assert result is False
