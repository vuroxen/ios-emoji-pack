#!/usr/bin/env python3
"""
iOS Emoji pack — picker ma'lumotlarini va spritesheet'ni yaratuvchi vosita.

Ishlashi:
  1. Mavjud index.html ichidagi `D` obyektidan kategoriyalar, kodlar, nomlar,
     kategoriya indekslari va qidiruv kalitlarini oladi (qo'lda yozilgan
     qidiruvlar saqlanadi).
  2. Emoji 17.0 dagi 8 ta yangi emojini qo'shadi.
  3. emoji.json dan skin-tone (teri rangi) variantlari xaritasini yaratadi.
  4. O'zbekcha qidiruv kalitlari va kategoriya nomlarini qo'llaydi.
  5. Barcha mavjud PNG lar asosida bitta spritesheet (sheet.png) yaratadi va
     har bir kod uchun [ustun, qator] xaritasini hisoblaydi.
  6. Natijani ../picker.js fayliga yozadi.

Foydalanish:
  python3 tools/build_picker.py
"""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EMOJI_DIR = os.path.join(ROOT, "emoji")
EMOJI_JSON = os.path.join(ROOT, "emoji.json")
BASE_DATA = os.path.join(ROOT, "tools", "base_data.json")
OUT_JS = os.path.join(ROOT, "picker.js")
SHEET = os.path.join(ROOT, "sheet.png")

TILE = 64          # har bir emoji o'lchami (px) — picker 36px da ko'rsatadi
COLS = 64          # spritesheet ustunlari
SKIN_TONES = ["1f3fb", "1f3fc", "1f3fd", "1f3fe", "1f3ff"]

# --- O'zbekcha kategoriya nomlari (D.cats tartibida) + Yangi (17.0) ---
UZ_CATS = [
    "Yuzlar va his-tuyg'ular",
    "Odamlar va tana",
    "Hayvonlar va tabiat",
    "Taom va ichimlik",
    "Faoliyat",
    "Sayohat va joylar",
    "Buyumlar",
    "Ramzlar",
    "Bayroqlar",
    "Yangi (17.0)",
]

# --- Emoji 17.0 (2025-09-09) dagi 8 ta yangi emoji (to'g'ri Unicode kodlari) ---
# Distorted Face 🫪=U+1FAEA, Fight Cloud 🫯=U+1FAEF, Hairy Creature 🫈=U+1FAC8,
# Orca 🫍=U+1FACD, Landslide 🛘=U+1F6D8, Trombone 🪊=U+1FA8A,
# Treasure Chest 🪎=U+1FA8E, Ballet Dancer 🧑‍🩰=U+1F9D1 U+200D U+1FA70
NEW_17 = [
    ("1faea",            "distorted_face",  "chalg'igan yuz"),
    ("1faef",            "fight_cloud",     "janjal buluti"),
    ("1fac8",            "hairy_creature",  "tukli maxluq"),
    ("1facd",            "orca",            "orca, kit"),
    ("1f6d8",            "landslide",       "ko'chish, opolis"),
    ("1fa8a",            "trombone",        "trombon"),
    ("1fa8e",            "treasure_chest",  "xazina qutisi"),
    ("1f9d1-200d-1fa70", "ballet_dancers",  "balet raqqosi"),
]
NEW_CAT = len(UZ_CATS) - 1  # "Yangi (17.0)"

# --- O'zbekcha qidiruv kalitlari: o'zbek so'z -> emoji short_name ---
# (short_name NAMES ro'yxatida bo'lmasa, avtomatik tashlab yuboriladi)
UZ_SEARCH = {
    "quyosh": "sun", "yomg'ir": "cloud_rain", "yulduz": "star", "oy": "moon",
    "yurak": "heart", "sevgi": "heart", "sevaman": "heart", "salom": "wave",
    "xayr": "wave", "yaxshi": "thumbsup", "yomon": "thumbsdown", "kulgi": "joy",
    "kulib": "smile", "yig'lash": "cry", "xafa": "frowning", "ko'ngilsiz": "disappointed",
    "g'azab": "angry", "hayrat": "astonished", "ko'z": "eye", "qo'l": "hand",
    "olov": "fire", "yorug'lik": "bulb", "suv": "droplet", "it": "dog", "mushuk": "cat",
    "qush": "bird", "baliq": "fish", "ot": "horse", "sigir": "cow", "cho'chqa": "pig",
    "quyon": "rabbit", "ayiq": "bear", "tulki": "fox", "sher": "lion", "yo'lbars": "tiger",
    "zirafa": "giraffe", "fil": "elephant", "maymun": "monkey", "ilon": "snake",
    "chumoli": "ant", "asalari": "bee", "gul": "rose", "daraxt": "tree", "olma": "apple",
    "banan": "banana", "uzum": "grapes", "tarvuz": "watermelon", "non": "bread",
    "pishloq": "cheese", "pizza": "pizza", "burger": "hamburger", "sendvich": "sandwich",
    "kofe": "coffee", "choy": "tea", "pivo": "beer", "vino": "wine", "keks": "cake",
    "shokolad": "chocolate", "muzqaymoq": "ice_cream", "uy": "house", "mashina": "car",
    "samolyot": "airplane", "kema": "ship", "poyezd": "train", "velosiped": "bike",
    "mototsikl": "motorcycle", "avtobus": "bus", "raketa": "rocket", "telefon": "phone",
    "kompyuter": "computer", "klaviatura": "keyboard", "kamera": "camera", "soat": "clock",
    "kitob": "book", "xat": "envelope", "pul": "moneybag", "bayram": "tada",
    "futbol": "soccer", "basketbol": "basketball", "to'p": "soccer", "bayroq": "flag",
    "dunyo": "earth_africa", "tinchlik": "peace", "g'alaba": "trophy",
    "musiqa": "musical_note", "kalit": "key", "kasalxona": "hospital", "mehmonxona": "hotel",
    "maktab": "school", "ish": "briefcase", "kalendar": "calendar", "yangilik": "newspaper",
    "kuch": "muscle", "yugurish": "runner", "suzish": "swimmer", "kino": "movie_camera",
    "sovg'a": "gift", "tug'ilgan kun": "birthday", "qor": "snowflake", "shamol": "wind",
    "bulut": "cloud", "momaqaldiroq": "zap", "yashil": "green_circle", "qizil": "red_circle",
    "ko'k": "blue_circle", "sariq": "yellow_circle", "qora": "black_circle",
    "oq": "white_circle", "quyosh ko'zoynak": "sunglasses", "noma'lum": "question",
}


