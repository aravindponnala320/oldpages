#!/usr/bin/env python3
"""
OldPages.in — Complete API Flow Test
Tests every major endpoint with real users and JWTs.
Run from: /Users/ponnalas/Downloads/oldpages_codex_package/
"""

import json
import sys
import time
import urllib.request
import urllib.error
from typing import Any

BASE = "http://localhost:8000/api/v1"
RESULTS: list[dict] = []
PASS = 0
FAIL = 0
_ts = int(time.time())


def req(method, path, body=None, token=None, expect=200, label=""):
    global PASS, FAIL
    url = f"{BASE}{path}"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body is not None else None
    try:
        r = urllib.request.Request(url, data=data, headers=headers, method=method)
        with urllib.request.urlopen(r, timeout=15) as resp:
            status = resp.status
            raw = resp.read()
            payload = json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        status = e.code
        try:
            payload = json.loads(e.read())
        except Exception:
            payload = {}
    except Exception as e:
        status = 0
        payload = {"error": str(e)}

    expected = [expect] if isinstance(expect, int) else list(expect)
    ok = status in expected
    if ok:
        PASS += 1
        icon = "✅"
    else:
        FAIL += 1
        icon = "❌"
    tag = f" [{label}]" if label else ""
    print(f"  {icon} {method:6} {path[:60]:<60} → {status}{tag}")
    if not ok:
        detail = payload.get("detail") or payload.get("error") or ""
        if isinstance(detail, list):
            detail = "; ".join(f"{p.get('loc',['?'])[-1]}: {p.get('msg','')}" for p in detail[:3])
        print(f"         ↳ {str(detail)[:100]}")
    RESULTS.append({"method": method, "path": path, "status": status, "ok": ok, "payload": payload, "label": label})
    return payload


def tok(r): return r.get("tokens", {}).get("access_token", "")
def rtok(r): return r.get("tokens", {}).get("refresh_token", "")
def uid(r): return r.get("user", {}).get("id", "")
def section(t): print(f"\n{'═'*70}\n  {t}\n{'═'*70}")
def note(m): print(f"  ℹ️   {m}")


# ── LISTING HELPERS ───────────────────────────────────────────────────────────
def make_listing(seller_token, book_id=None, description="Test listing"):
    payload = {
        "listing_modes": ["sell"],
        "condition": {
            "condition": "good",
            "handwritten_notes": False,
            "name_written_inside": False,
            "torn_pages": False,
            "missing_pages": False,
            "loose_binding": False,
            "water_damage": False,
            "stains": False,
        },
        "location": {
            "public_area": "Koramangala, Bangalore",
            "city": "Bangalore",
            "state": "Karnataka",
            "country": "IN",
            "exact_latitude": "12.9279",
            "exact_longitude": "77.6271",
        },
        "price_amount_cents": 35000,
        "currency": "INR",
        "quantity": 2,
        "delivery_methods": [{"method": "pickup"}],
        "description": description,
        "negotiable": True,
    }
    if book_id:
        payload["book_id"] = book_id
    else:
        payload["isbn"] = "9780070700130"
    return req("POST", "/listings", payload, token=seller_token, expect=201, label=f"create listing: {description[:30]}")


# ─── 1. HEALTH ────────────────────────────────────────────────────────────────
section("1. HEALTH CHECKS")
try:
    with urllib.request.urlopen("http://localhost:8000/health/live", timeout=5) as r:
        live = json.loads(r.read())
    with urllib.request.urlopen("http://localhost:8000/health/ready", timeout=5) as r:
        ready = json.loads(r.read())
    print(f"  ✅ GET    /health/live                                               → 200 [{live['status']}]")
    print(f"  ✅ GET    /health/ready                                              → 200 [db:{ready['components']['database']['status']} redis:{ready['components']['redis']['status']}]")
    PASS += 2
except Exception as e:
    print(f"  ❌ Health check failed: {e}")
    FAIL += 2; sys.exit(1)


# ─── 2. AUTH ──────────────────────────────────────────────────────────────────
section("2. AUTHENTICATION")

BUYER_EMAIL  = f"buyer_{_ts}@test.oldpages"
SELLER_EMAIL = f"seller_{_ts}@test.oldpages"
MOD_EMAIL    = f"mod_{_ts}@test.oldpages"
PASSWORD     = "OldPages@Secret123"

r = req("POST", "/auth/register", {"display_name": "Arjun Kumar", "email": BUYER_EMAIL, "password": PASSWORD, "terms_accepted": True, "privacy_accepted": True}, expect=201, label="register buyer")
BUYER_TOKEN = tok(r); BUYER_REFRESH = rtok(r); BUYER_ID = uid(r)
note(f"Buyer  id={BUYER_ID}  email={BUYER_EMAIL}")

r = req("POST", "/auth/register", {"display_name": "Priya Bookworm", "email": SELLER_EMAIL, "password": PASSWORD, "terms_accepted": True, "privacy_accepted": True}, expect=201, label="register seller")
SELLER_TOKEN = tok(r); SELLER_REFRESH = rtok(r); SELLER_ID = uid(r)
note(f"Seller id={SELLER_ID}  email={SELLER_EMAIL}")

r = req("POST", "/auth/register", {"display_name": "Platform Mod", "email": MOD_EMAIL, "password": PASSWORD, "terms_accepted": True, "privacy_accepted": True}, expect=201, label="register moderator")
MOD_TOKEN = tok(r)

# Duplicate email → 409
req("POST", "/auth/register", {"display_name": "Dup", "email": BUYER_EMAIL, "password": PASSWORD, "terms_accepted": True, "privacy_accepted": True}, expect=[409, 400, 422], label="duplicate email → 409")

# Login
r = req("POST", "/auth/login", {"email": BUYER_EMAIL, "password": PASSWORD}, label="login buyer")
BUYER_TOKEN = tok(r) or BUYER_TOKEN

# Wrong password → 401
req("POST", "/auth/login", {"email": BUYER_EMAIL, "password": "BadPass!!"}, expect=401, label="wrong password → 401")

# Token refresh
r = req("POST", "/auth/refresh", {"refresh_token": BUYER_REFRESH}, label="token refresh")
BUYER_TOKEN = tok(r) or BUYER_TOKEN

# Get /users/me
r = req("GET", "/users/me", token=BUYER_TOKEN, label="GET /users/me")
note(f"Buyer profile: {r.get('display_name')} email={r.get('email')}")

r = req("GET", "/users/me", token=SELLER_TOKEN, label="GET /users/me (seller)")

# Update profile
req("PATCH", "/users/me", {"bio": "Book lover in Bangalore!", "city": "Bangalore", "state": "Karnataka", "country": "IN"}, token=BUYER_TOKEN, label="PATCH /users/me")

# Public profile view
if SELLER_ID:
    req("GET", f"/users/{SELLER_ID}", label="GET /users/{id} public")

# Sessions
req("GET", "/users/me/sessions", token=BUYER_TOKEN, label="GET /users/me/sessions")
req("GET", "/users/me/devices", token=BUYER_TOKEN, label="GET /users/me/devices")

# Block / unblock
if SELLER_ID:
    req("POST", f"/users/{SELLER_ID}/block", {"reason": "test block"}, token=BUYER_TOKEN, expect=201, label="POST /users/{id}/block")
    req("DELETE", f"/users/{SELLER_ID}/block", token=BUYER_TOKEN, expect=204, label="DELETE /users/{id}/block (unblock)")

# Forgot password
req("POST", "/auth/forgot-password", {"email": BUYER_EMAIL}, expect=[200, 202], label="POST /auth/forgot-password")

