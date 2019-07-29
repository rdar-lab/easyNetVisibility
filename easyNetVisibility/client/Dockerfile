FROM ubuntu:16.04
ENV PATH /:$PATH
RUN apt-get update -y
RUN apt-get upgrade -y
RUN apt-get install -y python-pip
RUN apt-get install -y nmap
RUN apt-get install -y python-scapy
RUN apt-get install -y tcpdump
RUN pip install requests
copy ./sensor /opt/sensor
ENTRYPOINT python /opt/sensor/sensor.py
