FROM python:3.8-slim

ENV FLASK_ENV=production

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt

COPY ./src /app

EXPOSE 80

CMD ["python3", "monitor.py"]