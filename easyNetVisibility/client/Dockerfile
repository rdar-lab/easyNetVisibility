FROM ubuntu:24.04

# Install system dependencies and Python 3.10
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        python3-venv \
        nmap \
        tcpdump && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /opt/sensor

# Create virtual environment
RUN python3 -m venv /opt/sensor/venv

# Install Python dependencies in venv
COPY requirements.txt /opt/sensor/requirements.txt
RUN /opt/sensor/venv/bin/pip install --no-cache-dir -r /opt/sensor/requirements.txt

# Copy sensor code
COPY ./sensor /opt/sensor

ENTRYPOINT ["/opt/sensor/venv/bin/python", "sensor.py"]