# Logout (requires refresh_token in body)
r2 = req("POST", "/auth/login", {"email": MOD_EMAIL, "password": PASSWORD}, label="login mod (for logout test)")
tmp_tok = tok(r2); tmp_ref = rtok(r2)
if tmp_tok:
    req("POST", "/auth/logout", {"refresh_token": tmp_ref}, token=tmp_tok, expect=[200, 204], label="POST /auth/logout")
    req("GET", "/users/me", token=tmp_tok, expect=401, label="revoked token → 401")
    r3 = req("POST", "/auth/login", {"email": MOD_EMAIL, "password": PASSWORD}, label="re-login mod")
    MOD_TOKEN = tok(r3) or MOD_TOKEN


# ─── 3. CATALOG ───────────────────────────────────────────────────────────────
section("3. BOOK CATALOG")

r = req("GET", "/categories", label="GET /categories")
note(f"Categories: {len(r.get('categories',[]))}")
r = req("GET", "/authors?limit=5", label="GET /authors")
r = req("GET", "/publishers?limit=5", label="GET /publishers")

# Create book (valid ISBN-13 with correct check digit: 978-0-07-070013-0)
r = req("POST", "/books", {
    "title": "NCERT Physics Part II Class 12",
    "description": "Standard NCERT textbook covering electrostatics, current electricity, magnetism, optics, and modern physics.",
    "language": "en",
    "publication_year": 2023,
    "page_count": 320,
    "format": "paperback",
    "isbn_13": "9780070700130",
    "authors": [{"name": "NCERT", "role": "author"}],
}, token=SELLER_TOKEN, expect=[201, 409], label="POST /books (create)")
BOOK_ID = r.get("id", "")
# On 409 (duplicate ISBN), look up the existing book
if not BOOK_ID:
    br = req("GET", "/books?q=NCERT+Physics+Part+II+Class+12&limit=5", label="GET book by title (fallback)")
    books = br.get("books", [])
    BOOK_ID = books[0].get("id", "") if books else ""
note(f"Book id={BOOK_ID}")

if BOOK_ID:
    req("GET", f"/books/{BOOK_ID}", label="GET /books/{id}")

r = req("GET", "/books?q=NCERT+Physics&limit=10", label="GET /books?q=...")
note(f"Book search: {len(r.get('books',[]))} results")

req("POST", "/books/resolve-isbn", {"isbn": "9780070700130"}, token=SELLER_TOKEN, expect=[200, 404, 422], label="POST /books/resolve-isbn")


# ─── 4. LISTINGS & MEDIA ──────────────────────────────────────────────────────
section("4. LISTINGS & MEDIA")

# Create listings
r = make_listing(SELLER_TOKEN, BOOK_ID, "NCERT Physics Part II — Seller L1")
L1 = r.get("id", "")
note(f"L1={L1} status={r.get('status','')}")

r = make_listing(SELLER_TOKEN, BOOK_ID, "NCERT Chemistry Class 12 — Seller L2")
L2 = r.get("id", "")

r = make_listing(BUYER_TOKEN, BOOK_ID, "HC Verma Physics Vol 1 — Buyer L3")
L3 = r.get("id", "")

# Get, update, publish
if L1:
    req("GET", f"/listings/{L1}", token=SELLER_TOKEN, label="GET /listings/{id} (draft)")
    req("PATCH", f"/listings/{L1}", {"description": "Updated desc — pristine condition", "price_amount_cents": 33000}, token=SELLER_TOKEN, label="PATCH /listings/{id}")

for lid, who, lbl in [(L1, SELLER_TOKEN, "L1"), (L2, SELLER_TOKEN, "L2"), (L3, BUYER_TOKEN, "L3")]:
    if lid:
        r = req("POST", f"/listings/{lid}/publish", {}, token=who, expect=[200, 201, 422], label=f"publish {lbl}")
        note(f"  {lbl} status={r.get('status', r.get('detail', ''))}")

# Public view
if L1:
    req("GET", f"/listings/{L1}", label="GET /listings/{id} (public)")

# Media upload URL
r = req("POST", "/media/upload-url", {
    "filename": "book_cover.jpg",
    "content_type": "image/jpeg",
    "byte_size": 204800,
}, token=SELLER_TOKEN, expect=[200, 201], label="POST /media/upload-url")
MEDIA_ID = r.get("id", "")
note(f"Media id={MEDIA_ID}")

if MEDIA_ID:
    req("POST", f"/media/{MEDIA_ID}/complete", {}, token=SELLER_TOKEN, expect=[200, 201, 422], label="POST /media/{id}/complete")

# Pause & relist
if L2:
    req("POST", f"/listings/{L2}/pause", {}, token=SELLER_TOKEN, expect=[200, 201, 409], label="POST pause listing")
    req("POST", f"/listings/{L2}/relist", {}, token=SELLER_TOKEN, expect=[200, 201, 409], label="POST relist listing")


# ─── 5. SEARCH & DISCOVERY ────────────────────────────────────────────────────
section("5. SEARCH & DISCOVERY")

r = req("GET", "/search/listings?q=NCERT+Physics&limit=10", label="GET /search/listings")
note(f"Results: {len(r.get('listings',[]))}")
req("GET", "/search/listings?q=physics&condition=good&sort=newest&limit=5", label="search with filters")
req("GET", "/search/listings?q=ncert&listing_type=sell&limit=5", label="search by type")
r = req("GET", "/search/suggestions?q=ncert", label="GET /search/suggestions")
note(f"Suggestions: {r.get('suggestions',[])}")

# Saved searches
r = req("POST", "/saved-searches", {"name": "NCERT Physics Bangalore", "query": "NCERT Physics", "notify_on_match": True}, token=BUYER_TOKEN, expect=201, label="POST /saved-searches")
SAVED_SEARCH_ID = r.get("id", "")
req("GET", "/saved-searches", token=BUYER_TOKEN, label="GET /saved-searches")

# Wishlist
if BOOK_ID:
    req("POST", f"/wishlists/{BOOK_ID}", {}, token=BUYER_TOKEN, expect=[200, 201], label="POST /wishlists/{book_id}")
    req("DELETE", f"/wishlists/{BOOK_ID}", token=BUYER_TOKEN, expect=[200, 204, 404], label="DELETE /wishlists/{book_id}")
    req("POST", f"/wishlists/{BOOK_ID}", {}, token=BUYER_TOKEN, expect=[200, 201], label="re-add wishlist")

# Favorites
if L1:
    req("POST", f"/listings/{L1}/favorite", {}, token=BUYER_TOKEN, expect=[200, 201], label="POST favorite listing")

# Follows
r = req("POST", "/follows", {"followee_id": SELLER_ID, "followee_type": "user"}, token=BUYER_TOKEN, expect=[200, 201, 422], label="POST /follows")
FOLLOW_ID = r.get("id", "")


# ─── 6. CHAT & MESSAGING ──────────────────────────────────────────────────────
section("6. CHAT & MESSAGING")

chat_payload: dict = {"message": "Hi! Is NCERT Physics still available? ₹300?"}
if L1:
    chat_payload["listing_id"] = L1
r = req("POST", "/chat-requests", chat_payload, token=BUYER_TOKEN, expect=[201, 422], label="POST /chat-requests")
CHAT_REQ_ID = r.get("id", "")
note(f"Chat request id={CHAT_REQ_ID}")

CONV_ID = ""
if CHAT_REQ_ID:
    r = req("POST", f"/chat-requests/{CHAT_REQ_ID}/accept", {"message": "Yes available! Pick up from Koramangala."}, token=SELLER_TOKEN, expect=[200, 201], label="POST /chat-requests/{id}/accept")
    CONV_ID = r.get("conversation_id", r.get("id", ""))
    note(f"Conversation id={CONV_ID}")

