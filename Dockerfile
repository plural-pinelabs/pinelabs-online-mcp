FROM python:3.12-slim

# Apply all available Debian security patches and remove unnecessary packages
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get autoremove --purge -y && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

# Run as non-root user for security
RUN useradd --no-create-home --shell /bin/false appuser
USER appuser

ENTRYPOINT ["python", "-m", "cli.pinelabs_mcp_server.main", "stdio"]
