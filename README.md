# autoloop 🔄

**autoresearch for everything.**

Karpathy's [autoresearch](https://github.com/karpathy/autoresearch) showed us the loop: point an AI agent at a problem, give it a metric, let it run 100 experiments overnight. Wake up to a better system.

That loop was hardcoded to ML training. **autoloop generalizes it to any domain.**

```python
from autoloop import AutoLoop

loop = AutoLoop(
    target="optimize.py",        # what the agent edits
    metric=my_eval_function,     # returns a float
    directives="program.md",     # research goals in plain English
    budget_seconds=300,          # per experiment (default: 5 min)
)

loop.run(experiments=100)        # go to sleep
# wake up to a git log of 100 experiments and a better system
```

## It Works — Here's a Real Test Run

We ran autoloop on a naive recursive fibonacci function, giving it 4 experiments to find a faster implementation. No human involved after the initial setup:

```
📊 Baseline score: -0.1717s  (naive recursion, fibonacci(30))

🔬 Experiment 1/4
✅ KEPT     | Score: -0.0249 (+0.1467) | Add memoization with dict cache

🔬 Experiment 2/4
❌ DISCARDED | Score: -0.0280 (-0.0030) | Switch to iterative approach

🔬 Experiment 3/4
❌ DISCARDED | Score: -999.000 (-998.97) | Wrong shortcut — should be discarded

🔬 Experiment 4/4
✅ KEPT     | Score: -0.0217 (+0.0032) | Use functools.lru_cache decorator

🏁 Run complete: 4 experiments | 2 improvements | Best: -0.0217s
```

**6.9x speedup from baseline.** Broken code (exp 3) was automatically detected and discarded via the correctness check in the metric. The loop kept every genuine improvement and rejected everything else.

## Why This Exists

autoresearch works because of three design decisions:
1. **Single file to modify** — keeps scope manageable, diffs reviewable
2. **Fixed time/compute budget** — makes experiments directly comparable
3. **One unambiguous metric** — enables full autonomy, no human judgment needed

These decisions aren't specific to ML training. They apply to any system you want to improve autonomously. autoloop is just the abstraction.

## What You Can Optimize

| Domain | Target file | Metric |
|--------|-------------|--------|
| **Prompt optimization** | `prompt.md` | LLM-as-judge score / task accuracy |
| **SQL queries** | `query.sql` | Execution time / rows returned |
| **Trading strategies** | `strategy.py` | Sharpe ratio / win rate |
| **API pipelines** | `pipeline.py` | Latency / success rate |
| **Test suites** | `tests.py` | Coverage / mutation score |
| **Compiler flags** | `build.sh` | Binary size / compile time |
| **Agent system prompts** | `system_prompt.md` | Task completion rate |
| **RAG pipelines** | `retrieval.py` | RAGAS score / hit rate |

## Install

```bash
pip install autoloop
```

Requires Python 3.10+. Works with any LLM agent backend (Claude Code, Codex, local models via Ollama).

## Quickstart

### 1. Define your target

The file your agent will edit. Start small — one function, one prompt, one query.

```python
# optimize.py — your agent edits this
SYSTEM_PROMPT = """You are a helpful assistant."""
```

### 2. Define your metric

A Python function that returns a float. Lower or higher = better (you configure which).

```python
def my_metric(target_path: str) -> float:
    """Run eval and return score. autoloop calls this after every experiment."""
    result = run_eval(target_path)
    return result.accuracy  # higher is better
```

### 3. Write your directives

Plain English research goals in `program.md`. This is what you iterate on over time.

```markdown
# Research Directives

## Goal
Improve the system prompt to increase task completion rate on customer support queries.

## Hypotheses to explore
- More specific role definition
- Explicit handling of edge cases
- Chain-of-thought instructions
- Tone adjustments for different query types

## Constraints
- Keep under 500 tokens
- Must pass safety checks
```

### 4. Run

