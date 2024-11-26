FROM python:3.12

WORKDIR /app

COPY .env /app/.env
COPY getters.py /app/getters.py
COPY listener.py /app/listener.py
COPY schemas.py /app/schemas.py
COPY requirements.txt /app/requirements.txt

RUN pip install --upgrade -r /app/requirements.txt

CMD ["python", "listener.py"]
