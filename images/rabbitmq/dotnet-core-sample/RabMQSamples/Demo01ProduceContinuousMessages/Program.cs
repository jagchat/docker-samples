using RabbitMQ.Client;
using System;
using System.Text;

namespace Demo01ProduceContinuousMessages
{
    class Program
    {
        static void Main(string[] args)
        {
            //Produces / publishes continuous messages till user presses ^C
            //intentional delay of 1 sec

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

                    Console.WriteLine("Press ^C to exit.");
                    while (true) {
                        string message = $"Hello World - {DateTime.Now.Ticks.ToString()}";
                        var body = Encoding.UTF8.GetBytes(message);

                        channel.BasicPublish(exchange: "test-exchange",
                                     routingKey: "",
                                     basicProperties: null,
                                     body: body);
                        Console.WriteLine(" [x] Sent {0}", message);
                        System.Threading.Thread.Sleep(1000);
                    }                    
                }
            }
        }
    }
}
