using RabbitMQ.Client;
using System;
using System.Text;

namespace Demo01ProduceMultipleMessages
{
    class Program
    {
        static void Main(string[] args)
        {
            //Produces / publishes user provided messages till user types 'exit'

            Console.WriteLine("Starting up..");

            var factory = new ConnectionFactory() { HostName = "localhost" };
            using var connection = factory.CreateConnection();
            using var channel = connection.CreateModel();
            channel.QueueDeclare(queue: "test-queue",
                             durable: true,
                             exclusive: false,
                             autoDelete: false,
                             arguments: null);

            Console.WriteLine("Please type your message.");
            Console.WriteLine("Type 'exit' to exit.");

            while (true)
            {
                var message = Console.ReadLine();
                if (message == "exit")
                {
                    connection.Close();
                    break;
                }
                var body = Encoding.UTF8.GetBytes(message);
                channel.BasicPublish(exchange: "test-exchange",
                    routingKey: "",
                    basicProperties: null,
                    body: body);
                Console.WriteLine($"\t[x] Sent '{message}'. Type next message or 'exit'..");
            }
            Console.WriteLine("Stopped! \n\n");

        }
    }
}