def load_base():
    """Asosiy (16.0) ma'lumotlar — tools/base_data.json (git asl index.html dan)."""
    with open(BASE_DATA, encoding="utf-8") as f:
        return json.load(f)


def build():
    D = load_base()
    cats = list(D["cats"])
    codes = list(D["codes"])
    names = list(D["names"])
    cats_i = list(D["cats_i"])
    search = list(D["search"])

    assert len(codes) == len(names) == len(cats_i) == len(search), "D uzunliklari mos kelmadi"

    # 17.0 ni qo'shish
    for code, name, uz in NEW_17:
        codes.append(code)
        names.append(name)
        cats_i.append(NEW_CAT)
        search.append(f"{name} {uz} 17.0")

    # nom -> indeks xaritasi (o'zbek kalitlarini bog'lash uchun)
    name_to_idx = {}
    for i, n in enumerate(names):
        name_to_idx.setdefault(n, i)

    # o'zbekcha qidiruv kalitlarini qo'shish
    for uz, en_name in UZ_SEARCH.items():
        idx = name_to_idx.get(en_name)
        if idx is None:
            continue
        extra = " " + uz
        if uz not in search[idx]:
            search[idx] += extra

    # skin-tone xaritasi: base -> [tone0..tone4] (yo'q bo'lsa None)
    ej = json.load(open(EMOJI_JSON, encoding="utf-8"))
    skin = {}
    for e in ej:
        sv = e.get("skin_variations")
        if not sv:
            continue
        base = e["unified"].lower()
        arr = [None, None, None, None, None]
        for tone, info in sv.items():
            try:
                t = SKIN_TONES.index(tone.lower())
            except ValueError:
                continue
            arr[t] = info["unified"].lower()
        if any(arr):
            skin[base] = arr

    # spritesheet uchun faqat mavjud PNG larni olish (17.0 rasmlari hali yo'q)
    sheet_codes = [c for c in codes if os.path.exists(os.path.join(EMOJI_DIR, c + ".png"))]
    missing = [c for c in codes if not os.path.exists(os.path.join(EMOJI_DIR, c + ".png"))]
    cols = COLS
    rows = (len(sheet_codes) + cols - 1) // cols

    # montage uchun tartibli ro'yxat fayli
    order_txt = os.path.join(ROOT, "tools", "_sheet_order.txt")
    with open(order_txt, "w", encoding="utf-8") as f:
        for c in sheet_codes:
            f.write(os.path.join(EMOJI_DIR, c + ".png") + "\n")

    print(f"Spritesheet yaratilmoqda: {len(sheet_codes)} ta rasm, {cols}x{rows}...")
    subprocess.run(
        ["montage", "@" + order_txt, "-tile", f"{cols}x", "-geometry", f"{TILE}x{TILE}+0+0",
         "-background", "none", SHEET],
        check=True,
    )
    print("sheet.png tayyor:", SHEET)

    # kod -> [ustun, qator]
    sheet_map = {}
    for i, c in enumerate(sheet_codes):
        sheet_map[c] = [i % cols, i // cols]

    # picker.js yozish
    out = []
    out.append("// Avtomatik yaratilgan fayl — tools/build_picker.py bilan.\n")
    out.append("// Qo'lda tahrirlash tavsiya etilmaydi.\n")
    out.append("window.PICKER = {\n")
    out.append(f'  version: "17.0",\n')
    out.append(f"  tile: {TILE},\n")
    out.append(f"  cats_en: {json.dumps(cats, ensure_ascii=False)},\n")
    out.append(f"  cats_uz: {json.dumps(UZ_CATS, ensure_ascii=False)},\n")
    out.append(f"  codes: {json.dumps(codes, ensure_ascii=False)},\n")
    out.append(f"  names: {json.dumps(names, ensure_ascii=False)},\n")
    out.append(f"  cats_i: {json.dumps(cats_i)},\n")
    out.append(f"  search: {json.dumps(search, ensure_ascii=False)},\n")
    out.append(f"  skin: {json.dumps(skin, ensure_ascii=False)},\n")
    out.append(f"  new17: {json.dumps([c for c, _, _ in NEW_17])},\n")
    out.append(f"  sheet: {{ tile: {TILE}, cols: {cols}, rows: {rows}, "
               f"map: {json.dumps(sheet_map, ensure_ascii=False)} }}\n")
    out.append("};\n")
    with open(OUT_JS, "w", encoding="utf-8") as f:
        f.write("".join(out))
    print(f"picker.js yozildi ({len(codes)} ta emoji, {len(missing)} tasi 17.0 rasmisiz).")
    if missing:
        print("Rasmsiz kodlar (belgi sifatida ko'rsatiladi):", missing)


if __name__ == "__main__":
    build()
