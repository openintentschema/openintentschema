---
title: Measure non-functional criteria
description: Record k6 and JMeter results as measured evidence against the target of a non-functional criterion.
---

A non-functional criterion, such as a response time or an error rate, carries a measurable
`target` ([Write and approve intents](/approve-intents/)). It counts as covered only when evidence
carries a measure that meets the target. `ois measure` takes that measure from a load test run.

## 1. Give the criterion a target

```yaml
criteria:
  - key: AC-3
    notation: text
    kind: non-functional
    statement: 95 % of checkout requests answer within 500 ms
    target: {metric: responseTimeP95, operator: lte, value: 500, unit: ms}
```

`metric` is your own name for the value; the measure in the evidence carries the same name.

## 2. Run the load test with a result file

| Tool | How |
| --- | --- |
| k6 | `k6 run --summary-export=summary.json checkout.js`, or a `handleSummary` that writes the summary as JSON |
| JMeter | `jmeter -n -t checkout.jmx -l results.jtl`, with the default CSV format |

## 3. Record the run

```bash
ois measure summary.json --namespace https://ois.acme.example \
  --intent https://ois.acme.example/intents/INT-9@1 \
  --criterion "AC-3=http_req_duration:p(95)" \
  --test load/checkout.js --test-producer https://ois.acme.example/actors/qe-2c9d \
  --subject "$BUILD" --written-from-intent
```

```
ois measure: AC-3: responseTimeP95 5.98 ms, target lte 500 ms: pass
```

`--criterion` maps a criterion to a value of the run, as `METRIC:STAT`, and can be repeated:

| Results | Metrics | Statistics |
| --- | --- | --- |
| k6 | every metric of the summary, with submetrics such as `http_req_duration{expected_response:true}` | as in the summary: `avg`, `min`, `med`, `max`, `p(90)`, `p(95)`; `rate` and `count` |
| JMeter | `elapsed`, `Latency`, `Connect`, `IdleTime`, `bytes`, `sentBytes`; `samples` and `errors`; `{label:Checkout}` for one sampler | `avg`, `min`, `med`, `max`, `p(N)`; `count` and `rate` for `samples` (per second) and `errors` (share of failed samples) |

- **Evidence** per criterion, with the value as a measure named after the target's `metric`, in
  `ms` for times. Its result is `pass` when the value meets the target, otherwise `fail`. Units
  that differ from the target's are refused.
- **A test artifact** for the script or plan given with `--test`, pinned by its `sha256` and
  commit. As with [`ois junit --intent`](/link-tests/#3-derived-from-the-intent),
  `--written-from-intent` declares that it was written from the criteria it measures, and a test
  artifact already recorded for the same file is reused.
- **The time** of the evidence is the end of the last JMeter sample, or for k6, which records no
  time, when the summary file was written.

Percentiles of JMeter results are interpolated between the closest ranks, as k6 computes them.
URLs, response messages and thread names are not copied.
