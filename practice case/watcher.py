#!/usr/bin/env python3
import hashlib
import json
import logging
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
INBOX = BASE / "inbox"
PROCESSED = BASE / "processed"
FAILED = BASE / "failed"
SKIPPED = BASE / "skipped"
STATE_DIR = BASE / "state"
MARKS = STATE_DIR / "processed.jsonl"
LOG_FILE = BASE / "watcher.log"

POLL_SECONDS = 0.5
STABLE_SECONDS = 2.0     
IGNORE_NAMES = {"PLACE_FILES_HERE.txt", ".DS_Store", "Thumbs.db"}
IGNORE_SUFFIXES = (".part", ".tmp", ".crdownload", ".download", ".swp")
ORDER_LINE = re.compile(r"^Заказ \d{4}; товар: .+; сумма: \d+$")

log = logging.getLogger("watcher")


def setup_logging():
    fmt = logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s", "%Y-%m-%d %H:%M:%S")
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    sh = logging.StreamHandler(sys.stdout)
    for h in (fh, sh):
        h.setFormatter(fmt)
        log.addHandler(h)
    log.setLevel(logging.INFO)


def load_marks():
    marks = {}
    if MARKS.exists():
        with MARKS.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    log.warning("Повреждённая строка в отметках пропущена (обрыв записи?)")
                    continue
                if rec.get("status") == "processed":
                    marks[rec["sha256"]] = rec
    return marks


def write_mark(rec):
    with MARKS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def sha256_of(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def is_candidate(p):
    return (
        p.is_file()
        and p.name not in IGNORE_NAMES
        and not p.name.startswith(".")
        and not p.name.endswith(IGNORE_SUFFIXES)
    )


def unique_dest(folder, name, digest):
    dest = folder / name
    if not dest.exists():
        return dest
    stem, suffix = os.path.splitext(name)
    dest = folder / f"{stem}__{digest[:8]}{suffix}"
    n = 1
    while dest.exists():
        dest = folder / f"{stem}__{digest[:8]}_{n}{suffix}"
        n += 1
    return dest


def validate(path):
    if path.stat().st_size == 0:
        return "пустой файл"
    if path.suffix.lower() == ".txt":
        try:
            text = path.read_bytes().decode("utf-8")
        except UnicodeDecodeError:
            return "обрезан посреди символа (неверный UTF-8)"
        lines = [ln for ln in text.splitlines() if ln.strip()]
        if not lines:
            return "нет строк заказа"
        for i, ln in enumerate(lines, 1):
            if not ORDER_LINE.match(ln):
                return f"строка {i} не соответствует формату заказа (файл неполный)"
    return None


def can_open(path):
    try:
        with path.open("rb") as f:
            f.read(1)
        return True
    except OSError:
        return False


def handle(path, marks):
    try:
        digest = sha256_of(path)
        size = path.stat().st_size
    except FileNotFoundError:
        log.info("Файл %s исчез до обработки", path.name)
        return

    if digest in marks:
        prev = marks[digest]
        dest = unique_dest(SKIPPED, path.name, digest)
        os.replace(path, dest)
        log.info("ПРОПУСК  %s: такое содержимое уже обработано (%s, %s) → skipped/%s",
                 path.name, prev["name"], prev["time"], dest.name)
        return

    problem = validate(path)
    if problem:
        dest = unique_dest(FAILED, path.name, digest)
        os.replace(path, dest)
        write_mark({"status": "failed", "sha256": digest, "name": path.name, "size": size,
                    "reason": problem, "time": datetime.now().isoformat(timespec="seconds")})
        log.error("ОШИБКА   %s (%d Б): %s → failed/%s", path.name, size, problem, dest.name)
        return

    dest = unique_dest(PROCESSED, path.name, digest)
    os.replace(path, dest)                
    rec = {"status": "processed", "sha256": digest, "name": path.name, "dest": dest.name,
           "size": size, "time": datetime.now().isoformat(timespec="seconds")}
    write_mark(rec)                          
    marks[digest] = rec
    log.info("ГОТОВО   %s (%d Б, sha256=%s…) → processed/%s", path.name, size, digest[:8], dest.name)


def run(once=False):
    for d in (INBOX, PROCESSED, FAILED, SKIPPED, STATE_DIR):
        d.mkdir(exist_ok=True)
    setup_logging()
    marks = load_marks()
    log.info("Старт. Ранее обработано файлов: %d. Слежу за %s", len(marks), INBOX)

    seen = {} 
    try:
        while True:
            now = time.monotonic()
            current = {p for p in INBOX.iterdir() if is_candidate(p)}
            for gone in set(seen) - current:
                del seen[gone]

            for p in sorted(current):
                try:
                    st = p.stat()
                except FileNotFoundError:
                    continue
                sig = (st.st_size, st.st_mtime_ns)
                if p not in seen:
                    log.info("ПОЯВИЛСЯ %s (%d Б), жду завершения копирования", p.name, st.st_size)
                    seen[p] = (sig, now)
                    continue
                old_sig, since = seen[p]
                if sig != old_sig:
                    seen[p] = (sig, now)
                    continue
                if now - since >= STABLE_SECONDS and can_open(p):
                    del seen[p]
                    handle(p, marks)

            if once and not current:
                break
            time.sleep(POLL_SECONDS)
    except KeyboardInterrupt:
        log.info("Остановлен пользователем")


if __name__ == "__main__":
    run(once="--once" in sys.argv)