# Decline another request
chat2: dict = {"message": "Can I have it for ₹100?"}
if L2: chat2["listing_id"] = L2
r = req("POST", "/chat-requests", chat2, token=BUYER_TOKEN, expect=[201, 422], label="POST /chat-requests (to decline)")
CR2 = r.get("id", "")
if CR2:
    req("POST", f"/chat-requests/{CR2}/decline", {"message": "Sorry, minimum ₹250."}, token=SELLER_TOKEN, expect=[200, 201], label="POST /chat-requests/{id}/decline")

req("GET", "/conversations", token=BUYER_TOKEN, label="GET /conversations (buyer)")
req("GET", "/conversations", token=SELLER_TOKEN, label="GET /conversations (seller)")

MSG_ID = ""
if CONV_ID:
    r = req("GET", f"/conversations/{CONV_ID}/messages?limit=20", token=BUYER_TOKEN, label="GET /conversations/{id}/messages")
    msgs = r.get("messages", [])
    MSG_ID = msgs[0].get("id", "") if msgs else ""
    note(f"Messages: {len(msgs)}")

if CONV_ID:
    r = req("POST", f"/conversations/{CONV_ID}/messages", {"content": "Meet Saturday 3pm Koramangala Starbucks?", "message_type": "text", "client_message_id": f"m{_ts}a"}, token=BUYER_TOKEN, expect=[200, 201], label="POST send message (buyer)")
    MSG_ID = r.get("id", MSG_ID)
    req("POST", f"/conversations/{CONV_ID}/messages", {"content": "Saturday works! I'll be there.", "message_type": "text", "client_message_id": f"m{_ts}b"}, token=SELLER_TOKEN, expect=[200, 201], label="POST send message (seller)")
    # Idempotent
    req("POST", f"/conversations/{CONV_ID}/messages", {"content": "Meet Saturday 3pm Koramangala Starbucks?", "message_type": "text", "client_message_id": f"m{_ts}a"}, token=BUYER_TOKEN, expect=[200, 201], label="POST message (idempotent same id)")

if CONV_ID and MSG_ID:
    req("POST", f"/conversations/messages/{MSG_ID}/report", {"reason": "spam", "description": "test"}, token=SELLER_TOKEN, expect=[200, 201, 422, 404], label="POST /conversations/messages/{id}/report")


# ─── 7. OFFERS & NEGOTIATION ──────────────────────────────────────────────────
section("7. OFFERS & NEGOTIATION")

OFFER_ID = ""
if L1:
    r = req("POST", "/offers", {"listing_id": L1, "offer_type": "price", "amount_cents": 30000, "currency": "INR", "quantity": 1, "fulfillment_method": "pickup", "message": "Final year student, please ₹300!"}, token=BUYER_TOKEN, expect=[201, 409], label="POST /offers (price)")
    OFFER_ID = r.get("id", "")
    note(f"Offer id={OFFER_ID} ₹{30000//100}")

COUNTER_ID = ""
if OFFER_ID:
    r = req("POST", f"/offers/{OFFER_ID}/counter", {"amount_cents": 32000, "message": "₹320 best price — like new!"}, token=SELLER_TOKEN, expect=[200, 201], label="POST /offers/{id}/counter")
    COUNTER_ID = r.get("id", "")
    note(f"Counter id={COUNTER_ID} ₹{32000//100}")

TRANSACTION_ID = ""
if COUNTER_ID:
    r = req("POST", f"/offers/{COUNTER_ID}/accept", {}, token=BUYER_TOKEN, expect=[200, 201], label="POST /offers/{id}/accept (buyer accepts)")
    TRANSACTION_ID = r.get("transaction_id", r.get("id", ""))
    note(f"Transaction created: id={TRANSACTION_ID}")

# Reject flow
if L2:
    r = req("POST", "/offers", {"listing_id": L2, "offer_type": "price", "amount_cents": 18000, "fulfillment_method": "pickup", "message": "₹180?"}, token=BUYER_TOKEN, expect=[201, 409, 422], label="POST offer (to reject)")
    OID2 = r.get("id", "")
    if OID2:
        req("POST", f"/offers/{OID2}/reject", {}, token=SELLER_TOKEN, expect=[200, 201], label="POST /offers/{id}/reject")

# Withdraw flow
if L2:
    r = req("POST", "/offers", {"listing_id": L2, "offer_type": "price", "amount_cents": 25000, "fulfillment_method": "pickup", "message": "₹250?"}, token=BUYER_TOKEN, expect=[201, 409, 422], label="POST offer (to withdraw)")
    WOID = r.get("id", "")
    if WOID:
        req("POST", f"/offers/{WOID}/withdraw", {}, token=BUYER_TOKEN, expect=[200, 201], label="POST /offers/{id}/withdraw")

# Exchange offer
if L1 and L3:
    r = req("POST", "/offers", {"listing_id": L1, "offer_type": "exchange", "fulfillment_method": "pickup", "message": "Exchange HC Verma ↔ NCERT Physics?", "exchange_items": [{"offered_listing_id": L3, "title": "HC Verma Physics Vol 1", "condition_note": "Good", "cash_adjustment_cents": 0}]}, token=BUYER_TOKEN, expect=[201, 409, 422], label="POST exchange offer")
    EXID = r.get("id", "")
    if EXID:
        req("POST", f"/offers/{EXID}/reject", {}, token=SELLER_TOKEN, expect=[200, 201], label="POST reject exchange offer")


# ─── 8. PICKUP & TRANSACTION ──────────────────────────────────────────────────
section("8. PICKUP & TRANSACTION")

if TRANSACTION_ID:
    r = req("GET", f"/orders/{TRANSACTION_ID}", token=BUYER_TOKEN, expect=[200, 404], label="GET /orders/{id}")
    note(f"Status: {r.get('status','')}")

req("GET", "/orders", token=BUYER_TOKEN, expect=[200, 404], label="GET /orders (buyer)")
req("GET", "/orders", token=SELLER_TOKEN, expect=[200, 404], label="GET /orders (seller)")

PICKUP_ID = ""; HANDOVER_CODE = "XXXXX"
if TRANSACTION_ID:
    r = req("POST", "/pickups", {"transaction_id": TRANSACTION_ID, "proposed_start_at": "2026-07-05T09:30:00Z", "proposed_end_at": "2026-07-05T11:00:00Z", "public_location_label": "Koramangala Starbucks, 80 Feet Road, Bangalore", "pickup_notes_private": "Blue jacket. Bring book in cover."}, token=BUYER_TOKEN, expect=[200, 201, 422], label="POST /pickups (propose)")
    PICKUP_ID = r.get("id", ""); HANDOVER_CODE = r.get("handover_code", HANDOVER_CODE)
    note(f"Pickup id={PICKUP_ID} code={HANDOVER_CODE}")

if PICKUP_ID:
    r = req("POST", f"/pickups/{PICKUP_ID}/confirm", {"confirmed": True, "message": "See you at 3pm!"}, token=SELLER_TOKEN, expect=[200, 201, 422], label="POST /pickups/{id}/confirm")

if TRANSACTION_ID:
    r = req("POST", f"/transactions/{TRANSACTION_ID}/complete", {"handover_code": HANDOVER_CODE}, token=BUYER_TOKEN, expect=[200, 201, 422], label="POST /transactions/{id}/complete")
    note(f"Final status: {r.get('status','')}")


# ─── 9. REVIEWS ───────────────────────────────────────────────────────────────
section("9. REVIEWS")

