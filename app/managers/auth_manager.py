from pydantic import ValidationError

from app.schemas import Admin
from app.security import PasswordService
from app.storage.json_storage import read_json, write_json


class AuthManager:
    FILE_NAME = "admin.json"

    def __init__(self) -> None:
        self.password_service = PasswordService()
        self.users: list[Admin] = []
        self._load_users()

    def _load_users(self) -> None:
        records = read_json(self.FILE_NAME, [])
        try:
            self.users = [Admin.model_validate(record) for record in records]
        except ValidationError as exc:
            raise ValueError("Invalid admin data in admin.json") from exc

    def _save_users(self) -> None:
        write_json(
            self.FILE_NAME, [user.model_dump(mode="json") for user in self.users]
        )

    def authenticate_admin(self, email: str, password: str) -> Admin | None:
        for admin in self.users:
            if admin.email.lower() != email.lower():
                continue
            if not admin.is_active:
                return None
            if self.password_service.verify_password(
                password,
                admin.hashed_password,
            ):
                return admin
            return None
        return None

    def create_initial_admin(self, email: str, password: str) -> None:
        if self.users:
            raise ValueError("An admin account already exists.")

        normalized_email = email.strip().lower()
        if not normalized_email:
            raise ValueError("Email cannot be empty.")

        if len(password) < 12:
            raise ValueError("Password must be at least 12 characters long.")

        admin = Admin(
            id=1,
            email=normalized_email,
            hashed_password=self.password_service.hash_password(password),
            role="admin",
            is_active=True,
        )

        self.users.append(admin)

        try:
            self._save_users()
        except Exception:
            self.users.remove(admin)
            raise
