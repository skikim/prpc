FROM python:3.9.0

WORKDIR /home/

RUN echo "testing12"

RUN git clone https://github.com/skikim/prpc.git

WORKDIR /home/prpc/

RUN pip install -r requirements.txt

RUN pip install gunicorn

RUN pip install mysqlclient

EXPOSE 8000

CMD ["bash", "-c", "python manage.py collectstatic --noinput --settings=hospital_test.settings.deploy && python manage.py makemigrations --settings=hospital_test.settings.deploy && python manage.py migrate --settings=hospital_test.settings.deploy && gunicorn hospital_test.wsgi --env DJANGO_SETTINGS_MODULE=hospital_test.settings.deploy --bind 0.0.0.0:8000"]

#CMD ["bash", "-c", "python manage.py collectstatic --noinput --settings=hospital_test.settings.deploy && gunicorn hospital_test.wsgi --env DJANGO_SETTINGS_MODULE=hospital_test.settings.deploy --bind 0.0.0.0:8000"]
