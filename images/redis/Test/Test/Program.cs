using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using EasyConsole;

namespace Test
{
    class Program
    {
        private static RedisCache redis = null;

        static void Main(string[] args)
        {
            while (true)
            {
                Console.Clear();
                ShowMenu();
            }
        }

        private static void ShowMenu()
        {
            var menu = new Menu()
                .Add("Connect", () =>
                {
                    Console.Clear();
                    redis = new RedisCache("<your-redis-ip>:6379, allowAdmin=true");
                    Console.WriteLine("Connected");
                    Console.ReadLine();
                })
                .Add("Get Cache", () =>
                {
                    Console.Clear();
                    if (!redis.IsKeyExists("a"))
                    {
                        Console.WriteLine("Nothing in cache at the moment");
                    }
                    else
                    {
                        var v = redis.Get<int>("a");
                        Console.WriteLine($"Current value: {v}");
                    }

                    Console.ReadLine();
                })
                .Add("Set Cache (multiply by 2)", () =>
                {
                    Console.Clear();
                    var v = (redis.IsKeyExists("a") ? redis.Get<int>("a") : 1) * 2;
                    redis.Set("a", v);
                    Console.WriteLine($"Value set as: {v}");
                    Console.ReadLine();
                })
                .Add("Remove Cache", () =>
                {
                    Console.Clear();
                    redis.Remove("a");
                    Console.WriteLine($"Cache cleared for key");
                    Console.ReadLine();
                })
                .Add("Log (pub/demo)", () =>
                {
                    Console.Clear();
                    Console.WriteLine($"--Event Log--");
                    redis.Subscribe((msg) => Console.WriteLine(msg));
                    Console.ReadLine();
                    redis.Unsubscribe();
                })
                .Add("Quit", () =>
                {
                    redis.Close();
                    Environment.Exit(0);
                });
            menu.Display();
        }
    }
}
