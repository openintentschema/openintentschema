# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "cryptography>=50.0.2",
#     "jsonschema[format-nongpl]>=4.26.0",
#     "rfc8785>=0.1.4",
# ]
# ///
"""Generate the OIS conformance fixtures and their manifest.

Every fixture starts from one of three consistent bases (a bundle, a passport and a Level 1
bundle) and changes exactly one thing. Intent and criterion digests are computed with RFC 8785,
independently of any validator. Signed fixtures are DSSE envelopes signed with fixed Ed25519 test
keys; Ed25519 signs deterministically, so they are reproducible too. See README.md for the format
and the rule semantics.

    uv run fixtures/generate.py           # write the fixtures and manifest.json
    uv run fixtures/generate.py --check   # fail if a file is out of date or a fixture does
                                          # not behave as tagged against the schema
"""

import argparse
import base64
import copy
import hashlib
import json
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import rfc8785
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

HERE = Path(__file__).resolve().parent
SCHEMA = HERE.parent / "schema" / "ois.schema.json"

NS = "https://ois.acme.example"
STATEMENT_TYPE = "https://in-toto.io/Statement/v1"
PREDICATE_TYPE = "https://ois.example/passport/v0.1"
CRITERION_FIELDS = ("key", "statement", "notation", "kind", "target", "language")

Doc = dict[str, Any]
Expect = tuple[str, str]

R12_UNSIGNED: Expect = ("R12", "warning")
SIGNATURE_UNVERIFIED: Expect = ("signature", "warning")

IN_TOTO = "application/vnd.in-toto+json"
OIS_BUNDLE = "application/vnd.ois+json"
TRUSTED_KEYS = ("agent-runtime", "ci-recorder", "passport-issuer")  # keys/<name>.pub

# Keyless (Sigstore) fixtures cannot be generated: a GitHub Actions workflow signs the passport
# predicate written below (.github/workflows/sigstore-fixtures.yml) and its bundle is recorded.
SIGSTORE = HERE / "sigstore"
RECORDED = SIGSTORE / "passport.sigstore.json"
TRUSTED_ROOTS = ("keys/sigstore-public-good.trusted_root.json",)
GITHUB_ACTIONS = "https://token.actions.githubusercontent.com"
RECORDING_WORKFLOW = (
    "https://github.com/openintentschema/openintentschema/.github/workflows/"
    "sigstore-fixtures.yml@refs/heads/main"
)


# --- digests -----------------------------------------------------------------------------


def sha256(data: bytes) -> dict[str, str]:
    return {"sha256": hashlib.sha256(data).hexdigest()}


def content_digest(label: str) -> dict[str, str]:
    """Digest of external content. No validator can check it, so any stable value will do."""
    return sha256(f"ois fixture content: {label}".encode())


def seal_criteria(intent: Doc) -> None:
    for criterion in intent["criteria"]:
        fields = {k: criterion[k] for k in CRITERION_FIELDS if k in criterion}
        criterion["digest"] = sha256(rfc8785.dumps(fields))


def seal_intent(intent: Doc) -> None:
    content = {k: v for k, v in intent.items() if k not in ("digest", "status")}
    intent["digest"] = sha256(rfc8785.dumps(content))


def seal(doc: Doc) -> Doc:
    """Compute the digests of every approved or digested intent and bind its approvals."""
    for record in records(doc):
        if record["type"] == "intent" and (record["status"] == "approved" or "digest" in record):
            seal_criteria(record)
            seal_intent(record)
    bind_approvals(doc)
    return doc


def bind_approvals(doc: Doc) -> None:
    for record in records(doc):
        if record["type"] == "decision" and record["gate"] == "intent-approval":
            intent = find(doc, record["subject"])
            if intent is not None and "digest" in intent:
                record["subjectDigest"] = copy.deepcopy(intent["digest"])


# --- references and records --------------------------------------------------------------


def actor_ref(name: str, version: str | None = None) -> str:
    return f"{NS}/actors/{name}" + (f"@{version}" if version else "")


def intent_ref(name: str, version: int, key: str | None = None) -> str:
    return f"{NS}/intents/{name}@{version}" + (f"#{key}" if key else "")


def ref(kind: str, name: str) -> str:
    return f"{NS}/{kind}/{name}"


def record(type_: str, id_: str, created_at: str, **fields: Any) -> Doc:
    return {"ois": "0.1", "type": type_, "id": id_, "createdAt": created_at, **fields}


def records(doc: Doc) -> list[Doc]:
    if doc.get("_type") == STATEMENT_TYPE:
        result: list[Doc] = doc["predicate"]["records"]
        return result
    return doc["records"] if doc["type"] == "bundle" else [doc]


def find(doc: Doc, reference: str) -> Doc | None:
    """The record a reference resolves to, for the reference forms the bases use."""
    base, _, version = reference.partition("@")
    version = version.partition("#")[0]
    for candidate in records(doc):
        if candidate["id"] != base:
            continue
        if not version or str(candidate.get("version")) == version:
            return candidate
    return None


def get(doc: Doc, reference: str) -> Doc:
    found = find(doc, reference)
    assert found is not None, reference
    return found


def remove(doc: Doc, reference: str) -> None:
    records(doc).remove(get(doc, reference))


TS = "2026-09-01T08:00:00Z"
GIT = "git+https://git.acme.example/portal.git@a1b2c3d4e5f60718293a4b5c6d7e8f9012345678"

PO = actor_ref("po-7f3a")
QE_LEAD = actor_ref("qe-2c9d")
SUPPORT = actor_ref("support-4b1e")
REQ_AGENT = actor_ref("requirement-agent", "1.4")
DEV_AGENT = actor_ref("dev-agent", "3.0")
QE_AGENT = actor_ref("qe-agent", "2.1")
RUNTIME = actor_ref("agent-runtime", "4.3")
DATAGEN = actor_ref("testdata-generator", "5.2")
CI = actor_ref("ci-recorder", "1.2")
ISSUER = actor_ref("passport-issuer", "1.0")

INTENT = ref("intents", "INT-142")
CONTRACT = ref("artifacts", "ART-301")
CODE = ref("artifacts", "ART-302")
DATASET = ref("artifacts", "ART-303")
TEST = ref("artifacts", "ART-304")
BUILD = ref("artifacts", "ART-305")
EVIDENCE = ref("evidence", "EV-9021")
APPROVAL = ref("decisions", "DEC-77")
RELEASE = ref("decisions", "DEC-81")

