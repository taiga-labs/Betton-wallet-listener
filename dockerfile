FROM python:3.12

WORKDIR /app

COPY getters.py /app/getters.py
COPY schemas.py /app/schemas.py
COPY listener.py /app/listener.py
COPY requirements.txt /app/requirements.txt

RUN pip install --upgrade -r /app/requirements.txt

CMD ["python", "listener.py"]
