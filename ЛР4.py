import argparse
import os
from pathlib import Path
import hashlib
import struct


# -------------------- Вспомогательные функции --------------------

def ensure_parent(path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def pkcs7_pad(data: bytes, block_size: int) -> bytes:
    pad_len = block_size - (len(data) % block_size)
    return data + bytes([pad_len]) * pad_len


def pkcs7_unpad(data: bytes, block_size: int) -> bytes:
    if not data or (len(data) % block_size != 0):
        raise ValueError("Неверная длина данных для снятия padding")
    pad_len = data[-1]
    if pad_len < 1 or pad_len > block_size:
        raise ValueError("Неверный PKCS#7 padding")
    if data[-pad_len:] != bytes([pad_len]) * pad_len:
        raise ValueError("Неверный PKCS#7 padding")
    return data[:-pad_len]


def xor_bytes(a: bytes, b: bytes) -> bytes:
    return bytes(x ^ y for x, y in zip(a, b))


def derive_tea_key_16(passphrase: str) -> bytes:
    """
    Из пароля получаем ровно 16 байт ключа TEA.
    Делается через SHA-256 и обрезку до 16 байт.
    """
    h = hashlib.sha256(passphrase.encode("utf-8")).digest()
    return h[:16]


# -------------------- TEA (Tiny Encryption Algorithm) --------------------
# Блок: 64 бита (2x32)
# Ключ: 128 бит (4x32)
# Раунды: 32

DELTA = 0x9E3779B9
MASK32 = 0xFFFFFFFF


def tea_encrypt_block(block8: bytes, key16: bytes) -> bytes:
    v0, v1 = struct.unpack(">2I", block8)  # big-endian 2x32-bit
    k0, k1, k2, k3 = struct.unpack(">4I", key16)

    s = 0
    for _ in range(32):
        s = (s + DELTA) & MASK32
        v0 = (v0 + (((v1 << 4) + k0) ^ (v1 + s) ^ ((v1 >> 5) + k1))) & MASK32
        v1 = (v1 + (((v0 << 4) + k2) ^ (v0 + s) ^ ((v0 >> 5) + k3))) & MASK32

    return struct.pack(">2I", v0, v1)


def tea_decrypt_block(block8: bytes, key16: bytes) -> bytes:
    v0, v1 = struct.unpack(">2I", block8)
    k0, k1, k2, k3 = struct.unpack(">4I", key16)

    s = (DELTA * 32) & MASK32
    for _ in range(32):
        v1 = (v1 - (((v0 << 4) + k2) ^ (v0 + s) ^ ((v0 >> 5) + k3))) & MASK32
        v0 = (v0 - (((v1 << 4) + k0) ^ (v1 + s) ^ ((v1 >> 5) + k1))) & MASK32
        s = (s - DELTA) & MASK32

    return struct.pack(">2I", v0, v1)


# -------------------- CBC режим для файлов --------------------

BLOCK_SIZE = 8  # TEA block size


def encrypt_file_cbc(in_path: str, out_path: str, passphrase: str) -> None:
    key = derive_tea_key_16(passphrase)
    iv = os.urandom(BLOCK_SIZE)  # случайный IV

    ensure_parent(out_path)
    with open(in_path, "rb") as fin:
        plaintext = fin.read()

    padded = pkcs7_pad(plaintext, BLOCK_SIZE)

    ciphertext_blocks = []
    prev = iv
    for i in range(0, len(padded), BLOCK_SIZE):
        block = padded[i:i + BLOCK_SIZE]
        x = xor_bytes(block, prev)
        c = tea_encrypt_block(x, key)
        ciphertext_blocks.append(c)
        prev = c

    with open(out_path, "wb") as fout:
        # формат: IV (8 байт) + ciphertext
        fout.write(iv + b"".join(ciphertext_blocks))


def decrypt_file_cbc(in_path: str, out_path: str, passphrase: str) -> None:
    key = derive_tea_key_16(passphrase)

    with open(in_path, "rb") as fin:
        data = fin.read()

    if len(data) < BLOCK_SIZE or (len(data) % BLOCK_SIZE != 0):
        raise ValueError("Файл не похож на TEA-CBC (неверная длина)")

    iv = data[:BLOCK_SIZE]
    ciphertext = data[BLOCK_SIZE:]

    plaintext_blocks = []
    prev = iv
    for i in range(0, len(ciphertext), BLOCK_SIZE):
        c = ciphertext[i:i + BLOCK_SIZE]
        x = tea_decrypt_block(c, key)
        p = xor_bytes(x, prev)
        plaintext_blocks.append(p)
        prev = c

    padded_plain = b"".join(plaintext_blocks)
    plain = pkcs7_unpad(padded_plain, BLOCK_SIZE)

    ensure_parent(out_path)
    with open(out_path, "wb") as fout:
        fout.write(plain)


# -------------------- CLI --------------------

def main():
    parser = argparse.ArgumentParser(
        description="ЛР4: Итеративный блочный шифр TEA + шифрование/расшифрование файлов (CBC + PKCS#7)."
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_enc = sub.add_parser("encrypt", help="Зашифровать файл (TEA-CBC).")
    p_enc.add_argument("--in", dest="inp", required=True, help="Входной файл")
    p_enc.add_argument("--out", required=True, help="Выходной файл (cipher)")
    p_enc.add_argument("--pass", dest="pw", required=True, help="Пароль (из него делается ключ)")

    p_dec = sub.add_parser("decrypt", help="Расшифровать файл (TEA-CBC).")
    p_dec.add_argument("--in", dest="inp", required=True, help="Входной файл (cipher)")
    p_dec.add_argument("--out", required=True, help="Выходной файл (plain)")
    p_dec.add_argument("--pass", dest="pw", required=True, help="Пароль (из него делается ключ)")

    args = parser.parse_args()

    if args.cmd == "encrypt":
        encrypt_file_cbc(args.inp, args.out, args.pw)
        print(f"Готово: encrypt {args.inp} -> {args.out}")

    elif args.cmd == "decrypt":
        decrypt_file_cbc(args.inp, args.out, args.pw)
        print(f"Готово: decrypt {args.inp} -> {args.out}")


if __name__ == "__main__":
    main()
