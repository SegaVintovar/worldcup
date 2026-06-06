import sys
from encryptor import Encryptor
from prediction_creator import make_prediction, show_prediction

SEED          = 6769
ENCRYPTED_DIR = "encrypted_scores"
DECRYPTED_DIR = "decrypted_scores_out"

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "predict"

    if mode == "predict":
        user = make_prediction()
        show_prediction(user)

    elif mode == "decrypt":
        user_id = int(sys.argv[2])
        e = Encryptor(SEED)
        f = e.decrypt_by_id(user_id, encrypted_dir=ENCRYPTED_DIR, raw_dir=DECRYPTED_DIR)
        print(f"Decrypted -> {f.name}" if f else f"No file found for user_id {user_id}")

    elif mode == "decrypt-all":
        e = Encryptor(SEED)
        for f in e.decrypt_all(encrypted_dir=ENCRYPTED_DIR, raw_dir=DECRYPTED_DIR):
            print(f"Decrypted -> {f.name}")