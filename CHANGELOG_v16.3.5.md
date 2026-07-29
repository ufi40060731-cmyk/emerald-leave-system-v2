# v16.3.5 GitHub + MySQL + HTTPS

- Added a root Dockerfile for Railway full-stack deployment.
- FastAPI now serves the static frontend on the same origin.
- Added support for Railway `MYSQL_URL` and `mysql://` conversion to PyMySQL.
- Added automatic Railway HTTPS domain to allowed CORS origins.
- Frontend and auxiliary account pages use the same HTTPS origin.
- Added `railway.json` with Docker build and `/api/health` healthcheck.
- Removed GitHub Pages workflow to avoid frontend-only deployment.
- Removed secrets, runtime database files, caches, and duplicate backup source.
