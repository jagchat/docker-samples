docker container stop $(docker container list -a -q)
docker container prune -f
docker image rm $(docker image ls -a -q)
docker image prune -f
