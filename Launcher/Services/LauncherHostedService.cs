using System.Text.RegularExpressions;
using Microsoft.Extensions.Hosting;

namespace Launcher.Services;

internal sealed class LauncherHostedService(
    NapCatManager napcat,
    NonebotManager nonebot,
    LogService log) : BackgroundService
{
    private static readonly Regex s_napcatFolderRegex = new("^napcat\\d+$", RegexOptions.IgnoreCase | RegexOptions.Compiled);

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        var currentDir = Directory.GetCurrentDirectory();
        var nonebotDir = Path.Combine(currentDir, "nonebot");
        var napcatDirs = Directory.GetDirectories(currentDir)
            .Where(d => s_napcatFolderRegex.IsMatch(Path.GetFileName(d)))
            .Order()
            .ToArray();

        if (napcatDirs.Length == 0)
        {
            log.Write("app", "未找到 NapCat 文件夹 (napcat1, napcat2, ...)");
        }
        else
        {
            log.Write("app", $"找到 {napcatDirs.Length} NapCat 实例");
            foreach (var dir in napcatDirs)
            {
                log.Write("app", $" - {Path.GetFileName(dir)}");
            }

            LinkConfigs(napcatDirs, log);
            log.Write("app", "启动中...");
            nonebot.Start(nonebotDir);
            napcat.LaunchAll(napcatDirs);
        }

        while (!stoppingToken.IsCancellationRequested)
        {
            napcat.OpenPendingBrowsers();

            try
            {
                await Task.Delay(1000, stoppingToken);
            }
            catch (OperationCanceledException)
            {
                break;
            }
        }
    }

    private static void LinkConfigs(string[] dirs, LogService log)
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
                log.Write("app", $"[{name}] config linked to {primary}");
            }
            catch (Exception ex)
            {
                log.Write("app", $"[{name}] config link failed: {ex.Message}");
            }
        }
    }

}