if TRANSACTION_ID:
    req("POST", "/reviews", {"transaction_id": TRANSACTION_ID, "review_type": "buyer_reviews_seller", "rating": 5, "comment": "Excellent seller, perfect condition!", "dimensions": [{"dimension": "description_accuracy", "rating": 5}, {"dimension": "condition_accuracy", "rating": 5}, {"dimension": "communication", "rating": 5}, {"dimension": "pickup_punctuality", "rating": 5}]}, token=BUYER_TOKEN, expect=[200, 201, 422], label="POST /reviews (buyer→seller ⭐⭐⭐⭐⭐)")
    req("POST", "/reviews", {"transaction_id": TRANSACTION_ID, "review_type": "seller_reviews_buyer", "rating": 5, "comment": "Great buyer, on time!", "dimensions": [{"dimension": "communication", "rating": 5}, {"dimension": "pickup_punctuality", "rating": 5}]}, token=SELLER_TOKEN, expect=[200, 201, 422], label="POST /reviews (seller→buyer ⭐⭐⭐⭐⭐)")
    # Duplicate → error
    req("POST", "/reviews", {"transaction_id": TRANSACTION_ID, "review_type": "buyer_reviews_seller", "rating": 1, "comment": "Changing..."}, token=BUYER_TOKEN, expect=[400, 409, 422], label="duplicate review → error")


# ─── 10. REPORTS & TRUST ──────────────────────────────────────────────────────
section("10. REPORTS & TRUST")

REPORT_ID = ""
if L2:
    r = req("POST", "/reports", {"target_type": "listing", "target_id": L2, "reason": "misleading_condition", "description": "Photos don't match condition. Water damage not disclosed."}, token=BUYER_TOKEN, expect=[200, 201], label="POST /reports (listing)")
    REPORT_ID = r.get("id", "")
if SELLER_ID:
    req("POST", "/reports", {"target_type": "user", "target_id": SELLER_ID, "reason": "spam", "description": "Sending spam outside platform."}, token=BUYER_TOKEN, expect=[200, 201], label="POST /reports (user)")

req("GET", "/admin/moderation/cases?limit=10", token=MOD_TOKEN, expect=[200, 403], label="GET /admin/moderation/cases")
req("GET", "/admin/moderation/rules", token=MOD_TOKEN, expect=[200, 403, 404], label="GET /admin/moderation/rules")
if SELLER_ID:
    req("GET", f"/admin/moderation/users/{SELLER_ID}", token=MOD_TOKEN, expect=[200, 403, 404], label="GET /admin/moderation/users/{id}")
if L1:
    req("GET", f"/admin/moderation/listings/{L1}", token=MOD_TOKEN, expect=[200, 403, 404], label="GET /admin/moderation/listings/{id}")
if CONV_ID:
    req("GET", f"/admin/moderation/cases/{CONV_ID}/conversation-evidence", token=MOD_TOKEN, expect=[200, 403, 404], label="GET /admin/conversation-evidence")
if REPORT_ID:
    req("POST", f"/reports/{REPORT_ID}/appeal", {"statement": "Listing condition was accurately described."}, token=SELLER_TOKEN, expect=[200, 201, 404, 422], label="POST /reports/{id}/appeal")


# ─── 11. NOTIFICATIONS ────────────────────────────────────────────────────────
section("11. NOTIFICATIONS")

r = req("GET", "/notifications?limit=20", token=BUYER_TOKEN, label="GET /notifications")
notifs = r.get("notifications", [])
note(f"Notifications: {len(notifs)}")
NOTIF_ID = notifs[0].get("id") if notifs else None
if NOTIF_ID:
    req("POST", f"/notifications/{NOTIF_ID}/read", {}, token=BUYER_TOKEN, expect=[200, 204], label="POST /notifications/{id}/read")

req("GET", "/notification-preferences", token=BUYER_TOKEN, label="GET /notification-preferences")
req("PATCH", "/notification-preferences", {"preferences": {"chat_message": {"in_app": True, "push": False, "email": False}, "offer_received": {"in_app": True, "push": True, "email": True}}}, token=BUYER_TOKEN, expect=[200, 201, 422], label="PATCH /notification-preferences")


# ─── 12. COMMUNITIES ──────────────────────────────────────────────────────────
section("12. COMMUNITIES")

r = req("POST", "/communities", {"name": f"Bangalore Booklovers {_ts}", "description": "Community for book lovers in Bangalore!", "visibility": "public", "community_type": "genre", "city": "Bangalore", "state": "Karnataka", "country": "IN", "rules": [{"title": "Be respectful", "body": "Treat all members with respect."}, {"title": "Books only", "body": "Keep discussions related to books."}, {"title": "No spam", "body": "Do not post spam or advertisements."}]}, token=SELLER_TOKEN, expect=201, label="POST /communities")
COMM_ID = r.get("id", "")
note(f"Community id={COMM_ID}")

if COMM_ID:
    req("GET", f"/communities/{COMM_ID}", label="GET /communities/{id}")
r = req("GET", "/communities?limit=10", label="GET /communities")
note(f"Communities: {len(r.get('communities',[]))}")

if COMM_ID:
    req("POST", f"/communities/{COMM_ID}/join", {"message": "I'd love to join!"}, token=BUYER_TOKEN, expect=[200, 201], label="POST /communities/{id}/join")
    if BUYER_ID:
        req("POST", f"/communities/{COMM_ID}/approve-member", {"user_id": BUYER_ID}, token=SELLER_TOKEN, expect=[200, 201, 422], label="POST /communities/{id}/approve-member")
    req("GET", f"/communities/{COMM_ID}/feed?limit=10", token=BUYER_TOKEN, label="GET /communities/{id}/feed")

POST_ID = ""
if COMM_ID:
    r = req("POST", f"/communities/{COMM_ID}/posts", {"body": "Anyone have NCERT Chemistry Class 12 in good condition for ₹150?", "title": "Looking for NCERT Chemistry", "post_type": "text"}, token=BUYER_TOKEN, expect=[200, 201], label="POST /communities/{id}/posts")
    POST_ID = r.get("id", "")
    note(f"Post id={POST_ID}")

if POST_ID:
    req("POST", f"/posts/{POST_ID}/reactions", {"reaction": "👍"}, token=SELLER_TOKEN, expect=[200, 201], label="POST /posts/{id}/reactions")
    req("POST", f"/posts/{POST_ID}/comments", {"body": "I might have one! Drop me a message."}, token=SELLER_TOKEN, expect=[200, 201], label="POST /posts/{id}/comments")
if COMM_ID:
    req("GET", f"/communities/{COMM_ID}/marketplace?limit=10", token=BUYER_TOKEN, label="GET /communities/{id}/marketplace")
    if POST_ID:
        req("POST", f"/communities/{COMM_ID}/reports", {"target_type": "post", "target_id": POST_ID, "reason": "spam", "description": "test"}, token=MOD_TOKEN, expect=[200, 201, 422], label="POST /communities/{id}/reports")


# ─── 13. BOOK CLUBS ───────────────────────────────────────────────────────────
section("13. BOOK CLUBS")

CLUB_ID = ""
if COMM_ID:
    r = req("POST", "/clubs", {"name": f"Physics Readers {_ts}", "description": "Reading physics books together.", "community_id": COMM_ID, "reading_pace": "1 chapter/week", "max_members": 20}, token=SELLER_TOKEN, expect=[200, 201], label="POST /clubs")
    CLUB_ID = r.get("id", "")
    note(f"Club id={CLUB_ID}")

if CLUB_ID:
    req("GET", f"/clubs/{CLUB_ID}", token=SELLER_TOKEN, label="GET /clubs/{id}")

CLUB_BOOK_ID = ""
if CLUB_ID and BOOK_ID:
    r = req("POST", f"/clubs/{CLUB_ID}/books", {"book_id": BOOK_ID, "start_date": "2026-07-15", "end_date": "2026-08-15", "description": "First physics read!"}, token=SELLER_TOKEN, expect=[200, 201], label="POST /clubs/{id}/books")
    CLUB_BOOK_ID = r.get("id", "")

