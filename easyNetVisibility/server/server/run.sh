docker rm -f server
docker build -t easy_server .
docker run --name server -d -p 80:80 easy_server
