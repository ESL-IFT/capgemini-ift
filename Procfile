web: python manage.py migrate --noinput && gunicorn ift_platform.wsgi --bind 0.0.0.0:$PORT --timeout 60
release: python manage.py migrate --noinput && python manage.py collectstatic --noinput
