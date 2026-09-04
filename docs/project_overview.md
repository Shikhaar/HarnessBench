# HarnessBench: Project Overview & Architecture Specification

## 1. Executive Summary & Problem Statement

Existing agent benchmarks (such as SWE-bench, HumanEval, and SWE-bench Lite) focus on evaluating the **raw intelligence and reasoning capacity of Large Language Models (LLMs)**. They treat the execution harness as a negligible implementation detail or an opaque black box.

However, in real-world software engineering, developers interact with **execution harnesses**—such as [Claude Code](https://claude.ai/code), [Aider](https://aider.chat), [Codeless](https://github.com), OpenHands, or custom enterprise agent runtimes. The harness governs:
- **Prompt construction & repository mapping:** How context is selected, compressed, or injected into the LLM context window.
- **Cache-efficiency:** Whether the harness preserves Anthropic or OpenAI prompt cache prefixes or continuously invalidates them on every turn.
- **Tool calling ergonomics:** How bash, search, file editing, and verification tools are structured and executed.
- **Repository hygiene & pollution:** Whether the runtime leaves behind scratchpads, temporary debug files, broken diffs, or uncommitted files.
- **Regression prevention:** Whether the agent ensures pre-existing tests continue to pass while implementing fixes.

### The Core Hypothesis

> **Given the exact same LLM, repository, task, tests, and execution environment, different coding-agent harnesses produce significantly different outcomes in correctness, true financial cost, latency, token efficiency, repository cleanliness, and regression safety.**

HarnessBench isolates the **execution harness as the sole independent variable**, holding the base model, task, and environment strictly constant.

---

## 2. System Architecture

HarnessBench consists of six decoupled modules:

```text
                               ┌─────────────────────────────┐
                               │       harnessbench CLI      │
                               └──────────────┬──────────────┘
                                              │
              ┌───────────────────────────────┼──────────────────────────────┐
              ▼                               ▼                              ▼
   ┌────────────────────┐          ┌────────────────────┐         ┌────────────────────┐
   │    Task Loader     │          │ Network Proxy      │         │  Harness Adapters  │
   │      (tasks/)      │          │(127.0.0.1:8088 MITM│         │   (bench/adapters) │
   └──────────┬─────────┘          └──────────┬─────────┘         └──────────┬─────────┘
              │                               │                              │
              │                               │ Captures Wire Telemetry      │ Launches Subprocess
              ▼                               ▼                              ▼
   ┌───────────────────────────────────────────────────────────────────────────────────┐
   │                             Workspace Sandbox Manager                             │
   │                   - Disposable Git repository / worktree                          │
   │                   - Pre-run baseline pytest execution                             │
   │                   - Post-run evaluation pytest execution                          │
   │                   - Git diff & untracked file snapshotting                        │
   └──────────────────────────────────────────┬────────────────────────────────────────┘
                                              │
                                              ▼
                             ┌─────────────────────────────────┐
                             │ Evaluation & Pollution Engine   │
                             │  - Regression Detection         │
                             │  - Repository Pollution Score   │
                             └────────────────┬────────────────┘
                                              │
                                              ▼
                             ┌─────────────────────────────────┐
                             │    Reporting & Leaderboard      │
                             │  - results/benchmark_report.json│
                             │  - Rich Terminal Leaderboard    │
                             │  - results/benchmark_report.md  │
                             └─────────────────────────────────┘
```

---

## 3. Implementation Phases & Roadmap

### Phase 1: Core Foundation & Domain Models (Completed)
- [x] Standard PEP 621 packaging (`pyproject.toml`) with Python 3.11+ support.
- [x] Strongly typed Pydantic v2 schemas:
  - `BenchmarkTask`: Task metadata, expected files, commands, paths.
  - `HarnessConfig`: Command arguments, environment mapping, timeouts.
  - `HarnessExecutionResult`: Process return code, stdout, stderr, execution wall-clock time.
  - `PollutionReport`: Unexpected files, unexpected directories, unrelated modifications, pollution score.
  - `RunResult`: Unified, reproducible benchmark result record.
  - `BenchmarkReport`: Aggregate multi-run benchmark report.
- [x] Process execution wrapper with subprocess timeout controls and automated credential scrubbing (redacting `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, and bearer tokens from logs and outputs).

### Phase 2: Network Interceptor Proxy & Telemetry (Completed)
- [x] Async reverse proxy built on FastAPI and httpx (`src/harnessbench/telemetry/proxy.py`).
- [x] Server-Sent Events (SSE) streaming pass-through for Anthropic `/v1/messages`:
  - Inspects `message_start` events for initial prompt tokens, cache-read tokens, and cache-creation tokens.
  - Inspects `message_delta` events for completion/output tokens.
  - Zero buffering delay: streams SSE chunks to the harness in real-time.
- [x] Pricing catalog (`src/harnessbench/telemetry/costs.py`) with rates for Claude 3.5 Sonnet, Claude 3.5 Haiku, Claude 3 Opus, GPT-4o, and GPT-4o-mini.
- [x] Proxy session lifecycle management (`POST /proxy/session/start`, `POST /proxy/session/stop`, `GET /proxy/session/summary`).

### Phase 3: Workspace Sandbox & Git Analysis (Completed)
- [x] Disposable Git workspace manager (`src/harnessbench/execution/sandbox.py`).
- [x] Pre-run git snapshotting (`git status --porcelain`, `git rev-parse HEAD`).
- [x] Post-run diff analysis (`git diff HEAD`, `git diff --shortstat HEAD`).
- [x] Automated directory cleanup on run exit.

### Phase 4: Evaluation & Repository Hygiene (Completed)
- [x] Two-stage pytest evaluation (`src/harnessbench/evaluation/`):
  - **Baseline evaluation:** Verifies pre-existing tests pass before the agent touches code.
  - **Post-run evaluation:** Verifies task evaluation tests pass after the agent completes.
- [x] **Regression Detection:** Flags a failure if baseline tests passed but post-run tests broke pre-existing behavior (`baseline_passed and not post_passed`).
- [x] **Repository Pollution Analyzer:**
  - Compares touched files against `expected_files`.
  - Distinguishes untracked files (scratch files, debug scripts, markdown logs) and unexpected directories (e.g. `.aider.tags.cache/`).
  - Computes a weighted `pollution_score`.

### Phase 5: Harness Adapters & Benchmark Tasks (Completed)
- [x] `BaseHarnessAdapter` abstract interface (`setup()`, `run()`, `teardown()`).
- [x] Initial adapters:
  - `ClaudeCodeAdapter`: Runs `claude -p "<prompt>"` in headless mode.
  - `AiderAdapter`: Runs `aider --message "<prompt>" --yes --no-git`.
  - `CodelessAdapter`: Runs `codeless --permission-mode full_auto -p "<prompt>"`.
  - `MockAdapter`: Deterministic reference adapter for zero-cost dry runs, testing, and CI.
- [x] Initial Benchmark Task Suite (`tasks/`):
  - `python_bugfix_001`: Token Bucket Rate Limiter refill calculation bug.
  - `python_refactor_001`: Extract configuration module while maintaining backward compatibility.
  - `python_dependency_001`: Python 3.10+ `collections.Mapping` deprecation fix.
- [x] Comprehensive test suite (17/17 tests passing across proxy, sandbox, adapters, pollution, evaluator, and integration).

### Phase 6: Ecosystem Expansion & Feature Roadmap (Upcoming)
- [ ] **OpenAI & Local Model Proxy Wire Capture:** Extend SSE streaming decoder to support OpenAI `/v1/chat/completions` and Ollama/vLLM endpoints.
- [ ] **Granular Test Regressions:** Parse pytest JUnit XML test output to track exact function-level test pass/fail state transitions rather than whole-suite exit status.
- [ ] **SWE-bench Lite Task Importer:** Automated ingestion script to pull a subset of real-world GitHub issues from SWE-bench Lite into HarnessBench task format.
- [ ] **Interactive HTML Dashboard:** Standalone visual leaderboard and diff visualizer for web sharing and reporting.
- [ ] **Git Worktree Support:** Add native `git worktree add / remove` as an alternative sandbox isolation backend for huge repositories.

---

## 4. Core Metrics & Calculation Formulas

| Metric | Variable | Ground Truth Source | Calculation |
| :--- | :--- | :--- | :--- |
| **Pass Rate** | `success` | Sandbox Pytest Runner | `post_tests_passed and not regression_detected` |
| **Regression Flag** | `regression_detected` | Evaluator | `baseline_passed == True and post_passed == False` |
| **Input Tokens** | `input_tokens` | Network Proxy (Wire) | Total prompt tokens reported by API wire response |
| **Output Tokens** | `output_tokens` | Network Proxy (Wire) | Total completion tokens reported by API wire response |
| **Cache Read Tokens** | `cache_read_tokens` | Network Proxy (Wire) | Anthropic `cache_read_input_tokens` |
| **True API Cost ($)** | `cost_usd` | Pricing Engine | `(in * rate_in + out * rate_out + cache_r * rate_cr + cache_w * rate_cw) / 10^6` |
| **Pollution Score** | `pollution_score` | Git Status Analyzer | `len(unexpected_files) + 2*len(unrelated_modifications) + 2*len(unexpected_dirs)` |
| **Turn Count** | `turn_count` | Network Proxy | Total HTTP API request count captured in session |
| **Latency** | `duration_seconds` | Process Runner | Subprocess wall-clock execution time |

---

## 5. Benchmark Task Specification

Every task inside `tasks/<task_id>/` follows this directory structure:

```text
tasks/<task_id>/
├── task.json                 # Metadata manifest and expected modified files
├── prompt.md                 # Unambiguous instruction prompt provided to the agent
├── golden_solution.patch     # Git diff reference solution
└── workspace/                # Pristine seed repository files
    ├── src/
    │   └── ...               # Application source files
    ├── tests/
    │   └── test_baseline.py  # Tests verifying baseline application state
    └── test_eval.py          # Strict evaluation tests verifying task resolution
```

### Manifest Schema (`task.json`)
```json
{
  "id": "python_bugfix_001",
  "name": "Token Bucket Rate Limiter Refill Bug",
  "description": "Fix token bucket refill calculation where tokens fail to replenish due to inverted elapsed time subtraction.",
  "expected_files": [
    "src/rate_limiter.py"
  ]
}
```

---

## 6. Command-Line Interface (CLI) Guide

### Running Benchmark
```bash
# Dry run on all tasks using the mock reference adapter
harnessbench run --harnesses mock --tasks all --model claude-3-5-sonnet-20241022

# Real agent benchmark across Claude Code, Aider, and Codeless
export ANTHROPIC_API_KEY="sk-ant-..."
harnessbench run \
    --harnesses aider,claude,codeless \
    --tasks all \
    --model claude-3-5-sonnet-20241022 \
    --timeout 300 \
    --output-dir results/
```

### Inspecting Leaderboard
```bash
harnessbench leaderboard --report results/benchmark_report.json
```

### Listing Tasks & Harnesses
```bash
harnessbench tasks
harnessbench harnesses
harnessbench version
```

### Standalone Network Proxy
```bash
harnessbench serve-proxy --port 8088 --host 127.0.0.1
```

---

## 7. Security Model & Best Practices

1. **Subprocess Sandboxing:** Agent harnesses run in isolated disposable directories. No agent run can modify files outside its assigned sandbox.
2. **Secret Redaction:** `scrub_secrets()` automatically strips known API keys (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GITHUB_TOKEN`, and standard key formats) from standard output, standard error, and persisted JSON results.
3. **No Hardcoded Credentials:** The proxy forwards existing authorization headers supplied by the harness or caller; no secrets are ever persisted to disk.
