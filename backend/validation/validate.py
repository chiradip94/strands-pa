import asyncio
import time
import json
import importlib
import pkgutil
from pathlib import Path
from dataclasses import dataclass, field

from .utils.ws_client import WsClient, WsResponse
from .utils.judge import judge_response, JudgeResult
from .suites import TestCase


@dataclass
class TestResult:
    test: TestCase
    suite: str
    response: WsResponse
    judge: JudgeResult | None = None
    error: str | None = None
    duration: float = 0.0


@dataclass
class SuiteResult:
    name: str
    tests: list[TestResult]
    duration: float = 0.0

    @property
    def passed(self) -> int:
        return sum(1 for t in self.tests if t.judge and t.judge.passed)

    @property
    def failed(self) -> int:
        return sum(1 for t in self.tests if t.judge and not t.judge.passed)

    @property
    def errored(self) -> int:
        return sum(1 for t in self.tests if t.error)

    @property
    def total(self) -> int:
        return len(self.tests)

    @property
    def avg_score(self) -> float:
        scores = [t.judge.score for t in self.tests if t.judge]
        return sum(scores) / len(scores) if scores else 0.0


@dataclass
class Report:
    suites: list[SuiteResult]
    start_time: float
    end_time: float

    @property
    def total_passed(self) -> int:
        return sum(s.passed for s in self.suites)

    @property
    def total_failed(self) -> int:
        return sum(s.failed for s in self.suites)

    @property
    def total_errored(self) -> int:
        return sum(s.errored for s in self.suites)

    @property
    def total_tests(self) -> int:
        return sum(s.total for s in self.suites)

    @property
    def overall_score(self) -> float:
        scores = [t.judge.score for s in self.suites for t in s.tests if t.judge]
        return sum(scores) / len(scores) if scores else 0.0

    def to_text(self) -> str:
        lines = []
        lines.append("=" * 60)
        lines.append("  SYSTEM VALIDATION REPORT")
        lines.append("=" * 60)
        lines.append(f"  Started:  {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.start_time))}")
        lines.append(f"  Duration: {self.end_time - self.start_time:.1f}s")
        lines.append(f"  Overall Score: {self.overall_score:.1%}")
        lines.append(f"  Passed: {self.total_passed} / {self.total_tests}")
        if self.total_failed:
            lines.append(f"  Failed: {self.total_failed}")
        if self.total_errored:
            lines.append(f"  Errors: {self.total_errored}")
        lines.append("")

        for suite in self.suites:
            status = "✅" if suite.failed == 0 and suite.errored == 0 else "❌"
            lines.append(f"  {status} {suite.name} ({suite.passed}/{suite.total} passed, avg {suite.avg_score:.1%}) [{suite.duration:.1f}s]")
            for tr in suite.tests:
                status_icon = "✅" if tr.judge and tr.judge.passed else "❌"
                score_str = f"{tr.judge.score:.0%}" if tr.judge else "N/A"
                err = tr.error or ""
                label = f"  {status_icon} {tr.test.name} — {score_str} {err}"
                lines.append(f"    {label}")
                if tr.judge and not tr.judge.passed and tr.judge.score < 0.5:
                    lines.append(f"      ↳ {tr.judge.explanation}")
            lines.append("")

        if self.total_failed or self.total_errored:
            lines.append("  FAILED TESTS:")
            for suite in self.suites:
                for tr in suite.tests:
                    if (tr.judge and not tr.judge.passed) or tr.error:
                        label = f"    ❌ {suite.name} / {tr.test.name}"
                        if tr.error:
                            label += f" — {tr.error}"
                        elif tr.judge:
                            label += f" ({tr.judge.score:.0%}) — {tr.judge.explanation}"
                        lines.append(label)
            lines.append("")

        lines.append("=" * 60)
        lines.append(f"  SUMMARY: {self.total_passed}/{self.total_tests} passed, {self.total_failed} failed, {self.total_errored} errors")
        lines.append("=" * 60)
        return "\n".join(lines)

    def to_json(self, path: str | None = None) -> str:
        data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.start_time)),
            "duration_seconds": round(self.end_time - self.start_time, 2),
            "overall_score": round(self.overall_score, 4),
            "summary": {
                "total": self.total_tests,
                "passed": self.total_passed,
                "failed": self.total_failed,
                "errored": self.total_errored,
            },
            "suites": [],
        }
        for suite in self.suites:
            suite_data = {
                "name": suite.name,
                "duration_seconds": round(suite.duration, 2),
                "passed": suite.passed,
                "failed": suite.failed,
                "errored": suite.errored,
                "total": suite.total,
                "avg_score": round(suite.avg_score, 4),
                "tests": [],
            }
            for tr in suite.tests:
                test_data = {
                    "name": tr.test.name,
                    "prompt": tr.test.prompt,
                    "expected_behavior": tr.test.expected_behavior,
                    "duration_seconds": round(tr.duration, 2),
                    "tools_used": tr.response.tool_uses,
                    "handoffs": [(f, t) for f, t in tr.response.handoffs],
                    "response_text": tr.response.text,
                    "error": tr.error,
                }
                if tr.judge:
                    test_data["score"] = tr.judge.score
                    test_data["passed"] = tr.judge.passed
                    test_data["explanation"] = tr.judge.explanation
                suite_data["tests"].append(test_data)
            data["suites"].append(suite_data)

        output = json.dumps(data, indent=2, ensure_ascii=False)
        if path:
            Path(path).write_text(output)
        return output


