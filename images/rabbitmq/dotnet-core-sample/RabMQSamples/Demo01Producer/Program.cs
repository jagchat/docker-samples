using RabbitMQ.Client;
using System;
using System.Text;

namespace Demo01Producer
{
    class Program
    {
        static void Main(string[] args)
        {
            //Produces / publishes single message and stops.

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

                    string message = $"Hello World - {DateTime.Now.Ticks.ToString()}";
                    var body = Encoding.UTF8.GetBytes(message);

                    channel.BasicPublish(exchange: "test-exchange",
                                 routingKey: "",
                                 basicProperties: null,
                                 body: body);
                    Console.WriteLine(" [x] Sent {0}", message);
                }
            }
            Console.WriteLine(" Press [enter] to exit.");
            Console.ReadLine();
        }
    }
}
