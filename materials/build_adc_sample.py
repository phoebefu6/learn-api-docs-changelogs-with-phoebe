"""Build assets/adc-sample.js: the changelog checker's preset spec pairs and consumer list.

Run from the repo root:  python3 materials/build_adc_sample.py

Presets
- pp-major  Parcelpoint v1 (1.4.2) -> v2 (2.0.0)   constructed
- pp-minor  Parcelpoint v1 (1.4.2) -> v1.5 (1.5.0) constructed
- pp-docs   Parcelpoint v1 (1.4.2) -> 1.4.3        constructed, descriptions only
- petstore  Swagger Petstore OpenAPI 3.0.4 sample (REAL, Apache-2.0,
            github.com/swagger-api/swagger-petstore commit 5cb909f, 2026-10-30) -> a copy with
            six edits applied by Phoebe Fu for teaching (labelled "edited" on the widget)

Parcelpoint is a constructed parcel-locker network. Every Parcelpoint name is fictional.
The JS file is written with json.dumps, never string interpolation.
"""
import copy
import json
import pathlib

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent

JSON = "application/json"


def ref(name):
    return {"$ref": "#/components/schemas/" + name}


def body(schema, required=True):
    return {"required": required, "content": {JSON: {"schema": schema}}}


def resp(desc, schema=None):
    r = {"description": desc}
    if schema is not None:
        r["content"] = {JSON: {"schema": schema}}
    return r


def qparam(name, typ, desc, required=False, **extra):
    s = {"type": typ}
    s.update(extra)
    return {"name": name, "in": "query", "required": required, "description": desc, "schema": s}


def pparam(name, desc):
    return {"name": name, "in": "path", "required": True, "description": desc, "schema": {"type": "string"}}


SIZES = ["small", "medium", "large", "xl"]


