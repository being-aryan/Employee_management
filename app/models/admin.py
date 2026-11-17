from sqlalchemy import Boolean, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Admin(Base):
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    role: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="admin",
    )

    __table_args__ = (
        Index(
            "uq_admins_email_lower",
            func.lower(email),
            unique=True,
        ),
    )
