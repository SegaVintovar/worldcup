from pathlib import Path

from models.user import User
from models.groups import ALL_GROUPS
from models.acronyms import COUNTRY_ACRONYMS
from encryptor import Encryptor


SEED = 6769
ENCRYPTED_DIR = "encrypted_scores"
RAW_DIR = "raw_scores"


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

    # Filename is just the intra login (no extension),
    # encryptor adds .txt on decrypt
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


def make_prediction() -> User:
    intra_login = input("Enter your intra login: ").strip().lower()

    user = User(
        intra_login=intra_login,
        user_id=_next_user_id(),
    )

    for group_name, group in ALL_GROUPS.items():
        print(f"\n=== {group_name} ===")

        for team in group.values():
            print(f"- {team}")

        available_teams = list(group.values())
        prediction = {}

        for position in range(1, len(group) + 1):
            while True:
                team = (
                    input(f"Who finishes #{position}? ")
                    .strip()
                    .lower()
                    .replace(" ", "_")
                )

                if team not in available_teams:
                    print("Invalid team, try again.")
                    continue

                prediction[position] = team
                available_teams.remove(team)
                break

        user.predictions[group_name] = prediction

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
            print(f"{position}. {team}")

