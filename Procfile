web: python manage.py migrate && python manage.py collectstatic --noinput && gunicorn -c gunicorn.conf.py django_project.wsgi:application
worker: celery -A django_project worker --loglevel=info
beat: celery -A django_project beat --loglevel=info
