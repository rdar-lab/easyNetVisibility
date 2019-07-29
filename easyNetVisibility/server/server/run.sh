docker rm -f server
docker build -t easy_server .
docker run --name server -d -p 443:443 easy_server
