worker:
	celery -A app.worker.celery_app worker --loglevel=info --concurrency=4 -Q default,analysis,maintenance

beat:
	celery -A app.worker.celery_app beat --loglevel=info

api:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