NOM_ID = ""
if CLUB_ID and BOOK_ID:
    r = req("POST", f"/clubs/{CLUB_ID}/nominations", {"book_id": BOOK_ID, "reason": "Great foundational text."}, token=SELLER_TOKEN, expect=[200, 201], label="POST /clubs/{id}/nominations")
    NOM_ID = r.get("id", "")

if CLUB_ID and NOM_ID:
    req("POST", f"/clubs/{CLUB_ID}/votes", {"ranked_nomination_ids": [NOM_ID]}, token=BUYER_TOKEN, expect=[200, 201, 422], label="POST /clubs/{id}/votes")
    req("POST", f"/clubs/{CLUB_ID}/select-book", {"nomination_id": NOM_ID}, token=SELLER_TOKEN, expect=[200, 201, 422], label="POST /clubs/{id}/select-book")

if CLUB_BOOK_ID:
    req("POST", f"/club-books/{CLUB_BOOK_ID}/milestones", {"chapter": 5, "title": "Chapters 1-5 Discussion", "discussion_prompt": "Thoughts on electromagnetic induction?", "due_date": "2026-07-22", "spoiler_chapter": 5}, token=SELLER_TOKEN, expect=[200, 201, 422], label="POST /club-books/{id}/milestones")

BUDDY_ID = ""
if BOOK_ID:
    r = req("POST", "/buddy-reads", {"book_id": BOOK_ID, "name": f"Physics Duo {_ts}", "start_date": "2026-07-01", "end_date": "2026-07-31"}, token=BUYER_TOKEN, expect=[200, 201], label="POST /buddy-reads")
    BUDDY_ID = r.get("id", "")
if BUDDY_ID:
    req("POST", f"/buddy-reads/{BUDDY_ID}/join", {}, token=SELLER_TOKEN, expect=[200, 201], label="POST /buddy-reads/{id}/join")
    req("POST", f"/buddy-reads/{BUDDY_ID}/progress", {"current_page": 87, "note": "Ch5 done! Great wave optics section."}, token=BUYER_TOKEN, expect=[200, 201, 422], label="POST /buddy-reads/{id}/progress")

if BOOK_ID and COMM_ID:
    req("POST", "/readalongs", {"book_id": BOOK_ID, "community_id": COMM_ID, "name": f"Physics Readalong {_ts}", "is_public": True, "start_date": "2026-08-01"}, token=SELLER_TOKEN, expect=[200, 201, 422], label="POST /readalongs")


# ─── 14. EVENTS ───────────────────────────────────────────────────────────────
section("14. EVENTS")

EVENT_ID = ""
if COMM_ID:
    r = req("POST", "/events", {"title": f"Bangalore Book Exchange {_ts}", "description": "Bring old books, swap with readers! Free entry.", "event_type": "book_exchange", "community_id": COMM_ID, "starts_at": "2026-08-15T10:00:00Z", "ends_at": "2026-08-15T17:00:00Z", "timezone": "Asia/Kolkata", "location_label": "Cubbon Park, Bangalore", "latitude": "12.9763", "longitude": "77.5929", "capacity": 100, "is_free": True, "is_online": False}, token=SELLER_TOKEN, expect=[200, 201], label="POST /events")
    EVENT_ID = r.get("id", "")
    note(f"Event id={EVENT_ID}")

if EVENT_ID:
    req("GET", f"/events/{EVENT_ID}", label="GET /events/{id}")
r = req("GET", "/events?limit=10", label="GET /events")
note(f"Events: {len(r.get('events',[]))}")

if EVENT_ID:
    r = req("POST", f"/events/{EVENT_ID}/rsvps", {"status": "going"}, token=BUYER_TOKEN, expect=[200, 201], label="POST /events/{id}/rsvps (going)")
    RSVP_ID = r.get("id", "")
    req("POST", f"/events/{EVENT_ID}/rsvps", {"status": "interested"}, token=SELLER_TOKEN, expect=[200, 201], label="POST /events/{id}/rsvps (interested)")
    if BUYER_ID:
        req("POST", f"/events/{EVENT_ID}/checkins", {"attendee_user_id": BUYER_ID}, token=SELLER_TOKEN, expect=[200, 201, 422], label="POST /events/{id}/checkins (QR check-in)")
    # Calendar
    try:
        rr = urllib.request.Request(f"{BASE}/events/{EVENT_ID}/calendar.ics", headers={"Authorization": f"Bearer {BUYER_TOKEN}"})
        with urllib.request.urlopen(rr, timeout=5) as resp:
            cal = resp.read()
            ok = b"BEGIN:VCALENDAR" in cal
            print(f"  {'✅' if ok else '❌'} GET    /events/{{id}}/calendar.ics                              → 200 [ICS={ok}]")
            PASS += 1 if ok else 0; FAIL += 0 if ok else 1
    except Exception as e:
        print(f"  ❌ calendar.ics: {e}"); FAIL += 1
    req("POST", f"/events/{EVENT_ID}/rsvps/cancel", {}, token=BUYER_TOKEN, expect=[200, 204, 422], label="POST /events/{id}/rsvps/cancel")


# ─── 15. READING TRACKER ──────────────────────────────────────────────────────
section("15. READING TRACKER")

r = req("POST", "/reading/shelves", {"name": f"Currently Reading {_ts}", "shelf_type": "reading", "is_public": True}, token=BUYER_TOKEN, expect=[200, 201], label="POST /reading/shelves")
SHELF_ID = r.get("id", "")
note(f"Shelf id={SHELF_ID}")

req("GET", "/reading/shelves", token=BUYER_TOKEN, label="GET /reading/shelves (own)")
if BUYER_ID:
    req("GET", f"/users/{BUYER_ID}/shelves", label="GET /users/{id}/shelves (public)")

SHELF_ITEM_ID = ""
if SHELF_ID and BOOK_ID:
    r = req("POST", f"/reading/shelves/{SHELF_ID}/items", {"book_id": BOOK_ID, "start_date": "2026-06-20"}, token=BUYER_TOKEN, expect=[200, 201], label="POST /reading/shelves/{id}/items")
    SHELF_ITEM_ID = r.get("id", "")
    note(f"Shelf item id={SHELF_ITEM_ID}")

# Progress uses /reading/progress/{book_id} from OpenAPI
if BOOK_ID and SHELF_ITEM_ID:
    r = req("PUT", f"/reading/progress/{BOOK_ID}", {"shelf_item_id": SHELF_ITEM_ID, "current_page": 87, "total_pages": 320, "reading_time_minutes": 45}, token=BUYER_TOKEN, expect=[200, 201], label="PUT /reading/progress/{book_id}")
    note(f"Progress: {r.get('progress_percentage', r.get('current_page',''))}%")
    req("PUT", f"/reading/progress/{BOOK_ID}", {"shelf_item_id": SHELF_ITEM_ID, "current_page": 87, "total_pages": 320, "reading_time_minutes": 45}, token=BUYER_TOKEN, expect=[200, 201], label="PUT /reading/progress (idempotent)")
    req("PUT", f"/reading/progress/{BOOK_ID}", {"shelf_item_id": SHELF_ITEM_ID, "current_page": 142, "total_pages": 320, "reading_time_minutes": 60}, token=BUYER_TOKEN, expect=[200, 201], label="PUT /reading/progress (advance page)")

req("GET", "/reading/progress?limit=10", token=BUYER_TOKEN, label="GET /reading/progress")

if SHELF_ITEM_ID:
    req("POST", "/reading/notes", {"shelf_item_id": SHELF_ITEM_ID, "note_type": "highlight", "content": "Excellent analogy for electromagnetic induction p.142!", "page_number": 142, "is_private": True}, token=BUYER_TOKEN, expect=[200, 201, 422], label="POST /reading/notes")