AC1 = (
    "Given a logged-in customer, when they submit a valid Swiss address, "
    "then the new address is saved with the chosen effective date"
)
AC2 = "WHEN an address cannot be assigned to a canton, THE portal SHALL flag the premium region for manual review"
AC2_CHANGED = (
    "WHEN an address cannot be assigned to a canton, THE portal SHALL flag the premium region "
    "for manual review and notify the customer"
)
NFR1 = "THE portal SHALL confirm an address change within 500 milliseconds at the 95th percentile"


def human(name: str, display: str, **fields: Any) -> Doc:
    return record("actor", actor_ref(name), TS, kind="human", name=display, **fields)


def machine(kind: str, name: str, version: str, display: str, **fields: Any) -> Doc:
    return record("actor", actor_ref(name), TS, kind=kind, name=display, version=version, **fields)


def model(provider: str, name: str) -> dict[str, str]:
    return {"provider": provider, "name": name, "version": "2026-09"}


def actors() -> list[Doc]:
    return [
        human("po-7f3a", "PO 7f3a", operator="Team Portal"),
        machine("agent", "requirement-agent", "1.4", "Requirement agent",
                model=model("ExampleAI", "model-a"), autonomyLevel=1),
        machine("agent", "dev-agent", "3.0", "Developer agent",
                model=model("ExampleAI", "model-a"), autonomyLevel=2),
        machine("agent", "qe-agent", "2.1", "QE agent",
                model=model("OtherAI", "model-b"), autonomyLevel=2),
        machine("tool", "agent-runtime", "4.3", "Agent runtime and gateway",
                identity={"issuer": "https://oidc.acme.example",
                          "subject": "spiffe://acme.example/agent-runtime"}),
        machine("tool", "testdata-generator", "5.2", "Synthetic test data generator"),
        machine("tool", "ci-recorder", "1.2", "CI evidence recorder"),
    ]


def intent(
    version: int,
    status: str = "approved",
    ac2: str = AC2,
    created_at: str = "2026-10-14T09:12:00Z",
) -> Doc:
    criteria = [
        {"key": "AC-1", "statement": AC1, "notation": "gherkin", "kind": "functional",
         "criticality": "high"},
        {"key": "AC-2", "statement": ac2, "notation": "ears", "kind": "functional",
         "criticality": "high"},
        {"key": "NFR-1", "statement": NFR1, "notation": "ears", "kind": "non-functional",
         "target": {"metric": "responseTimeP95", "operator": "lte", "value": 500, "unit": "ms"},
         "criticality": "medium"},
    ]
    result = record(
        "intent", INTENT, created_at, version=version,
        title="Customers change their address in the portal", status=status, language="en",
        producedBy=REQ_AGENT, source="https://jira.acme.example/browse/PORTAL-1187",
    )
    if version > 1:
        result["supersedes"] = intent_ref("INT-142", version - 1)
    result["risk"] = "high"
    result["criteria"] = criteria
    return result


def approval(id_: str, version: int, decided_at: str = "2026-10-14T10:05:00Z") -> Doc:
    return record(
        "decision", ref("decisions", id_), decided_at, gate="intent-approval",
        subject=intent_ref("INT-142", version), outcome="approved", decidedBy=PO,
        decidedAt=decided_at, subjectDigest={},
        policy={"id": f"{NS}/policies/definition-of-ready", "version": "4"},
    )


def artifact(id_: str, created_at: str, kind: str, producer: str, **fields: Any) -> Doc:
    location = fields.pop("location", GIT)
    return record("artifact", id_, created_at, kind=kind, location=location,
                  **fields, digest=content_digest(id_), producedBy=producer)


def base_records() -> list[Doc]:
    return [
        *actors(),
        intent(1),
        artifact(CONTRACT, "2026-10-15T11:20:00Z", "contract", DEV_AGENT,
                 mediaType="application/yaml", path="api/address.openapi.yaml",
                 context=[intent_ref("INT-142", 1)], contextRecordedBy=RUNTIME),
        artifact(CODE, "2026-10-18T16:40:00Z", "code", DEV_AGENT,
                 context=[intent_ref("INT-142", 1), CONTRACT], contextRecordedBy=RUNTIME),
        artifact(DATASET, "2026-10-16T08:05:00Z", "dataset", DATAGEN,
                 classification="synthetic",
                 location="https://testdata.acme.example/sets/addresses-without-canton-v1",
                 context=[intent_ref("INT-142", 1, "AC-2")], contextRecordedBy=RUNTIME),
        artifact(TEST, "2026-10-18T17:05:00Z", "test", QE_AGENT, path="tests/address.spec.ts",
                 context=[intent_ref("INT-142", 1), CONTRACT, DATASET],
                 contextRecordedBy=RUNTIME),
        evidence(EVIDENCE, "AC-2", "2026-10-20T14:31:58Z", inputs=[DATASET],
                 measures=[{"name": "mutationScore", "value": 0.84,
                            "method": f"{NS}/methods/mutation-score"}]),
        approval("DEC-77", 1),
    ]


def evidence(id_: str, key: str, observed_at: str, version: int = 1, **fields: Any) -> Doc:
    created_at = observed_at.replace(":58Z", ":59Z")
    return record(
        "evidence", id_, created_at, criterion=intent_ref("INT-142", version, key), test=TEST,
        subject=CODE, **fields, derivedFrom="intent", result="pass", observedAt=observed_at,
        recordedBy=CI, run="https://ci.acme.example/pipelines/portal/runs/5531",
    )


def bundle(recs: list[Doc]) -> Doc:
    return seal(record("bundle", ref("bundles", "B-2026-10-20-01"), "2026-10-20T15:00:00Z",
                       records=recs))


def base_bundle() -> Doc:
    return bundle(base_records())


def passport_records() -> list[Doc]:
    return [
        *base_records(),
        human("qe-2c9d", "QE lead 2c9d", operator="Team Portal"),
        machine("tool", "passport-issuer", "1.0", "Passport issuer"),
        artifact(BUILD, "2026-10-20T16:10:00Z", "build", CI,
                 location="pkg:oci/customer-portal?repository_url=registry.acme.example",
                 inputs=[CODE]),
        record("decision", RELEASE, "2026-10-21T08:45:00Z", gate="release", subject=BUILD,
               subjectDigest=content_digest(BUILD), outcome="approved", decidedBy=QE_LEAD,
               decidedAt="2026-10-21T08:45:00Z", evidence=[EVIDENCE]),
    ]


