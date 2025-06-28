FROM python:3.11-slim

# make Python unbuffered so we see prints in real time
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY src ./src
COPY config ./config

RUN pip install --no-cache-dir requests pyyaml

CMD ["python3", "src/check.py"]