def parcelpoint_v1():
    return {
        "openapi": "3.1.0",
        "info": {"title": "Parcelpoint API (constructed example)", "version": "1.4.2",
                 "description": "Lockers, parcels, reservations and pickup webhooks."},
        "servers": [{"url": "https://api.parcelpoint.example/v1"}],
        "security": [{"apiKey": []}],
        "paths": {
            "/lockers": {"get": {
                "operationId": "listLockers", "summary": "List lockers",
                "description": "Returns lockers, one page at a time.",
                "parameters": [
                    qparam("page", "integer", "Page number, starting at 1."),
                    qparam("per_page", "integer", "Lockers per page, up to 100."),
                    qparam("city", "string", "Only lockers in this city."),
                ],
                "responses": {
                    "200": resp("A page of lockers.", {
                        "type": "object", "required": ["data", "page", "total_pages"],
                        "properties": {
                            "data": {"type": "array", "items": ref("Locker")},
                            "page": {"type": "integer"},
                            "total_pages": {"type": "integer"}}}),
                    "401": resp("Missing or invalid API key.", ref("Error"))}}},
            "/lockers/{locker_id}": {"get": {
                "operationId": "getLocker", "summary": "Get a locker",
                "description": "Returns one locker.",
                "parameters": [pparam("locker_id", "The locker id, for example LK-0042.")],
                "responses": {"200": resp("The locker.", ref("Locker")),
                              "404": resp("No locker with that id.", ref("Error"))}}},
            "/lockers/{locker_id}/status": {"get": {
                "operationId": "getLockerStatus", "summary": "Get free slots",
                "description": "Returns how many slots are free right now.",
                "parameters": [pparam("locker_id", "The locker id.")],
                "responses": {"200": resp("Free slots.", {
                    "type": "object", "required": ["locker_id", "free_slots"],
                    "properties": {"locker_id": {"type": "string"},
                                   "free_slots": {"type": "integer"}}})}}},
            "/parcels": {"post": {
                "operationId": "createParcel", "summary": "Create a parcel",
                "description": "Registers a parcel for delivery to a locker.",
                "requestBody": body(ref("ParcelCreate")),
                "responses": {"201": resp("Parcel created.", ref("Parcel")),
                              "400": resp("The request body is invalid.", ref("Error")),
                              "409": resp("The locker has no free slot of that size.", ref("Error"))}}},
            "/parcels/{parcel_id}": {"get": {
                "operationId": "getParcel", "summary": "Get a parcel",
                "description": "Returns one parcel and its pickup code.",
                "parameters": [pparam("parcel_id", "The parcel id.")],
                "responses": {"200": resp("The parcel.", ref("Parcel")),
                              "404": resp("No parcel with that id.", ref("Error"))}}},
            "/reservations": {"post": {
                "operationId": "createReservation", "summary": "Reserve a slot",
                "description": "Holds a slot for 30 minutes.",
                "requestBody": body({"type": "object", "required": ["locker_id", "size"],
                                     "properties": {"locker_id": {"type": "string"},
                                                    "size": {"type": "string", "enum": SIZES}}}),
                "responses": {"201": resp("Reservation created.", ref("Reservation")),
                              "409": resp("No free slot of that size.", ref("Error"))}}},
            "/reservations/{reservation_id}": {"delete": {
                "operationId": "cancelReservation", "summary": "Cancel a reservation",
                "description": "Releases the slot.",
                "parameters": [pparam("reservation_id", "The reservation id.")],
                "responses": {"204": resp("Cancelled."),
                              "404": resp("No reservation with that id.", ref("Error"))}}},
            "/webhooks": {"post": {
                "operationId": "createWebhook", "summary": "Subscribe to pickup events",
                "description": "Registers a URL that receives parcel events.",
                "requestBody": body({"type": "object", "required": ["url", "events"],
                                     "properties": {
                                         "url": {"type": "string", "format": "uri"},
                                         "events": {"type": "array", "items": {
                                             "type": "string",
                                             "enum": ["parcel.delivered", "parcel.picked_up", "parcel.expired"]}}}}),
                "responses": {"201": resp("Subscription created.", {
                    "type": "object", "properties": {"webhook_id": {"type": "string"},
                                                     "url": {"type": "string"}}})}}},
        },
        "components": {
            "securitySchemes": {
                "apiKey": {"type": "apiKey", "in": "header", "name": "X-Api-Key"},
                "bearer": {"type": "http", "scheme": "bearer"}},
            "schemas": {
                "Locker": {"type": "object", "required": ["locker_id", "address", "city"],
                           "properties": {
                               "locker_id": {"type": "string"},
                               "address": {"type": "string"},
                               "city": {"type": "string"},
                               "size_classes": {"type": "array", "items": {"type": "string", "enum": SIZES}},
                               "open_24h": {"type": "boolean"}}},
                "ParcelCreate": {"type": "object", "required": ["locker_id", "recipient_phone", "size"],
                                 "properties": {
                                     "locker_id": {"type": "string"},
                                     "recipient_phone": {"type": "string"},
                                     "size": {"type": "string", "enum": SIZES}}},
                "Parcel": {"type": "object", "required": ["parcel_id", "status", "locker_id"],
                           "properties": {
                               "parcel_id": {"type": "string"},
                               "status": {"type": "string",
                                          "enum": ["created", "in_locker", "picked_up", "expired"]},
                               "locker_id": {"type": "string"},
                               "pickup_code": {"type": "string"},
                               "created_at": {"type": "string", "format": "date-time"}}},
                "Reservation": {"type": "object", "required": ["reservation_id", "locker_id"],
                                "properties": {
                                    "reservation_id": {"type": "string"},
                                    "locker_id": {"type": "string"},
                                    "size": {"type": "string", "enum": SIZES},
                                    "expires_at": {"type": "string", "format": "date-time"}}},
                "Error": {"type": "object", "required": ["code", "message"],
                          "properties": {"code": {"type": "string"}, "message": {"type": "string"}}},
            },
        },
    }


