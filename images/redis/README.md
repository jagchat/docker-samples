# simple redis client console test in c# (using StackExchange.redis client)

> - Redis cache demo using c# console,
> - set / get / remove cache,
> - simple pub / sub demo,


## Build Setup

``` bash
# install/run docker *linux* image for redis (on windows) - you need to enable linux container support in this case
docker run -d -p 6379:6379 --name psfy-redis redis:5.0.0

```

- Using Visual Studio, Open the solution
- modify the connection info 
- run / debug "test" solution.
- Test using multiple instances of "test.exe" (multiple console windows)
