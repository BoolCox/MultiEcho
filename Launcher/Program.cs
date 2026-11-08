using System.Runtime.InteropServices;
using System.Text.RegularExpressions;
using Launcher.Services;

using var mutex = new Mutex(true, @"Global\MultiEcho_Launcher_Mutex", out bool createdNew);
if (!createdNew)
{
    MessageBoxW(IntPtr.Zero, "MultiEcho Launcher 已经在运行中，请勿重复启动！", "提示", 0x00000040 | 0x00040000);
    return;
}

Console.Title = "Multi Echo Launcher";

using var job = new Job();
using var cts = new CancellationTokenSource();
var napcat = new NapCatManager(job);
var nonebot = new NonebotManager(job);
var exitRequested = false;

Console.CancelKeyPress += (_, e) =>
{
    e.Cancel = true;
    exitRequested = true;
    cts.Cancel();
};
AppDomain.CurrentDomain.ProcessExit += (_, _) =>
{
    cts.Cancel();
    job.Dispose();
};

var currentDir = Directory.GetCurrentDirectory();
var napcatDirs = Directory.GetDirectories(currentDir)
    .Where(d => NapCatFolderRegex().IsMatch(Path.GetFileName(d)))
    .Order()
    .ToArray();

if (napcatDirs.Length == 0)
{
    Console.WriteLine("No NapCat folders found (napcat1, napcat2, ...)");
    Console.ReadKey();
    return;
}

Console.WriteLine($"Found {napcatDirs.Length} NapCat instance(s):");
foreach (var dir in napcatDirs)
    Console.WriteLine($" - {Path.GetFileName(dir)}");

LinkConfigs(napcatDirs);

Console.WriteLine("\nStarting...\n");
nonebot.Start(currentDir);

// 后台逐个错峰启动 NapCat，不阻塞浏览器打开与状态刷新循环
_ = Task.Run(async () =>
{
    try
    {
        await napcat.LaunchAllAsync(napcatDirs, cts.Token);
    }
    catch (OperationCanceledException) { }
    catch (Exception ex)
    {
        Console.WriteLine($"NapCat 启动异常: {ex.Message}");
    }
});

while (!exitRequested)
{
    napcat.OpenPendingBrowsers();
    Console.Clear();
    Console.WriteLine("NapCat status:\n");
    Console.WriteLine($"[nonebot] PID={nonebot.PidDisplay,-6} Status={nonebot.Status}");
    Console.WriteLine();

    foreach (var inst in napcat.Instances)
    {
        Console.WriteLine(
            $"[{inst.Name}] PID={inst.PidDisplay,-6} Status={inst.Status,-8} WebUI={inst.WebUiUrl ?? "waiting..."}");
    }

    Thread.Sleep(1000);
}

static void LinkConfigs(string[] dirs)
{
    var primary = Path.Combine(dirs[0], "config");
    foreach (var dir in dirs.Skip(1))
    {
        var link = Path.Combine(dir, "config");
        var name = Path.GetFileName(dir);
        try
        {
            if (Directory.Exists(link) || File.Exists(link))
            {
                if ((File.GetAttributes(link) & FileAttributes.ReparsePoint) != 0)
                    continue;
                Directory.Delete(link, true);
            }
            Directory.CreateSymbolicLink(link, primary);
            Console.WriteLine($"[{name}] config linked to {primary}");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[{name}] config link failed: {ex.Message}");
        }
    }
}

partial class Program
{
    [GeneratedRegex(@"^napcat\d+$", RegexOptions.IgnoreCase)]
    private static partial Regex NapCatFolderRegex();

    [LibraryImport("user32.dll", EntryPoint = "MessageBoxW", StringMarshalling = StringMarshalling.Utf16)]
    private static partial int MessageBoxW(IntPtr hWnd, string text, string caption, uint type);
}
