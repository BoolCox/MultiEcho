using System.Diagnostics;
using System.Text;
using System.Text.RegularExpressions;

namespace Launcher.Services;

internal sealed partial class NonebotManager(Job job)
{
    private Process? _process;
    private volatile bool _started;
    private volatile string _status = "Not started";

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

    public void Start(string baseDir)
    {
        var nonebotDir = Path.Combine(baseDir, "nonebot");
        if (!Directory.Exists(nonebotDir))
        {
            Console.WriteLine("[nonebot] directory not found, skipping");
            return;
        }

        var venvDir = Path.Combine(nonebotDir, ".venv");
        if (!Directory.Exists(venvDir))
        {
            Console.WriteLine("[nonebot] .venv not found, running uv sync...");
            _status = "Syncing dependencies...";

            if (!RunUvSync(nonebotDir))
            {
                _status = "Sync failed";
                return;
            }

            Console.WriteLine("[nonebot] uv sync completed");
        }

        var nbExe = Path.Combine(nonebotDir, ".venv", "Scripts", "nb.exe");
        if (!File.Exists(nbExe))
        {
            Console.WriteLine("[nonebot] nb.exe not found in .venv\\Scripts");
            _status = "Failed";
            return;
        }

        var psi = new ProcessStartInfo
        {
            FileName = nbExe,
            Arguments = "run --reload",
            WorkingDirectory = nonebotDir,

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
            Console.WriteLine($"[nonebot] started (PID {proc.Id})");

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
            Console.WriteLine($"[nonebot] failed: {ex.Message}");
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
                    Console.WriteLine($"[nonebot/uv] {e.Data}");
            };
            proc.ErrorDataReceived += (_, e) =>
            {
                if (!string.IsNullOrWhiteSpace(e.Data))
                    Console.WriteLine($"[nonebot/uv] {e.Data}");
            };

            proc.Start();
            proc.BeginOutputReadLine();
            proc.BeginErrorReadLine();
            proc.WaitForExit();

            return proc.ExitCode == 0;
        }
        catch (Exception ex)
        {
            Console.WriteLine($"[nonebot] uv sync failed: {ex.Message}");
            return false;
        }
    }

    private void HandleOutput(string? line)
    {
        if (string.IsNullOrWhiteSpace(line) || _started)
            return;

        if (StartupRegex().IsMatch(line))
        {
            _started = true;
            _status = "Running";
        }
    }

    [GeneratedRegex(@"\[INFO\]\s+uvicorn\s+\|\s+Application startup complete\.", RegexOptions.IgnoreCase)]
    private static partial Regex StartupRegex();
}
