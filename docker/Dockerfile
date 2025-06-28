FROM python:3.11-slim
WORKDIR /app
COPY src ./src
COPY config ./config
RUN pip install --no-cache-dir requests pyyaml

# Temporary entrypoint to debug:
ENTRYPOINT ["sh", "-c", "echo \"[DEBUG] Container started: listing /app\"; ls -R /app; echo \"[DEBUG] Now running check.py\"; python3 src/check.py"]