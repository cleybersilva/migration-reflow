using System.IO;
using System.Net.Http;
using Shared.Common;

class Program
{
    static async System.Threading.Tasks.Task Main()
    {
        var payload = File.ReadAllText("lote.json");
        using var client = new HttpClient();
        await client.PostAsync(Settings.Endpoint, new StringContent(payload));
    }
}
