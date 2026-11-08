using System.Collections.Concurrent;
using System.Diagnostics;
using System.Text.RegularExpressions;
using Launcher.Models;

namespace Launcher.Services;

internal sealed partial class NapCatManager(Job job)
{
    private const int BaseWebUiPort = 6099;
    private static readonly TimeSpan s_launchInterval = TimeSpan.FromSeconds(2);

    // 整体替换数组，避免 UI/轮询线程遍历时集合被并发修改
    private volatile NapCatInstance[] _instances = [];
    private readonly ConcurrentQueue<string> _pendingUrls = new();

    public IReadOnlyList<NapCatInstance> Instances => _instances;

    public async Task LaunchAllAsync(string[] dirs, CancellationToken cancellationToken = default)
    {
        for (var i = 0; i < dirs.Length; i++)
        {
            if (i > 0)
                await Task.Delay(s_launchInterval, cancellationToken);

            // 为每个实例分配独立的 WebUI 端口，避免并发启动时抢占同一端口
            if (Launch(dirs[i], BaseWebUiPort + i) is { } inst)
                _instances = [.. _instances, inst];
        }
    }

    public void LaunchAll(string[] dirs)
    {
        for (var i = 0; i < dirs.Length; i++)
        {
            if (Launch(dirs[i], BaseWebUiPort + i) is { } inst)
                _instances = [.. _instances, inst];
        }
    }

    public void OpenPendingBrowsers()
    {
        while (_pendingUrls.TryDequeue(out var url))
        {
            try { Process.Start(new ProcessStartInfo(url) { UseShellExecute = true }); } catch { }
            Thread.Sleep(200);
        }
    }

    private NapCatInstance? Launch(string napcatDir, int webUiPort)
    {
        var name = Path.GetFileName(napcatDir);
        var launcher = Path.Combine(napcatDir, "launcher.bat");

        if (!File.Exists(launcher))
        {
            Console.WriteLine($"[{name}] launcher.bat not found");
            return null;
        }

        var psi = new ProcessStartInfo
        {
            FileName = "cmd.exe",
            Arguments = $"/c \"\"{launcher}\"\"",
            WorkingDirectory = napcatDir,
            UseShellExecute = false,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            CreateNoWindow = true,
            Environment =
            {
                ["NO_COLOR"] = "1",
                ["NAPCAT_WEBUI_PREFERRED_PORT"] = webUiPort.ToString()
            }
        };

        var instance = new NapCatInstance(name);

        try
        {
            var proc = new Process { StartInfo = psi, EnableRaisingEvents = true };
            proc.OutputDataReceived += (_, e) => HandleOutput(e.Data, instance);
            proc.ErrorDataReceived += (_, e) => HandleOutput(e.Data, instance);
            proc.Start();
            job.AddProcess(proc);
            proc.BeginOutputReadLine();
            proc.BeginErrorReadLine();
            instance.Process = proc;
            Console.WriteLine($"[{name}] started (PID {proc.Id}, preferred WebUI port {webUiPort})");
            return instance;
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[{name}] failed: {ex.Message}");
            return null;
        }
    }

    private static readonly Regex s_ansiEscapeRegex = new(@"\x1B\[[0-9;]*[A-Za-z]", RegexOptions.Compiled);

    private void HandleOutput(string? line, NapCatInstance inst)
    {
        if (string.IsNullOrWhiteSpace(line))
            return;

        var cleaned = s_ansiEscapeRegex.Replace(line, "");
        var match = WebUiRegex().Match(cleaned);
        if (match.Success && inst.TrySetWebUiUrl(match.Groups[1].Value))
            _pendingUrls.Enqueue(inst.WebUiUrl!);
    }

    [GeneratedRegex(@"WebUi User Panel Url:\s*(https?://127\.0\.0\.1:\d+[^\s]*)", RegexOptions.IgnoreCase)]
    private static partial Regex WebUiRegex();
}
