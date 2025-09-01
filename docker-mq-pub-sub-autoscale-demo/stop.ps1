docker-compose down --remove-orphans; 
docker ps -aq --filter "label=autoscaler.owner=true" | ForEach-Object { if($_) { docker rm -f $_ *>$null } }; 
docker ps -aq --filter "name=rabbitmq-worker" | ForEach-Object { if($_) { docker rm -f $_ *>$null } }; 
docker ps -aq --filter "label=com.docker.compose.project=myapp" | ForEach-Object { if($_) { docker rm -f $_ *>$null } }; 
docker network prune -f *>$null; 
Write-Host "✅ Cleanup complete!" -ForegroundColor Green