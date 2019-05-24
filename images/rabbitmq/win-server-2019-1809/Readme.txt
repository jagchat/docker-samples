1. run "build-image.bat"
2. run "start-container.bat"
3. get the ip of container using "docker inspect" (say: 172.21.137.89)
4. open http://172.21.137.89:15672 -> guest/guest

--------------------------------------------
5. next you can test pub/sub in nodejs-sample

6. switch to nodejs-sample/sample-subscriber folder
7. run "npm install"
8. modify ip and then run "node receive"


6. switch to nodejs-sample/sample-publisher folder
7. run "npm install"
8. modify ip and then run "node send"

9. you should see messages in "receive" window for every "node send" in another window
--------------------------------------
10. you should be able to see "hello" queue in "queues" tab using http://172.21.137.89:15672