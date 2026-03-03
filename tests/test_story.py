# SPDX-FileCopyrightText: © 2025 Fatih Burak Karagöz
# SPDX-License-Identifier: MIT

"""
Bu betik, `durak` kütüphanesinin temel temizleme ve işleme fonksiyonlarının
`sample_story.txt` üzerindeki etkisini göstermek için hazırlanmıştır.
"""
import json
from pathlib import Path

from durak import Pipeline, clean_text


def main() -> None:
    story_path = Path(__file__).parent / "data" / "sample_story.txt"
    original_text = story_path.read_text(encoding="utf-8")

    cleaned_text = clean_text(original_text)
    output_clean_text = Path(__file__).parent / ".." / "tmp" / "output_clean_text.txt"
    output_clean_text.write_text(cleaned_text, encoding="utf-8")
    
    pipeline = Pipeline(["clean", "tokenize", "remove_stopwords"])
    processed_tokens = pipeline(original_text)
    output_processed_tokens = (
        Path(__file__).parent / ".." / "tmp" / "output_tokens.json"
    )
    with output_processed_tokens.open("w", encoding="utf-8") as f:
        json.dump(processed_tokens, f, ensure_ascii=False, indent=4)
    print(f"\nİşlenmiş token'lar '{output_processed_tokens}' dosyasına kaydedildi.")


if __name__ == "__main__":
    main()
