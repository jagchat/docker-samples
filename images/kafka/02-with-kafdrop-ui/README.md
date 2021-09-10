# Demo

- instantiate kafka using docker
- basic pub/sub demo using python
- check the status using Kafdrop

# Build Setup

- Make sure python is installed
- Open command prompt
- Start Kafka instance (using docker-compose)
``` bash
>start.bat
```
- Install kafka-python package/library
``` bash
>pip install kafka-python
```
- start pub (producer)
``` bash
>python producer.py
```

- start sub (consumer)
``` bash
>python consumer.py
```

- Open http://localhost:9000 for Kafdrop