def passport(recs: list[Doc] | None = None) -> Doc:
    coverage = [{"name": "intentCoverage", "value": 0.5,
                 "method": "https://ois.example/methods/basic-intent-coverage/v0.1"}]
    statement = {
        "_type": STATEMENT_TYPE,
        "subject": [{"name": "customer-portal", "digest": content_digest(BUILD)}],
        "predicateType": PREDICATE_TYPE,
        "predicate": {
            "ois": "0.1",
            "release": {"name": "customer-portal", "version": "2026.10.3"},
            "intents": [intent_ref("INT-142", 1)],
            "scope": [intent_ref("INT-142", 1, "AC-1"), intent_ref("INT-142", 1, "AC-2")],
            "records": passport_records() if recs is None else recs,
            "assessments": coverage,
            "issuedBy": ISSUER,
            "issuedAt": "2026-10-21T09:00:00Z",
        },
    }
    return seal(statement)


L1_ADAPTER = actor_ref("junit-adapter", "0.3")
L1_SUITE = actor_ref("billing-test-suite", "legacy")
L1_INTENT = ref("intents", "INT-900")
L1_TEST = ref("artifacts", "ART-501")


def level1_bundle() -> Doc:
    """The quick start of section 11.4: a JUnit XML adapter on an existing pipeline."""
    tests = ["InvoiceTest.roundsToFiveRappen", "InvoiceTest.rejectsNegativeAmounts"]
    return bundle([
        machine("tool", "junit-adapter", "0.3", "JUnit XML adapter"),
        machine("tool", "billing-test-suite", "legacy", "Team Billing test suite"),
        record("intent", L1_INTENT, "2026-10-20T06:00:00Z", version=1,
               title="Characterization of the billing test suite", status="draft",
               producedBy=L1_ADAPTER,
               criteria=[{"key": f"TC-{n}", "statement": name, "notation": "text",
                          "kind": "functional"} for n, name in enumerate(tests, 1)]),
        artifact(L1_TEST, "2026-10-20T06:00:00Z", "test", L1_SUITE,
                 location="git+https://git.acme.example/billing.git@"
                          "9f8e7d6c5b4a39281706f5e4d3c2b1a098765432",
                 path="src/test/java/InvoiceTest.java"),
        *(record("evidence", ref("evidence", f"EV-50{n}"), "2026-10-20T06:00:05Z",
                 criterion=f"{L1_INTENT}@1#TC-{n}", test=L1_TEST, derivedFrom="unknown",
                 result=result, observedAt="2026-10-20T05:59:58Z", recordedBy=L1_ADAPTER)
          for n, result in ((1, "pass"), (2, "fail"))),
    ])


def finding(id_: str, severity: str = "high", **fields: Any) -> Doc:
    if not {"intent", "criterion", "subject"} & fields.keys():
        fields = {"intent": intent_ref("INT-142", 1), "subject": CODE, **fields}
    return record(
        "finding", ref("findings", id_), "2026-10-20T18:30:00Z", **fields, source="test",
        severity=severity,
        summary="Address change to a Liechtenstein postcode aborts the premium calculation",
        observedAt="2026-10-20T18:12:00Z", reportedBy=SUPPORT,
    )


def with_support(doc: Doc, *added: Doc) -> Doc:
    records(doc).extend([human("support-4b1e", "Support 4b1e"), *added])
    return seal(doc)


def resolved_finding(doc: Doc, decided_by: str) -> Doc:
    """A high finding, its classified successor resolved by new evidence, and the decision."""
    fix_evidence = ref("evidence", "EV-9030")
    later = record(
        "finding", ref("findings", "FND-19"), "2026-10-21T07:30:00Z",
        intent=intent_ref("INT-142", 1), subject=CODE, source="test", severity="high",
        summary="Address change to a Liechtenstein postcode aborts the premium calculation",
        observedAt="2026-10-20T18:12:00Z", reportedBy=SUPPORT, cause="implementation",
        resolvedBy=[fix_evidence], supersedes=ref("findings", "FND-18"),
    )
    resolution = record(
        "decision", ref("decisions", "DEC-90"), "2026-10-21T08:00:00Z", gate="finding-resolution",
        subject=later["id"], outcome="approved", decidedBy=decided_by,
        decidedAt="2026-10-21T08:00:00Z", evidence=[fix_evidence],
    )
    fix = evidence(fix_evidence, "AC-1", "2026-10-21T06:58:58Z")
    return with_support(doc, finding("FND-18"), fix, later, resolution)


def add_version_2(doc: Doc, status: str = "approved", ac2: str = AC2_CHANGED) -> Doc:
    records(doc).append(intent(2, status=status, ac2=ac2, created_at="2026-10-19T09:00:00Z"))
    if status == "approved":
        records(doc).append(approval("DEC-78", 2, decided_at="2026-10-19T10:00:00Z"))
    return seal(doc)


# --- fixtures ----------------------------------------------------------------------------


@dataclass(frozen=True)
class Fixture:
    path: str
    description: str
    expect: tuple[Expect, ...]
    build: Callable[[], Doc]


FIXTURES: list[Fixture] = []


def fixture(path: str, description: str, *expect: Expect) -> Callable[[Callable[[], Doc]], None]:
    def register(build: Callable[[], Doc]) -> None:
        FIXTURES.append(Fixture(path, description, expect, build))

    return register


def violation(rule: str) -> Expect:
    return (rule, "violation")


# valid ------------------------------------------------------------------------------------

fixture("valid/bundle.json",
        "The Appendix A bundle, made consistent: approved intent, approval, artifacts, evidence. "
        "Unsigned, so the recorded contexts are self-declared.",
        R12_UNSIGNED)(base_bundle)

fixture("valid/passport.json",
        "A self-contained Quality Passport for the bundle above, with build and release decision.",
        R12_UNSIGNED)(passport)

fixture("valid/level-1-bundle.json",
        "The Level 1 quick start (section 11.4): a characterization intent in draft, one test "
        "file and two results with derivedFrom unknown. Nothing to report.")(level1_bundle)


@fixture("valid/intent.json", "A single approved intent with correct digests.")
def _() -> Doc:
    return seal(intent(1))


@fixture("valid/finding.json", "A single finding from production (section 4.7).")
def _() -> Doc:
    return record(
        "finding", ref("findings", "FND-18"), "2026-11-03T07:40:00Z",
        intent=intent_ref("INT-142", 1), subject=BUILD, source="production", severity="high",
        summary="Address change to a Liechtenstein postcode aborts the premium calculation",
        observedAt="2026-11-02T18:12:00Z", reportedBy=SUPPORT,
        ticket="https://jira.acme.example/browse/PORTAL-1302", cause="spec-gap",
    )


