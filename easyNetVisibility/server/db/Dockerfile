FROM mysql:latest

ADD schema.sql /docker-entrypoint-initdb.d
ADD password.sql /docker-entrypoint-initdb.d

EXPOSE 3306