using Launcher.Services;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using MultipageApp.Components;
using RazorConsole.Core;

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
