redis:
	docker run -p 6379:6379 -d --name redis-stack redis/redis-stack:latest
  
rm-redis:
	docker rm redis-stack

redis-tmp:
	docker run -p 6379:6379 -d --rm --name redis-stack redis/redis-stack:latest