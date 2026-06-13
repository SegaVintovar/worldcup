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
	$(PSQL) -c "SELECT * FROM users LIMIT 20;"

show-matches:
	$(PSQL) -c "SELECT * FROM matches ORDER BY match_date LIMIT 20;"

show-predictions:
	$(PSQL) -c "SELECT * FROM predictions LIMIT 20;"

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
	@echo "Waiting for DB to be ready..."
	@sleep 3
	docker compose up -d predictor_app