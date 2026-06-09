run:
	@if [ ! -d ".venv" ]; then \
		echo "No .venv found, creating..."; \
		python3 -m venv .venv; \
	fi
	docker compose up --build

show-db:
	docker exec -it predictor_db psql -U $$(grep POSTGRES_USER .env | cut -d= -f2) -d $$(grep POSTGRES_DB .env | cut -d= -f2) -c "\dt" 
	docker exec -it predictor_db psql -U $$(grep POSTGRES_USER .env | cut -d= -f2) -d $$(grep POSTGRES_DB .env | cut -d= -f2) -c "SELECT id, home_team, away_team, match_date, played FROM matches LIMIT 20;"

reset-db:
	docker compose down -v
	docker compose up -d db