import csv
import os

def get_nllb_codes():
    file_path = os.path.join(os.path.dirname(__file__), "metrics.csv")
    codes = set()
    with open(file_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            direction = row["direction"]
            src, tgt = direction.split("-")
            codes.add(src)
            codes.add(tgt)
    return sorted(list(codes))

NAME_TO_NLLB = {
    "vietnamese": "vie_Latn",
    "vi": "vie_Latn",
    "english": "eng_Latn",
    "en": "eng_Latn",
    "french": "fra_Latn",
    "fr": "fra_Latn",
    "german": "deu_Latn",
    "de": "deu_Latn",
    "spanish": "spa_Latn",
    "es": "spa_Latn",
    "chinese": "zho_Hans",
    "zh": "zho_Hans",
    "japanese": "jpn_Jpan",
    "ja": "jpn_Jpan",
    "korean": "kor_Hang",
    "ko": "kor_Hang"
}

def map_to_nllb(lang_name: str) -> str:
    lang_name = lang_name.lower().strip()
    if lang_name in NAME_TO_NLLB:
        return NAME_TO_NLLB[lang_name]
    return "eng_Latn"
