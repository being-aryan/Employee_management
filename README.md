# Employee Management API (Async PostgreSQL)

FastAPI application using SQLAlchemy's asynchronous ORM with PostgreSQL and
`asyncpg`. Existing API routes, request/response schemas, business rules, soft
delete/restore behaviour, filtering, pagination, JWT authentication, and Alembic
revision are retained.

## Requirements

- Python 3.11 or newer (within the range declared in `pyproject.toml`)
- PostgreSQL
- Poetry 2.x

## Setup

1. Create your local environment file:

   ```bash
   cp .env.example .env
   ```

2. Set `DATABASE_URL` and `JWT_SECRET_KEY` in `.env`. The PostgreSQL URL should
   use `postgresql+asyncpg://`. The application also normalizes the common
   `postgresql://` and `postgresql+psycopg://` prefixes to `asyncpg` at runtime.

3. Resolve the updated dependency lock and install packages:

   ```bash
   poetry lock
   poetry install
   ```

4. Apply the existing Alembic migrations:

   ```bash
   poetry run alembic upgrade head
   ```

5. Start the API:

   ```bash
   poetry run uvicorn app.main:app --reload
   ```

6. Open Swagger UI at `http://127.0.0.1:8000/docs`.

## Async database design

- `create_async_engine()` creates the async SQLAlchemy engine.
- `async_sessionmaker()` creates request-scoped `AsyncSession` objects.
- Routers and database-backed manager methods use `async def` and `await`.
- Password hash verification is offloaded to Starlette's thread pool because
  Argon2 verification is CPU-bound.
- Alembic uses an async engine and `connection.run_sync()` for migration context.
- The JSON import utility is asynchronous and refuses to import when any target
  table already contains rows.

## Important data-safety notes

- The archive intentionally does not include `.env`, credentials, or a virtual
  environment. Create `.env` from `.env.example`; do not commit it.
- The existing migration revision is retained. `alembic upgrade head` applies
  migrations that have not yet been applied; it does not recreate existing tables.
- The JSON import utility is a one-time import. Do not run it against a database
  that already contains imported records.
- Back up your PostgreSQL database before applying migrations or importing data.
