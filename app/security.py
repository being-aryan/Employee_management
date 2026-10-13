from pwdlib import PasswordHash


class PasswordService:
    def __init__(self) -> None:
        self.password_hasher = PasswordHash.recommended()

    def hash_password(self, password: str) -> str:
        return self.password_hasher.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.password_hasher.verify(plain_password, hashed_password)


password_service = PasswordService()
