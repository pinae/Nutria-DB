#!/usr/bin/env bash
cd /var/www
python3 manage.py migrate
python3 manage.py collectstatic
python3 manage.py initadmin