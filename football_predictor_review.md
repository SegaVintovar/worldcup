# Football Predictor App — Code & Security Review

## Executive Summary

The app is well-structured for an internal/campus tool built with NiceGUI + PostgreSQL + Docker. The OAuth flow, DB schema, and infra separation are solid. However, there are several issues ranging from **critical** (secrets committed to the repo) to **moderate** (debug flags left on, no rate limiting) and **low** (UX edge cases). Each finding below includes a concrete fix.

---

## 🔴 Critical

### 1. Real credentials committed to the `.env` file

**File:** `.env`

The `.env` file contains live OAuth credentials and the app secret key and was included in the ZIP (and presumably the Git repo):

```
OAUTH_CLIENT_ID=u-s4t2ud-783e8d896cf18...
OAUTH_CLIENT_SECRET=s-s4t2ud-cd0e7022083cf...
APP_SECRET_KEY=5ac8e859a3f08ff666...
```

The `.gitignore` does list `.env`, but the file was still tracked (it exists in the Git object store). Anyone with repo access can extract it with `git log -p`.

**Fix:**

1. Revoke and regenerate the 42 OAuth client secret and app secret key immediately.
2. Verify `.env` is not in any commit: `git log --all --full-history -- .env`
3. If it appears, purge it: `git filter-repo --path .env --invert-paths`
4. Keep only `.env_example` in the repo. Never commit `.env`.

---

### 2. No OAuth `state` parameter (CSRF on login)

**File:** `src/services/auth.py` → `get_login_url()`

The OAuth authorize URL is built without a `state` parameter:

```python
return (
    f"{AUTHORIZE_URL}"
    f"?client_id={OAUTH_CLIENT_ID}"
    f"&redirect_uri={OAUTH_REDIRECT_URI}"
    f"&response_type=code"
    # ← no &state=...
)
```

An attacker can craft a malicious link to `/auth/callback?code=...` and trick a victim's browser into authenticating as the attacker's 42 account (login CSRF).

**Fix:**

```python
import secrets

def get_login_url() -> str:
    state = secrets.token_urlsafe(32)
    app.storage.user["oauth_state"] = state   # store in session
    return (
        f"{AUTHORIZE_URL}"
        f"?client_id={OAUTH_CLIENT_ID}"
        f"&redirect_uri={OAUTH_REDIRECT_URI}"
        f"&response_type=code"
        f"&state={state}"
    )
```

Then in the callback, verify before using the code:

```python
@app.get("/auth/callback")
async def oauth_callback(request: Request):
    state = request.query_params.get("state")
    if not state or state != app.storage.user.get("oauth_state"):
        return RedirectResponse("/?error=csrf")
    app.storage.user.pop("oauth_state", None)
    # ... rest of flow
```

---

## 🟠 High

### 3. `PREDICTION_LIMITS = False` — predictions bypass deadline enforcement

**File:** `src/services/prediction_search.py`, line 9

```python
PREDICTION_LIMITS = False  # False = allow late predictions (debug/admin mode)
```

This is a module-level constant that disables kickoff enforcement globally. Users can currently submit or change predictions after a match has started or even after it has finished. The comment acknowledges this is "debug/admin mode" but it was shipped this way.

**Fix:**

Remove the flag entirely and enforce the rule unconditionally:

```python
def get_matches_without_predictions(current_user, matches):
    db = SessionLocal()
    now = datetime.now(AMSTERDAM)
    try:
        available = []
        for match in matches:
            if match.played:
                continue
            if match.match_date.astimezone(AMSTERDAM) <= now:
                continue
            prediction = db.query(Prediction).filter(
                Prediction.user_id == current_user.id,
                Prediction.match_id == match.id,
            ).first()
            if prediction is None:
                available.append(match)
        return available
    finally:
        db.close()
```

Do the same in `get_upcoming_predictions` — remove the `if PREDICTION_LIMITS` guard around `.filter(Match.played == False)`.

---

### 4. No rate limiting on the OAuth callback or prediction endpoints

**Files:** `main.py`, `nginx/conf.d/default.conf`

