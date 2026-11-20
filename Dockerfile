FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Hugging Face Spaces runs as user 1000 and expects port 7860. Render sets $PORT.
RUN useradd -m -u 1000 user && mkdir -p /app/data && chown -R user /app
USER user
ENV PORT=7860
EXPOSE 7860
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