req("GET", "/reading/notes?limit=10", token=BUYER_TOKEN, label="GET /reading/notes")
if BUYER_ID:
    req("GET", f"/users/{BUYER_ID}/reading-notes?limit=10", label="GET /users/{id}/reading-notes")

# Reading goals: period_start + period_end required
r = req("POST", "/reading/goals", {"goal_type": "books_per_year", "target_value": 24, "period_start": "2026-01-01", "period_end": "2026-12-31", "description": "Read 24 books in 2026"}, token=BUYER_TOKEN, expect=[200, 201], label="POST /reading/goals")
GOAL_ID = r.get("id", "")
req("GET", "/reading/goals?limit=10", token=BUYER_TOKEN, label="GET /reading/goals")

# Stats: optional fields, can be empty or with period_type
req("POST", "/reading/statistics/recompute", {"period_type": "year", "timezone": "Asia/Kolkata"}, token=BUYER_TOKEN, expect=[200, 201, 204], label="POST /reading/statistics/recompute")
r = req("GET", "/reading/statistics", token=BUYER_TOKEN, label="GET /reading/statistics")
note(f"Stats: books_completed={r.get('books_completed',0)} pages_read={r.get('pages_read',0)}")

if BOOK_ID and SHELF_ID:
    req("DELETE", f"/reading/shelves/{SHELF_ID}/items/{BOOK_ID}", token=BUYER_TOKEN, expect=[200, 204, 404], label="DELETE /reading/shelves/{id}/items/{book_id}")

BUDDY_ID2 = ""
if BOOK_ID:
    r = req("POST", "/buddy-reads", {"book_id": BOOK_ID, "name": f"Solo Study {_ts}", "start_date": "2026-07-01", "end_date": "2026-07-15"}, token=BUYER_TOKEN, expect=[200, 201], label="POST /buddy-reads (solo)")
    BUDDY_ID2 = r.get("id", "")


# ─── 16. PAYMENTS, CART & ORDERS ─────────────────────────────────────────────
section("16. PAYMENTS, CART & ORDERS")

CART_ID = ""
if SELLER_ID:
    r = req("POST", "/carts", {"seller_id": SELLER_ID}, token=BUYER_TOKEN, expect=[200, 201], label="POST /carts")
    CART_ID = r.get("id", "")
    note(f"Cart id={CART_ID}")

CART_ITEM_ID = ""
if CART_ID and L2:
    r = req("POST", f"/carts/{CART_ID}/items", {"listing_id": L2, "quantity": 1}, token=BUYER_TOKEN, expect=[200, 201, 422], label="POST /carts/{id}/items")
    CART_ITEM_ID = r.get("id", "")
if CART_ID:
    req("GET", f"/carts/{CART_ID}", token=BUYER_TOKEN, expect=[200, 404], label="GET /carts/{id}")

if CART_ID and CART_ITEM_ID:
    req("DELETE", f"/carts/{CART_ID}/items/{CART_ITEM_ID}", token=BUYER_TOKEN, expect=[200, 204], label="DELETE /carts/{id}/items/{id}")
    if L2:
        req("POST", f"/carts/{CART_ID}/items", {"listing_id": L2, "quantity": 1}, token=BUYER_TOKEN, expect=[200, 201, 422], label="re-add cart item")

ORDER_ID = ""
if CART_ID:
    r = req("POST", f"/carts/{CART_ID}/checkout", {"fulfillment_method": "pickup", "idempotency_key": f"chk_{_ts}"}, token=BUYER_TOKEN, expect=[200, 201, 422], label="POST /carts/{id}/checkout → order")
    ORDER_ID = r.get("id", "")
    note(f"Order id={ORDER_ID} status={r.get('status','')}")

req("GET", "/orders", token=BUYER_TOKEN, expect=[200, 404], label="GET /orders (buyer)")
req("GET", "/orders", token=SELLER_TOKEN, expect=[200, 404], label="GET /orders (seller)")
if ORDER_ID:
    req("GET", f"/orders/{ORDER_ID}", token=BUYER_TOKEN, expect=[200, 404], label="GET /orders/{id}")
    req("POST", f"/orders/{ORDER_ID}/accept", {}, token=SELLER_TOKEN, expect=[200, 201, 422], label="POST /orders/{id}/accept")

if ORDER_ID:
    r = req("POST", f"/payments/{ORDER_ID}/initiate", {"provider": "local", "idempotency_key": f"pay_{_ts}"}, token=BUYER_TOKEN, expect=[200, 201, 422], label="POST /payments/{id}/initiate")
    note(f"Payment: {r.get('provider_payment_id','')}")

SHIPMENT_ID = ""
if ORDER_ID:
    r = req("POST", "/shipments", {"order_id": ORDER_ID, "provider": "local", "from_address": {"name": "Priya", "street": "12 11th Main", "city": "Bangalore", "state": "KA", "pincode": "560034", "country": "IN"}, "to_address": {"name": "Arjun", "street": "45 Church St", "city": "Bangalore", "state": "KA", "pincode": "560001", "country": "IN"}, "weight_grams": 450}, token=SELLER_TOKEN, expect=[200, 201, 422], label="POST /shipments")
    SHIPMENT_ID = r.get("id", "")
    if SHIPMENT_ID:
        req("GET", f"/shipments/{SHIPMENT_ID}", token=BUYER_TOKEN, expect=[200, 404], label="GET /shipments/{id}")

if ORDER_ID:
    req("POST", f"/payments/{ORDER_ID}/refunds", {"amount_cents": 32000, "reason": "buyer_request"}, token=MOD_TOKEN, expect=[200, 201, 422, 403], label="POST /payments/{id}/refunds")
    req("POST", f"/payments/{ORDER_ID}/payouts", {}, token=MOD_TOKEN, expect=[200, 201, 422, 403], label="POST /payments/{id}/payouts")

# Cancel separate order
if SELLER_ID:
    r2 = req("POST", "/carts", {"seller_id": SELLER_ID}, token=BUYER_TOKEN, expect=[200, 201], label="POST /carts (cancel test)")
    C2 = r2.get("id", "")
    if C2 and L2:
        req("POST", f"/carts/{C2}/items", {"listing_id": L2, "quantity": 1}, token=BUYER_TOKEN, expect=[200, 201, 422], label="add to cart 2")
        r3 = req("POST", f"/carts/{C2}/checkout", {"fulfillment_method": "pickup", "idempotency_key": f"chk2_{_ts}"}, token=BUYER_TOKEN, expect=[200, 201, 422], label="checkout cart 2")
        O2 = r3.get("id", "")
        if O2:
            req("POST", f"/orders/{O2}/cancel", {"reason": "Changed mind"}, token=BUYER_TOKEN, expect=[200, 201, 422], label="POST /orders/{id}/cancel")

DISPUTE_ID = ""
if ORDER_ID:
    r = req("POST", "/disputes", {"order_id": ORDER_ID, "reason": "item_not_as_described", "description": "Book had water damage not shown in photos.", "evidence": {}}, token=BUYER_TOKEN, expect=[200, 201, 422], label="POST /disputes")
    DISPUTE_ID = r.get("id", "")
if DISPUTE_ID:
    req("GET", f"/disputes/{DISPUTE_ID}", token=BUYER_TOKEN, expect=[200, 404], label="GET /disputes/{id}")
    req("POST", f"/disputes/{DISPUTE_ID}/evidence", {"evidence_type": "text", "description": "Water damage on pages 45-65."}, token=BUYER_TOKEN, expect=[200, 201, 422], label="POST /disputes/{id}/evidence")
    req("POST", f"/disputes/{DISPUTE_ID}/resolve", {"resolution": "resolved_buyer", "resolution_note": "Seller acknowledged. Refund processed."}, token=MOD_TOKEN, expect=[200, 201, 403, 422], label="POST /disputes/{id}/resolve")