There is no rate limiting anywhere. An attacker can:
- Brute-force OAuth codes against `/auth/callback`
- Submit thousands of predictions per second (the `save_prediction` function opens a new DB session per call)

**Fix — add Nginx rate limiting:**

```nginx
# In nginx.conf or conf.d/default.conf, add at the http block level:
limit_req_zone $binary_remote_addr zone=auth:10m rate=5r/m;
limit_req_zone $binary_remote_addr zone=api:10m  rate=30r/m;

# In the server block:
location /auth/callback {
    limit_req zone=auth burst=3 nodelay;
    proxy_pass http://nicegui_app;
}

location / {
    limit_req zone=api burst=10 nodelay;
    proxy_pass http://nicegui_app;
}
```

---

### 5. Unhandled exception silently swallows OAuth errors

**File:** `main.py`, `oauth_callback()`

```python
try:
    profile = await exchange_code_for_user(code)
except Exception as e:
    return RedirectResponse("/")   # ← user sees nothing, error is lost
```

Any failure (network error, invalid token, 42 API down) silently redirects to `/`. Users get no feedback and you get no visibility into errors.

**Fix:**

```python
except Exception as e:
    logger.error("OAuth exchange failed: %s", e, exc_info=True)
    return RedirectResponse("/?error=login_failed")
```

Then on the login page, display a toast if `?error=login_failed` is in the query string.

---

## 🟡 Moderate

### 6. Scheduler runs every 10 minutes, not at 03:00 as the comment claims

**File:** `main.py`

```python
# Schedule daily sync at 03:00, scoring at 03:30 (Amsterdam time)
scheduler.add_job(daily_sync, "cron", minute="*/10", timezone="Europe/Amsterdam")
```

The comment says daily at 03:00, but the cron expression fires every 10 minutes all day. This hammers the external `openfootball` GitHub URL 144 times per day instead of once, and reloads all connected clients every 10 minutes.

**Fix** — decide what you actually want:

```python
# Every 10 minutes (during the tournament this is fine, but label it correctly):
scheduler.add_job(daily_sync, "cron", minute="*/10", timezone="Europe/Amsterdam")

# OR truly daily at 03:00:
scheduler.add_job(daily_sync, "cron", hour=3, minute=0, timezone="Europe/Amsterdam")
```

Also consider not calling `ui.navigate.reload()` on all clients during night syncs — it interrupts active users.

---

### 7. DB session left open if `db.close()` is never called in `login_info`

**File:** `src/services/login_info.py`

```python
def login_info(user: User):
    db = SessionLocal()
    prd = db.query(...).all()
    # ... build UI ...
    db.close()   # ← only called at the very end; if an exception occurs mid-function, session leaks
```

**Fix:** use a `try/finally` block like every other service does:

```python
def login_info(user: User):
    db = SessionLocal()
    try:
        prd = db.query(Prediction)\
            .filter(Prediction.user_id == user.id)\
            .order_by(Prediction.id.desc())\
            .limit(5).all()
        # build UI
    finally:
        db.close()
```

---

### 8. `source_id` collision risk for matches on the same day

**File:** `src/results/football_api.py`

```python
"source_id": f"{home}_vs_{away}_{date}".replace(" ", "_").lower()
```

If the same two teams play twice on the same day (e.g., group stage rescheduling), or if team names contain special characters, this ID collides or becomes inconsistent. The openfootball JSON already provides a unique match `id` field.

**Fix:**

```python
"source_id": str(m.get("id")) if m.get("id") else f"{home}_vs_{away}_{date}".replace(" ", "_").lower()
```

---

### 9. No HTTPS — running on plain HTTP port 8000

**Files:** `docker-compose.yml`, `nginx/conf.d/default.conf`

The Nginx config only listens on port 80 (mapped to 8000). All traffic, including session cookies, is sent in cleartext.

**Fix:** add a TLS termination layer. Since there is already an `ssl_cert.txt` placeholder in the repo, the intent was there. Options:

