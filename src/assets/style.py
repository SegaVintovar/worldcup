# from nicegui import ui
# from src.assets import theme


# def apply_global_styles():
#     ui.add_head_html(
#     "<style>",
#     f"""html, body {{
#         background-color: {theme.BG} !important;
#         font-family: 'Helvetica Neue', Arial, sans-serif;
#         color: {theme.INK};
#     }}

#     #app {{
#         background-color: {theme.BG} !important;
#         min-height: 100vh;
#     }}

#     .nicegui-content {{
#         background-color: {theme.BG} !important;
#         min-height: 100vh;
#     }}

#     .q-page {{
#         background-color: {theme.BG} !important;
#     }}

#     /* ── Header bar ─────────────────────────────────────────── */
#     .q-header {{
#         background-color: {theme.BG} !important;
#         color: {theme.INK} !important;
#         border-bottom: 2px solid {theme.INK};
#         box-shadow: none !important;
#     }}

#     /* ── Default cards: badge-like, crisp border, no soft shadow ── */
#     .q-card {{
#         background-color: {theme.CARD_BG} !important;
#         border: 1px solid {theme.INK};
#         border-radius: {theme.RADIUS} !important;
#         box-shadow: none !important;
#         color: {theme.INK};
#     }}

#     /* ── Buttons ────────────────────────────────────────────── */
#     .q-btn {{
#         border-radius: 8px !important;
#         font-weight: 600;
#         letter-spacing: 0.2px;
#     }}

#     .sq-btn-primary {{
#         background-color: {theme.GREEN} !important;
#         color: {theme.BG} !important;
#     }}

#     .sq-btn-ghost {{
#         background-color: transparent !important;
#         color: {theme.INK} !important;
#         border: 1px solid {theme.INK} !important;
#     }}

#     .sq-btn-active {{
#         background-color: {theme.INK} !important;
#         color: {theme.BG} !important;
#     }}

#     /* ── Headings ───────────────────────────────────────────── */
#     h1, h2, h3, .sq-heading {{
#         color: {theme.INK} !important;
#     }}

#     /* ── Chat bubble (sq.clubs.codam messages) ─────────────────── */
#     .q-message-text--received {{
#         background-color: {theme.CARD_BG} !important;
#         border: 1px solid {theme.INK} !important;
#         color: {theme.INK} !important;
#     }}

#     /* ── Scrollbar accent (subtle brand touch) ─────────────────── */
#     ::-webkit-scrollbar-thumb {{
#         background-color: {theme.GREEN};
#         border-radius: 8px;
#     }}""",
#     "</style>")


from nicegui import ui
from src.assets import theme


def apply_global_styles() -> None:
    ui.add_head_html(f"""
    <style>
    html, body {{
        background-color: {theme.BG} !important;
        font-family: 'Helvetica Neue', Arial, sans-serif;
        color: {theme.INK};
    }}

    #app {{
        background-color: {theme.BG} !important;
        min-height: 100vh;
    }}

    .nicegui-content {{
        background-color: {theme.BG} !important;
        min-height: 100vh;
    }}

    .q-page {{
        background-color: {theme.BG} !important;
    }}

    /* ── Header bar ─────────────────────────────────────────── */
    .q-header {{
        background-color: {theme.BG} !important;
        color: {theme.INK} !important;
        border-bottom: 2px solid {theme.INK};
        box-shadow: none !important;
    }}

    /* ── Default cards: badge-like, crisp border, no soft shadow ── */
    .q-card {{
        background-color: {theme.CARD_BG} !important;
        border: 1px solid {theme.INK};
        border-radius: {theme.RADIUS}px !important;
        box-shadow: none !important;
        color: {theme.INK};
    }}

    /* ── Buttons ────────────────────────────────────────────── */
    .q-btn {{
        border-radius: 8px !important;
        font-weight: 600;
        letter-spacing: 0.2px;
    }}

    .sq-btn-primary {{
        background-color: {theme.GREEN} !important;
        color: {theme.BG} !important;
    }}

    .sq-btn-ghost {{
        background-color: transparent !important;
        color: {theme.INK} !important;
        border: 1px solid {theme.INK} !important;
    }}

    .sq-btn-active {{
        background-color: {theme.INK} !important;
        color: {theme.BG} !important;
    }}

    /* ── Headings ───────────────────────────────────────────── */
    h1, h2, h3, .sq-heading {{
        color: {theme.INK} !important;
    }}

    /* ── Chat bubble (sq.clubs.codam messages) ───────────────── */
    .q-message-text--received {{
        background-color: {theme.CARD_BG} !important;
        border: 1px solid {theme.INK} !important;
        color: {theme.INK} !important;
    }}

    /* ── Scrollbar accent (subtle brand touch) ───────────────── */
    ::-webkit-scrollbar {{
        width: 10px;
        height: 10px;
    }}

    ::-webkit-scrollbar-thumb {{
        background-color: {theme.GREEN};
        border-radius: 8px;
    }}

    ::-webkit-scrollbar-track {{
        background-color: {theme.BG};
    }}
    </style>
    """)