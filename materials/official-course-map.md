# learn-api-docs-changelogs-with-phoebe - source map

Internal build document. Not linked from any audience-facing page.

Bucket `docs`, difficulty 2, audience builder, 6 sessions, single track, running case. Built 2026-11-16
by the course lead from the Phoebe-approved skeleton (Phase 1, 2026-11-16).

Question across the course: could a stranger make a first successful call in five minutes, and would
they know from your changelog what to do when v2 lands?

---

## Seams (picked out loud, linked, never retaught)

| Sibling | They own | This course owns |
|---|---|---|
| learn-tech-writing s5 Diataxis, s6 reference/ADRs/changelogs, 91 error messages, s7 docs as code | the four doc kinds, general reference and changelog craft, error-message writing, the docs-as-code pipeline | API-specific depth: spec-first OpenAPI, runnable examples tested in CI, breaking-change detection, SemVer, deprecation and sunset |
| learn-runbooks-postmortems | ops docs library, postmortems | nothing |
| learn-mcp, learn-github-for-builders | MCP servers, GitHub workflow (Actions authoring is github-for-builders 05) | nothing; s4 links Actions for the CI wiring |
| learn-system-design (02 boundaries and contracts) | choosing an architecture, data contracts | API design decisions only as they show up in docs |

Links (absolute):
- https://phoebefu6.github.io/learn-tech-writing-with-phoebe/courses/05-diataxis.html
- https://phoebefu6.github.io/learn-tech-writing-with-phoebe/courses/06-reference-adrs-changelogs.html
- https://phoebefu6.github.io/learn-tech-writing-with-phoebe/courses/91-error-messages.html
- https://phoebefu6.github.io/learn-tech-writing-with-phoebe/courses/07-docs-as-code.html
- https://phoebefu6.github.io/learn-github-for-builders-with-phoebe/courses/05-actions-authoring.html
- https://phoebefu6.github.io/learn-system-design-with-phoebe/courses/02-boundaries-and-contracts.html
- https://phoebefu6.github.io/learn-runbooks-postmortems-with-phoebe/

Sibling titles checked 2026-11-16 (no collisions): tech-writing 01-08 + 91-94, runbooks a1-a6 b1-b4,
mcp a1-a6 b1-b8, system-design 01-08, github-for-builders 01-06. Widget prefix `adc-` and case name
Parcelpoint: 0 hits in any sibling `assets/` or `courses/`.

---

## Running case (constructed, every mention labelled "Constructed Parcelpoint example")

Parcelpoint: a parcel-locker network with a public REST API (lockers, parcels, reservations, webhooks for
pickup events). v1 docs grew by accretion. v2 renames fields, changes pagination and removes an
endpoint. Running artifact: Parcelpoint's docs kit, one piece per session:

| Session | Kit piece |
|---|---|
| 1 | time-to-first-call audit of the v1 docs |
| 2 | OpenAPI 3.1 description of `/lockers` and `/parcels` |
| 3 | rewritten reference page for `POST /parcels` |
| 4 | quickstart + an example test that fails when the example stops working |
| 5 | v1 to v2 diff, SemVer bump, drafted changelog entry |
| 6 | deprecation notice + migration guide + sunset timeline; the kit scored |

The spec documents for every session are the ones in `assets/adc-sample.js` (built by
`materials/build_adc_sample.py`). Pages quote from them; never invent a field that is not there.

