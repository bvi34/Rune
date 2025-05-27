# Example for rune00/Dockerfile

FROM python:3.11-slim

WORKDIR /app

# Install simple lightweight services (expand later for memory/logic)
RUN pip install fastapi uvicorn chromadb

COPY . /app

EXPOSE 8000

CMD ["uvicorn", "--factory", "main:create_app", "--host", "0.0.0.0", "--port", "8000"]

