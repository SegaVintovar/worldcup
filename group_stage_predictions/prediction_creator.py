import os
import re
from pathlib import Path

from models.user import User
from models.groups import ALL_GROUPS
from models.acronyms import COUNTRY_ACRONYMS, COUNTRY_LOOKUP
from encryptor import Encryptor

try:
    import readline
except ImportError:
    readline = None

SEED             = 6769
ENCRYPTED_DIR    = "encrypted_scores"
RAW_DIR          = "raw_scores"
REGISTERED_DIR   = "registered_users"

# Only lowercase letters and hyphens allowed in intra logins
_LOGIN_RE = re.compile(r'^[a-z][a-z-]*[a-z]$|^[a-z]$')

INFO_TEXT = """
=========================================
WORLD CUP PREDICTIONS

You may enter either:
- Full country name
- Country acronym

Examples:
    mexico
    mex

    south-korea
    kor

Predictions are stored as acronyms.

=========================================
"""


def clear_terminal():
    os.system("cls" if os.name == "nt" else "clear")


def setup_country_completion(options):
    if readline is None:
        return

    def completer(text, state):
        matches = [opt for opt in options if opt.startswith(text.lower())]
        if state < len(matches):
            return matches[state]
        return None

    readline.set_completer(completer)
    readline.parse_and_bind("tab: complete")


# ------------------------------------------------------------------
# Registered users helpers
# ------------------------------------------------------------------

def _registered_dir() -> Path:
    d = Path(REGISTERED_DIR)
    d.mkdir(exist_ok=True)
    return d


def _registered_logins() -> set[str]:
    """Return the set of already-registered intra logins."""
    return {f.name.split("_", 1)[1] for f in _registered_dir().iterdir() if f.is_file()}


def _register_user(user_id: int, intra_login: str) -> None:
    """Write a plain {user_id}_{intra_login} marker file (no extension, no encryption)."""
    (_registered_dir() / f"{user_id}_{intra_login}").touch()


# ------------------------------------------------------------------
# ID / write helpers
# ------------------------------------------------------------------

def _next_user_id() -> int:
    encrypted_dir = Path(ENCRYPTED_DIR)
    encrypted_dir.mkdir(exist_ok=True)

    ids = []
    for f in encrypted_dir.glob("*.txt"):
        try:
            uid = int(f.name.split("_", 1)[0])
            ids.append(uid)
        except ValueError:
            continue

    return max(ids, default=0) + 1


def _write_and_encrypt(user: User) -> Path:
    raw_dir = Path(RAW_DIR)
    raw_dir.mkdir(exist_ok=True)

    filepath = raw_dir / user.intra_login

    lines = []
    for group_name, prediction in user.predictions.items():
        lines.append(f"{group_name}:")
        for position, team in sorted(prediction.items()):
            acronym = COUNTRY_ACRONYMS[team]
            lines.append(f"{position}:{acronym}")
        lines.append("")

    filepath.write_text("\n".join(lines).rstrip())

    encryptor = Encryptor(SEED)
    encrypted_path = encryptor.encrypt_file(
        str(filepath),
        ENCRYPTED_DIR,
        user_id=user.user_id,
    )

    return encrypted_path


# ------------------------------------------------------------------
# Main flow
# ------------------------------------------------------------------

def make_prediction() -> User:
    existing_logins = _registered_logins()

    while True:
        raw = input("Enter your intra login: ").strip().lower()

        # Normalise spaces/underscores to hyphens
        intra_login = raw.replace(" ", "-").replace("_", "-")

        if not _LOGIN_RE.match(intra_login):
            print("Login must contain only letters (a-z) and hyphens, and must start/end with a letter.")
            continue

        if intra_login in existing_logins:
            print(f"'{intra_login}' is already registered. Please use a different login.")
            continue

        break

    user_id = _next_user_id()

    user = User(
        intra_login=intra_login,
        user_id=user_id,
    )

    # Register immediately so a concurrent run can't grab the same login
    _register_user(user_id, intra_login)

    clear_terminal()
    print(INFO_TEXT)

    for group_name, group in ALL_GROUPS.items():
        print(f"\n=== {group_name} ===")

        for team in group.values():
            print(f"- {team} ({COUNTRY_ACRONYMS[team]})")

        available_teams = list(group.values())
        prediction = {}

        for position in range(1, len(group) + 1):
            while True:
                completion_options = (
                    available_teams +
                    [COUNTRY_ACRONYMS[t] for t in available_teams]
                )
                setup_country_completion(completion_options)

                user_input = (
                    input(f"Who finishes #{position}? ")
                    .strip()
                    .lower()
                    .replace(" ", "-")
                    .replace("_", "-")
                )

                country = COUNTRY_LOOKUP.get(user_input)

                if country is None:
                    print("Unknown country/acronym, try again.")
                    continue

                if country not in available_teams:
                    print("Invalid team, try again.")
                    continue

                prediction[position] = country
                available_teams.remove(country)
                break

        user.predictions[group_name] = prediction
        clear_terminal()
        print(INFO_TEXT)

    encrypted_path = _write_and_encrypt(user)
    print(f"\nPrediction saved and encrypted -> {encrypted_path.name}")

    return user


def show_prediction(user: User):
    print("\n=== USER ===")
    print(f"Login: {user.intra_login}")
    print(f"ID: {user.user_id}")

    for group_name, prediction in user.predictions.items():
        print(f"\n{group_name}")
        for position, team in sorted(prediction.items()):
            print(f"{position}. {team} ({COUNTRY_ACRONYMS[team]})")