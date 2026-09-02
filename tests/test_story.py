# SPDX-FileCopyrightText: © 2025 Fatih Burak Karagöz
# SPDX-License-Identifier: LicenseRef-Durak-NonCommercial-1.2

"""
Bu betik, `durak` kütüphanesinin temel temizleme ve işleme fonksiyonlarının
`sample_story.txt` üzerindeki etkisini göstermek için hazırlanmıştır.
"""

import json
from pathlib import Path

from durak import clean_text, process_text


def main() -> None:
    story_path = Path(__file__).parent / "data" / "sample_story.txt"
    original_text = story_path.read_text(encoding="utf-8")

    cleaned_text = clean_text(original_text)
    output_clean_text = Path(__file__).parent / ".." / "tmp" / "output_clean_text.txt"
    output_clean_text.write_text(cleaned_text, encoding="utf-8")

    processed_tokens = process_text(original_text, remove_stopwords=True)
    otuput_processed_tokens = (
        Path(__file__).parent / ".." / "tmp" / "output_tokens.json"
    )
    with otuput_processed_tokens.open("w", encoding="utf-8") as f:
        json.dump(processed_tokens, f, ensure_ascii=False, indent=4)
    print(f"\nİşlenmiş token'lar '{otuput_processed_tokens}' dosyasına kaydedildi.")


if __name__ == "__main__":
    main()
