from nicegui import ui
from src.assets import theme
from src.services.prediction_components import AMSTERDAM
from collections import defaultdict
from src.services.database import SessionLocal, User, Match, Prediction
from src.services.export import export_pivot_to_xlsx


def add_export_button():
    async def on_export():
        path = export_pivot_to_xlsx("/tmp/wc_predictions.xlsx")
        ui.download(path, "wc_predictions.xlsx")
        ui.notify("Excel file ready!", color="positive")

    ui.button("⬇ Export to Excel", on_click=on_export).style(
        f"background-color: {theme.GREEN}; color: white;"
    )


def get_pivot_data():
    db = SessionLocal()
    try:
        matches = db.query(
            Match).filter(
                Match.phase == "Knockout Phase").order_by(
                    Match.match_date).all()
        users = db.query(User).order_by(User.login_42).all()
        preds = db.query(Prediction).all()
    finally:
        db.close()

    # { (user_id, match_id) -> Prediction }
    pred_map = {(p.user_id, p.match_id): p for p in preds}

    rows = []
    for user in users:
        row = {"login": user.login_42, "total": user.p_score, "cells": []}
        for match in matches:
            p = pred_map.get((user.id, match.id))
            if p:
                row["cells"].append({
                    "pred":   f"{p.pred_home_score}–{p.pred_away_score}",
                    "points": p.points_earned,
                    "done":   True,
                })
            else:
                row["cells"].append({"done": False})
        rows.append(row)

    return matches, rows


def pivot_page():
    matches, rows = get_pivot_data()

    # Scrollable container — table can be very wide
    with ui.scroll_area().classes("w-full"):
        with ui.element("table").style(
            f"border-collapse: collapse; font-size: 0.78rem; color: {theme.INK};"
        ):
            # ── Header row ───────────────────────────────────────────────────
            with ui.element("thead"):
                with ui.element("tr"):
                    # Sticky first column
                    ui.element("th").style(
                        f"position: sticky; left: 0; background: {theme.INK}; "
                        f"color: white; padding: 6px 10px; text-align: left; z-index: 2;"
                    ).text = "User"
                    ui.element("th").style(
                        f"background: {theme.INK}; color: white; padding: 6px 10px;"
                    ).text = "Total"
                    # for m in matches:
                    #     kickoff = (
                    #         m.match_date.astimezone(AMSTERDAM).strftime("%d/%m %H:%M")
                    #         if m.match_date else "—"
                    #     )
                    #     label = f"{m.home_team[:3].upper()} v {m.away_team[:3].upper()}\n{kickoff}"
                    #     th = ui.element("th").style(
                    #         f"background: {theme.INK}; color: white; padding: 4px 6px; "
                    #         f"text-align: center; white-space: pre; min-width: 72px;"
                    #     )
                    #     th.text = label
                    headers = ["User", "Total pts"]
                    for m in matches:
                        kickoff = (
                            m.match_date.astimezone(AMSTERDAM).strftime("%d/%m %H:%M")
                            if m.match_date else "—"
                        )
                        if m.played and m.home_score is not None:
                            result = f"{m.home_score}–{m.away_score}"
                            if m.winner:
                                result += f" (p. {m.winner[:3].upper()})"
                        else:
                            result = "upcoming"

                        headers.append(
                            f"{result}\n{m.home_team[:3].upper()} v {m.away_team[:3].upper()}\n{kickoff}\n{m.stage or ''}"
                        )

            # ── Body rows ────────────────────────────────────────────────────
            with ui.element("tbody"):
                for i, row in enumerate(rows):
                    bg = theme.CARD_BG if i % 2 == 0 else theme.BG
                    with ui.element("tr").style(f"background: {bg};"):
                        # login — sticky
                        ui.element("td").style(
                            f"position: sticky; left: 0; background: {bg}; "
                            f"padding: 5px 10px; font-weight: 600; z-index: 1;"
                        ).text = row["login"]
                        # total points
                        ui.element("td").style(
                            f"padding: 5px 10px; text-align: center; "
                            f"font-weight: 700; color: {theme.GREEN};"
                        ).text = str(row["total"])
                        # one cell per match
                        for cell in row["cells"]:
                            td = ui.element("td").style(
                                "padding: 4px 6px; text-align: center;"
                            )
                            if cell["done"]:
                                pts = cell["points"]
                                color = (
                                    theme.GREEN if pts > 0
                                    else theme.BROWN if pts == 0
                                    else theme.INK_MUTED
                                )
                                td.text = f"{cell['pred']}\n({pts}pts)"
                                td.style(
                                    f"padding: 4px 6px; text-align: center; "
                                    f"color: {color}; white-space: pre;"
                                )
                            else:
                                td.text = "—"
                                td.style(
                                    f"padding: 4px 6px; text-align: center; "
                                    f"color: {theme.DIVIDER};"
                                )
    add_export_button()
