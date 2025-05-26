web: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
worker: supervisord -c supervisord.conf
beat: celery -A config beat -l info 