# Learn API Docs & Changelogs with Phoebe

Reference pages, examples that run, and a changelog someone can act on. Write the spec first, keep every
example working, and ship a breaking change without breaking trust.

Six 45-minute sessions for engineers who ship APIs, platform and developer-experience teams, and the tech
writers next to them. One running case throughout: Parcelpoint, a constructed parcel-locker API whose docs
kit is rebuilt piece by piece.

1. Docs as the API's interface: who reads them and what they need
2. Spec-first: describing an API in OpenAPI 3.1
3. Reference pages that answer the real question
4. Examples that run: quickstarts, samples and tests that keep them true
5. The bench: changelog checker
6. Versioning and deprecation: a changelog someone can act on

## The bench

Session 5 runs a real OpenAPI diff engine in the browser (`assets/adc-live.js`): two API descriptions in
(JSON), every change classified breaking, non-breaking or docs-only by 28 written rules, the SemVer bump it
forces, and a drafted Keep a Changelog entry. A "ship it as a minor" button shows which constructed
consumers break. `materials/adc_reference.py` is the Python twin: every rule has a firing test and a
near-miss test, and `materials/compare-ladder.py` checks that Python and the browser engine agree on
every preset.

Presets: three constructed Parcelpoint version pairs, and the real Swagger Petstore OpenAPI 3.0.4 sample
(Apache-2.0, github.com/swagger-api/swagger-petstore) against a copy with six edits, labelled as edited.

Nothing needs an account, a server or an install. Static HTML, open `index.html`.

By Phoebe Fu.
