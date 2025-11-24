# Performance Benchmarks

Historical benchmark data stored in this directory.

## Common Commands

```bash
# Run performance tests and save results
uv run poe perf

# Compare two benchmarks
uv run pytest-benchmark compare benchmark-1.1.0.json benchmark-1.1.1.json

# Compare with histogram visualization
uv run pytest-benchmark compare benchmark-1.1.0.json benchmark-1.1.1.json --histogram

# List all benchmarks
uv run poe perf-list
```

## Files

- `benchmark-{suffix}.json` - pytest-benchmark results
- `benchmark-{suffix}.svg` - performance histogram
