FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt* ./
RUN pip install --no-cache-dir -r requirements.txt 2>/dev/null || pip install fastapi uvicorn sqlalchemy
COPY . .
ENV MODULE_PORT=9000
CMD sh -c "uvicorn module:app --host 0.0.0.0 --port ${MODULE_PORT}"
