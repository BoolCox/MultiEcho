import time


class AsyncProfiler:
    """
    轻量 async profiler
    - 用于记录函数分段耗时
    - 适合 bot / middleware / handler 调试
    """

    def __init__(self):
        self.records: list[tuple[str, float]] = []
        self.start_total = time.perf_counter()  # 自动启动，避免 None

    def mark(self, name: str):
        """
        记录一个时间点
        """
        now = time.perf_counter()
        self.records.append((name, now))

    def report(self):
        """
        输出耗时报告
        """
        if not self.records:
            total = (time.perf_counter() - self.start_total) * 1000
            print(f"\n===== PROFILER (EMPTY) =====")
            print(f"TOTAL: {total:.2f} ms")
            return

        print("\n===== PROFILER =====")

        prev = self.start_total

        for name, t in self.records:
            cost = (t - prev) * 1000
            print(f"{name}: {cost:.2f} ms")
            prev = t

        total = (prev - self.start_total) * 1000
        print(f"TOTAL: {total:.2f} ms")