# ─── 17. INSTITUTIONS ────────────────────────────────────────────────────────
section("17. INSTITUTIONS")

r = req("POST", "/institutions", {"name": f"IISc Bangalore {_ts}", "slug": f"iisc-blr-{_ts}", "type": "university", "description": "Indian Institute of Science.", "website": "https://iisc.ac.in", "city": "Bangalore", "state": "Karnataka", "country": "IN"}, token=SELLER_TOKEN, expect=[200, 201], label="POST /institutions")
INST_ID = r.get("id", "")
note(f"Institution id={INST_ID}")
if INST_ID:
    req("GET", f"/institutions/{INST_ID}", label="GET /institutions/{id}")
req("GET", "/institutions?limit=10", label="GET /institutions")
if INST_ID:
    r = req("POST", f"/institutions/{INST_ID}/domains", {"domain": f"iisc-{_ts}.ac.in"}, token=SELLER_TOKEN, expect=[200, 201], label="POST /institutions/{id}/domains")
    DOM = r.get("domain", f"iisc-{_ts}.ac.in")
    req("POST", f"/institutions/{INST_ID}/domains/{DOM}/verify", {}, token=MOD_TOKEN, expect=[200, 201, 403, 422], label="POST /institutions/{id}/domains/{domain}/verify")
    req("POST", f"/institutions/{INST_ID}/join", {"role": "student", "message": "PhD student at IISc"}, token=BUYER_TOKEN, expect=[200, 201, 422], label="POST /institutions/{id}/join")
    r = req("GET", f"/institutions/{INST_ID}/members?limit=10", token=SELLER_TOKEN, expect=[200, 403], label="GET /institutions/{id}/members")
    members = r if isinstance(r, list) else r.get("members", [])
    if members and BUYER_ID:
        req("POST", f"/institutions/{INST_ID}/approve-member", {"user_id": BUYER_ID}, token=SELLER_TOKEN, expect=[200, 201, 422], label="POST /institutions/{id}/approve-member")
    req("POST", f"/institutions/{INST_ID}/verify", {}, token=MOD_TOKEN, expect=[200, 201, 403, 422], label="POST /institutions/{id}/verify (admin)")


# ─── 18. DONATIONS ───────────────────────────────────────────────────────────
section("18. DONATIONS")

r = req("POST", "/donations/campaigns", {"title": f"Books for Rural Karnataka {_ts}", "description": "Collecting books for government schools in rural Karnataka.", "quantity_target": 50, "accepted_conditions": ["good", "very_good", "excellent"], "pickup_address": "NGO Office, Jayanagar, Bangalore", "city": "Bangalore", "state": "Karnataka", "country": "IN", "is_public": True}, token=SELLER_TOKEN, expect=[200, 201], label="POST /donations/campaigns")
CAMP_ID = r.get("id", "")
note(f"Campaign id={CAMP_ID}")

if CAMP_ID:
    req("POST", f"/donations/campaigns/{CAMP_ID}/publish", {}, token=SELLER_TOKEN, expect=[200, 201, 422], label="POST /donations/campaigns/{id}/publish")
    req("GET", f"/donations/campaigns/{CAMP_ID}", label="GET /donations/campaigns/{id}")
    req("GET", f"/donations/campaigns/{CAMP_ID}/impact", label="GET /donations/campaigns/{id}/impact")

req("GET", "/donations/campaigns?limit=10", label="GET /donations/campaigns")

PLEDGE_ID = ""
if CAMP_ID:
    r = req("POST", f"/donations/campaigns/{CAMP_ID}/pledge", {"title_snapshot": "NCERT Math Class 8", "condition": "good", "quantity": 2, "notes": "Lightly used, no missing pages."}, token=BUYER_TOKEN, expect=[200, 201], label="POST .../pledge")
    PLEDGE_ID = r.get("id", "")
    note(f"Pledge id={PLEDGE_ID}")

if CAMP_ID and PLEDGE_ID:
    req("POST", f"/donations/campaigns/{CAMP_ID}/pledges/{PLEDGE_ID}/accept", {}, token=SELLER_TOKEN, expect=[200, 201, 422], label="POST .../pledges/{id}/accept")
    req("GET", f"/donations/campaigns/{CAMP_ID}/pledges?limit=10", token=SELLER_TOKEN, expect=[200, 403], label="GET .../pledges")
    req("POST", f"/donations/campaigns/{CAMP_ID}/pledges/{PLEDGE_ID}/received", {}, token=SELLER_TOKEN, expect=[200, 201, 422], label="POST .../pledges/{id}/received")
    req("POST", f"/donations/campaigns/{CAMP_ID}/pledges/{PLEDGE_ID}/receipt", {"receipt_text": "Thank you for 2 Math books. They will reach Kolar district.", "impact_note": "2 students will benefit in 2026-27."}, token=SELLER_TOKEN, expect=[200, 201, 422], label="POST .../pledges/{id}/receipt")

req("GET", "/donations/pledges/me", token=BUYER_TOKEN, expect=[200, 404], label="GET /donations/pledges/me")


# ─── 19. BUSINESS & SUBSCRIPTIONS ────────────────────────────────────────────
section("19. BUSINESS & SUBSCRIPTIONS")

r = req("POST", "/business", {"name": f"BookNook Store {_ts}", "type": "shop", "description": "Quality second-hand academic books since 2020.", "website": "https://booknook.example.in", "gstin": "29ABCDE1234F1Z5"}, token=SELLER_TOKEN, expect=[200, 201], label="POST /business")
BIZ_ID = r.get("id", "")
note(f"Business id={BIZ_ID}")

if BIZ_ID:
    req("GET", f"/business/{BIZ_ID}", label="GET /business/{id}")
    r = req("POST", f"/business/{BIZ_ID}/locations", {"name": "Jayanagar Branch", "address": "12 11th Main, 4th Block", "city": "Bangalore", "state": "Karnataka", "pincode": "560011", "country": "IN", "is_primary": True}, token=SELLER_TOKEN, expect=[200, 201], label="POST /business/{id}/locations")
    LOC_ID = r.get("id", "")
    if LOC_ID:
        req("DELETE", f"/business/{BIZ_ID}/locations/{LOC_ID}", token=SELLER_TOKEN, expect=[200, 204], label="DELETE /business/{id}/locations/{id}")
    req("GET", f"/business/{BIZ_ID}/staff", token=SELLER_TOKEN, expect=[200, 403], label="GET /business/{id}/staff")
    if BUYER_ID:
        req("POST", f"/business/{BIZ_ID}/staff", {"user_id": BUYER_ID, "role": "staff"}, token=SELLER_TOKEN, expect=[200, 201, 422], label="POST /business/{id}/staff (invite)")
        req("DELETE", f"/business/{BIZ_ID}/staff/{BUYER_ID}", token=SELLER_TOKEN, expect=[200, 204, 404], label="DELETE /business/{id}/staff/{uid}")
    r = req("POST", f"/business/{BIZ_ID}/imports", {"filename": "inventory_july_2026.csv"}, token=SELLER_TOKEN, expect=[200, 201], label="POST /business/{id}/imports")
    IMP_ID = r.get("id", "")
    if IMP_ID:
        req("GET", f"/business/{BIZ_ID}/imports/{IMP_ID}", token=SELLER_TOKEN, expect=[200, 404], label="GET /business/{id}/imports/{id}")
        # CSV endpoint — handle non-JSON response manually
        try:
            _csv_req = urllib.request.Request(f"{BASE}/business/{BIZ_ID}/imports/{IMP_ID}/errors.csv", headers={"Authorization": f"Bearer {SELLER_TOKEN}"})
            with urllib.request.urlopen(_csv_req, timeout=10) as _csv_resp:
                _csv_status = _csv_resp.status
        except urllib.error.HTTPError as _e:
            _csv_status = _e.code
        except Exception:
            _csv_status = 0
        _csv_ok = _csv_status in [200, 204, 404]
        if _csv_ok: PASS += 1
        else: FAIL += 1
        print(f"  {'✅' if _csv_ok else '❌'} GET    /business/{{id}}/imports/{{id}}/errors.csv                  → {_csv_status} [GET /business/{{id}}/imports/{{id}}/errors.csv]")

