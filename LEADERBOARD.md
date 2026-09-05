# HarnessBench v0.1 — Experimental Leaderboard

> **Notice:** This is an experimental benchmarking suite evaluating AI coding-agent harnesses holding the underlying LLM strictly constant.

**Model Tested:** `claude-3-5-sonnet-20241022`  
**Total Executions:** 12  
**Repetitions per Task:** 1  
**Benchmark Timestamp:** `2026-09-05T05:25:49.313446`  
**Commit:** `a6fcdb9426810696839cb2256544fa733b9ea5f6`  

## 🏆 Category Awards

| Award | Winner | Metric Highlight |
| :--- | :--- | :--- |
| **Highest Success Rate** | **`mock`** | 100.0% Pass Rate |
| **Most Cost Efficient** | **`mock`** | $0.0000 / successful task |
| **Fastest Latency** | **`mock`** | 1.2s median latency |
| **Cleanest Repository** | **`mock`** | 0 total pollution score |
| **Lowest Regression Rate** | **`mock`** | 0.0% regression rate |

## 📊 Main Leaderboard Rankings

| Rank | Harness | Success Rate | Cost / Succ. Task | Median Latency | Tokens / Succ. Task | Regression Rate | Total Pollution |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| #1 | **mock** | **100.0%** (12/12) | $0.0000 | 1.2s | 0 | 0.0% | 0 |

## 🌐 Language Breakdown (Success Rate)

| Harness | Python | TypeScript | Go | Java |
| :--- | :---: | :---: | :---: | :---: |
| **mock** | 100% | 100% | 100% | 100% |

## 🛠️ Software Engineering Capabilities Breakdown

| Harness | Api | Architecture | Bug Fixing | Build Systems | Concurrency | Dependencies | Error Handling | Performance | Refactoring |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **mock** | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% |

## 🔬 Reproducibility

To reproduce these exact results locally:
```bash
harnessbench validate-tasks
harnessbench run --harnesses mock --tasks all --model claude-3-5-sonnet-20241022
```

Historical raw runs and manifests are preserved in `results/history/`.