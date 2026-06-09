# ⚽ Football Predictor

## Architecture

```
Internet
   │
[nginx :80]              ← reverse proxy + WebSocket upgrade
   │  HTTP + WS
[NiceGUI/FastAPI :8080]  ← UI + business logic
   │
[PostgreSQL :5432]       ← users, matches, predictions
```

## Quick Start

```bash
cp .env.example .env
# Add your 42 OAuth credentials (see below)

docker compose up --build
# Visit http://localhost
```

## 42 OAuth Setup
1. Go to https://profile.intra.42.fr/oauth/applications
2. Create app, set redirect URI: http://localhost/auth/callback
3. Paste Client ID + Secret into .env

## Production
1. Update .env with strong passwords and your domain
2. Change server_name in nginx/conf.d/default.conf
3. Add HTTPS via Certbot
4. docker compose up -d --build

## Scoring Rules
| Result            | Points |
|-------------------|--------|
| Exact score       | 5 pts  |
| Correct goal diff | 3 pts  |
| Correct winner    | 1 pt   |
| Wrong             | 0 pts  |