def parcelpoint_v2(v1):
    d = copy.deepcopy(v1)
    d["info"]["version"] = "2.0.0"
    d["servers"] = [{"url": "https://api.parcelpoint.example/v2"}]
    s = d["components"]["schemas"]
    # Locker: locker_id renamed to id, free_slots folded in, xl lockers retired
    lk = s["Locker"]
    lk["properties"] = {"id": {"type": "string"}, **{k: v for k, v in lk["properties"].items() if k != "locker_id"}}
    lk["required"] = ["id", "address", "city"]
    lk["properties"]["size_classes"] = {"type": "array", "items": {"type": "string", "enum": SIZES[:3]}}
    lk["properties"]["free_slots"] = {"type": "integer"}
    # Cursor pagination replaces page numbers
    lst = d["paths"]["/lockers"]["get"]
    lst["description"] = "Returns lockers, one page at a time. Pass next_cursor back as cursor."
    lst["parameters"] = [
        qparam("cursor", "string", "Opaque cursor from the previous page."),
        qparam("limit", "integer", "Lockers per page, up to 100."),
        qparam("city", "string", "Only lockers in this city."),
    ]
    lst["responses"]["200"] = resp("A page of lockers.", {
        "type": "object", "required": ["data"],
        "properties": {"data": {"type": "array", "items": ref("Locker")},
                       "next_cursor": {"type": ["string", "null"]}}})
    # The status endpoint is removed (free_slots now lives on Locker)
    del d["paths"]["/lockers/{locker_id}/status"]
    # Parcels: email becomes required, phone optional, xl retired, a new status value
    pc = s["ParcelCreate"]
    pc["properties"]["recipient_email"] = {"type": "string", "format": "email"}
    pc["properties"]["size"] = {"type": "string", "enum": SIZES[:3]}
    pc["required"] = ["locker_id", "recipient_email", "size"]
    s["Parcel"]["properties"]["status"]["enum"] = ["created", "in_locker", "picked_up", "expired", "returned"]
    s["Parcel"]["properties"]["weight_grams"] = {"type": "integer"}
    # A new list endpoint
    d["paths"]["/parcels"]["get"] = {
        "operationId": "listParcels", "summary": "List parcels",
        "description": "Returns your parcels, newest first.",
        "parameters": [qparam("cursor", "string", "Opaque cursor from the previous page."),
                       qparam("status", "string", "Only parcels in this status.")],
        "responses": {"200": resp("A page of parcels.", {
            "type": "object", "required": ["data"],
            "properties": {"data": {"type": "array", "items": ref("Parcel")},
                           "next_cursor": {"type": ["string", "null"]}}})}}
    # Reservations become asynchronous: 202 instead of 201
    rv = d["paths"]["/reservations"]["post"]
    rv["responses"] = {"202": resp("Reservation accepted; confirmed by webhook.", ref("Reservation")),
                       "409": resp("No free slot of that size.", ref("Error"))}
    rv["requestBody"]["content"][JSON]["schema"]["properties"]["size"] = {"type": "string", "enum": SIZES[:3]}
    # Cancelling: wording only
    d["paths"]["/reservations/{reservation_id}"]["delete"]["description"] = \
        "Releases the slot. Cancelling twice returns 404."
    # Webhooks need an OAuth bearer token instead of the API key
    d["paths"]["/webhooks"]["post"]["security"] = [{"bearer": []}]
    return d


def parcelpoint_v15(v1):
    d = copy.deepcopy(v1)
    d["info"]["version"] = "1.5.0"
    s = d["components"]["schemas"]
    s["Locker"]["properties"]["free_slots"] = {"type": "integer"}
    s["ParcelCreate"]["properties"]["recipient_email"] = {"type": "string", "format": "email"}
    st = d["paths"]["/lockers/{locker_id}/status"]["get"]
    st["deprecated"] = True
    st["description"] = "Deprecated: read free_slots on the locker instead."
    d["paths"]["/lockers"]["get"]["parameters"].append(
        qparam("open_24h", "boolean", "Only lockers open around the clock."))
    d["paths"]["/parcels"]["get"] = {
        "operationId": "listParcels", "summary": "List parcels",
        "description": "Returns your parcels, newest first.",
        "parameters": [qparam("page", "integer", "Page number, starting at 1.")],
        "responses": {"200": resp("A page of parcels.", {
            "type": "object", "required": ["data"],
            "properties": {"data": {"type": "array", "items": ref("Parcel")},
                           "page": {"type": "integer"}}})}}
    return d


def parcelpoint_v143(v1):
    d = copy.deepcopy(v1)
    d["info"]["version"] = "1.4.3"
    d["paths"]["/lockers"]["get"]["description"] = "Returns lockers, one page at a time, sorted by locker id."
    d["paths"]["/parcels"]["post"]["summary"] = "Create a parcel for delivery"
    d["paths"]["/reservations"]["post"]["description"] = "Holds a slot for 30 minutes, then releases it."
    return d


