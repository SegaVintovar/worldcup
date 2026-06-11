PSQL = docker exec -it predictor_db psql \
	-U $$(grep POSTGRES_USER .env | cut -d= -f2) \
	-d $$(grep POSTGRES_DB .env | cut -d= -f2)

run:
	@if [ ! -d ".venv" ]; then \
		echo "No .venv found, creating..."; \
		python3 -m venv .venv; \
	fi
	docker compose up --build

# ── Show tables ─────────────────────────────────────────────────────────────

show-users:
	$(PSQL) -c "SELECT id, login_42, avatar_url, p_score, created_at FROM users;"

show-matches:
	$(PSQL) -c "SELECT id, home_team, away_team, match_date, stage, played, home_score, away_score FROM matches ORDER BY match_date LIMIT 30;"

show-predictions:
	$(PSQL) -c "SELECT p.id, u.login_42, m.home_team, m.away_team, p.pred_home_score, p.pred_away_score, p.points_earned FROM predictions p JOIN users u ON p.user_id = u.id JOIN matches m ON p.match_id = m.id;"

show-db: show-users show-matches show-predictions

# ── Reset tables ─────────────────────────────────────────────────────────────

reset-users:
	$(PSQL) -c "TRUNCATE users CASCADE;"

reset-matches:
	$(PSQL) -c "TRUNCATE matches CASCADE;"

reset-predictions:
	$(PSQL) -c "TRUNCATE predictions CASCADE;"

reset-db:
	docker compose down -v
	docker compose up -d db