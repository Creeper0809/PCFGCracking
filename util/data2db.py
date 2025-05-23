import os
from pathlib import Path

from Constants import TRAINING_DATA_PATH
from model.password_train_data import PasswordTrainData

if __name__ == '__main__':
    db = PasswordTrainData()
    path1 = Path(os.path.join(TRAINING_DATA_PATH, "비번/credentials.txt"))
    path2 = Path(os.path.join(TRAINING_DATA_PATH, "비번/credentials2.txt"))

    file = open(
        path2,
        "r",
        encoding="utf-8")

    passwords = []
    for line in file:
        arrs = line.strip().split(":")
        passwords.append((arrs[0],":".join(arrs[1:])))

    file = open(
        path1,
        "r",
        encoding="utf-8")

    for line in file:
        arrs = line.strip().split(":")
        passwords.append((arrs[0], ":".join(arrs[1:])))

    db.add_passwords(passwords)




