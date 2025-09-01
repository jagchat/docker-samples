- RABBITMQ_API: http://rabbitmq:15672/api/queues/%2f/my-queue
- RabbitMQ Management: http://localhost:15672 (guest/guest)
- Publisher API: http://localhost:8080
- Grafana: http://localhost:3000 (admin/admin)
- Loki API: http://localhost:3100 (for debugging)

What is %2f

- %2f = URL encoding of /
- It means default vhost in RabbitMQ
- Safe to leave as-is unless you create your own vhosts
- if our own vhost: RABBITMQ_API: http://rabbitmq:15672/api/queues/myvhost/my-queue

Publish a message

```
curl -X POST http://localhost:8080/publish `
  -H "Content-Type: application/json"`
  -d '{"message":"Hello World"}'
```

Publish a batch of messages

```
curl.exe -X POST http://localhost:8080/publish/batch `
  -H "Content-Type: application/json"`
  -d '{"count": 10, "delay": 0.2}'
```

```
 curl http://localhost:8080/queue/status
```
