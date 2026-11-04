using System.Runtime.InteropServices;
using Launcher.Services;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using MultipageApp.Components;
using RazorConsole.Core;

using var mutex = new Mutex(true, @"Global\MultiEcho_Candy_Launcher_Mutex", out bool createdNew);
if (!createdNew)
{
    MessageBoxW(IntPtr.Zero, "Candy Launcher 已经在运行中，请勿重复启动！", "提示", 0x00000040 | 0x00040000);
    return;
}

Console.Title = "Candy Launcher";

var builder = Host.CreateApplicationBuilder(args);
builder.UseRazorConsole<App>();

// 注册服务
builder.Services.AddSingleton<LogService>();
builder.Services.AddSingleton<Job>();
builder.Services.AddSingleton<NapCatManager>();
builder.Services.AddSingleton<NonebotManager>();
builder.Services.AddHostedService<LauncherHostedService>();

var app = builder.Build();

await app.RunAsync();

[DllImport("user32.dll", CharSet = CharSet.Unicode)]
static extern int MessageBoxW(IntPtr hWnd, string text, string caption, uint type);
