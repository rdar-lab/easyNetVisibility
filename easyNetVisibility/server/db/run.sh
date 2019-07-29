docker rm -f db
docker build -t easy_db .
docker run --name db -e MYSQL_ROOT_PASSWORD=1234 -d -p 3306:3306 easy_db
