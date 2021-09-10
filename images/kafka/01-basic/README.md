# Demo

- instantiate kafka using docker
- basic pub/sub demo using python

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

---
**NOTE**
We can make use of any of the following tools to monitor Kafka
- Conduktor
- Kafdrop
- Kafka UI
- etc.
---


