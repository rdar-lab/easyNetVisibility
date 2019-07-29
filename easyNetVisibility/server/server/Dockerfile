FROM ubuntu:16.04
ENV PATH /:$PATH
RUN apt-get update -y
RUN apt-get upgrade -y
RUN apt-get install -y apache2
RUN apt-get install -y libapache2-mod-wsgi
RUN apt-get install -y python-pip
RUN apt-get install -y libmysqlclient-dev
RUN a2enmod wsgi
RUN pip install Flask
RUN pip install flask_mail
RUN pip install flask_wtf
RUN pip install requests
RUN pip install MySQL-connector-python
copy ./webapp /var/www/webapp
COPY FlaskApp.conf /etc/apache2/sites-available/FlaskApp.conf
COPY settings.cfg /conf/settings.cfg
RUN a2ensite FlaskApp
RUN service apache2 restart
RUN rm -rf /etc/apache2/sites-available/000-default.conf
RUN rm -rf /etc/apache2/sites-enabled/000-default.conf
EXPOSE 80
EXPOSE 443
ENTRYPOINT export APP_CONFIG=/conf/settings.cfg && /usr/sbin/apache2ctl -D BACKGROUND && tail -f /var/log/apache2/*