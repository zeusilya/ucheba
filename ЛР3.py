import argparse
import os
from pathlib import Path


# -------------------- Утилиты --------------------

def ensure_parent(path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def xor_files(in_path: str, key_path: str, out_path: str, chunk_size: int = 1024 * 1024) -> None:
    """
    Шифр Вернама для файлов: out = in XOR key.
    Требование: ключевой файл должен быть НЕ МЕНЬШЕ входного.
    """
    in_size = os.path.getsize(in_path)
    key_size = os.path.getsize(key_path)
    if key_size < in_size:
        raise ValueError(f"Ключ короче входного файла: key={key_size} байт, in={in_size} байт")

    ensure_parent(out_path)
    with open(in_path, "rb") as fin, open(key_path, "rb") as fkey, open(out_path, "wb") as fout:
        while True:
            data = fin.read(chunk_size)
            if not data:
                break
            key = fkey.read(len(data))
            out = bytes(a ^ b for a, b in zip(data, key))
            fout.write(out)


# -------------------- Генерация ключа --------------------

def gen_key_urandom(out_path: str, size: int) -> None:
    ensure_parent(out_path)
    with open(out_path, "wb") as f:
        f.write(os.urandom(size))


class LCG:
    """
    Линейный конгруэнтный генератор:
      X_{n+1} = (a*X_n + c) mod m
    Генерируем байты из X_n.
    """
    def __init__(self, seed: int, a: int = 1103515245, c: int = 12345, m: int = 2**31):
        self.x = seed % m
        self.a = a
        self.c = c
        self.m = m

    def next_u31(self) -> int:
        self.x = (self.a * self.x + self.c) % self.m
        return self.x

    def next_byte(self) -> int:
        return self.next_u31() & 0xFF


def gen_key_lcg(out_path: str, size: int, seed: int) -> None:
    ensure_parent(out_path)
    gen = LCG(seed=seed)
    with open(out_path, "wb") as f:
        f.write(bytes(gen.next_byte() for _ in range(size)))


# -------------------- RC4 --------------------

def rc4_keystream(key_bytes: bytes):
    """
    Генератор байтов потока RC4 (PRGA) после KSA.
    """
    # KSA
    S = list(range(256))
    j = 0
    key_len = len(key_bytes)
    for i in range(256):
        j = (j + S[i] + key_bytes[i % key_len]) % 256
        S[i], S[j] = S[j], S[i]

    # PRGA
    i = 0
    j = 0
    while True:
        i = (i + 1) % 256
        j = (j + S[i]) % 256
        S[i], S[j] = S[j], S[i]
        K = S[(S[i] + S[j]) % 256]
        yield K


def rc4_crypt_file(in_path: str, out_path: str, key: str, chunk_size: int = 1024 * 1024) -> None:
    """
    RC4 шифрование/расшифрование файла (одно и то же действие).
    """
    if not key:
        raise ValueError("RC4 ключ не должен быть пустым")

    ensure_parent(out_path)
    ks = rc4_keystream(key.encode("utf-8"))

    with open(in_path, "rb") as fin, open(out_path, "wb") as fout:
        while True:
            data = fin.read(chunk_size)
            if not data:
                break
            out = bytes(b ^ next(ks) for b in data)
            fout.write(out)


# -------------------- CLI --------------------

def main():
    parser = argparse.ArgumentParser(
        description="ЛР3: Вернам (XOR с ключом-файлом) и поточный шифр RC4."
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # Генерация ключа
    p_key = sub.add_parser("gen-key", help="Сгенерировать ключевой файл.")
    p_key.add_argument("--out", required=True, help="Путь к ключевому файлу")
    p_key.add_argument("--size", type=int, required=True, help="Размер ключа (байт)")
    p_key.add_argument("--method", choices=["urandom", "lcg"], default="urandom",
                       help="Метод генерации: urandom или lcg")
    p_key.add_argument("--seed", type=int, default=123456789,
                       help="Seed для LCG (используется только при method=lcg)")

    # Вернам XOR
    p_v = sub.add_parser("vernam", help="Зашифровать/расшифровать Вернамом: out = in XOR key_file.")
    p_v.add_argument("--in", dest="inp", required=True, help="Входной файл")
    p_v.add_argument("--keyfile", required=True, help="Ключевой файл (не короче входного)")
    p_v.add_argument("--out", required=True, help="Выходной файл")

    # RC4
    p_rc4 = sub.add_parser("rc4", help="Зашифровать/расшифровать RC4.")
    p_rc4.add_argument("--in", dest="inp", required=True, help="Входной файл")
    p_rc4.add_argument("--out", required=True, help="Выходной файл")
    p_rc4.add_argument("--key", required=True, help="Строковый ключ RC4 (UTF-8)")

    args = parser.parse_args()

    if args.cmd == "gen-key":
        if args.size <= 0:
            raise ValueError("size должен быть > 0")
        if args.method == "urandom":
            gen_key_urandom(args.out, args.size)
        else:
            gen_key_lcg(args.out, args.size, args.seed)
        print(f"Ключ создан: {args.out} ({args.size} байт), method={args.method}")

    elif args.cmd == "vernam":
        xor_files(args.inp, args.keyfile, args.out)
        print(f"Готово (Вернам XOR): {args.inp} XOR {args.keyfile} -> {args.out}")

    elif args.cmd == "rc4":
        rc4_crypt_file(args.inp, args.out, args.key)
        print(f"Готово (RC4): {args.inp} -> {args.out}")

    else:
        raise RuntimeError("Неизвестная команда")


if __name__ == "__main__":
    main()
