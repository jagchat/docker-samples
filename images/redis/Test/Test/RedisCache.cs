using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Newtonsoft.Json;
using StackExchange.Redis;

namespace Test
{
    public class RedisCache
    {
        private ConnectionMultiplexer redis = null;
        private const string CHANNEL = "EventLogChannel";
        public RedisCache(string connInfo)
        {
            redis = ConnectionMultiplexer.Connect(connInfo);
        }

        public bool IsKeyExists(string key)
        {
            return redis.GetDatabase().KeyExists(key);
        }

        public void Set<T>(string key, T value)
        {
            var json = JsonConvert.SerializeObject(value);
            redis.GetDatabase().StringSet(key, json);
            redis.GetSubscriber().Publish(CHANNEL, $"Value of '{key}' changed to (json): {json}");
        }

        public T Get<T>(string key)
        {
            var result = default(T);
            if (IsKeyExists(key))
            {
                result = JsonConvert.DeserializeObject<T>(redis.GetDatabase().StringGet(key));
            }
            return result;
        }

        public void Remove(string key)
        {
            redis.GetDatabase().KeyDelete(key);
        }

        public void Subscribe(Action<string> a)
        {
            redis.GetSubscriber().Subscribe(CHANNEL, (channel, message) => a(message));
        }

        public void Unsubscribe()
        {
            redis.GetSubscriber().Unsubscribe(CHANNEL);
        }

        public void Close()
        {
            redis.Dispose();
        }
    }
}
