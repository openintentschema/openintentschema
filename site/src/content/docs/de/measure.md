---
title: Nicht funktionale Kriterien messen
description: Halte Ergebnisse von k6 und JMeter als gemessene Evidence gegen das Ziel eines nicht funktionalen Kriteriums fest.
---

Ein nicht funktionales Kriterium, etwa eine Antwortzeit oder eine Fehlerquote, trägt ein messbares
`target` ([Intents schreiben und freigeben](/de/approve-intents/)). Es gilt nur dann als
abgedeckt, wenn Evidence einen Messwert trägt, der das Ziel erfüllt. `ois measure` nimmt diesen
Messwert aus einem Lasttest.
Die Befehle setzen voraus, dass `ois` installiert und `OIS_NAMESPACE` gesetzt ist
([Erste Schritte](/de/getting-started/#nächste-schritte)).

## 1. Dem Kriterium ein Ziel geben

```yaml
criteria:
  - key: AC-3
    notation: text
    kind: non-functional
    statement: 95 % of checkout requests answer within 500 ms
    target: {metric: responseTimeP95, operator: lte, value: 500, unit: ms}
```

`metric` ist dein eigener Name für den Wert; der Messwert in der Evidence trägt denselben Namen.
Gib das Intent wie jedes andere frei ([Intents schreiben und freigeben](/de/approve-intents/)), und
erfasse den Build, bevor der Lasttest läuft, wie bei jedem Test ([Tests mit Kriterien verknüpfen](/de/link-tests/#2-den-build-vor-dem-testlauf-erfassen)).

## 2. Den Lasttest mit einer Ergebnisdatei ausführen

| Werkzeug | Wie |
| --- | --- |
| k6 | `k6 run --summary-export=summary.json load/checkout.js`, oder ein `handleSummary`, das die Zusammenfassung als JSON schreibt |
| JMeter | `jmeter -n -t load/checkout.jmx -l results.jtl`, im voreingestellten CSV-Format |

## 3. Den Lauf aufzeichnen

```bash
ois measure summary.json --intent https://ois.acme.example/intents/INT-9@1 \
  --criterion "AC-3=http_req_duration:p(95)" \
  --test load/checkout.js --test-producer "$QE" \
  --subject "$BUILD" --written-from-intent
```

Nach einer Zeile pro geschriebenem Record meldet es:

```
ois measure: AC-3: responseTimeP95 5.98 ms, target lte 500 ms: pass
```

`--criterion` ordnet einem Kriterium einen Wert des Laufs zu, als `METRIC:STAT`, und lässt sich
wiederholen:

| Ergebnisse | Metriken | Statistiken |
| --- | --- | --- |
| k6 | jede Metrik der Zusammenfassung, mit Submetriken wie `http_req_duration{expected_response:true}` | wie in der Zusammenfassung: `avg`, `min`, `med`, `max`, `p(90)`, `p(95)`; `rate` und `count` |
| JMeter | `elapsed`, `Latency`, `Connect`, `IdleTime`, `bytes`, `sentBytes`; `samples` und `errors`; `{label:Checkout}` für einen Sampler | `avg`, `min`, `med`, `max`, `p(N)`; `count` und `rate` für `samples` (pro Sekunde) und `errors` (Anteil fehlgeschlagener Samples) |

- **Evidence** pro Kriterium, mit dem Wert als Messwert, benannt nach `metric` des Ziels, in `ms`
  für Zeiten. Ihr Ergebnis ist `pass`, wenn der Wert das Ziel erfüllt, sonst `fail`. Eine Einheit
  in den Ergebnissen, die von der des Ziels abweicht, wird abgelehnt; ein Wert ohne Einheit, etwa
  eine Anzahl, wird so verglichen, wie er ist, mit einem Hinweis. Ordne deshalb jedem Kriterium eine Metrik der
  passenden Art zu.
- **Ein Test-Artefakt** für das Skript oder den Testplan aus `--test`, festgelegt durch seinen
  `sha256` und den Commit. Wie bei [`ois junit --intent`](/de/link-tests/#4-aus-dem-intent-abgeleitet)
  erklärt `--written-from-intent`, dass es aus den gemessenen Kriterien geschrieben wurde, und ein
  bereits festgehaltenes Test-Artefakt für dieselbe Datei wird wiederverwendet.
- **Der Zeitpunkt** der Evidence ist das Ende des letzten JMeter-Samples, oder bei k6, das keinen
  Zeitpunkt festhält, der Moment, in dem die Datei der Zusammenfassung geschrieben wurde.

Perzentile von JMeter-Ergebnissen werden zwischen den nächsten Rängen interpoliert, so wie k6 sie
berechnet. URLs, Antwortmeldungen und Thread-Namen werden nicht übernommen.