- Add a Certbot/Let's Encrypt sidecar to the compose file
- Terminate TLS at a reverse proxy or load balancer in front of this stack
- At minimum, set the session cookie `Secure` flag (NiceGUI: `storage_secret` sessions use Starlette — configure `SessionMiddleware` with `https_only=True` when behind TLS)

---

### 10. Avatar URL from 42 API is rendered without sanitization

**File:** `src/services/login_info.py`

```python
avatar = user.avatar_url or '/assets/image.png'
ui.image(avatar)
```

The `avatar_url` value comes directly from the 42 API and is stored as-is in the database. If the URL were ever tampered with (e.g., via a compromised 42 profile or DB injection), it could point to arbitrary external content. NiceGUI renders `<img src="...">` directly.

**Fix:** validate that the URL is an `https://` URL from a trusted domain before using it:

```python
from urllib.parse import urlparse

TRUSTED_AVATAR_HOSTS = {"cdn.intra.42.fr", "avatars.githubusercontent.com"}

def safe_avatar(url: str | None) -> str:
    if not url:
        return "/assets/image.png"
    try:
        parsed = urlparse(url)
        if parsed.scheme == "https" and parsed.hostname in TRUSTED_AVATAR_HOSTS:
            return url
    except Exception:
        pass
    return "/assets/image.png"
```

---

## 🟢 Low / Quality

### 11. `get_current_user()` opens a DB session and never closes it on the error path

**File:** `main.py`

```python
def get_current_user() -> User | None:
    user_id = app.storage.user.get("user_id")
    if not user_id:
        return None          # ← no session opened, fine
    db = SessionLocal()
    try:
        return db.query(User).filter_by(id=user_id).first()
    finally:
        db.close()           # ← this is correct, no issue here
```

This is actually fine — just make sure it stays this way as the function grows.

### 12. Finished matches are capped at 5 in the predictions view

**File:** `src/services/prediction_search.py`

```python
.limit(5)
```

Both `get_finished_matches_with_predictions` and `get_upcoming_predictions` hard-cap at 5 results. As the tournament progresses users won't be able to see most of their history. Consider adding pagination or raising the limit (or making it configurable).

### 13. Score comments say "5 points / 3 points" but code gives 3 / 1

**File:** `src/services/scoring.py`

The docstring at the top says:
```
- Exact score:          5 points
- Correct goal diff:    3 points
- Correct winner only:  1 point
```
But the actual code gives 3 for exact and 1 for correct winner (goal diff isn't even implemented). The rules card in the UI shows the correct 3/1 values. Remove or update the misleading docstring.

### 14. Available matches grid is capped at 9 with no indication

**File:** `src/pages/predictions.py`

```python
for match in pred_available[:9]:
```

If there are more than 9 available matches the user sees no indication that more exist. Add a "show more" button or a note like "Showing 9 of N matches — use search to find others."

---

## Summary Table

| # | Severity | Issue | File |
|---|----------|-------|------|
| 1 | 🔴 Critical | Live credentials in committed `.env` | `.env` / `.git` |
| 2 | 🔴 Critical | No OAuth `state` param (CSRF) | `auth.py` |
| 3 | 🟠 High | `PREDICTION_LIMITS = False` in production | `prediction_search.py` |
| 4 | 🟠 High | No rate limiting on any endpoint | `nginx/conf.d/default.conf` |
| 5 | 🟠 High | Silent exception swallow on OAuth error | `main.py` |
| 6 | 🟡 Moderate | Scheduler runs every 10 min, not daily | `main.py` |
| 7 | 🟡 Moderate | DB session leak in `login_info` | `login_info.py` |
| 8 | 🟡 Moderate | `source_id` collision risk | `football_api.py` |
| 9 | 🟡 Moderate | No HTTPS / TLS | `docker-compose.yml` |
| 10 | 🟡 Moderate | Unsanitized external avatar URL | `login_info.py` |
| 11 | 🟢 Low | Misleading scoring docstring | `scoring.py` |
| 12 | 🟢 Low | History capped at 5 rows | `prediction_search.py` |
| 13 | 🟢 Low | Available matches grid capped at 9, no notice | `predictions.py` |
