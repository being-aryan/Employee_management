import asyncio
import json
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import func, select, text

from app.database import AsyncSessionLocal
from app.models import Admin, Department, Employee
from app.models.employee import EmployeeStatus

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIRECTORY = PROJECT_ROOT / "data"


def read_json_file(filename: str) -> list[dict[str, Any]] | list[str]:
    """Read and return records from a JSON file."""
    file_path = DATA_DIRECTORY / filename

    if not file_path.exists():
        raise FileNotFoundError(f"JSON file not found: {file_path}")

    with file_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON list in {filename}")

    return data


async def reset_id_sequence(session: Any, table_name: str) -> None:
    """Synchronize a PostgreSQL ID sequence with existing IDs."""
    sequence_queries = {
        "employees": text(
            """
            SELECT setval(
                pg_get_serial_sequence('public.employees', 'id'),
                COALESCE(MAX(id), 1),
                MAX(id) IS NOT NULL
            )
            FROM public.employees
            """
        ),
        "admins": text(
            """
            SELECT setval(
                pg_get_serial_sequence('public.admins', 'id'),
                COALESCE(MAX(id), 1),
                MAX(id) IS NOT NULL
            )
            FROM public.admins
            """
        ),
    }
    if table_name not in sequence_queries:
        raise ValueError(f"Unsupported table for sequence reset: {table_name}")

    await session.execute(sequence_queries[table_name])


async def migrate_json_to_postgres() -> None:
    """Import departments, employees, and admins into PostgreSQL."""
    departments_data = read_json_file("departments.json")
    employees_data = read_json_file("employees.json")
    admins_data = read_json_file("admin.json")

    print("JSON files loaded successfully.")

    if not all(isinstance(item, str) for item in departments_data):
        raise ValueError("Invalid department records.")

    if not all(isinstance(item, dict) for item in employees_data):
        raise ValueError("Invalid employee records.")

    if not all(isinstance(item, dict) for item in admins_data):
        raise ValueError("Invalid admin records.")

    async with AsyncSessionLocal() as session:
        async with session.begin():
            existing_counts = {
                "departments": await session.scalar(
                    select(func.count()).select_from(Department)
                ),
                "employees": await session.scalar(
                    select(func.count()).select_from(Employee)
                ),
                "admins": await session.scalar(select(func.count()).select_from(Admin)),
            }

            if any(existing_counts.values()):
                raise RuntimeError(
                    "Migration stopped: one or more database tables "
                    "already contain records. No data was imported."
                )

            department_objects = [Department(name=name) for name in departments_data]
            session.add_all(department_objects)
            await session.flush()

            department_map = {
                department.name.casefold(): department.id
                for department in department_objects
            }
            print(f"Imported {len(department_objects)} departments.")

            employee_objects = []
            for record in employees_data:
                department_name = record["department"]
                department_key = department_name.casefold()
                department_id = department_map.get(department_key)

                if department_id is None:
                    raise ValueError(
                        f"Department '{department_name}' "
                        f"not found for employee ID {record['id']}."
                    )

                employee_objects.append(
                    Employee(
                        id=record["id"],
                        name=record["name"],
                        email=record["email"],
                        department_id=department_id,
                        salary=Decimal(str(record["salary"])),
                        status=EmployeeStatus(record["status"]),
                        is_deleted=record.get("is_deleted", False),
                    )
                )

            session.add_all(employee_objects)
            await session.flush()
            print(f"Imported {len(employee_objects)} employees.")

            admin_objects = [
                Admin(
                    id=record["id"],
                    email=record["email"],
                    hashed_password=record["hashed_password"],
                    is_active=record["is_active"],
                    role=record["role"],
                )
                for record in admins_data
            ]
            session.add_all(admin_objects)
            await session.flush()
            print(f"Imported {len(admin_objects)} admins.")

            await reset_id_sequence(session, "employees")
            await reset_id_sequence(session, "admins")

    print("\nJSON to PostgreSQL migration completed successfully.")


if __name__ == "__main__":
    asyncio.run(migrate_json_to_postgres())
