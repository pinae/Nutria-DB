#!/usr/bin/env bash
cd /var/www
python3 manage.py migrate
python3 manage.py collectstatic
python3 manage.py initadmin
python3 manage.py initial_data
cd /home/docker
/usr/local/bin/uwsgi --ini /etc/uwsgi/apps-enabled/uwsgi-app.ini