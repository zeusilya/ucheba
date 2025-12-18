import argparse
import math
import os
import random
from collections import Counter
from pathlib import Path


def byte_frequencies(file_path: str) -> tuple[Counter, int]:
    """
    Возвращает частоты байтов (0..255) и общее число байтов.
    Читает файл в бинарном режиме, корректно для любых файлов.
    """
    counter = Counter()
    total = 0

    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(1024 * 1024)  # 1 MB
            if not chunk:
                break
            counter.update(chunk)
            total += len(chunk)

    return counter, total


def shannon_entropy(counter: Counter, total: int) -> float:
    """
    Энтропия Шеннона H = - sum(p_i * log2(p_i))
    total — общее число символов.
    """
    if total == 0:
        return 0.0

    h = 0.0
    for count in counter.values():
        p = count / total
        h -= p * math.log2(p)
    return h


def analyze_file(file_path: str, top: int = 10) -> None:
    counter, total = byte_frequencies(file_path)
    h = shannon_entropy(counter, total)

    alphabet_size = len(counter)
    max_h = math.log2(alphabet_size) if alphabet_size > 0 else 0.0

    print(f"\nФайл: {file_path}")
    print(f"Размер: {total} байт")
    print(f"Размер алфавита (уникальных байтов): {alphabet_size}")
    print(f"Энтропия: {h:.6f} бит/символ")
    print(f"Log2(размер алфавита): {max_h:.6f} бит/символ")

    if total > 0:
        print("\nТоп наиболее частых байтов:")
        for b, c in counter.most_common(top):
            # b — это int 0..255
            frac = c / total
            print(f"  byte={b:3d}  count={c:10d}  freq={frac:.6f}")


# -------------------- Генерация тестовых файлов --------------------

def write_bytes(path: str, data: bytes) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


def gen_same_byte(path: str, size: int, value: int) -> None:
    if not (0 <= value <= 255):
        raise ValueError("value должен быть от 0 до 255")
    write_bytes(path, bytes([value]) * size)


def gen_random_bits(path: str, size: int) -> None:
    # случайные байты 0 или 1
    data = bytes(random.getrandbits(1) for _ in range(size))
    write_bytes(path, data)


def gen_random_bytes(path: str, size: int) -> None:
    # случайные байты 0..255
    data = os.urandom(size)
    write_bytes(path, data)


def gen_pattern(path: str, size: int, pattern: bytes) -> None:
    if not pattern:
        raise ValueError("pattern не должен быть пустым")
    data = (pattern * (size // len(pattern) + 1))[:size]
    write_bytes(path, data)


def run_demo(out_dir: str, size: int) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    files = [
        (out / "same_A.bin", lambda p: gen_same_byte(str(p), size, ord("A"))),
        (out / "same_00.bin", lambda p: gen_same_byte(str(p), size, 0)),
        (out / "random_bits.bin", lambda p: gen_random_bits(str(p), size)),
        (out / "random_bytes.bin", lambda p: gen_random_bytes(str(p), size)),
        (out / "pattern_abc.bin", lambda p: gen_pattern(str(p), size, b"abc")),
        (out / "pattern_01.bin", lambda p: gen_pattern(str(p), size, b"\x00\x01")),
    ]

    print(f"\nГенерация файлов в: {out.resolve()}")
    for fp, maker in files:
        maker(fp)
        print(f"  создан: {fp.name} ({size} байт)")

    print("\nАнализ сгенерированных файлов:")
    for fp, _ in files:
        analyze_file(str(fp), top=5)


# -------------------- CLI --------------------

def main():
    parser = argparse.ArgumentParser(
        description="ЛР2: частоты символов (байтов) и энтропия файла (Шеннон)."
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_an = sub.add_parser("analyze", help="Проанализировать файл: частоты и энтропия.")
    p_an.add_argument("file", help="Путь к файлу")
    p_an.add_argument("--top", type=int, default=10, help="Сколько самых частых байтов показать")

    p_demo = sub.add_parser("demo", help="Сгенерировать тестовые файлы и сравнить энтропию.")
    p_demo.add_argument("--out", default="entropy_demo_files", help="Папка для файлов")
    p_demo.add_argument("--size", type=int, default=200_000, help="Размер каждого файла (байт)")

    args = parser.parse_args()

    if args.cmd == "analyze":
        analyze_file(args.file, top=args.top)
    elif args.cmd == "demo":
        run_demo(args.out, args.size)


if __name__ == "__main__":
    main()
