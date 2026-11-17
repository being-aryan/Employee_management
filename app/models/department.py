from typing import TYPE_CHECKING

from sqlalchemy import Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.employee import Employee


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    employees: Mapped[list["Employee"]] = relationship(
        back_populates="department",
        passive_deletes=True,
    )

    __table_args__ = (
        Index(
            "uq_departments_name_lower",
            func.lower(name),
            unique=True,
        ),
    )
