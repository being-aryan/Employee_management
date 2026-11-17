from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Index,
    Numeric,
    String,
    func,
    text,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.department import Department


class EmployeeStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ON_LEAVE = "on_leave"


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    department_id: Mapped[int] = mapped_column(
        ForeignKey("departments.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    salary: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[EmployeeStatus] = mapped_column(
        SAEnum(
            EmployeeStatus,
            name="employee_status",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
        default=EmployeeStatus.ACTIVE,
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    department: Mapped["Department"] = relationship(
        back_populates="employees",
    )

    __table_args__ = (
        Index(
            "uq_employees_active_email",
            func.lower(email),
            unique=True,
            postgresql_where=text("is_deleted = false"),
        ),
    )