def _discover_suites() -> list[tuple[str, list[TestCase]]]:
    suites = []
    pkg_path = Path(__file__).parent / "suites"
    for _, name, _ in pkgutil.iter_modules([str(pkg_path)]):
        if name == "__init__":
            continue
        mod = importlib.import_module(f".suites.{name}", __package__)
        tests = getattr(mod, "tests", None)
        if tests is not None:
            suites.append((name, tests))
    return suites


async def run_test(
    tc: TestCase,
    client: WsClient,
    session_id: str,
) -> TestResult:
    start = time.monotonic()
    try:
        resp = await client.send(tc.prompt, session_id=f"{session_id}_{tc.name.lower().replace(' ', '_')[:48]}")
        duration = time.monotonic() - start

        if resp.error:
            return TestResult(test=tc, suite="", response=resp, error=resp.error, duration=duration)

        judge = await judge_response(
            prompt=tc.prompt,
            expected_behavior=tc.expected_behavior,
            actual_response=resp.text,
            tools_used=resp.tool_uses,
        )
        result = TestResult(test=tc, suite="", response=resp, judge=judge, duration=duration)
    except Exception as e:
        duration = time.monotonic() - start
        result = TestResult(
            test=tc, suite="", response=WsResponse(), error=str(e), duration=duration
        )

    # Cleanup: revert any state changes regardless of test outcome
    if tc.cleanup_prompt:
        cleanup_sid = f"{session_id}_cleanup"
        try:
            await client.send(tc.cleanup_prompt, session_id=cleanup_sid)
        except Exception:
            pass  # best-effort cleanup

    return result


async def run_suite(
    name: str,
    tests: list[TestCase],
    client: WsClient,
    session_prefix: str = "val",
) -> SuiteResult:
    start = time.monotonic()
    session_id = f"{session_prefix}_{name}"
    results = []
    total = len(tests)
    for i, tc in enumerate(tests):
        print(f"  [{i+1}/{total}] {tc.name}...", end="", flush=True)
        result = await run_test(tc, client, f"{session_id}_{i}")
        result.suite = name
        results.append(result)
        if result.error:
            print(f" ❌ ERROR: {result.error}")
        elif result.judge and result.judge.passed:
            print(f" ✅ {result.judge.score:.0%}", end="")
        elif result.judge:
            print(f" ❌ {result.judge.score:.0%} — {result.judge.explanation}", end="")
        else:
            print(f" ❌ (no judge)", end="")
        if tc.cleanup_prompt:
            print(f" 🧹", end="")
        print()
    duration = time.monotonic() - start
    return SuiteResult(name=name, tests=results, duration=duration)


async def run_all(
    suites: list[tuple[str, list[TestCase]]] | None = None,
    ws_url: str = "ws://localhost:8000/ws",
    session_prefix: str = "val",
) -> Report:
    if suites is None:
        suites = _discover_suites()

    client = WsClient(url=ws_url)
    start_time = time.time()
    suite_results = []

    for name, tests in suites:
        sr = await run_suite(name, tests, client, session_prefix)
        suite_results.append(sr)

    return Report(suites=suite_results, start_time=start_time, end_time=time.time())


def print_report(report: Report, json_path: str | None = None):
    print(report.to_text())
    if json_path:
        report.to_json(json_path)
        print(f"  JSON report saved to: {json_path}")


async def main():
    import argparse

    parser = argparse.ArgumentParser(description="Run system validation against the backend")
    parser.add_argument("--url", default="ws://localhost:8000/ws", help="WebSocket URL of the backend")
    parser.add_argument("--json", default="", help="Save JSON report to this path")
    parser.add_argument("--suite", default="", help="Run only this suite (filename without .py)")
    parser.add_argument("--session-prefix", default="val", help="Prefix for session IDs")
    args = parser.parse_args()

    suites = _discover_suites()
    if args.suite:
        suites = [(n, t) for n, t in suites if n == args.suite]
        if not suites:
            print(f"Suite '{args.suite}' not found. Available: {[n for n, _ in suites]}")
            return 1

    total_tests = sum(len(t) for _, t in suites)
    print(f"Running {total_tests} tests across {len(suites)} suites...\n")

    report = await run_all(suites, ws_url=args.url, session_prefix=args.session_prefix)
    print_report(report, args.json or None)

    if report.total_failed > 0 or report.total_errored > 0:
        return 1
    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))
