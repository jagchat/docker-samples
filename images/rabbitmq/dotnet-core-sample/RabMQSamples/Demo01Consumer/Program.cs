using RabbitMQ.Client;
using RabbitMQ.Client.Events;
using System;
using System.Text;

namespace Demo01Consumer
{
    class Program
    {
        static void Main(string[] args)
        {
            //consumes queue
            //intentional delay of 1sec
            //can be executed multiple times for multiple consumers and
            //a queue item will be consumed only once.  The next consumer consumes next item 

            Console.WriteLine("Starting up..");

            var factory = new ConnectionFactory() { HostName = "localhost" };
            using (var connection = factory.CreateConnection())
            {
                using (var channel = connection.CreateModel())
                {
                    channel.QueueDeclare(queue: "test-queue",
                                     durable: true,
                                     exclusive: false,
                                     autoDelete: false,
                                     arguments: null);

                    var consumer = new EventingBasicConsumer(channel);
                    consumer.Received += (model, ea) =>
                    {
                        var body = ea.Body.ToArray();
                        var message = Encoding.UTF8.GetString(body);
                        Console.WriteLine(" [x] Received {0}", message);
                        System.Threading.Thread.Sleep(1000);
                    };
                    channel.BasicConsume(queue: "test-queue",
                                         autoAck: true,
                                         consumer: consumer);

                    Console.WriteLine("Wating for messages..\n\n");
                    Console.WriteLine(" Press [enter] to exit.");
                    Console.ReadLine();
                }
            }
        }
    }
}