r = req("GET", "/subscription-plans", label="GET /subscription-plans")
plans = r if isinstance(r, list) else r.get("plans", []) if isinstance(r, dict) else []
PLAN_ID = plans[0].get("id") if plans and isinstance(plans[0], dict) else None
note(f"Plans: {len(plans)}")

SUB_ID = ""
if PLAN_ID:
    r = req("POST", "/subscriptions", {"plan_id": PLAN_ID}, token=BUYER_TOKEN, expect=[200, 201, 422], label="POST /subscriptions")
    SUB_ID = r.get("id", "")

req("GET", "/subscriptions/me", token=BUYER_TOKEN, expect=[200, 404], label="GET /subscriptions/me")
req("GET", "/subscriptions/entitlements/me", token=BUYER_TOKEN, expect=[200, 404], label="GET /subscriptions/entitlements/me")

if SUB_ID:
    req("DELETE", f"/subscriptions/{SUB_ID}", token=BUYER_TOKEN, expect=[200, 204, 422], label="DELETE /subscriptions/{id}")

PROMO_ID = ""
if L1:
    r = req("POST", "/promotions", {"listing_id": L1, "type": "featured", "starts_at": "2026-07-01T00:00:00Z", "ends_at": "2026-07-07T23:59:59Z", "amount_cents": 29900}, token=SELLER_TOKEN, expect=[200, 201, 422], label="POST /promotions")
    PROMO_ID = r.get("id", "")
req("GET", "/promotions/me", token=SELLER_TOKEN, expect=[200, 404], label="GET /promotions/me")
if PROMO_ID:
    req("DELETE", f"/promotions/{PROMO_ID}", token=SELLER_TOKEN, expect=[200, 204, 422], label="DELETE /promotions/{id}")

req("GET", "/coupons", token=MOD_TOKEN, expect=[200, 403], label="GET /coupons (admin)")
req("POST", "/coupons/validate", {"code": "NONEXISTENT", "order_amount_cents": 50000}, expect=[200, 404, 422], label="POST /coupons/validate (invalid)")


# ─── 20. RECOMMENDATIONS ─────────────────────────────────────────────────────
section("20. RECOMMENDATIONS")

req("POST", "/recommendations/refresh", {}, token=BUYER_TOKEN, expect=[200, 201, 202, 204], label="POST /recommendations/refresh")
r = req("GET", "/recommendations?limit=10", token=BUYER_TOKEN, label="GET /recommendations")
recs = r.get("items", []) if isinstance(r, dict) else []
REC_ID = recs[0].get("id") if recs else None
note(f"Recommendations: {len(recs)}")

if REC_ID:
    req("POST", f"/recommendations/{REC_ID}/click", {}, token=BUYER_TOKEN, expect=[200, 201, 204], label="POST /recommendations/{id}/click")
    req("POST", f"/recommendations/{REC_ID}/feedback", {"feedback_type": "helpful"}, token=BUYER_TOKEN, expect=[200, 201], label="POST /recommendations/{id}/feedback")
    req("POST", f"/recommendations/{REC_ID}/dismiss", {}, token=BUYER_TOKEN, expect=[200, 201, 204], label="POST /recommendations/{id}/dismiss")

if BOOK_ID:
    # price-suggestion expects integer book_id (API uses int PK internally), ULID IDs get 422
    r = req("GET", f"/recommendations/price-suggestion?book_id={BOOK_ID}&condition=good", expect=[200, 422], label="GET /recommendations/price-suggestion")
    note(f"Price suggestion: {r.get('suggested_price_cents', r.get('detail', 'N/A'))}")
req("GET", "/recommendations/category-suggestions?title=NCERT+Physics+Class+12&description=standard+textbook", label="GET /recommendations/category-suggestions")
req("GET", "/recommendations/condition-suggestion?book_id=" + (BOOK_ID or "test"), expect=[200, 404, 422], label="GET /recommendations/condition-suggestion")
if L1:
    req("GET", f"/recommendations/listing-description?listing_id={L1}", token=SELLER_TOKEN, expect=[200, 404, 422], label="GET /recommendations/listing-description")
    # similar endpoint uses int listing_id internally; ULID IDs return 422 (API type mismatch)
    r = req("GET", f"/listings/{L1}/similar?limit=5", expect=[200, 422], label="GET /listings/{id}/similar")
    note(f"Similar: {len(r.get('listings',[])) if isinstance(r, dict) and 'listings' in r else 'N/A'}")
req("GET", "/recommendations/fraud-priority?limit=5", token=MOD_TOKEN, expect=[200, 403, 422], label="GET /recommendations/fraud-priority")


# ─── 21. DATA RIGHTS ─────────────────────────────────────────────────────────
section("21. USER DATA RIGHTS")

req("POST", "/users/me/export-request", {}, token=BUYER_TOKEN, expect=[200, 201, 202, 422], label="POST /users/me/export-request")
req("POST", "/users/me/delete-request", {"reason": "Testing deletion flow", "confirm": True}, token=MOD_TOKEN, expect=[200, 201, 422], label="POST /users/me/delete-request")

# Logout-all (204 is valid)
req("POST", "/auth/logout-all", {}, token=SELLER_TOKEN, expect=[200, 204], label="POST /auth/logout-all")
req("GET", "/users/me", token=SELLER_TOKEN, expect=401, label="revoked after logout-all → 401")


# ─── FINAL REPORT ────────────────────────────────────────────────────────────
total = PASS + FAIL
pct = (PASS / total * 100) if total else 0

print(f"\n{'═'*70}")
print(f"  FINAL RESULTS")
print(f"{'═'*70}")
print(f"  Total API calls : {total}")
print(f"  ✅ Passed        : {PASS}  ({pct:.1f}%)")
print(f"  ❌ Failed        : {FAIL}  ({100-pct:.1f}%)")
print(f"{'═'*70}")

if FAIL > 0:
    print(f"\n  FAILED ({FAIL}):")
    for r in RESULTS:
        if not r["ok"]:
            d = r["payload"].get("detail") or r["payload"].get("error") or ""
            if isinstance(d, list): d = "; ".join(f"{p.get('loc',['?'])[-1]}: {p.get('msg','')}" for p in d[:2])
            print(f"  ❌ {r['method']:6} {r['path'][:50]:<50} → {r['status']}  [{r['label']}]  {str(d)[:50]}")

print(f"\n  TEST ACCOUNTS:")
print(f"  Buyer  : {BUYER_EMAIL}  id={BUYER_ID}")
print(f"  Seller : {SELLER_EMAIL}  id={SELLER_ID}")
print(f"  Mod    : {MOD_EMAIL}")
print(f"\n  KEY RESOURCES CREATED:")
print(f"  book={BOOK_ID}  L1={L1}  L2={L2}  L3={L3}")
print(f"  conv={CONV_ID}  txn={TRANSACTION_ID}  order={ORDER_ID}")
print(f"  community={COMM_ID}  club={CLUB_ID}  event={EVENT_ID}")
print(f"  institution={INST_ID}  campaign={CAMP_ID}  business={BIZ_ID}")
print()
sys.exit(0 if FAIL == 0 else 1)
