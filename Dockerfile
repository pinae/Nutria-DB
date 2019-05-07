FROM debian
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y \
	python3 \
	python3-dev \
	python3-setuptools \
	python3-pip \
	libmariadbclient-dev \
	pip3 install uwsgi && \
    rm -rf /var/lib/apt/lists/*
COPY requirements.txt /home/docker/requirements.txt
COPY nutriaDB /var/www/
COPY docker-setup/uwsgi-app.ini /etc/uwsgi/apps-enabled/uwsgi-app.ini
COPY docker-setup/init_database.sh /home/docker/docker-entrypoint.sh
WORKDIR /home/docker/
RUN pip3 install -r requirements.txt && pip3 install mysqlclient
EXPOSE 3031
CMD ["/usr/local/bin/uwsgi", "--ini", "/etc/uwsgi/apps-enabled/uwsgi-app.ini"]