@fixture("valid/carry-over-unchanged-criterion.json",
         "Version 2 changes AC-2 only. Evidence for version 2 AC-1 rests on a test whose context "
         "names version 1, which is fine because AC-1 has the same digest in both (R4).",
         R12_UNSIGNED)
def _() -> Doc:
    doc = add_version_2(base_bundle())
    get(doc, EVIDENCE)["criterion"] = intent_ref("INT-142", 2, "AC-1")
    return doc


@fixture("valid/draft-and-approved-intent.json",
         "The same intent version as draft and as approved record. They differ only in status, "
         "so they count as one record in two states (R10).",
         R12_UNSIGNED)
def _() -> Doc:
    doc = base_bundle()
    draft = copy.deepcopy(get(doc, intent_ref("INT-142", 1)))
    draft["status"] = "draft"
    records(doc).insert(records(doc).index(get(doc, APPROVAL)), draft)
    return doc


@fixture("valid/evidence-revocation.json",
         "Evidence withdrawn by an evidence-revocation decision with rationale (R11).",
         R12_UNSIGNED)
def _() -> Doc:
    doc = base_bundle()
    records(doc).append(record(
        "decision", ref("decisions", "DEC-95"), "2026-10-22T09:00:00Z",
        gate="evidence-revocation", subject=EVIDENCE, outcome="rejected", decidedBy=PO,
        decidedAt="2026-10-22T09:00:00Z", rationale="Flaky test: the run used a stale cache",
    ))
    return doc


@fixture("valid/passport-resolved-finding.json",
         "A high finding whose successor is resolved by new evidence and confirmed by an actor "
         "that produced none of it (R14), so R13 has nothing to report.",
         R12_UNSIGNED)
def _() -> Doc:
    return resolved_finding(passport(), QE_LEAD)


@fixture("valid/passport-low-finding.json",
         "An open finding with severity low does not trigger R13.",
         R12_UNSIGNED)
def _() -> Doc:
    return with_support(passport(), finding("FND-18", severity="low"))


# schema -----------------------------------------------------------------------------------

SCHEMA_FAIL = violation("schema")


@fixture("invalid/schema/unknown-top-level-field.json",
         "A top-level field that the record type does not define (section 4).", SCHEMA_FAIL)
def _() -> Doc:
    return {**finding("FND-18"), "score": 7}


@fixture("invalid/schema/wrong-ois-version.json", "ois is not \"0.1\".", SCHEMA_FAIL)
def _() -> Doc:
    return {**finding("FND-18"), "ois": "0.2"}


@fixture("invalid/schema/id-with-version.json",
         "An id that contains @, which is reserved for references (section 6.1).", SCHEMA_FAIL)
def _() -> Doc:
    test = copy.deepcopy(get(base_bundle(), TEST))
    test["id"] += "@1"
    return test


@fixture("invalid/schema/timestamp-without-offset.json",
         "observedAt has no time zone offset (section 2).", SCHEMA_FAIL)
def _() -> Doc:
    ev = copy.deepcopy(get(base_bundle(), EVIDENCE))
    ev["observedAt"] = "2026-10-20T14:31:58"
    return ev


@fixture("invalid/schema/agent-without-model.json", "An agent without model (section 4.4).",
         SCHEMA_FAIL)
def _() -> Doc:
    agent = copy.deepcopy(get(base_bundle(), DEV_AGENT))
    del agent["model"]
    return agent


@fixture("invalid/schema/approved-intent-without-digest.json",
         "An approved intent without digest (section 4.2).", SCHEMA_FAIL)
def _() -> Doc:
    result = seal(intent(1))
    del result["digest"]
    return result


@fixture("invalid/schema/unversioned-criterion-reference.json",
         "A criterion reference without intent version (section 6.2).", SCHEMA_FAIL)
def _() -> Doc:
    ev = copy.deepcopy(get(base_bundle(), EVIDENCE))
    ev["criterion"] = f"{INTENT}#AC-2"
    return ev


@fixture("invalid/schema/criterion-with-unknown-field.json",
         "A criterion with a field that section 4.2 does not define.", SCHEMA_FAIL)
def _() -> Doc:
    result = seal(intent(1))
    result["criteria"][0]["priority"] = 1
    return result


@fixture("invalid/schema/dataset-without-classification.json",
         "A dataset artifact without classification (section 4.3).", SCHEMA_FAIL)
def _() -> Doc:
    dataset = copy.deepcopy(get(base_bundle(), DATASET))
    del dataset["classification"]
    return dataset


@fixture("invalid/schema/release-without-subject-digest.json",
         "A release decision without subjectDigest (section 4.6).", SCHEMA_FAIL)
def _() -> Doc:
    release = copy.deepcopy(get(passport(), RELEASE))
    del release["subjectDigest"]
    return release


@fixture("invalid/schema/finding-without-target.json",
         "A finding with none of criterion, intent or subject (section 4.7).", SCHEMA_FAIL)
def _() -> Doc:
    result = finding("FND-18")
    del result["intent"], result["subject"]
    return result


@fixture("invalid/schema/bundle-with-nested-bundle.json",
         "A bundle whose records contain another bundle (section 4.8).", SCHEMA_FAIL)
def _() -> Doc:
    inner = level1_bundle()
    doc = base_bundle()
    records(doc).append(inner)
    return doc


@fixture("invalid/schema/passport-without-intents.json",
         "A passport predicate with an empty intents list (section 8.2).", SCHEMA_FAIL)
def _() -> Doc:
    doc = passport()
    doc["predicate"]["intents"] = []
    return doc


@fixture("invalid/schema/waiver-without-rationale.json",
         "A waived decision without rationale. This is the MUST of R9, enforced by the schema.",
         SCHEMA_FAIL)
def _() -> Doc:
    return record("decision", ref("decisions", "DEC-80"), "2026-10-19T12:00:00Z", gate="merge",
                  subject=CODE, outcome="waived", decidedBy=PO, decidedAt="2026-10-19T12:00:00Z")


@fixture("invalid/schema/revocation-without-rationale.json",
         "An evidence revocation without rationale. This is the rationale MUST of R11, enforced "
         "by the schema.", SCHEMA_FAIL)
def _() -> Doc:
    return record("decision", ref("decisions", "DEC-95"), "2026-10-22T09:00:00Z",
                  gate="evidence-revocation", subject=EVIDENCE, outcome="rejected",
                  decidedBy=PO, decidedAt="2026-10-22T09:00:00Z")


# R1 ---------------------------------------------------------------------------------------


@fixture("invalid/R1/approved-intent-without-approval.json",
         "An approved intent without intent-approval decision.", violation("R1"), R12_UNSIGNED)