```python
from autoloop import AutoLoop

loop = AutoLoop(
    target="optimize.py",
    metric=my_metric,
    directives="program.md",
    budget_seconds=300,
    agent="claude",           # "claude", "codex", "ollama"
    higher_is_better=True,
)

loop.run(experiments=100)
```

### 5. Review

```bash
autoloop history          # git log of all experiments
autoloop best             # show the best-performing version
autoloop diff 12 best     # compare experiment 12 to best
autoloop rollback 12      # restore experiment 12
```

## How It Works

```
┌─────────────────────────────────────────────────────────┐
│                      autoloop                           │
│                                                         │
│  Read directives.md                                     │
│         │                                               │
│         ▼                                               │
│  Agent proposes modification to target file             │
│         │                                               │
│         ▼                                               │
│  Apply modification                                     │
│         │                                               │
│         ▼                                               │
│  Run metric() with fixed budget                         │
│         │                                               │
│         ▼                                               │
│  Score improved? ──YES──▶ git commit + update best      │
│         │                                               │
│        NO                                               │
│         │                                               │
│         ▼                                               │
│  Discard + log                                          │
│         │                                               │
│         ▼                                               │
│  Repeat N times                                         │
└─────────────────────────────────────────────────────────┘
```

Each experiment is logged with: timestamp, modification description, score delta, and the full diff. The git history is your research log.

## Advanced Usage

### Parallel experiments

```python
loop.run(experiments=100, parallel=4)  # 4 agents running simultaneously
```

### Custom agent backends

```python
from autoloop.backends import OllamaBackend

loop = AutoLoop(
    target="prompt.md",
    metric=my_metric,
    directives="program.md",
    backend=OllamaBackend(model="llama3.1:70b"),
)
```

### Warm starts

```python
# Resume from a previous run's best result
loop.run(experiments=50, warm_start="./autoloop-results/best.py")
```

### Metric composition

```python
from autoloop import CompositeMetric

metric = CompositeMetric([
    (accuracy_metric, 0.7),   # 70% weight
    (latency_metric, 0.3),    # 30% weight
])
```

## Examples

- [`examples/prompt_optimization/`](examples/prompt_optimization/) — optimize a Claude system prompt for customer support
- [`examples/sql_optimization/`](examples/sql_optimization/) — optimize a slow SQL query
- [`examples/trading_strategy/`](examples/trading_strategy/) — evolve a trading strategy (inspired by AutoStrategy)
- [`examples/rag_pipeline/`](examples/rag_pipeline/) — optimize a RAG retrieval pipeline

## Comparison to autoresearch

| | autoresearch | autoloop |
|--|--|--|
| Domain | ML training only | Any |
| Target | `train.py` | Any file |
| Metric | `val_bpb` | Any Python function |
| Budget | 5-min wall clock | Configurable |
| Agent | Claude Code / Codex | Any |
| Parallel | No | Yes |

autoloop is autoresearch with the ML-specific parts removed and replaced with a general interface.

## Philosophy

The insight from autoresearch isn't about ML. It's about loop design:

1. **Unambiguous feedback** — the metric must be objective and quantitative
2. **Fixed budget** — experiments must be comparable
3. **Narrow scope** — one file, reviewable diffs
4. **Overnight scale** — 100 experiments while you sleep

Wherever you can satisfy these four conditions, you can run autonomous improvement. autoloop makes that loop accessible without writing the scaffolding yourself.

## Roadmap

- [ ] Web UI for experiment visualization
- [ ] Multi-file optimization with dependency tracking  
- [ ] MCP server (use autoloop as a tool inside Claude Code)
- [ ] Hosted experiment tracking (autoloop cloud)
- [ ] Pre-built metric libraries (RAGAS, finance, code quality)

## Contributing

PRs welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT

---

*Inspired by [karpathy/autoresearch](https://github.com/karpathy/autoresearch). autoloop generalizes the loop.*
