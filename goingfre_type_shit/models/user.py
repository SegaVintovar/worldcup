from pydantic import BaseModel


class User(BaseModel):

    # 4 to 12 characters
    intra_login: str

    # howmanyth user — also drives the shuffle count in the encryptor
    user_id: int

    # GROUP STAGE: { "GROUP_A": { 1: "mexico", 2: "south_africa", ... }, ... }
    # KO STAGE: can extend with match dicts later
    predictions: dict[str, dict[int, str]] = {}

    # is the user an admin
    is_admin: bool = False