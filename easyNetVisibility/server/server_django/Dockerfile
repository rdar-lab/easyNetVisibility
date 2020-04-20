# Dockerfile

FROM python:3.7-buster

# install nginx
RUN apt-get update && apt-get install sudo nginx vim -y --no-install-recommends
COPY nginx.default /etc/nginx/sites-available/default
RUN ln -sf /dev/stdout /var/log/nginx/access.log \
    && ln -sf /dev/stderr /var/log/nginx/error.log

# copy source and install dependencies
RUN mkdir -p /opt/app
RUN mkdir -p /opt/app/easy_net_visibility
COPY requirements.txt start-server.sh /opt/app/
COPY easy_net_visibility /opt/app/easy_net_visibility/
RUN pip install -r /opt/app/requirements.txt
RUN chown -R www-data:www-data /opt/app

# start server
EXPOSE 8000
# STOPSIGNAL SIGTERM
WORKDIR /opt/app
CMD ["/opt/app/start-server.sh"]
