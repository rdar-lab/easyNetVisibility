#!/usr/bin/env bash
export PRODUCTION=1

(cd easy_net_visibility; runuser -u www-data -- python manage.py collectstatic --no-input)
(cd easy_net_visibility; runuser -u www-data -- python manage.py migrate)

if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ] ; then
    (cd easy_net_visibility; runuser -u www-data -- python manage.py createsuperuser --no-input)
fi
(cd easy_net_visibility; gunicorn easy_net_visibility.wsgi --user www-data --bind 0.0.0.0:8010 --workers 3) &
nginx -g "daemon off;"