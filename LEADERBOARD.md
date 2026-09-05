# HarnessBench v0.1 — Experimental Leaderboard

> **Notice:** This benchmarking suite evaluates AI coding-agent harnesses holding the underlying LLM strictly constant. External benchmark reference data is strictly segregated in its own section below and never combined with controlled HarnessBench results.

# HarnessBench Controlled Results

**Model Tested:** `claude-3-5-sonnet-20241022`  
**Total Executions:** 13  
**Repetitions per Task:** 1  
**Benchmark Timestamp:** `2026-09-05T06:34:07.156617`  
**Commit:** `8dddb6a99d913f81b84d6ed52cf61e37e51e6969`  

## Category Awards

| Award | Winner | Metric Highlight |
| :--- | :--- | :--- |
| **Highest Success Rate** | **`mock`** | 92.3% Pass Rate |
| **Most Cost Efficient** | **`mock`** | $0.0000 / successful task |
| **Fastest Latency** | **`mock`** | 1.2s median latency |
| **Cleanest Repository** | **`mock`** | 0 total pollution score |
| **Lowest Regression Rate** | **`mock`** | 0.0% regression rate |

## Main Leaderboard Rankings

| Rank | Harness | Success Rate | Cost / Succ. Task | Median Latency | Tokens / Succ. Task | Regression Rate | Total Pollution |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| #1 | **mock** | **92.3%** (12/13) | $0.0000 | 1.2s | 0 | 0.0% | 0 |

## Language Breakdown (Success Rate)

| Harness | Python | TypeScript | Go | Java | Rust |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **mock** | 100% | 100% | 100% | 100% | 0% |

## Software Engineering Capabilities Breakdown

| Harness | Api | Architecture | Bug Fixing | Build Systems | Concurrency | Dependencies | Error Handling | Performance | Refactoring |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **mock** | 100% | 100% | 100% | 100% | 100% | 100% | 50% | 100% | 100% |

---

# External Benchmark Reference Data

> **Methodological Separation:** These results were measured by third-party benchmarks under different experimental protocols. They are provided solely for contextual reference and must not be directly ranked against controlled HarnessBench runs.

| Benchmark | Version | Model | Harness | Language | Result / Score | Cost ($) | Runtime (s) | Source | Retrieved |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :--- | :---: |
| Aider Polyglot | 2024-05 | `claude-3-5-sonnet-20241022` | **aider** | Python | 100.0% | $0.0420 | 18.5s | [Aider Polyglot](https://raw.githubusercontent.com/Aider-AI/aider/main/benchmark/polyglot-results.json) | 2026-09-05 |
| Aider Polyglot | 2024-05 | `gpt-4o-2024-08-06` | **aider** | Rust | 100.0% | $0.0380 | 22.1s | [Aider Polyglot](https://raw.githubusercontent.com/Aider-AI/aider/main/benchmark/polyglot-results.json) | 2026-09-05 |
| Aider Polyglot | 2024-05 | `claude-3-5-sonnet-20241022` | **aider** | Go | 0.0% | $0.0610 | 31.0s | [Aider Polyglot](https://raw.githubusercontent.com/Aider-AI/aider/main/benchmark/polyglot-results.json) | 2026-09-05 |
| OpenHands Evaluation Index | v0.12.0 | `claude-3-5-sonnet-20241022` | **CodeActAgent** | Python | 100.0% | $0.3800 | 115.6s | [OpenHands Evaluation Index](https://raw.githubusercontent.com/All-Hands-AI/OpenHands/main/evaluation/results/index.json) | 2026-09-05 |
| OpenHands Evaluation Index | v0.12.0 | `gpt-4o-2024-08-06` | **CodeActAgent** | Python | 100.0% | $0.2900 | 88.2s | [OpenHands Evaluation Index](https://raw.githubusercontent.com/All-Hands-AI/OpenHands/main/evaluation/results/index.json) | 2026-09-05 |
| OpenHands Evaluation Index | v0.12.0 | `claude-3-5-sonnet-20241022` | **CodeActAgent** | Python | 0.0% | $0.5500 | 240.0s | [OpenHands Evaluation Index](https://raw.githubusercontent.com/All-Hands-AI/OpenHands/main/evaluation/results/index.json) | 2026-09-05 |
| SWE-bench Verified | v1.0 | `claude-3-5-sonnet-20241022` | **SWE-agent** | Python | 100.0% | $0.4500 | 182.4s | [SWE-bench Verified](https://raw.githubusercontent.com/princeton-nlp/SWE-bench/main/docs/leaderboard.json) | 2026-09-05 |
| SWE-bench Lite | v1.0 | `gpt-4o-2024-08-06` | **Aider** | Python | 100.0% | $0.2800 | 94.2s | [SWE-bench Lite](https://raw.githubusercontent.com/princeton-nlp/SWE-bench/main/docs/leaderboard.json) | 2026-09-05 |
| SWE-bench Verified | v1.0 | `claude-3-5-sonnet-20241022` | **SWE-agent** | Python | 0.0% | $0.5200 | 210.0s | [SWE-bench Verified](https://raw.githubusercontent.com/princeton-nlp/SWE-bench/main/docs/leaderboard.json) | 2026-09-05 |

## Reproducibility

To reproduce controlled HarnessBench executions locally:
```bash
harnessbench validate-tasks
harnessbench run --harnesses mock --tasks all --model claude-3-5-sonnet-20241022
```

To fetch official external benchmark reference datasets:
```bash
harnessbench dataset list
harnessbench dataset fetch aider-polyglot
harnessbench dataset fetch swebench
harnessbench dataset fetch openhands
```

Historical controlled runs are preserved in `results/harnessbench/` and external data in `results/external/`.