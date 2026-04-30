web: gunicorn app.main:app --workers=1 --worker-class=uvicorn.workers.UvicornWorker
release: python scripts/render_migrate.py