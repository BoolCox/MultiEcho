using System.Diagnostics;
using System.Text;
using System.Text.RegularExpressions;

namespace Launcher.Services;

internal sealed partial class NonebotManager(Job job, LogService log)
{
    private Process? _process;
    private volatile bool _started;
    private volatile string _status = "Not started";
    private readonly LogService _log = log;

    public string Status
    {
        get
        {
            if (_started) return _status;
            if (_process == null) return "Not started";
            return _process.HasExited ? "Stopped" : "Starting...";
        }
    }

    public string PidDisplay => _process?.Id.ToString() ?? "N/A";

    public void Start(string dir)
    {
        if (!Directory.Exists(dir))
        {
            _log.Write("nonebot", "目录不存在, 跳过启动");
            return;
        }

        var venvDir = Path.Combine(dir, ".venv");
        if (!Directory.Exists(venvDir))
        {
            _log.Write("nonebot", ".venv 不存在, 正在运行 uv sync...");
            _status = "Syncing dependencies...";

            if (!RunUvSync(dir))
            {
                _status = "Sync failed";
                return;
            }

            _log.Write("nonebot", "uv sync completed");
        }

        var nbExe = Path.Combine(dir, ".venv", "Scripts", "nb.exe");
        if (!File.Exists(nbExe))
        {
            _log.Write("nonebot", "nb.exe not found in .venv\\Scripts");
            _status = "Failed";
            return;
        }

        var psi = new ProcessStartInfo
        {
            FileName = nbExe,
            Arguments = "run --reload",
            WorkingDirectory = dir,

            RedirectStandardInput = true,
            RedirectStandardOutput = true,
            RedirectStandardError = true,

            StandardInputEncoding = new UTF8Encoding(false),
            StandardOutputEncoding = new UTF8Encoding(false),
            StandardErrorEncoding = new UTF8Encoding(false),

            UseShellExecute = false,
            CreateNoWindow = true,
            Environment = { ["PYTHONUTF8"] = "1" }
        };

        try
        {
            var proc = new Process { StartInfo = psi, EnableRaisingEvents = true };
            proc.OutputDataReceived += (_, e) => HandleOutput(e.Data);
            proc.ErrorDataReceived += (_, e) => HandleOutput(e.Data);
            proc.Exited += (_, _) => _status = "Stopped";
            proc.Start();
            job.AddProcess(proc);
            _process = proc;
            proc.BeginOutputReadLine();
            proc.BeginErrorReadLine();
            _status = "Starting...";
            _log.Write("nonebot", $"started (PID {proc.Id})");

            _ = Task.Run(async () =>
            {
                await Task.Delay(TimeSpan.FromSeconds(10));
                if (proc.HasExited) return;
                await proc.StandardInput.WriteLineAsync("y");
                await proc.StandardInput.FlushAsync();
            });
        }
        catch (Exception ex)
        {
            _log.Write("nonebot", $"failed: {ex.Message}");
            _status = "Failed";
        }
    }

    private bool RunUvSync(string workingDir)
    {
        var psi = new ProcessStartInfo
        {
            FileName = "uv",
            Arguments = "sync",
            WorkingDirectory = workingDir,
            UseShellExecute = false,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            CreateNoWindow = true
        };

        try
        {
            using var proc = new Process { StartInfo = psi };
            proc.OutputDataReceived += (_, e) =>
            {
                if (!string.IsNullOrWhiteSpace(e.Data))
                    _log.Write("nonebot", $"[uv] {e.Data}");
            };
            proc.ErrorDataReceived += (_, e) =>
            {
                if (!string.IsNullOrWhiteSpace(e.Data))
                    _log.Write("nonebot", $"[uv] {e.Data}");
            };

            proc.Start();
            proc.BeginOutputReadLine();
            proc.BeginErrorReadLine();
            proc.WaitForExit();

            return proc.ExitCode == 0;
        }
        catch (Exception ex)
        {
            _log.Write("nonebot", $"uv 进程处理错误: {ex.Message}");
            return false;
        }
    }

    private void HandleOutput(string? line)
    {
        if (string.IsNullOrWhiteSpace(line))
            return;

        _log.Write("nonebot", line);

        if (!_started && StartupRegex().IsMatch(line))
        {
            _started = true;
            _status = "Running";
        }
    }

    [GeneratedRegex(@"\[INFO\]\s+uvicorn\s+\|\s+Application startup complete\.", RegexOptions.IgnoreCase)]
    private static partial Regex StartupRegex();
}