def _() -> Doc:
    doc = base_bundle()
    remove(doc, APPROVAL)
    return doc


@fixture("invalid/R1/approval-digest-mismatch.json",
         "The approval's subjectDigest differs from the intent's digest.",
         violation("R1"), R12_UNSIGNED)
def _() -> Doc:
    doc = base_bundle()
    get(doc, APPROVAL)["subjectDigest"] = content_digest("an earlier draft")
    return doc


@fixture("invalid/R1/approval-rejected.json",
         "The only intent-approval decision has outcome rejected.", violation("R1"), R12_UNSIGNED)
def _() -> Doc:
    doc = base_bundle()
    get(doc, APPROVAL)["outcome"] = "rejected"
    return doc


@fixture("invalid/R1/approval-by-agent.json",
         "The intent is approved by an agent; R1 says the approver SHOULD be human.",
         ("R1", "info"), R12_UNSIGNED)
def _() -> Doc:
    doc = base_bundle()
    get(doc, APPROVAL)["decidedBy"] = REQ_AGENT
    return doc


# R2 ---------------------------------------------------------------------------------------


@fixture("invalid/R2/unknown-criterion-key.json",
         "Evidence references a criterion key that the intent version does not have.",
         violation("R2"), R12_UNSIGNED)
def _() -> Doc:
    doc = base_bundle()
    get(doc, EVIDENCE)["criterion"] = intent_ref("INT-142", 1, "AC-9")
    return doc


@fixture("invalid/R2/passport-scope-unknown-key.json",
         "The passport scope names a criterion key that the intent version does not have.",
         violation("R2"), R12_UNSIGNED)
def _() -> Doc:
    doc = passport()
    doc["predicate"]["scope"].append(intent_ref("INT-142", 1, "AC-9"))
    return doc


# R3 ---------------------------------------------------------------------------------------


@fixture("invalid/R3/test-is-not-a-test.json",
         "Evidence names a dataset artifact as its test.", violation("R3"), R12_UNSIGNED)
def _() -> Doc:
    doc = base_bundle()
    get(doc, EVIDENCE)["test"] = DATASET
    return doc


@fixture("invalid/R3/subject-is-a-contract.json",
         "Evidence names a contract artifact as its subject.", violation("R3"), R12_UNSIGNED)
def _() -> Doc:
    doc = base_bundle()
    get(doc, EVIDENCE)["subject"] = CONTRACT
    return doc


# R4 ---------------------------------------------------------------------------------------


@fixture("invalid/R4/context-includes-code.json",
         "derivedFrom intent, but the test's context includes the code artifact.",
         violation("R4"), R12_UNSIGNED)
def _() -> Doc:
    doc = base_bundle()
    get(doc, TEST)["context"].append(CODE)
    return doc


@fixture("invalid/R4/context-without-criterion.json",
         "derivedFrom intent, but the test's context includes neither the intent nor the criterion.",
         violation("R4"), R12_UNSIGNED)
def _() -> Doc:
    doc = base_bundle()
    get(doc, TEST)["context"] = [CONTRACT, DATASET]
    return doc


@fixture("invalid/R4/test-without-context.json",
         "derivedFrom intent, but the test artifact has no context at all.",
         violation("R4"), R12_UNSIGNED)
def _() -> Doc:
    doc = base_bundle()
    del get(doc, TEST)["context"], get(doc, TEST)["contextRecordedBy"]
    return doc


@fixture("invalid/R4/criterion-changed-since-context.json",
         "Evidence for version 2 AC-2 rests on a test whose context names version 1, where AC-2 "
         "had a different digest.",
         violation("R4"), R12_UNSIGNED)
def _() -> Doc:
    doc = add_version_2(base_bundle())
    get(doc, EVIDENCE)["criterion"] = intent_ref("INT-142", 2, "AC-2")
    return doc


# R5 ---------------------------------------------------------------------------------------


@fixture("invalid/R5/same-producer.json",
         "derivedFrom intent, but the developer agent produced both the test and the code.",
         violation("R5"), R12_UNSIGNED)
def _() -> Doc:
    doc = base_bundle()
    get(doc, TEST)["producedBy"] = DEV_AGENT
    return doc


@fixture("invalid/R5/same-producer-other-version.json",
         "derivedFrom intent, but test and code come from two versions of the same agent.",
         violation("R5"), R12_UNSIGNED)
def _() -> Doc:
    doc = base_bundle()
    newer = copy.deepcopy(get(doc, DEV_AGENT))
    newer["version"] = "3.1"
    records(doc).insert(records(doc).index(get(doc, DEV_AGENT)) + 1, newer)
    get(doc, TEST)["producedBy"] = actor_ref("dev-agent", "3.1")
    return doc


# R8 ---------------------------------------------------------------------------------------


@fixture("invalid/R8/production-dataset.json",
         "Evidence lists an input dataset classified as production.",
         ("R8", "warning"), R12_UNSIGNED)
def _() -> Doc:
    doc = base_bundle()
    get(doc, DATASET)["classification"] = "production"
    return doc


# R9 ---------------------------------------------------------------------------------------


@fixture("invalid/R9/waiver-by-agent.json",
         "A merge waiver with rationale, decided by an agent; R9 says it SHOULD be a human.",
         ("R9", "info"), R12_UNSIGNED)
def _() -> Doc:
    doc = base_bundle()
    records(doc).append(record(
        "decision", ref("decisions", "DEC-80"), "2026-10-19T12:00:00Z", gate="merge",
        subject=CODE, outcome="waived", decidedBy=DEV_AGENT, decidedAt="2026-10-19T12:00:00Z",
        rationale="Hotfix for the premium calculation; review follows",
    ))
    return doc


# R10 --------------------------------------------------------------------------------------


@fixture("invalid/R10/unresolved-reference.json",
         "recordedBy names an actor version that is not in the bundle.",
         violation("R10"), R12_UNSIGNED)
def _() -> Doc:
    doc = base_bundle()
    get(doc, EVIDENCE)["recordedBy"] = actor_ref("ci-recorder", "1.3")
    return doc


@fixture("invalid/R10/unversioned-agent-reference.json",
         "producedBy references an agent in plain form; agents need the versioned form (section "
         "6.2), so the reference resolves to nothing.",
         violation("R10"), R12_UNSIGNED)
def _() -> Doc:
    doc = base_bundle()
    get(doc, TEST)["producedBy"] = actor_ref("qe-agent")
    return doc


@fixture("invalid/R10/conflicting-records.json",
         "Two artifact records share an id but differ in content: one dataset is synthetic, the "
         "other anonymized.",
         violation("R10"), R12_UNSIGNED)
