# simple rabbit mq client console test in c# 

> - RabbitMQ demo using c# console,
> - simple pub / sub demo,
> - continuous pub / sub demo,
> - continuous pub / multiple sub demo,


## Build Setup

- install/run docker *linux* image for rabbitmq (on windows) - you need to enable linux container support in this case

``` bash
docker run --rm -it --hostname my-rabbit -p 15672:15672 -p 5672:5672 rabbitmq:3-management
```
- use http://localhost:15672 with creds: guest/guest 
- configure RabbitMQ with "test-exchange" (as exchange) and "test-queue" (as queue) and bind them together (or import the config file 'config-export.json')
- Build solution.


## Scenarios

##### 1. One Producer with one message and One Consumer with continuous message handling
- Run Demo01Producer.exe to add one message to queue
- Run Demo01Consumer.exe to handle (consume) messages sent to queue (check intentional thread delay)

##### 2. Publish Multiple messages and One Consumer with continuous message handling
- Run Demo01Consumer.exe to handle (consume) messages sent to queue  (check intentional thread delay)
- Run Demo01ProduceMultipleMessages.exe to add typed messages to queue till you type "exit"

##### 3. Publish Continuous messages and One Consumer with continuous message handling
- Run Demo01Consumer.exe to handle (consume) messages sent to queue  (check intentional thread delay)
- Run Demo01ProduceContinuousMessages.exe to add 1 sec interval messages to queue till you hit ^C

##### 4. Publish Continuous messages and One Consumer with continuous message handling
- Run Demo01Consumer.exe twice or thrice to handle (consume) messages sent to queue  (check intentional thread delay)
- Run Demo01ProduceContinuousMessages.exe to add 1 sec interval messages to queue till you hit ^C (modify intentional thread delay as needed)


