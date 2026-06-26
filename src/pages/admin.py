# from nicegui import ui, app
# # from pathlib import Path
# # from src.services.match_calender import build_match_calendar
# # from src.services.login_info import login_info
# from src.services.database import SessionLocal, Match
# from src.services.header import header
# from src.assets import theme


# def admin_page():
#     header("/admin")
#     ui.query('.nicegui-content').style(f'background-color: {theme.BG}')
#     db = SessionLocal()

#     predictions = db.query(Match).filter(Match.)




"""Admin page — view and manually edit all matches in the database."""

from nicegui import ui
from src.services.database import SessionLocal, Match
from src.services.scoring import update_prediction_scores, update_user_scores
from src.services.header import header
from src.assets import theme
from src.services.prediction_components import AMSTERDAM


def admin_page():
    header("/admin")
    ui.query(".nicegui-content").style(f"background-color: {theme.BG}")

    ui.label("⚙️ Admin — Match Editor").classes("text-3xl font-bold mb-4").style(
        f"color: {theme.INK}; font-weight: 600;"
    )

    # ── State ────────────────────────────────────────────────────────────────
    selected = {"match": None}  # currently open match in the edit form

    # ── Layout: match list (left) + edit form (right) ────────────────────────
    with ui.row().classes("w-full gap-4 items-start"):

        # ── Match list ───────────────────────────────────────────────────────
        with ui.card().classes("flex-1 p-4"):
            ui.label("All Matches").classes("text-xl font-bold mb-2").style(
                f"color: {theme.INK};"
            )

            match_list = ui.column().classes("w-full gap-1")

            def render_match_list():
                match_list.clear()
                db = SessionLocal()
                try:
                    matches = db.query(Match).filter(Match.phase == "Knockout Phase").order_by(Match.match_date).all()
                finally:
                    db.close()

                for m in matches:
                    is_selected = selected["match"] and selected["match"].id == m.id

                    kickoff = (
                        m.match_date.astimezone(AMSTERDAM).strftime("%d %b %H:%M")
                        if m.match_date
                        else "—"
                    )
                    score_str = (
                        f"  {m.home_score}–{m.away_score}" if m.played else ""
                    )
                    label = f"{m.home_team} vs {m.away_team}{score_str}  ·  {kickoff}  ·  {m.stage or m.phase}"

                    def make_select(match_id):
                        def handler():
                            db2 = SessionLocal()
                            try:
                                fresh = db2.query(Match).filter_by(id=match_id).first()
                                selected["match"] = fresh
                            finally:
                                db2.close()
                            render_edit_form()
                            # render_match_list()  # re-render to update highlight
                        return handler

                    btn = ui.button(label, on_click=make_select(m.id)).classes(
                        "w-full text-left"
                    )
                    btn.props("flat dense align=left")
                    if is_selected:
                        btn.style(
                            f"background-color: {theme.GREEN}; color: white; border-radius: {theme.RADIUS};"
                        )
                    elif m.played:
                        btn.style(f"color: {theme.INK_MUTED};")
                    else:
                        btn.style(f"color: {theme.INK};")

            render_match_list()

        # ── Edit form ────────────────────────────────────────────────────────
        with ui.card().classes("p-4").style("min-width: 320px;"):
            edit_area = ui.column().classes("w-full gap-3")

            def render_edit_form():
                edit_area.clear()
                m = selected["match"]

                with edit_area:
                    if m is None:
                        ui.label("← Select a match to edit").style(
                            f"color: {theme.INK_MUTED};"
                        )
                        return

                    ui.label("Edit Match").classes("text-xl font-bold").style(
                        f"color: {theme.INK}; font-weight: 600;"
                    )
                    ui.label(
                        m.match_date.astimezone(AMSTERDAM).strftime("%d %b %Y  %H:%M")
                        if m.match_date else "—"
                    ).style(f"color: {theme.INK_MUTED}; font-size: 0.85rem;")

                    ui.separator()

                    # Team names
                    ui.label("Teams").classes("text-sm font-semibold").style(
                        f"color: {theme.INK};"
                    )
                    home_input = ui.input("Home team", value=m.home_team).classes("w-full")
                    away_input = ui.input("Away team", value=m.away_team).classes("w-full")

                    ui.separator()

                    # Score
                    ui.label("Score  (leave blank if not played)").classes(
                        "text-sm font-semibold"
                    ).style(f"color: {theme.INK};")

                    with ui.row().classes("items-center gap-3"):
                        home_score = ui.number(
                            "Home",
                            value=m.home_score,
                            min=0,
                            max=99,
                        ).classes("w-24")
                        ui.label("–").style(f"color: {theme.INK}; font-weight: 600;")
                        away_score = ui.number(
                            "Away",
                            value=m.away_score,
                            min=0,
                            max=99,
                        ).classes("w-24")

                    # Winner override (penalties)
                    ui.label("Winner  (only for penalty shootouts)").classes(
                        "text-sm font-semibold"
                    ).style(f"color: {theme.INK};")

                    winner_options = ["—", m.home_team, m.away_team]
                    current_winner = m.winner if m.winner in winner_options else "—"
                    winner_select = ui.select(
                        winner_options,
                        value=current_winner,
                        label="Winner after extra time / penalties",
                    ).classes("w-full")

                    played_toggle = ui.checkbox(
                        "Mark as played / finished", value=m.played
                    )

                    ui.separator()

                    # ── Save button ───────────────────────────────────────────
                    def on_save():
                        db = SessionLocal()
                        try:
                            match = db.query(Match).filter_by(id=m.id).first()
                            if not match:
                                ui.notify("Match not found.", color="negative")
                                return

                            match.home_team = home_input.value.strip() or match.home_team
                            match.away_team = away_input.value.strip() or match.away_team

                            h = home_score.value
                            a = away_score.value
                            if h is not None and a is not None:
                                match.home_score = int(h)
                                match.away_score = int(a)

                            raw_winner = winner_select.value
                            match.winner = None if raw_winner == "—" else raw_winner
                            match.played = played_toggle.value

                            db.commit()

                            # refresh selected match so form stays up to date
                            db.refresh(match)
                            selected["match"] = match

                        finally:
                            db.close()

                        ui.notify("Match saved!", color="positive")
                        render_match_list()
                        render_edit_form()

                    # ── Recalculate scores button ─────────────────────────────
                    def on_recalc():
                        update_prediction_scores()
                        update_user_scores()
                        ui.notify("Scores recalculated!", color="positive")

                    with ui.row().classes("w-full gap-2 mt-2"):
                        ui.button("Save", on_click=on_save).classes(
                            "flex-1 text-white"
                        ).style(f"background-color: {theme.GREEN};")
                        ui.button(
                            "Recalc scores", on_click=on_recalc
                        ).props("flat").style(f"color: {theme.BROWN};")

            render_edit_form()