def _() -> Doc:
    doc = base_bundle()
    other = copy.deepcopy(get(doc, DATASET))
    other["classification"] = "anonymized"
    records(doc).insert(records(doc).index(get(doc, DATASET)) + 1, other)
    return doc


@fixture("invalid/R10/supersedes-outside-bundle.json",
         "Intent version 2 supersedes version 1, which the bundle does not carry. The history "
         "must stay verifiable, so supersedes must resolve like every other reference.",
         violation("R10"), R12_UNSIGNED)
def _() -> Doc:
    text = json.dumps(base_records()).replace(intent_ref("INT-142", 1), intent_ref("INT-142", 2))
    recs: list[Doc] = json.loads(text)
    current = next(r for r in recs if r["type"] == "intent")
    recs[recs.index(current)] = intent(2)
    return bundle(recs)


@fixture("invalid/R10/finding-supersedes-outside-bundle.json",
         "A finding supersedes a finding that the bundle does not carry.",
         violation("R10"), R12_UNSIGNED)
def _() -> Doc:
    later = {**finding("FND-19", severity="medium"), "cause": "implementation",
             "supersedes": ref("findings", "FND-18")}
    return with_support(base_bundle(), later)


@fixture("invalid/R10/artifact-digest-differs.json",
         "Two artifact records share an id and differ only in digest, so a reference to that id "
         "no longer says which content it means. Only intents ignore status and digest "
         "(proposed clarification of R10).",
         violation("R10"), R12_UNSIGNED)
def _() -> Doc:
    doc = base_bundle()
    other = copy.deepcopy(get(doc, TEST))
    other["digest"] = content_digest("a test that always passes")
    records(doc).insert(records(doc).index(get(doc, TEST)) + 1, other)
    return doc


@fixture("invalid/R10/passport-missing-record.json",
         "The release decision lists evidence that the passport does not carry.",
         violation("R10"), R12_UNSIGNED)
def _() -> Doc:
    doc = passport()
    remove(doc, EVIDENCE)
    return doc


# R11 --------------------------------------------------------------------------------------


@fixture("invalid/R11/revocation-of-an-artifact.json",
         "An evidence-revocation decision whose subject is an artifact, not evidence.",
         violation("R11"), R12_UNSIGNED)
def _() -> Doc:
    doc = base_bundle()
    records(doc).append(record(
        "decision", ref("decisions", "DEC-95"), "2026-10-22T09:00:00Z",
        gate="evidence-revocation", subject=TEST, outcome="rejected", decidedBy=PO,
        decidedAt="2026-10-22T09:00:00Z", rationale="The test file was replaced",
    ))
    return doc


# R12 --------------------------------------------------------------------------------------


def level1_with_context(recorded_by: str | None) -> Doc:
    doc = level1_bundle()
    test = get(doc, L1_TEST)
    test["context"] = [f"{L1_INTENT}@1"]
    if recorded_by:
        test["contextRecordedBy"] = recorded_by
    return doc


@fixture("invalid/R12/context-without-recorder.json",
         "A context without contextRecordedBy is self-declared.", R12_UNSIGNED)
def _() -> Doc:
    return level1_with_context(None)


@fixture("invalid/R12/context-recorded-by-producer.json",
         "A context recorded by its own producer is self-declared.", R12_UNSIGNED)
def _() -> Doc:
    return level1_with_context(L1_SUITE)


@fixture("invalid/R12/recorder-did-not-sign.json",
         "A context recorded by another actor, but the bundle is not signed by that actor.",
         R12_UNSIGNED)
def _() -> Doc:
    return level1_with_context(L1_ADAPTER)


# R13 --------------------------------------------------------------------------------------


@fixture("invalid/R13/open-high-finding.json",
         "The passport lists an intent that an open high finding references.",
         ("R13", "warning"), R12_UNSIGNED)
def _() -> Doc:
    return with_support(passport(), finding("FND-18"))


@fixture("invalid/R13/open-critical-finding-on-criterion.json",
         "An open critical finding references a criterion of a listed intent.",
         ("R13", "warning"), R12_UNSIGNED)
def _() -> Doc:
    return with_support(passport(), finding(
        "FND-18", severity="critical", criterion=intent_ref("INT-142", 1, "AC-1"), subject=CODE))


@fixture("invalid/R13/resolution-not-independent.json",
         "The finding-resolution decision is made by the actor that recorded the resolving "
         "evidence, so the finding is not resolved (R14) and stays open.",
         ("R13", "warning"), R12_UNSIGNED)
def _() -> Doc:
    return resolved_finding(passport(), CI)


# R14 --------------------------------------------------------------------------------------


@fixture("invalid/R14/fork.json", "Two findings supersede the same finding.",
         violation("R14"), R12_UNSIGNED)
def _() -> Doc:
    successors = [
        {**finding(f"FND-18-{n}", severity="medium"), "cause": cause,
         "supersedes": ref("findings", "FND-18")}
        for n, cause in ((1, "implementation"), (2, "spec-gap"))
    ]
    return with_support(base_bundle(), finding("FND-18", severity="medium"), *successors)


# R15 --------------------------------------------------------------------------------------


@fixture("invalid/R15/draft-intent-listed.json",
         "The passport lists an intent version in draft.", violation("R15"), R12_UNSIGNED)
def _() -> Doc:
    doc = passport()
    draft = record("intent", ref("intents", "INT-143"), "2026-10-19T09:00:00Z", version=1,
                   title="Customers download their policy as PDF", status="draft",
                   producedBy=REQ_AGENT,
                   criteria=[{"key": "AC-1", "notation": "text", "kind": "functional",
                              "statement": "The policy PDF contains the current address"}])
    records(doc).append(draft)
    doc["predicate"]["intents"].append(intent_ref("INT-143", 1))
    return doc


@fixture("invalid/R15/withdrawn-intent-listed.json",
         "The passport lists version 1, but version 2 withdraws the intent.",
         violation("R15"), R12_UNSIGNED)
def _() -> Doc:
    return add_version_2(passport(), status="withdrawn", ac2=AC2)


@fixture("invalid/R15/not-latest-approved.json",
         "The passport lists version 1, but version 2 was approved before issuedAt; the "
         "listed version SHOULD be the latest.",
         ("R15", "info"), R12_UNSIGNED)
def _() -> Doc:
    return add_version_2(passport())


# R16 (proposed) ---------------------------------------------------------------------------


@fixture("invalid/R16/no-release-decision.json",
         "The passport carries no release decision.", violation("R16"), R12_UNSIGNED)
