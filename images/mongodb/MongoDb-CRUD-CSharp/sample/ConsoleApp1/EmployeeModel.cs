using MongoDB.Bson;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace ConsoleApp1
{
    public class EmployeeModel
    {
        public ObjectId _id { get; set; } //used during document deserilization from bson
        public string empno { get; set; }
        public string ename { get; set; }
        public string sal { get; set; }
        public string deptno { get; set; }
    }
}
