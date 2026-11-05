using Launcher.Models;
using System.Collections.Concurrent;
using System.Diagnostics;
using System.Text;
using System.Text.RegularExpressions;

namespace Launcher.Services;

internal sealed partial class NapCatManager(Job job, LogService log)
{
    private const int BaseWebUiPort = 6099;
    private static readonly TimeSpan s_launchInterval = TimeSpan.FromSeconds(2);

    // 整体替换数组，避免 UI 线程遍历时集合被修改
    private volatile NapCatInstance[] _instances = [];
    private readonly ConcurrentQueue<string> _pendingUrls = new();
    private readonly LogService _log = log;

    public IReadOnlyList<NapCatInstance> Instances => _instances;

    public async Task LaunchAllAsync(string[] dirs, CancellationToken cancellationToken)
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

    public void OpenPendingBrowsers()
    {
        while (_pendingUrls.TryDequeue(out var url))
        {
            try
            {
                Process.Start(new ProcessStartInfo(url) { UseShellExecute = true });
                _log.Write("napcat", $"opened WebUI: {url}");
            }
            catch (Exception ex)
            {
                _log.Write("napcat", $"failed to open browser {url}: {ex.Message}");
            }

            Thread.Sleep(200);
        }
    }

    private NapCatInstance? Launch(string napcatDir, int webUiPort)
    {
        var name = Path.GetFileName(napcatDir);
        var launcher = Path.Combine(napcatDir, "launcher.bat");

        if (!File.Exists(launcher))
        {
            _log.Write("napcat", $"[{name}] launcher.bat not found");
            return null;
        }

        var psi = new ProcessStartInfo
        {
            FileName = "cmd.exe",
            Arguments = $"/c \"\"{launcher}\"\"",
            WorkingDirectory = napcatDir,
            UseShellExecute = false,
            StandardOutputEncoding = Encoding.UTF8,
            StandardErrorEncoding = Encoding.UTF8,
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
            _log.Write("napcat", $"[{name}] started (PID {proc.Id}, preferred WebUI port {webUiPort})");
            return instance;
        }
        catch (Exception ex)
        {
            _log.Write("napcat", $"[{name}] failed: {ex.Message}");
            return null;
        }
    }

    private static readonly Regex s_ansiEscapeRegex = new(@"\x1B\[[0-9;]*[A-Za-z]", RegexOptions.Compiled);

    private void HandleOutput(string? line, NapCatInstance inst)
    {
        if (string.IsNullOrWhiteSpace(line))
            return;

        var cleaned = s_ansiEscapeRegex.Replace(line, "");
        _log.Write("napcat", $"[{inst.Name}] {cleaned}");

        var match = WebUiRegex().Match(cleaned);
        if (match.Success && inst.TrySetWebUiUrl(match.Groups[1].Value))
        {
            _pendingUrls.Enqueue(inst.WebUiUrl!);
            _log.Write("napcat", $"[{inst.Name}] WebUI ready: {inst.WebUiUrl}");
        }
    }

    [GeneratedRegex(@"WebUi User Panel Url:\s*(https?://127\.0\.0\.1:\d+[^\s]*)", RegexOptions.IgnoreCase)]
    private static partial Regex WebUiRegex();
}
