import random
from pathlib import Path

from models.acronyms import COUNTRY_ACRONYMS

ACRONYM_TO_COUNTRY = {
    acronym: country
    for country, acronym in COUNTRY_ACRONYMS.items()
}

BASE_CHARS = list("abcdefghijklmnopqrstuvwxyz_-")

FILENAME_SEP = "_"


class Encryptor:
    """
    Deterministic substitution-cipher encryptor.

    Uses a chardict: a list of (original_char, shuffled_char) tuples.
    The key (original_char) never changes — only the value (shuffled_char) does,
    depending on how many times we shuffle (= user_id).

    Encrypt: find the char in keys -> return the corresponding value.
    Decrypt: find the char in values -> return the corresponding key.

    Filename format: {user_id}_{encrypted_intra_login}.txt
      - user_id      : plaintext integer (used to determine next ID without decrypting)
      - encrypted_intra_login : intra login encrypted with the per-user chardict
    """

    def __init__(self, seed: int):
        self.seed = seed

    # ------------------------------------------------------------------
    # Chardict generation
    # ------------------------------------------------------------------

    def _get_chardict(self, user_id: int) -> list[tuple[str, str]]:
        """
        Build a chardict for a given user_id.

        Algorithm:
          1. Seed a Random instance with the global seed.
          2. Shuffle the character list exactly `user_id` times.
          3. Zip BASE_CHARS (keys) against the shuffled list (values).

        Returns a list of (original_char, encrypted_char) tuples.
        """
        rng = random.Random(self.seed)

        shuffled = BASE_CHARS.copy()
        for _ in range(user_id):
            rng.shuffle(shuffled)

        return list(zip(BASE_CHARS, shuffled))

    # ------------------------------------------------------------------
    # Text helpers
    # ------------------------------------------------------------------

    def encrypt_text(self, text: str, user_id: int) -> str:
        chardict = self._get_chardict(user_id)
        key_to_val = {k: v for k, v in chardict}
        return "".join(key_to_val[c] if c in key_to_val else c for c in text)

    def decrypt_text(self, text: str, user_id: int) -> str:
        chardict = self._get_chardict(user_id)
        val_to_key = {v: k for k, v in chardict}
        return "".join(val_to_key[c] if c in val_to_key else c for c in text)

    # ------------------------------------------------------------------
    # File API
    # ------------------------------------------------------------------

    def _next_user_id(self, encrypted_dir: Path) -> int:
        """
        Return the next user_id by reading the plaintext user_id prefix
        from existing filenames. No decryption needed.
        Starts at 1.
        """
        ids = []
        for f in encrypted_dir.glob("*.txt"):
            try:
                uid = int(f.name.split(FILENAME_SEP, 1)[0])
                ids.append(uid)
            except ValueError:
                continue
        return max(ids, default=0) + 1

    def encrypt_file(self, path: str, encrypted_dir: str = "encrypted_scores", user_id: int = None) -> Path:
        path = Path(path)
        out_dir = Path(encrypted_dir)
        out_dir.mkdir(exist_ok=True)

        if user_id is None:
            user_id = self._next_user_id(out_dir)

        with open(path, "r") as f:
            content = f.read().strip()

        encrypted_content = self._encrypt_content(content, user_id)

        enc_login = self.encrypt_text(path.stem, user_id)

        out_name = f"{user_id}{FILENAME_SEP}{enc_login}.txt"
        out_path = out_dir / out_name

        with open(out_path, "w") as f:
            f.write(encrypted_content)

        path.unlink()
        return out_path

    def decrypt_file(self, path: str, raw_dir: str = "decrypted_scores") -> Path:
        path = Path(path)
        out_dir = Path(raw_dir)
        out_dir.mkdir(exist_ok=True)

        # Extract user_id from filename prefix (plaintext)
        user_id = int(path.name.split(FILENAME_SEP, 1)[0])

        with open(path, "r") as f:
            content = f.read().strip()

        decrypted_content = self._decrypt_content(content, user_id)

        # Decrypt the login from the filename to use as output filename
        enc_login = path.stem.split(FILENAME_SEP, 1)[1]
        login = self.decrypt_text(enc_login, user_id)

        out_path = out_dir / f"{login}.txt"

        with open(out_path, "w") as f:
            f.write(decrypted_content)

        return out_path

    # ------------------------------------------------------------------
    # Content helpers
    # ------------------------------------------------------------------

    def _encrypt_content(self, content: str, user_id: int) -> str:
        """
        Encrypt only the country acronym values in the file content.
        Lines like 'GROUP_A:' and '1:mex' -> '1:{encrypted_mex}'
        """
        lines = []
        for line in content.splitlines():
            if ":" in line and not line.startswith("GROUP"):
                prefix, value = line.split(":", 1)
                lines.append(f"{prefix}:{self.encrypt_text(value, user_id)}")
            else:
                lines.append(line)
        return "\n".join(lines)

    def _decrypt_content(self, content: str, user_id: int) -> str:
        """
        Decrypt acronym values then expand them to full country names.

        encrypted  -> decrypt_text -> acronym -> ACRONYM_TO_COUNTRY -> full name
        e.g. 'kfg' -> 'mex' -> 'mexico'
        """
        lines = []
        for line in content.splitlines():
            if ":" in line and not line.startswith("GROUP"):
                prefix, value = line.split(":", 1)
                acronym = self.decrypt_text(value, user_id)
                country = ACRONYM_TO_COUNTRY.get(acronym, acronym)
                lines.append(f"{prefix}:{country}")
            else:
                lines.append(line)
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Bulk API
    # ------------------------------------------------------------------

    def encrypt_all(self, raw_dir: str = "raw_scores", encrypted_dir: str = "encrypted_scores") -> list[Path]:
        results = []
        for file in sorted(Path(raw_dir).iterdir()):
            if file.is_file():
                results.append(self.encrypt_file(str(file), encrypted_dir))
        return results

    def decrypt_all(self, encrypted_dir: str = "encrypted_scores", raw_dir: str = "decrypted_scores") -> list[Path]:
        results = []
        for file in sorted(Path(encrypted_dir).glob("*.txt")):
            if file.is_file():
                results.append(self.decrypt_file(str(file), raw_dir))
        return results

    def decrypt_by_id(self, user_id: int, encrypted_dir: str = "encrypted_scores", raw_dir: str = "decrypted_scores") -> Path | None:
        """Decrypt a single file matching the given user_id."""
        for f in Path(encrypted_dir).glob(f"{user_id}_*.txt"):
            return self.decrypt_file(str(f), raw_dir)
        return None