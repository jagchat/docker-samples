using EasyConsole;
using MongoDB.Bson;
using MongoDB.Bson.Serialization;
using MongoDB.Driver;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace ConsoleApp1
{
    class Program
    {
        private static MongoClient client = null;

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
                    client = new MongoClient("mongodb://172.21.135.20");
                    Console.WriteLine("Connected");
                    Console.ReadLine();
                })
                .Add("List Databases", () =>
                {
                    Console.Clear();
                    var names = client.ListDatabaseNamesAsync()
                        .GetAwaiter().GetResult().ToList();
                    Console.WriteLine(String.Join("\n", names));
                    Console.ReadLine();
                })
                .Add("List Collections (in SampleDb)", () =>
                {
                    Console.Clear();
                    var db = client.GetDatabase("SampleDb");
                    var names = db.ListCollectionNamesAsync()
                        .GetAwaiter().GetResult().ToList();
                    Console.WriteLine(String.Join("\n", names));
                    Console.ReadLine();
                })
                .Add("List Documents (in SampleDb.employees)", () =>
                {
                    Console.Clear();
                    var db = client.GetDatabase("SampleDb");
                    var empCollection = db.GetCollection<EmployeeModel>("employees");
                    var empDocuments = empCollection.FindAsync(new BsonDocument())
                        .GetAwaiter().GetResult().ToList(); //no filter, means all docs.
                    if (empDocuments.Count == 0)
                    {
                        Console.WriteLine("No documents found");
                    }
                    foreach (var empItem in empDocuments)
                    {
                        Console.WriteLine($"\n{empItem.empno} | {empItem.ename} | {empItem.sal} | {empItem.deptno}");
                    }
                    Console.ReadLine();
                })
                .Add("Get Document using filter (from SampleDb.employees)", () =>
                {
                    Console.Clear();
                    var db = client.GetDatabase("SampleDb");
                    var empCollection = db.GetCollection<EmployeeModel>("employees");
                    var filter = Builders<EmployeeModel>.Filter.Eq("empno", "1001");
                    var empDocuments = empCollection.FindAsync(filter)
                        .GetAwaiter().GetResult().ToList(); //no filter, means all docs.
                    if (empDocuments.Count == 0)
                    {
                        Console.WriteLine("No documents found");
                    }
                    foreach (var empItem in empDocuments)
                    {
                        Console.WriteLine($"\n{empItem.empno} | {empItem.ename} | {empItem.sal} | {empItem.deptno}");
                    }
                    Console.ReadLine();
                })
                .Add("Add Document", () =>
                {
                    Console.Clear();
                    var db = client.GetDatabase("SampleDb");
                    var empCollection = db.GetCollection<EmployeeModel>("employees");
                    empCollection.InsertOneAsync(new EmployeeModel()
                    {
                        empno = "1001",
                        ename = "jag",
                        sal = "3400",
                        deptno = "10"
                    })
                        .GetAwaiter().GetResult();
                    Console.WriteLine($"\nSuccessfully added a document");
                    Console.ReadLine();
                })
                .Add("Update Document", () =>
                {
                    Console.Clear();
                    var db = client.GetDatabase("SampleDb");
                    var empCollection = db.GetCollection<EmployeeModel>("employees");
                    var filter = Builders<EmployeeModel>.Filter.Eq("empno", "1001");
                    var update = Builders<EmployeeModel>.Update.Set("ename", "Chat").Set("deptno", "20");
                    empCollection.FindOneAndUpdateAsync(filter, update)
                        .GetAwaiter().GetResult();
                    Console.WriteLine($"\nSuccessfully updated a document");
                    Console.ReadLine();
                })
                .Add("Delete Document", () =>
                {
                    Console.Clear();
                    var db = client.GetDatabase("SampleDb");
                    var empCollection = db.GetCollection<EmployeeModel>("employees");
                    var filter = Builders<EmployeeModel>.Filter.Eq("empno", "1001");
                    empCollection.FindOneAndDeleteAsync(filter)
                        .GetAwaiter().GetResult();
                    Console.WriteLine($"\nSuccessfully deleted a document");
                    Console.ReadLine();
                })
                .Add("Delete all Documents (from SampleDb.employees", () =>
                {
                    Console.Clear();
                    var db = client.GetDatabase("SampleDb");
                    var empCollection = db.GetCollection<EmployeeModel>("employees");
                    var deletedCount = empCollection.DeleteManyAsync(new BsonDocument())
                        .GetAwaiter().GetResult().DeletedCount;
                    Console.WriteLine($"\nDeleted {deletedCount} documents");
                    Console.ReadLine();
                })
                .Add("Pure JSON (no model) - List Documents", () =>
                {
                    Console.Clear();
                    var db = client.GetDatabase("SampleDb");
                    var empCollection = db.GetCollection<BsonDocument>("employees");
                    var empDocuments = empCollection.FindAsync(new BsonDocument())
                        .GetAwaiter().GetResult().ToList(); //no filter, means all docs.
                    if (empDocuments.Count == 0)
                    {
                        Console.WriteLine("No documents found");
                    }
                    foreach (var empItem in empDocuments)
                    {
                        Console.WriteLine($"\n{empItem.ToJson()}");
                        Console.WriteLine($"\n{empItem.GetValue("empno")} | {empItem.GetValue("ename")} | {empItem.GetValue("sal")} | {empItem.GetValue("deptno")}");
                        Console.WriteLine($"\n-------");
                    }
                    Console.ReadLine();
                })
                .Add("Pure JSON (no model) - Get Document using filter", () =>
                {
                    Console.Clear();
                    var db = client.GetDatabase("SampleDb");
                    var empCollection = db.GetCollection<BsonDocument>("employees");
                    var filter = Builders<BsonDocument>.Filter.Eq("empno", "1001");
                    var empDocuments = empCollection.FindAsync(filter)
                        .GetAwaiter().GetResult().ToList(); //no filter, means all docs.
                    if (empDocuments.Count == 0)
                    {
                        Console.WriteLine("No documents found");
                    }
                    foreach (var empItem in empDocuments)
                    {
                        Console.WriteLine($"\n{empItem.ToJson()}");
                        Console.WriteLine($"\n{empItem.GetValue("empno")} | {empItem.GetValue("ename")} | {empItem.GetValue("sal")} | {empItem.GetValue("deptno")}");
                        Console.WriteLine($"\n-------");
                    }
                    Console.ReadLine();
                })
                .Add("Pure JSON (no model) - Add Document", () =>
                {
                    Console.Clear();
                    var db = client.GetDatabase("SampleDb");
                    var jsonText = @"{
                        ""empno"": ""1002"",
                        ""ename"": ""chat"",
                        ""sal"": ""4500"",
                        ""deptno"": ""20""
                    }";
                    var doc = BsonSerializer.Deserialize<BsonDocument>(jsonText);
                    var empCollection = db.GetCollection<BsonDocument>("employees");
                    empCollection.InsertOneAsync(doc)
                        .GetAwaiter().GetResult();
                    Console.WriteLine($"\nSuccessfully added a document");
                    Console.ReadLine();
                })
                .Add("Pure JSON (no model) - Update Document", () =>
                {
                    Console.Clear();
                    var db = client.GetDatabase("SampleDb");
                    var jsonText = @"{
                        $set: {
                            ""sal"": ""9500"",
                            ""deptno"": ""10""
                        }
                    }";
                    var filterText = @"{
                        ""empno"": ""1002""
                    }";
                    var filter = BsonDocument.Parse(filterText); //just another way
                    var doc = BsonDocument.Parse(jsonText);
                    var empCollection = db.GetCollection<BsonDocument>("employees");
                    empCollection.UpdateOneAsync(filter, doc)
                        .GetAwaiter().GetResult();
                    Console.WriteLine($"\nSuccessfully updated a document");
                    Console.ReadLine();
                })
                .Add("Pure JSON (no model) - Delete Document", () =>
                {
                    Console.Clear();
                    var db = client.GetDatabase("SampleDb");
                    var filterText = @"{
                        ""empno"": ""1002""
                    }";
                    var filter = BsonDocument.Parse(filterText); //just another way
                    var empCollection = db.GetCollection<BsonDocument>("employees");
                    empCollection.DeleteOneAsync(filter)
                        .GetAwaiter().GetResult();
                    Console.WriteLine($"\nSuccessfully deleted a document");
                    Console.ReadLine();
                })
                .Add("Pure JSON (no model) - Delete all Documents", () =>
                {
                    Console.Clear();
                    var db = client.GetDatabase("SampleDb");
                    var empCollection = db.GetCollection<BsonDocument>("employees");
                    var deletedCount = empCollection.DeleteManyAsync(new BsonDocument())
                        .GetAwaiter().GetResult().DeletedCount;
                    Console.WriteLine($"\nDeleted {deletedCount} documents");
                    Console.ReadLine();
                }).Add("Quit", () =>
                {
                    Environment.Exit(0);
                });
            menu.Display();
        }
    }
}
