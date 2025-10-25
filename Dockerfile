FROM python:3.14
RUN apt-get update && \
    apt-get install -y cython3

WORKDIR /app
COPY requirements.txt /app

COPY app /app
RUN pip install --no-cache-dir --upgrade -r requirements.txt

CMD ["fastapi", "run", "main.py", "--port", "8000"]
