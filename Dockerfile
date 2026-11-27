FROM python:3.11

WORKDIR /home/

RUN apt-get update && apt-get install -y --no-install-recommends default-libmysqlclient-dev pkg-config && rm -rf /var/lib/apt/lists/*

RUN echo "testing47"

RUN git clone https://github.com/skikim/prpc.git

WORKDIR /home/prpc/

RUN pip install --no-cache-dir -r requirements.txt

RUN pip install --no-cache-dir mysqlclient

EXPOSE 8000

CMD ["bash", "-c", "python manage.py collectstatic --noinput --settings=hospital_test.settings.deploy && python manage.py migrate --settings=hospital_test.settings.deploy && gunicorn hospital_test.wsgi --env DJANGO_SETTINGS_MODULE=hospital_test.settings.deploy --bind 0.0.0.0:8000"]