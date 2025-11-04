# Bruno Backend - Submission Package

This package contains a working FastAPI backend for managing pattern components and a mock transpiler service.

## What's included
- `app/` - FastAPI application
- `transpiler_mock/` - Simple mock transpiler service (used for offline testing)
- `Dockerfile` - Builds the service image
- `transpiler_mock/Dockerfile` - Builds mock transpiler image
- `docker-compose.yml` - Orchestrates service, db, and mock transpiler
- `db_schema.sql` - PostgreSQL DDL
- `requirements.txt`
- `tests/` - Pytest test suite (basic)
- `bruno_assignment.zip` - This package (zipped)

## How to run (local / dev)
1. Ensure Docker and docker-compose are installed.
2. Build and start services:
   ```
   docker compose up --build
   ```
3. Service will be available at `http://localhost:8000`
   - Create component: POST `/components/`
   - Refine: POST `/components/{component_id}/refine`
   - Get: GET `/components/{component_id}`
   - History: GET `/components/{component_id}/history`

## Notes
- The included transpiler is a mock service that returns deterministic Python code so you can develop and test without the real external API.
- Database schema is in `db_schema.sql`. The app uses SQLAlchemy and will create tables if the DB is empty.
- For production, replace `transpiler_mock` with the real transpiler endpoint (update TRANSPILE_URL env var).

## Design decisions (abridged)
- **Component versions**: simple integer version bump stored in `component_versions`. Easy to query and reason about.
- **Chat history retention**: stored JSONB in each version for auditing; retained indefinitely in this assignment.
- **Concurrency**: database transactions are used; unique constraints prevent version collisions.
- **Error handling**: external transpiler errors are proxied as 502 to the client. Retries/backoff could be added.

## Test image for working endpoint and docker

<img width="1501" height="899" alt="image" src="https://github.com/user-attachments/assets/3b0ccb0a-f821-4ac0-abfa-8eae829039b4" />
<img width="1493" height="881" alt="create component" src="https://github.com/user-attachments/assets/6a3c97fd-0393-4883-bdd5-87eb69867f72" />
<img width="1920" height="1080" alt="docker" src="https://github.com/user-attachments/assets/e4038771-78fb-4544-98a5-56eb0670a431" />
<img width="1492" height="901" alt="get component" src="https://github.com/user-attachments/assets/a9873170-b15c-4669-8297-07fd7df40bb6" />
<img width="1500" height="896" alt="history of component" src="https://github.com/user-attachments/assets/13422591-cb5e-46aa-ba6c-36b7d2034a46" />