def _() -> Doc:
    doc = passport()
    remove(doc, RELEASE)
    return doc


@fixture("invalid/R16/release-rejected.json",
         "The only release decision has outcome rejected.", violation("R16"), R12_UNSIGNED)
def _() -> Doc:
    doc = passport()
    get(doc, RELEASE)["outcome"] = "rejected"
    return doc


@fixture("invalid/R16/release-of-another-build.json",
         "The release decision approves a build whose digest matches no subject of the statement.",
         violation("R16"), R12_UNSIGNED)
def _() -> Doc:
    doc = passport()
    doc["subject"][0]["digest"] = content_digest("another build")
    return doc


# R17 (proposed) ---------------------------------------------------------------------------


@fixture("invalid/R17/intent-digest-mismatch.json",
         "The intent digest does not match its canonical form. The approval binds the same wrong "
         "value, so R1 holds.", violation("R17"), R12_UNSIGNED)
def _() -> Doc:
    doc = base_bundle()
    get(doc, intent_ref("INT-142", 1))["digest"] = content_digest("an earlier draft")
    bind_approvals(doc)
    return doc


@fixture("invalid/R17/criterion-digest-mismatch.json",
         "A criterion digest does not match its canonical form. The intent digest is computed "
         "over the record as it is, so only the criterion is wrong.",
         violation("R17"), R12_UNSIGNED)
def _() -> Doc:
    doc = base_bundle()
    found = get(doc, intent_ref("INT-142", 1))
    found["criteria"][0]["digest"] = content_digest("an earlier AC-1")
    seal_intent(found)
    bind_approvals(doc)
    return doc


@fixture("invalid/R17/single-intent-digest-mismatch.json",
         "A single approved intent whose digest does not match its canonical form.",
         violation("R17"))
def _() -> Doc:
    result = seal(intent(1))
    result["digest"] = content_digest("an earlier draft")
    return result


# --- signing ------------------------------------------------------------------------------


def test_key(name: str) -> Ed25519PrivateKey:
    """A fixed Ed25519 test key derived from its name. For fixtures only: anyone can derive it."""
    seed = hashlib.sha256(f"ois fixture key: {name}".encode()).digest()
    return Ed25519PrivateKey.from_private_bytes(seed)


def public_pem(name: str) -> str:
    key = test_key(name).public_key()
    pem = key.public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
    return pem.decode()


def keyid(name: str) -> str:
    """Lowercase hex SHA-256 of the DER SubjectPublicKeyInfo of the public key."""
    key = test_key(name).public_key()
    der = key.public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
    return hashlib.sha256(der).hexdigest()


def pae(payload_type: str, body: bytes) -> bytes:
    """DSSE pre-authentication encoding (DSSE v1.0)."""
    kind = payload_type.encode()
    return b"DSSEv1 %d %s %d %s" % (len(kind), kind, len(body), body)


def envelope(doc: Doc, *signers: str, payload_type: str | None = None) -> Doc:
    """The document as a DSSE envelope, signed by the test keys named."""
    kind = payload_type or (IN_TOTO if doc.get("_type") == STATEMENT_TYPE else OIS_BUNDLE)
    body = rfc8785.dumps(doc)
    signatures = [
        {"keyid": keyid(name), "sig": base64.b64encode(test_key(name).sign(pae(kind, body))).decode()}
        for name in signers
    ]
    return {"payloadType": kind, "payload": base64.b64encode(body).decode(), "signatures": signatures}


def payload(doc: Doc) -> Doc:
    """The document inside an envelope or a Sigstore bundle, or the document itself."""
    if "dsseEnvelope" in doc:
        doc = doc["dsseEnvelope"]
    if "payloadType" in doc:
        decoded: Doc = json.loads(base64.b64decode(doc["payload"]))
        return decoded
    return doc


def with_key_ids(doc: Doc) -> Doc:
    """Give the actors that hold a test key that key's id as their identity (section 4.4)."""
    for name in TRUSTED_KEYS:
        for record in records(doc):
            if record["type"] == "actor" and record["id"] == ref("actors", name):
                record["identity"] = {**record.get("identity", {}), "keyId": keyid(name)}
    return doc


# signed fixtures --------------------------------------------------------------------------

fixture("valid/signed-bundle.json",
        "The bundle as a DSSE envelope, signed by the agent runtime, which recorded every "
        "context, and by the CI recorder. Both keys are trusted, so every context is attested "
        "and R12 stays silent.")(
    lambda: envelope(with_key_ids(base_bundle()), "agent-runtime", "ci-recorder"))

fixture("valid/signed-passport.json",
        "The passport as a DSSE envelope with payload type application/vnd.in-toto+json, signed "
        "by the passport issuer and the agent runtime.")(
    lambda: envelope(with_key_ids(passport()), "passport-issuer", "agent-runtime"))

fixture("valid/signed-without-recorder.json",
        "Signed by the CI recorder only. The signature is valid, but the agent runtime that "
        "recorded the contexts did not sign, so they stay self-declared.",
        R12_UNSIGNED)(
    lambda: envelope(with_key_ids(base_bundle()), "ci-recorder"))

fixture("valid/signed-by-untrusted-key.json",
        "Signed by a key the verifier does not trust. The signature cannot be checked, so the "
        "envelope counts as unsigned.",
        SIGNATURE_UNVERIFIED, R12_UNSIGNED)(
    lambda: envelope(with_key_ids(base_bundle()), "untrusted-recorder"))


@fixture("invalid/signature/tampered-payload.json",
         "The payload was changed after the agent runtime signed it: the signature does not "
         "verify, and the envelope counts as unsigned.",
         violation("signature"), R12_UNSIGNED)
def _() -> Doc:
    signed = envelope(with_key_ids(base_bundle()), "agent-runtime")
    changed = payload(signed)
    changed["createdAt"] = "2026-10-21T15:00:00Z"
    signed["payload"] = base64.b64encode(rfc8785.dumps(changed)).decode()
    return signed


fixture("invalid/signature/wrong-payload-type.json",
        "A bundle signed with the payload type of an in-toto Statement. Section 8.3 gives bundles "
        "application/vnd.ois+json.",
        violation("signature"), R12_UNSIGNED)(
    lambda: envelope(with_key_ids(base_bundle()), "agent-runtime", payload_type=IN_TOTO))

fixture("invalid/signature/no-signature.json",
        "A DSSE envelope without any signature.",
        violation("signature"), R12_UNSIGNED)(
    lambda: envelope(with_key_ids(base_bundle())))


# profile: regulated industries -------------------------------------------------------------