Parcelpoint v1 (1.4.2, OpenAPI 3.1.0, server https://api.parcelpoint.example/v1, auth `X-Api-Key` header):
- `GET /lockers` (page, per_page, city; returns data, page, total_pages)
- `GET /lockers/{locker_id}` (200 Locker, 404)
- `GET /lockers/{locker_id}/status` (free_slots)
- `POST /parcels` (ParcelCreate: locker_id, recipient_phone, size required; size enum small, medium,
  large, xl; 201 Parcel, 400, 409)
- `GET /parcels/{parcel_id}` (200 Parcel, 404)
- `POST /reservations` (locker_id, size; 201 Reservation, 409)
- `DELETE /reservations/{reservation_id}` (204, 404)
- `POST /webhooks` (url, events: parcel.delivered, parcel.picked_up, parcel.expired; 201)
- Schemas Locker (locker_id, address, city, size_classes, open_24h), Parcel (parcel_id, status created,
  in_locker, picked_up, expired; locker_id, pickup_code, created_at), Reservation, Error (code, message).

Parcelpoint v2 (2.0.0): Locker.locker_id renamed to id; free_slots added to Locker; size xl retired
(request and response); cursor pagination (cursor, limit, next_cursor replace page, per_page,
total_pages); `GET /lockers/{locker_id}/status` removed; ParcelCreate gains required recipient_email,
recipient_phone becomes optional; Parcel status gains `returned`, weight_grams added; new
`GET /parcels`; `POST /reservations` answers 202 instead of 201; `POST /webhooks` needs a bearer token.

Parcelpoint v1.5 (1.5.0): additions only plus the deprecation of `GET /lockers/{locker_id}/status`.
Parcelpoint 1.4.3: three description edits.

Constructed consumers (simulated): Shopfront checkout plugin, Courier handheld app, Recipient mobile
app, Partner analytics export, SMS notification service, Locker kiosk firmware.

---

## The bench (session 5): changelog checker

Engine `assets/adc-live.js`, data `assets/adc-sample.js` (77 KB), Python twin
`materials/adc_reference.py`, node runner `materials/adc-node.js`, comparer `materials/compare-ladder.py`.
JSON only (no YAML parser loaded; said on the widget). Compares paths, operations, parameters
(path-level merged), request bodies and responses (the JSON media type only), and auth. Does NOT compare
top-level `webhooks`, callbacks, links, response headers, or response `required` changes; says so.
A rename shows as removed + added: a diff cannot see intent, and the old name breaks for the caller
either way.

### Rule table (28 rules; every rule has a firing test and a near-miss test, 57/57 pass in python and node)

Basis read at source 2026-11-16: oasdiff breaking-changes list and check pages; GitHub REST "API
versions" breaking vs additive lists; SemVer 2.0.0 rule 7 (deprecation = minor).

| Rule | Severity | Category | Source / disagreement |
|---|---|---|---|
| OP_REMOVED | breaking | Removed | oasdiff api-path-removed-without-deprecation = breaking; with deprecation = info. SemVer still makes removal a major. |
| OP_ADDED | non-breaking | Added | oasdiff endpoint-added = info; GitHub additive |
| OP_DEPRECATED | non-breaking | Deprecated | SemVer rule 7 |
| SECURITY_CHANGED | breaking | Changed | GitHub: changing auth requirements is breaking. oasdiff: api-security-removed breaking, api-security-added info |
| PARAM_REMOVED | breaking | Removed | GitHub breaking; oasdiff request-parameter-removed = warning ("potentially breaking") |
| PARAM_ADDED_REQUIRED | breaking | Changed | oasdiff new-required-request-parameter |
| PARAM_ADDED_OPTIONAL | non-breaking | Added | oasdiff new-optional-request-parameter = info |
| PARAM_BECAME_REQUIRED | breaking | Changed | oasdiff request-parameter-became-required |
| PARAM_BECAME_OPTIONAL | non-breaking | Changed | |
| PARAM_DEPRECATED | non-breaking | Deprecated | oasdiff request-parameter-deprecated = info |
| REQ_BODY_BECAME_REQUIRED | breaking | Changed | |
| REQ_PROP_REMOVED | breaking | Removed | GitHub (removing a parameter) |
| REQ_PROP_ADDED_REQUIRED | breaking | Changed | oasdiff new-required-request-property |
| REQ_PROP_ADDED_OPTIONAL | non-breaking | Added | oasdiff new-optional-request-property = info |
| REQ_PROP_BECAME_REQUIRED | breaking | Changed | oasdiff request-property-became-required |
| REQ_PROP_BECAME_OPTIONAL | non-breaking | Changed | |
| REQ_TYPE_CHANGED | breaking | Changed | oasdiff request-body-type-changed; GitHub |
| REQ_ENUM_NARROWED | breaking | Changed | oasdiff request-property-enum-value-removed, request-property-became-enum |
| REQ_ENUM_WIDENED | non-breaking | Changed | |
| RESP_PROP_REMOVED | breaking | Removed | GitHub: removing a response field is breaking. oasdiff splits: required removed = breaking, OPTIONAL removed = info. Teach the disagreement. |
| RESP_PROP_ADDED | non-breaking | Added | GitHub additive |
| RESP_TYPE_CHANGED | breaking | Changed | oasdiff response-property-type-changed |
| RESP_ENUM_NARROWED | non-breaking | Changed | oasdiff response-property-enum-value-removed = info (a client never sees the value again) |
| RESP_ENUM_WIDENED | non-breaking | Changed | GitHub: adding enum values is additive. oasdiff flags new response enum values as a warning (clients with exhaustive switches). Teach the disagreement. |
| RESP_SUCCESS_STATUS_REMOVED | breaking | Removed | oasdiff response-success-status-removed |
| RESP_STATUS_REMOVED | non-breaking | Removed | oasdiff response-non-success-status-removed = info |
| RESP_STATUS_ADDED | non-breaking | Added | oasdiff response-*-status-added = info |
| DOCS_CHANGED | docs-only | Changed | summary / description edits |

Bump: any breaking -> MAJOR; else any non-breaking -> MINOR; else docs-only -> PATCH. Pre-release
suffix ignored (Petstore 1.0.30-SNAPSHOT bumps from 1.0.30). SemVer rule 4 (0.y.z anything may change)
not modelled; said in s6.

Changelog draft: Keep a Changelog order Added, Changed, Deprecated, Removed; identical lines across
operations merged; breaking lines first and marked **BREAKING**. Fixed and Security are never drafted:
a diff cannot tell a bug fix or a vulnerability fix from any other change (said under the widget).

Anti-lever: "Ship it as a minor" forces the minor bump on a breaking diff. Consumers whose operation /
field is hit by a breaking change move from "warned and must migrate" to "broken without warning".
A consumer is hit when a breaking change is operation-wide (removed op, auth, new required input,
success status removed) or names a field the consumer reads.

### Canon (python = node, 1090 values, planted fault caught; 2026-11-16)

| Preset | Changes | Breaking / non-breaking / docs-only | Required bump | Version | Consumers hit | Honest: silent / warned | Ship as minor |
|---|---|---|---|---|---|---|---|
| pp-major Parcelpoint v1 to v2 | 30 | 12 / 16 / 2 | MAJOR | 1.4.2 to 2.0.0 | 4 of 6 | 0 / 4 | 1.5.0, 4 of 6 broken without warning |
| pp-minor Parcelpoint v1 to v1.5 | 7 | 0 / 6 / 1 | MINOR | 1.4.2 to 1.5.0 | 0 of 6 | 0 / 0 | no effect (already minor) |
| pp-docs Parcelpoint wording fix | 3 | 0 / 0 / 3 | PATCH | 1.4.2 to 1.4.3 | 0 of 6 | 0 / 0 | no effect |
| petstore Swagger Petstore, edited | 14 | 3 / 10 / 1 | MAJOR | 1.0.30-SNAPSHOT to 2.0.0 | no consumer list | | 1.1.0 |

pp-major breaking 12: page removed, per_page removed, locker_id removed (GET /lockers), page removed
and total_pages removed (response, GET /lockers), locker_id removed (GET /lockers/{locker_id}),
GET /lockers/{locker_id}/status removed, recipient_email new required, size no longer accepts xl
(POST /parcels and POST /reservations: two changes, one changelog line), 201 removed
(POST /reservations), auth apiKey to bearer (POST /webhooks).
Consumers hit: Shopfront (6 hits), Courier (2), Partner analytics (total_pages), SMS notification
(auth). Unaffected: Recipient mobile app (status may now return `returned`: non-breaking by the
GitHub rule, a warning by oasdiff), Locker kiosk firmware.
pp-major non-breaking 16 include: cursor, limit added; id, free_slots added (twice each), next_cursor;
size_classes no longer returns xl (x2, response narrowing); recipient_phone now optional; status may
return `returned` (x2); weight_grams (x2); GET /parcels new; 202 new. Docs 2: GET /lockers and
DELETE /reservations/{reservation_id} descriptions.
Changelog draft for pp-major: 8 Added lines, 7 Changed lines (3 breaking), 7 Removed lines (all
breaking).
petstore breaking 3: Pet.status no longer accepts `pending` on POST /pet and PUT /pet; findByTags
removed. Non-breaking 10: five response operations no longer return `pending`; limit param added;
trackingUrl as optional request field (POST /store/order) and response field (x2); DELETE
/user/{username} deprecated. Docs 1: /store/inventory description.

---

## Verified facts (tier: R = read at source 2026-11-16; Rp = reported, secondary or vendor)

### Session 1 - readers and time to first call
- R: Postman blog "Improve your time to first API call by 20x" (2023-04-04, by Postman's developer relations lead): states
  "The most important API metric is time to first call"; one publisher's call took about 17 minutes,
  about 10 with a collection (1.7x faster); developers were 1.7 to 56 times faster with a forked
  collection. Vendor post about its own product: teach as a vendor claim.
- Rp: Twilio has framed a five-minute goal (secondary blog). NOT quoted on pages; the five-minute bar is
  presented as the course's own audit bar, not as Twilio's.
- R: Diataxis reference: reference is "technical descriptions of the machinery"; "mirror the structure
  of the product"; examples illustrate without instructing. (Owned by tech-writing s5: one-card recap.)
- Reader jobs (evaluate, first call, integrate, debug, upgrade) are the course's own frame, labelled as such.

### Session 2 - OpenAPI 3.1
- R: OAS 3.1.1 dated 24 October 2024; 3.1.0 dated 15 February 2021 (spec.openapis.org).
- R: OAS 3.2.0 dated 19 September 2025 exists (adds a `query` method field, `additionalOperations`, a `querystring`
  parameter location, `$self`). The skeleton teaches 3.1 (approved); s2 says 3.2.0 exists and that the pages use 3.1.
- R: root fixed fields: openapi, info, jsonSchemaDialect, servers, paths, webhooks, components, security,
  tags, externalDocs; only openapi and info are REQUIRED; an OAD MUST contain at least one of paths,
  components or webhooks.
- R: Schema Object is "a superset of the JSON Schema Specification Draft 2020-12".
- R: Operation fields include operationId, parameters, requestBody, responses, callbacks, deprecated,
  security, servers. Parameter `in`: query, header, path, cookie. deprecated defaults to false.
- R: Components holds schemas, responses, parameters, examples, requestBodies, headers,
  securitySchemes, links, callbacks, pathItems.
- R: webhooks: "The incoming webhooks that MAY be received as part of this API".
- R (OAI blog, 2021-02-16, migrating 3.0 to 3.1): nullable removed, use a type array with "null";
  exclusiveMinimum/Maximum are numbers; schema `example` -> `examples` array; OpenAPI 3.1 is a JSON
  Schema dialect.
- R: Swagger Petstore README says the third iteration "switched to the design first approach"
  (spec-first side). R: FastAPI generates OpenAPI and interactive docs (Swagger UI, ReDoc) from code
  (code-first side). Contested: teach both, no verdict.
- R: Petstore sample is OpenAPI 3.0.4 (not 3.1): say so wherever it appears.

### Session 3 - reference pages
- R: GitHub REST "Create an issue" reference entry lists headers, path parameters, body parameters,
  HTTP response status codes (201, 400, 403, 404, 410, 422, 503) and code samples. Structure only.
- R: Stripe API reference collapses nested parameters by default (versioning page note). Structure only.
- Error message craft: link tech-writing 91, never reteach.
- Rate limits, idempotency keys, pagination: taught as what a page owes the reader; no vendor numbers.

### Session 4 - examples that run
- Examples validated against the spec, doc tests in CI, drift: taught as practice. Tools named as a
  category only (contract testers, mock servers, doc linters). Self-study.
- The example test in the build-along is written against the Parcelpoint spec and runs in the page
  (adc-live.js engine is NOT used there; the page has its own small validator if it needs one).

### Session 5 - the bench (see above)
- R: oasdiff reports changes at three levels: Breaking, Warning, Info; defines breaking as a change
  that "could cause existing API clients to fail without code changes"; when a change cannot be proven
  safe it is reported as breaking. Page counts quoted by the fetch (359 / 23 / 402) are NOT used:
  they change release to release.

### Session 6 - versioning and deprecation
- R SemVer 2.0.0: MAJOR incompatible API changes, MINOR backward-compatible functionality, PATCH
  backward-compatible bug fixes; rule 1 a public API must be declared; rule 4 0.y.z is initial
  development, anything may change; rule 7 MINOR MUST be incremented when public API functionality is
  marked deprecated; FAQ: deprecate in a minor, remove in a later major, at least one minor release
  carrying the deprecation.
- R Keep a Changelog 1.1.0: changelogs are for humans, not machines; entry per version; latest first;
  release date shown (ISO 8601 YYYY-MM-DD); Unreleased section at the top; six types Added, Changed,
  Deprecated, Removed, Fixed, Security; yanked releases tagged [YANKED]; commit-log diffs as changelogs
  are "a bad idea".
- R RFC 9745 (March 2025, Standards Track): Deprecation response header, a Structured Field Date,
  `Deprecation: @1688169599`; date may be in the past or future; `Link rel="deprecation"` points to
  human-readable docs; Sunset timestamp MUST NOT be earlier than the Deprecation date.
- R RFC 8594 (May 2019, Informational): Sunset header, an HTTP-date, `Sunset: Sat, 31 Dec 2018 23:59:59
  GMT`; `sunset` link relation; after sunset expect 4xx, 3xx or nothing; a hint, not a guarantee.
- R GitHub REST versioning: `X-GitHub-Api-Version` header; date-named versions (2022-11-28, 2026-03-10);
  no header = 2022-11-28; previous version supported at least 24 months after a newer one; 2022-11-28
  supported until March 10, 2028; breaking list (remove endpoint, remove/rename param or response field,
  new required param, type change, remove enum values, new validation, auth change) vs additive list.
- R Stripe: since 2024-09-30.acacia, monthly releases with no breaking changes and two major releases a
  year; versions named date.codename (current 2026-10-28.endive at fetch); `Stripe-Version` header
  overrides the account default; webhooks use the endpoint's or account's version; changelog rows carry
  an explicit "Breaking change?" column. Re-verify before delivery: the current version changes monthly.
- R Google AIP-185: major version in the URL path (v1, never v1.0); minor and patch applied in place;
  channel-based versioning (alpha, beta, stable); 180 days recommended for beta deprecation; also
  describes date-based versions via `X-Goog-Api-Version`.
- Versioning styles taught: URL path (Google), header with dates (GitHub), dated releases pinned per
  account (Stripe). Contested: no single right answer; trade-offs only.

---

## Not covered (honest list)
- GraphQL, gRPC and AsyncAPI documentation; SDK generation in depth; API style guides and linting rule
  sets (named as a category only); developer portals and hosted doc tools (Postman, Redocly, Stoplight:
  self-study, named as a category); localisation of docs; analytics on docs traffic.
- The diff engine does not compare top-level webhooks, callbacks, links, response headers, response
  `required` changes, or non-JSON media types; YAML input.
- No Twilio, Stripe or GitHub internal numbers on adoption or TTFC; no claim that TTFC predicts revenue.

---

## Citation appendix (use these exact forms on pages)
- OpenAPI Specification v3.1.1 (24 October 2024) and v3.1.0 (15 February 2021), spec.openapis.org
- OpenAPI Specification v3.2.0 (19 September 2025), spec.openapis.org (existence and headline fields only)
- OpenAPI Initiative, "Migrating from OpenAPI 3.0 to 3.1.0" (16 February 2021), openapis.org/blog
- JSON Schema Draft 2020-12, via the OAS 3.1 Schema Object
- Keep a Changelog 1.1.0, keepachangelog.com
- Semantic Versioning 2.0.0, semver.org
- RFC 9745, The Deprecation HTTP Response Header Field (March 2025)
- RFC 8594, The Sunset HTTP Header Field (May 2019)
- oasdiff, "Breaking changes" rule list and check pages, oasdiff.com/docs/breaking-changes
- GitHub Docs, "API Versions" (REST), docs.github.com/en/rest/about-the-rest-api/api-versions
- GitHub Docs, REST reference "Issues" (Create an issue entry)
- Stripe Docs, "Versioning" and "Changelog", docs.stripe.com
- Google AIP-185, "API Versioning", google.aip.dev/185
- Diataxis, "Reference", diataxis.fr/reference
- Postman blog, "Improve your time to first API call by 20x" (2023-04-04) - vendor claim
- FastAPI, "Features", fastapi.tiangolo.com/features
- Swagger Petstore, github.com/swagger-api/swagger-petstore (Apache-2.0, commit 5cb909f)
- Re-verify vendor docs (Stripe current version, GitHub supported versions) before delivery.