def petstore_pair():
    real = yaml.safe_load((ROOT / "materials/sources/petstore-openapi.yaml").read_text())
    real = json.loads(json.dumps(real))  # plain JSON types only
    ed = copy.deepcopy(real)
    ed["info"]["version"] = "1.0.31-SNAPSHOT"
    # 1. findByTags removed
    del ed["paths"]["/pet/findByTags"]
    # 2. the 'pending' pet status retired
    ed["components"]["schemas"]["Pet"]["properties"]["status"]["enum"] = ["available", "sold"]
    # 3. optional limit on findByStatus
    ed["paths"]["/pet/findByStatus"]["get"]["parameters"].append(
        {"name": "limit", "in": "query", "required": False, "description": "Maximum pets returned.",
         "schema": {"type": "integer", "format": "int32"}})
    # 4. orders gain a tracking URL
    ed["components"]["schemas"]["Order"]["properties"]["trackingUrl"] = {"type": "string", "format": "uri"}
    # 5. a wording fix
    ed["paths"]["/store/inventory"]["get"]["description"] = "Returns a map of pet status to quantity."
    # 6. deleting users is deprecated
    ed["paths"]["/user/{username}"]["delete"]["deprecated"] = True
    return real, ed


# Constructed consumers of the Parcelpoint API (simulated). A consumer breaks when a BREAKING
# change hits an operation it calls and either the change is operation-wide or names a field it reads.
CONSUMERS = [
    {"id": "shopfront", "name": "Shopfront checkout plugin",
     "uses": [{"op": "GET /lockers", "fields": ["page", "per_page", "locker_id", "city"]},
              {"op": "POST /parcels", "fields": ["size", "recipient_phone", "locker_id"]}]},
    {"id": "courier", "name": "Courier handheld app",
     "uses": [{"op": "GET /lockers/{locker_id}/status", "fields": ["free_slots"]},
              {"op": "POST /reservations", "fields": ["reservation_id", "expires_at"]}]},
    {"id": "recipient", "name": "Recipient mobile app",
     "uses": [{"op": "GET /parcels/{parcel_id}", "fields": ["status", "pickup_code"]}]},
    {"id": "analytics", "name": "Partner analytics export",
     "uses": [{"op": "GET /lockers", "fields": ["total_pages", "data", "open_24h"]}]},
    {"id": "notify", "name": "SMS notification service",
     "uses": [{"op": "POST /webhooks", "fields": ["url", "events"]}]},
    {"id": "kiosk", "name": "Locker kiosk firmware",
     "uses": [{"op": "GET /lockers/{locker_id}", "fields": ["address", "open_24h"]},
              {"op": "DELETE /reservations/{reservation_id}", "fields": []}]},
]


def main():
    v1 = parcelpoint_v1()
    real, edited = petstore_pair()
    presets = [
        {"id": "pp-major", "label": "Parcelpoint v1 to v2", "kind": "constructed",
         "note": "Constructed Parcelpoint example: renamed fields, cursor pagination, a removed endpoint.",
         "date": "2026-11-16", "old": v1, "new": parcelpoint_v2(v1), "consumers": True},
        {"id": "pp-minor", "label": "Parcelpoint v1 to v1.5", "kind": "constructed",
         "note": "Constructed Parcelpoint example: additions and one deprecation.",
         "date": "2026-11-16", "old": v1, "new": parcelpoint_v15(v1), "consumers": True},
        {"id": "pp-docs", "label": "Parcelpoint wording fix", "kind": "constructed",
         "note": "Constructed Parcelpoint example: descriptions only.",
         "date": "2026-11-16", "old": v1, "new": parcelpoint_v143(v1), "consumers": True},
        {"id": "petstore", "label": "Swagger Petstore, edited", "kind": "real-edited",
         "note": "Real Swagger Petstore OpenAPI 3.0.4 sample (Apache-2.0) against a copy with six edits applied for teaching.",
         "date": "2026-11-16", "old": real, "new": edited, "consumers": False},
    ]
    data = {"presets": presets, "consumers": CONSUMERS,
            "source": {"petstore": "https://github.com/swagger-api/swagger-petstore (commit 5cb909f, Apache-2.0)"}}
    out = ROOT / "assets/adc-sample.js"
    out.write_text("/* adc-sample.js - generated by materials/build_adc_sample.py with json.dumps. "
                   "Parcelpoint is constructed; the Petstore 'old' document is the real Apache-2.0 sample. */\n"
                   "window.ADC_SAMPLE = " + json.dumps(data, separators=(",", ":")) + ";\n")
    print(out, out.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