REGULATED = "https://openintentschema.io/profiles/regulated/v0.1"
P = "regulated/P"


def regulated(doc: Doc) -> Doc:
    """The intent lists the regulated profile, so the whole document is checked against it."""
    get(doc, intent_ref("INT-142", 1))["profiles"] = [REGULATED]
    return seal(doc)


fixture("valid/regulated-passport.json",
        "A signed passport whose intent lists the regulated profile and meets P1 to P4.")(
    lambda: envelope(with_key_ids(regulated(passport())), "passport-issuer", "agent-runtime"))


@fixture("invalid/regulated/P1/intent-without-risk.json",
         "The intent lists the regulated profile but carries no risk.",
         violation(f"{P}1"), R12_UNSIGNED)
def _() -> Doc:
    doc = base_bundle()
    del get(doc, intent_ref("INT-142", 1))["risk"]
    return regulated(doc)


@fixture("invalid/regulated/P2/agent-approves-release.json",
         "A signed passport under the regulated profile whose release an agent approved.",
         violation(f"{P}2"))
def _() -> Doc:
    statement = passport()
    get(statement, RELEASE)["decidedBy"] = DEV_AGENT
    return envelope(with_key_ids(regulated(statement)), "passport-issuer", "agent-runtime")


fixture("invalid/regulated/P3/unsigned-passport.json",
        "A passport under the regulated profile that is not signed.",
        violation(f"{P}3"), R12_UNSIGNED)(lambda: regulated(passport()))


@fixture("invalid/regulated/P4/production-dataset.json",
         "Under the regulated profile, evidence lists an input dataset classified as production.",
         violation(f"{P}4"), ("R8", "warning"), R12_UNSIGNED)
def _() -> Doc:
    doc = base_bundle()
    get(doc, DATASET)["classification"] = "production"
    return regulated(doc)


# keyless fixtures --------------------------------------------------------------------------


def keyless_passport() -> Doc:
    """The passport, with the agent runtime and the issuer identified as the recording workflow,
    which signs it keylessly: every recorded context is then attested."""
    statement = passport()
    for record in records(statement):
        if record["type"] == "actor" and record["id"] in (ref("actors", "agent-runtime"),
                                                         ref("actors", "passport-issuer")):
            record["identity"] = {"issuer": GITHUB_ACTIONS, "subject": RECORDING_WORKFLOW}
    return statement


def recorded() -> Doc | None:
    if not RECORDED.exists():
        return None
    loaded: Doc = json.loads(RECORDED.read_text(encoding="utf-8"))
    return loaded


if recorded() is not None:
    fixture("valid/keyless-passport.json",
            "The passport, signed keylessly by a GitHub Actions workflow through the public-good "
            "Sigstore instance (a recorded Sigstore bundle). The workflow is the agent runtime's "
            "certificate identity, so every recorded context is attested.")(
        lambda: copy.deepcopy(recorded()))

    @fixture("invalid/signature/keyless-tampered.json",
             "The recorded keyless passport with its payload changed after signing.",
             violation("signature"), R12_UNSIGNED)
    def _() -> Doc:
        bundle = copy.deepcopy(recorded())
        changed = payload(bundle["dsseEnvelope"])
        changed["predicate"]["issuedAt"] = "2026-10-22T09:00:00Z"
        bundle["dsseEnvelope"]["payload"] = base64.b64encode(rfc8785.dumps(changed)).decode()
        return bundle


# --- output and checks -------------------------------------------------------------------


def render(doc: Doc) -> str:
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"


def manifest() -> str:
    entries = [
        {"path": f.path, "description": f.description,
         "expect": [{"rule": rule, "level": level} for rule, level in f.expect]}
        for f in FIXTURES
    ]
    keys = [f"keys/{name}.pub" for name in TRUSTED_KEYS]
    return render({"ois": "0.1", "trustedKeys": keys, "trustedRoots": list(TRUSTED_ROOTS),
                   "fixtures": entries})


def outputs() -> dict[Path, str]:
    result = {HERE / f.path: render(f.build()) for f in FIXTURES}
    result[HERE / "manifest.json"] = manifest()
    for name in TRUSTED_KEYS:
        result[HERE / "keys" / f"{name}.pub"] = public_pem(name)
    statement = keyless_passport()
    result[SIGSTORE / "passport-predicate.json"] = render(statement["predicate"])
    result[SIGSTORE / "passport-subject.json"] = render(statement["subject"][0])
    return result


def schema_errors(doc: Doc) -> list[str]:
    doc = payload(doc)
    root = json.loads(SCHEMA.read_text(encoding="utf-8"))
    registry: Registry[Any] = Registry().with_resource(root["$id"], Resource.from_contents(root))
    target, pointer = doc, ""
    if doc.get("_type") == STATEMENT_TYPE:
        target, pointer = doc["predicate"], "#/$defs/passportPredicate"
    validator = Draft202012Validator(
        {"$ref": root["$id"] + pointer}, registry=registry,
        format_checker=Draft202012Validator.FORMAT_CHECKER,
    )
    return [e.message for e in validator.iter_errors(target)]


def generated_on_disk() -> set[Path]:
    """Fixture files; recorded bundles and trusted roots are inputs, never removed."""
    return {p for folder in ("valid", "invalid") for p in (HERE / folder).glob("**/*.json")}


def check(files: dict[Path, str]) -> list[str]:
    problems = []
    for path, text in files.items():
        if not path.exists() or path.read_text(encoding="utf-8") != text:
            problems.append(f"{path.relative_to(HERE)}: out of date, run generate.py")
    on_disk = generated_on_disk()
    for stray in sorted(on_disk - files.keys()):
        problems.append(f"{stray.relative_to(HERE)}: not generated, remove it")
    bundle = recorded()
    if bundle is not None and payload(bundle) != keyless_passport():
        problems.append(f"{RECORDED.relative_to(HERE)}: signs another passport than "
                        "passport-predicate.json; record it again")
    for f in FIXTURES:
        errors = schema_errors(f.build())
        if f.path.startswith("invalid/schema/") and not errors:
            problems.append(f"{f.path}: expected a schema violation, found none")
        if not f.path.startswith("invalid/schema/") and errors:
            problems.append(f"{f.path}: schema violation: {errors[0]}")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    files = outputs()
    if args.check:
        problems = check(files)
        for problem in problems:
            print(problem, file=sys.stderr)
        return 1 if problems else 0
    for stray in generated_on_disk() - files.keys():
        stray.unlink()
    for path, text in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    print(f"wrote {len(FIXTURES)} fixtures and manifest.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
