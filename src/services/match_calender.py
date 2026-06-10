from src.services.database import SessionLocal, Match

from nicegui import ui


def build_match_calendar():
    upcoming, finished = get_split_matches()

    with ui.row().classes('w-full gap-8'):

        # Upcoming matches
        with ui.column().classes('w-1/2'):
            ui.label('📅 Upcoming Matches').classes('text-xl font-bold')

            for match in upcoming:
                with ui.card().classes('w-full'):
                    ui.label(
                        f'{match.home_team} vs {match.away_team}'
                    ).classes('font-semibold')

                    ui.label(
                        match.match_date.strftime('%d %b %Y %H:%M')
                    )

                    if match.stage:
                        ui.label(match.stage)

        # Finished matches
        with ui.column().classes('w-1/2'):
            ui.label('✅ Finished Matches').classes('text-xl font-bold')

            for match in finished:
                with ui.card().classes('w-full'):
                    ui.label(
                        f'{match.home_team} {match.home_score} - {match.away_score} {match.away_team}'
                    ).classes('font-semibold')

                    ui.label(
                        match.match_date.strftime('%d %b %Y %H:%M')
                    )

                    if match.winner:
                        ui.label(f'Winner: {match.winner}')


def get_split_matches() -> tuple[list[Match], list[Match]]:
    db = SessionLocal()

    try:
        upcoming_matches: list[Match] = (
            db.query(Match)
            .filter(Match.played == False)
            .order_by(Match.match_date)
            .all()
        )

        finished_matches: list[Match] = (
            db.query(Match)
            .filter(Match.played == True)
            .order_by(Match.match_date.desc())
            .all()
        )

        return upcoming_matches, finished_matches

    finally:
        db.close()