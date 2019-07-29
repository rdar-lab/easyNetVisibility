docker rm -f sensor
docker build -t sensor .
docker run --name sensor --network host -d sensor
