---
title: Kernkonzepte
description: Die OIS-Record-Typen, wie sie aufeinander verweisen, und die Konformitätslevel.
---

OIS beschreibt Softwareauslieferung mit sechs Record-Typen, dem in einem Intent eingebetteten
Kriterium und dem Bundle als Transportcontainer. Alle Records sind JSON und teilen die Felder `ois`, `type`, `id` und
`createdAt`. Die normativen Definitionen stehen in
[Abschnitt 4 der Spezifikation](/de/specification/core-data-model/).

## Records

| Record | Aussage | Beispiel |
| --- | --- | --- |
| **Intent** | Was eine Änderung erreichen muss, mit **Akzeptanzkriterien**. Versioniert; nach der Freigabe unveränderlich. | "Kunden ändern ihre Adresse im Portal", Kriterium AC-2 in EARS |
| **Artefakt** | Etwas Erzeugtes: Code, ein Test, ein Contract, ein Datensatz, ein Dokument oder ein Build. Referenziert über Ort und Digest, nie gespeichert. | Die Testdatei `tests/address.spec.ts` in einem Commit |
| **Actor** | Ein Mensch, ein KI-Agent oder ein Werkzeug. Agenten nennen ihr Modell. | Ein QE-Agent auf Modell B, Version 2.1 |
| **Evidence** | Dass ein Testlauf ein Ergebnis für ein Kriterium erbracht hat, und ob der Test aus dem Intent, aus der Implementierung oder aus keinem von beiden abgeleitet wurde. | AC-2 bestanden, abgeleitet aus dem Intent |
| **Entscheidung** | Das Ergebnis eines Gates, gebunden an den Inhalt, auf dessen Grundlage es zustande kam. | Der Product Owner gibt eine Intent-Version frei, gebunden an ihren Digest |
| **Finding** | Ein Defekt oder Vorfall; nur durch eine unabhängige Entscheidung aufgelöst. | Ein Postleitzahl-Fall, den niemand gefordert hat, bricht die Prämienberechnung |

Ein **Bundle** transportiert mehrere Records gemeinsam. Ein **Quality Passport** ist eine
in-toto-Attestation, die jeden Record hinter einem Release sammelt.

## Referenzen und Integritätsregeln

Records verweisen per URI aufeinander: Ein Evidence-Record benennt ein Kriterium als
`<intent-id>@<version>#<key>`, seinen Test und den getesteten Code. Weil jedes Artefakt seinen
Producer nennt und was dieser bekommen hat (`context`), kann ein Validator Behauptungen prüfen,
die sonst auf Vertrauen beruhen würden, zum Beispiel:

- **R4, Ableitung:** Ein Test, der angibt, aus dem Intent abgeleitet zu sein, hat das Kriterium
  und keinen Code gesehen.
- **R5, Unabhängigkeit:** Ein aus dem Intent abgeleiteter Test wurde nicht von dem Actor
  geschrieben, der den Code geschrieben hat.
- **R1, Freigabe:** Ein freigegebenes Intent ist über einen Digest an seine Freigabe gebunden,
  sodass eine Änderung nach der Freigabe erkennbar ist.

Alle Regeln stehen in [Abschnitt 5](/de/specification/relationships-and-integrity-rules/).

## Versionen und Historie

Nichts wird gelöscht. Ein freigegebenes Intent ändert sich nur durch eine neue Version; Evidence
für eine ältere Version zählt für eine neuere nur, wenn das Kriterium unverändert ist, was ein
Digest zeigt ([Abschnitt 6.3](/de/specification/identifiers-versioning-and-digests/)). Falsche
Evidence wird durch eine Entscheidung widerrufen, und Findings werden durch neue Records ersetzt.

## Konformitätslevel

| Level | Name | Was ein Producer tut |
| --- | --- | --- |
| 1 | Observe | Erzeugt Artefakt- und Evidence-Records für seine eigenen Ergebnisse. `derivedFrom` darf `unknown` sein. |
| 2 | Intent-aware | Liest Intents, referenziert Kriterien und hält den vollständigen Kontext dessen fest, was er erzeugt. |
| 3 | Attested | Trägt eine Identität und signiert die Bundles und Passports, die er ausgibt. |

Ein Validator prüft Records gegen das Schema und die Integritätsregeln und meldet jedes Problem
als violation, warning oder info, jeweils mit seiner Regel. Die
[Konformitäts-Testsuite](/de/conformance/) legt fest, was er melden muss.
