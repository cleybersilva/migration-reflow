using System.Net.Http;
using System.IO;

class Program {
    void Run() {
        var client = new HttpClient();
        File.ReadAllText("synthetic.txt");
    }
}
