FROM python:3.11-slim

WORKDIR /app

RUN pip install fastapi uvicorn requests

COPY . /app

EXPOSE 4033

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "4033"]
