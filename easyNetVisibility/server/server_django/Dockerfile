# Dockerfile

FROM python:3.11-bullseye

# install nginx and vim
RUN apt-get update && apt-get install -y --no-install-recommends nginx vim \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY nginx.default /etc/nginx/sites-available/default
RUN ln -sf /dev/stdout /var/log/nginx/access.log \
    && ln -sf /dev/stderr /var/log/nginx/error.log

# copy source and install dependencies
RUN mkdir -p /opt/app
RUN mkdir -p /opt/app/easy_net_visibility
COPY requirements.txt start-server.sh /opt/app/
RUN chmod +x /opt/app/start-server.sh
COPY easy_net_visibility /opt/app/easy_net_visibility/
# upgrade pip and install Python dependencies
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r /opt/app/requirements.txt
RUN chown -R www-data:www-data /opt/app

EXPOSE 8000
WORKDIR /opt/app
CMD ["/opt/app/start-server.sh"]
