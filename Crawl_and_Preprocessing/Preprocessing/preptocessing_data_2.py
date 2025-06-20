import pandas as pd
import re


def reduce_repeated_chars(word):
    return re.sub(r'(.)\1+', r'\1', word)  # Giảm ký tự lặp về 1 lần


def split_compound_word(word):
    word = reduce_repeated_chars(word)
    vowels = r'[aeiouyàáảãạèéẻẽẹìíỉĩịòóỏõọùúủũụỳýỷỹỵăâêôơưằắẳẵặầấẩẫậềếểễệồốổỗộờớởỡợừứửữựđ]'
    parts = []
    current_part = ""

    for char in word:
        current_part += char
        if re.search(vowels, char) and len(current_part) > 1:
            if re.search(vowels, current_part[:-1]):
                parts.append(current_part[:-1])
                current_part = char
    if current_part:
        parts.append(current_part)

    return parts


def is_valid_vietnamese_word(word, removed_words):
    if len(word) < 1 or len(word) > 10:
        removed_words.append(word)
        return False

    if not re.search(r'[aeiouyàáảãạèéẻẽẹìíỉĩịòóỏõọùúủũụỳýỷỹỵăâêôơưằắẳẵặầấẩẫậềếểễệồốổỗộờớởỡợừứửữựđ]', word):
        removed_words.append(word)
        return False

    return True


def preprocess_text_vietnamese(text):
    removed_words = []
    if isinstance(text, str):
        text = re.sub(r'\.(?!\s|$)', '. ', text)
        text = re.sub(r',(?!\s|$)', ', ', text)
        text = text.lower()
        text = re.sub(r'[^a-zA-ZÀ-ỹ\s.,]', ' ', text)
        if text.strip() == 'đánh giá':
            return '', removed_words

        parts = re.split(r'([.,]\s)', text)
        filtered_parts = []

        for part in parts:
            if part in ['. ', ', ']:
                filtered_parts.append(part)
                continue
            words = part.split()
            filtered_words = []

            for word in words:
                if len(word) > 10:
                    split_words = split_compound_word(word)
                else:
                    split_words = [word]

                for split_word in split_words:
                    split_word = reduce_repeated_chars(split_word)
                    if is_valid_vietnamese_word(split_word, removed_words):
                        filtered_words.append(split_word)

            filtered_part = ' '.join(filtered_words)
            if filtered_part:
                filtered_parts.append(filtered_part)

        text = ''.join(filtered_parts)
        text = re.sub(r'\s+', ' ', text).strip()

        if not text:
            return '', removed_words
    else:
        text = ''
    return text, removed_words


def preprocess_dataset(input_file, output_file):
    df = pd.read_excel(input_file)
    all_removed_words = []

    def apply_preprocessing(row):
        text, removed = preprocess_text_vietnamese(row['review_text'])
        all_removed_words.extend(removed)
        return text

    df['review_text'] = df.apply(apply_preprocessing, axis=1)
    df = df[df['review_text'] != '']
    df.to_excel(output_file, index=False)
    print(f"Đã lưu dataset đã tiền xử lý vào file Excel: {output_file}")
    unique_removed_words = sorted(set(all_removed_words))
    print("\nCác từ bị xóa:")
    print(unique_removed_words)

   
if __name__ == "__main__":

    BASE_DIR = Path(__file__).resolve().parents[1]

    RAW_DIR         = BASE_DIR / "Data" / "raw"
    PREP_DIR        = BASE_DIR / "Data" / "preprocessed"

    input_file      = RAW_DIR / "lazada_reviews_full.xlsx"
    output_file     = PREP_DIR / "lazada_reviews_full_preprocessed.xlsx"

    input_file_tiki  = RAW_DIR / "tiki_reviews_full.xlsx"
    output_file_tiki = PREP_DIR / "tiki_reviews_full_preprocessed.xlsx"

    PREP_DIR.mkdir(parents=True, exist_ok=True)

    preprocess_dataset(str(input_file), str(output_file))
    preprocess_dataset(str(input_file_tiki), str(output_file_tiki))

    print("Done preprocessing:")
    print(f"  • {output_file}")
    print(f"  • {output_file_tiki}")
