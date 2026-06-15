from src.services.database import SessionLocal, Match

from nicegui import ui

from zoneinfo import ZoneInfo
AMSTERDAM = ZoneInfo("Europe/Amsterdam")

def build_match_calendar():
    upcoming, finished = get_split_matches()

    with ui.row().classes('w-full gap-6 items-start'):

        # Upcoming matches
        with ui.column().classes('flex-1 gap-2'):
            ui.label('📅 Upcoming Matches').classes('text-xl font-bold')

            if upcoming:
                for match in upcoming[:5]:
                    with ui.card().classes('w-full bg-green-50 border-l-4 border-green-400 py-1'):
                        with ui.column().classes('gap-0'):

                            ui.label(
                                f'{match.home_team} vs {match.away_team}'
                            ).classes('font-semibold text-sm m-0 leading-tight')

                            ui.label(
                                match.match_date.astimezone(AMSTERDAM).strftime('%d %b %Y %H:%M')
                            ).classes('text-xs text-gray-600 m-0 leading-tight')

                            if match.stage:
                                ui.label(match.stage).classes('text-xs text-gray-400 m-0 leading-tight')

            else:
                ui.label('No upcoming matches').classes('text-gray-500 italic')

        # Finished matches
        with ui.column().classes('flex-1 gap-2'):
            ui.label('✅ Finished Matches').classes('text-xl font-bold')

            if finished:
                for match in finished[:5]:
                    with ui.card().classes('w-full bg-red-50 border-l-4 border-red-400 py-1'):
                        with ui.column().classes('gap-0'):

                            ui.label(
                                f'{match.home_team} {match.home_score} - {match.away_score} {match.away_team}'
                            ).classes('font-semibold text-sm m-0 leading-tight')

                            ui.label(
                                match.match_date.astimezone(AMSTERDAM).strftime('%d %b %Y %H:%M')
                            ).classes('text-xs text-gray-600 m-0 leading-tight')

                            if match.winner:
                                ui.label(f'Winner: {match.winner}') \
                                    .classes('text-xs text-gray-400 m-0 leading-tight')
                            elif match.stage:
                                ui.label(match.stage).classes('text-xs text-gray-400 m-0 leading-tight')
            else:
                ui.label('No finished matches yet').classes('text-gray-500 italic')


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