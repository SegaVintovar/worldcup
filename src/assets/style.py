from nicegui import ui

def apply_global_styles():
    ui.add_head_html("""
    <style>
    html, body {
        background-color: #F5EAD8 !important;
    }

    #app {
        background-color: #F5EAD8 !important;
        min-height: 100vh;
    }

    .nicegui-content {
        background-color: #F5EAD8 !important;
        min-height: 100vh;
    }

    .q-page {
        background-color: #F5EAD8 !important;
    }
    </style>
    """)