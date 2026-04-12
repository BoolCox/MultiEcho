using System.Collections.Concurrent;

namespace Launcher.Services;

public sealed class LogService
{
    private readonly ConcurrentQueue<LogLine> _lines = new();
    public event Action<LogLine>? LineReceived;

    public void Write(string source, string message)
    {
        if (string.IsNullOrWhiteSpace(message))
            return;

        var line = new LogLine(DateTimeOffset.Now, source, message);
        _lines.Enqueue(line);
        LineReceived?.Invoke(line);
    }

    public void Write(string message) => Write("app", message);

    public IReadOnlyCollection<LogLine> Snapshot() => [.. _lines];
}

public readonly record struct LogLine(DateTimeOffset Timestamp, string Source, string Message);