import pandas as pd
import re
import asyncio
import time
import sys
from itertools import cycle
import json
import os
from groq import Groq, RateLimitError, APIError
from pathlib import Path
# Danh sách API key và model
API_KEYS = [

     "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",
]
MODELS = [
    "deepseek-r1-distill-llama-70b",
]

if len(API_KEYS) != len(MODELS):
    raise ValueError("Số lượng API key và model phải khớp nhau!")


def parse_label_string(label_str, expected_count):

    json_match = re.search(r'```json\s*\n(.*?)\n```', label_str, re.DOTALL)
    if json_match:
        json_str = json_match.group(1).strip()
    else:
        print(f"Could not find JSON block in response, attempting raw parse: {label_str}")
        json_str = label_str.strip()
        json_str = re.sub(r'<think>.*?</think>', '', json_str, flags=re.DOTALL).strip()

    try:

        labels = json.loads(json_str)
        if not isinstance(labels, list):
            print(f"Invalid structure: Expected a list, got {type(labels)}. Raw string: {json_str}")
            return None
        if len(labels) != expected_count:
            print(f"Invalid structure: Expected {expected_count} sublists, got {len(labels)} sublists. Raw string: {json_str}")
            return None
        for i, sublist in enumerate(labels):
            if not isinstance(sublist, list):
                print(f"Invalid structure: Sublist {i} is not a list, got {type(sublist)}. Raw string: {json_str}")
                return None
            if len(sublist) != 6:
                print(f"Invalid structure: Sublist {i} does not have 6 elements, got {len(sublist)}. Raw string: {json_str}")
                return None
            if sublist[0] not in ["positive", "negative", "neutral"]:
                print(f"Invalid structure: Sublist {i} has invalid emotion: {sublist[0]}. Raw string: {json_str}")
                return None
            if not all(label in ["yes", "no"] for label in sublist[1:]):
                print(f"Invalid structure: Sublist {i} has invalid category values: {sublist[1:]}. Raw string: {json_str}")
                return None
        return labels
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}. Original JSON string: {json_str}")
        return None
    except Exception as e:
        print(f"Parse error: {e}. Original JSON string: {json_str}")
        return None


async def get_labels_from_grok(client, texts, model):
    if not texts or not all(isinstance(t, str) for t in texts):
        return None

    prompt = (
        """
        Bạn là chuyên gia phân tích nội dung khách hàng. Nhiệm vụ: Phân loại 5 đoạn văn bản (tiếng Việt hoặc tiếng Anh) dựa trên các tiêu chí sau:

1. **Cảm xúc (emotion)**: Chỉ chọn một trong "positive", "negative", hoặc "neutral".
   - "negative": Nếu có bất kỳ yếu tố tiêu cực nào (dù nhẹ), như lỗi giao hàng, sản phẩm không đúng mô tả, không hài lòng (ví dụ: "giao sai", "làm sao đẹp bằng").
   - "positive": Nếu chỉ có yếu tố tích cực (hài lòng, khen ngợi) và không có yếu tố tiêu cực.
   - "neutral": Nếu không có cảm xúc rõ ràng, không tích cực cũng không tiêu cực, hoặc câu có cả khen hoặc chê trong câu cân bằng nhau.
    - **Xử lý typo và từ không rõ nghĩa**: Hiểu các từ viết sai chính tả (ví dụ: "rât hai long" là "rất hài lòng"). Nếu gặp từ không rõ nghĩa (ví dụ: "quyê"), dựa vào ngữ cảnh chính để đánh giá cảm xúc (ví dụ: "khá thích quyê" có ngữ cảnh tích cực từ "khá thích" → "positive").

2. **Danh mục**: Gán "yes" nếu có, "no" nếu không.
   - **sản phẩm**: Đề cập đến chất lượng, đặc điểm, hoặc vấn đề của sản phẩm (bao gồm "đúng như hình", "ko giống mẫu").
   - **giá cả**: Đề cập đến giá tiền, chi phí.
   - **vận chuyển**: Đề cập đến giao hàng, vận chuyển.
   - **thái độ và dịch vụ khách hàng**: Đề cập đến thái độ phục vụ, dịch vụ hỗ trợ.
   - **Khác**: Chỉ gán "yes" nếu có nội dung không thuộc 4 danh mục trên (ví dụ: lời khuyên chung, ngữ cảnh mua sắm như "để tiền mua gì mà ăn").

**Đầu ra**: 
- Trả về JSON gồm 2 mảng con, mỗi mảng 6 phần tử: [emotion, sản phẩm, giá cả, vận chuyển, thái độ và dịch vụ khách hàng, Khác].
- Định dạng: [["emotion", "yes/no", "yes/no", "yes/no", "yes/no", "yes/no"], ["emotion", "yes/no", "yes/no", "yes/no", "yes/no", "yes/no"]].
- **Chỉ trả về JSON**, không thêm bất kỳ nội dung nào khác . 

**Ví dụ**:
vd1. "giao sai, đặt màu đen giao màu nâu" → ["negative", "yes", "no", "yes", "no", "no"]
   (Lỗi giao hàng → "negative", liên quan sản phẩm và vận chuyển.)
vd2. "với giá tiền rẻ, thì làm sao đẹp bằng, chờ xem chất lượng" → ["negative", "yes", "yes", "no", "no", "no"]
   ("làm sao đẹp bằng" là tiêu cực → "negative", liên quan sản phẩm và giá cả.)
vd3. "ae để tiền mua gì mà ăn chứ đừng mua cái này" → ["negative", "yes", "no", "no", "no", "yes"]
   ("đừng mua" là tiêu cực → "negative", "để tiền mua gì mà ăn" là lời khuyên chung → "Khác".)

**Phân loại các đoạn văn bản sau**:
        """
    )

    for i, text in enumerate(texts, 1):
        prompt += f"{i}. {text}\n"

    try:
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model=model,
            messages=[{"role": "user", "content": prompt}],
            timeout=30
        )
        label_str = response.choices[0].message.content.strip()
        print(f"API response with model '{model}': {label_str}")
        return parse_label_string(label_str, len(texts))
    except RateLimitError as e:
        print(f"Rate limit error: {e}")
        return None
    except APIError as e:
        print(f"API error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

async def process_reviews_batch(reviews, key_model_cycle):
    attempts = 0
    max_attempts = len(API_KEYS) * 5

    while attempts < max_attempts:
        key, model = next(key_model_cycle)
        client = Groq(api_key=key)
        result = await get_labels_from_grok(client, reviews, model)
        if result is not None:
            return result
        print(f"Attempt {attempts + 1}/{max_attempts} failed with key '{key[:10]}...' and model '{model}'")
        attempts += 1
        await asyncio.sleep(1)
    print(f"Failed to process batch after {max_attempts} attempts")
    return None

async def categorize_reviews(input_file, output_file, temp_file, api_keys, models):
    start_time = time.time()

    categories = ["emotion", "sản phẩm", "giá cả", "vận chuyển", "thái độ và dịch vụ khách hàng", "Khác"]

    if os.path.exists(output_file):
        print(f"File {output_file} exists. Checking for incomplete rows...")
        try:
            df = pd.read_excel(output_file)
            print(f"Loaded output file with {len(df)} rows")
            for category in categories:
                if category not in df.columns:
                    df[category] = None
        except Exception as e:
            print(f"Error reading output file: {e}. Starting from input file...")
            df = pd.read_excel(input_file)
            for category in categories:
                df[category] = None
    else:
        print(f"File {output_file} does not exist. Starting labeling from input file {input_file}...")
        try:
            df = pd.read_excel(input_file)
            print(f"Loaded input file with {len(df)} rows")
            for category in categories:
                df[category] = None
        except Exception as e:
            print(f"Error reading input file: {e}")
            return

    if os.path.exists(temp_file):
        print(f"File {temp_file} exists. Loading temporary progress...")
        try:
            df = pd.read_excel(temp_file)
            print(f"Loaded temp file with {len(df)} rows")
        except Exception as e:
            print(f"Error reading temp file: {e}. Continuing with current DataFrame...")

    df = df[df['review_text'].notna() & (df['review_text'] != '')]
    print(f"After filtering, {len(df)} rows remain")

    incomplete_rows = df[categories].isna().any(axis=1)
    incomplete_reviews = df[incomplete_rows]['review_text'].tolist()
    incomplete_indices = df[incomplete_rows].index.tolist()

    if not incomplete_reviews:
        print("All reviews have been labeled. No further processing needed.")
        df.to_excel(output_file, index=False)
        return

    print(f"Found {len(incomplete_reviews)} reviews with missing labels")

    batch_size = 5
    max_concurrent =  3
    key_model_cycle = cycle(zip(api_keys, models))

    batches = [incomplete_reviews[i:i + batch_size] for i in range(0, len(incomplete_reviews), batch_size)]
    batch_indices = [incomplete_indices[i:i + batch_size] for i in range(0, len(incomplete_indices), batch_size)]

    processed_reviews = 0
    lock = asyncio.Lock()

    async def process_all_batches():
        nonlocal processed_reviews

        for i in range(0, len(batches), max_concurrent):
            batch_group = batches[i:i + max_concurrent]
            indices_group = batch_indices[i:i + max_concurrent]
            tasks = []
            for batch, indices in zip(batch_group, indices_group):
                if len(batch) < batch_size:
                    batch.extend([""] * (batch_size - len(batch)))
                tasks.append((process_reviews_batch(batch, key_model_cycle), indices))

            results = await asyncio.gather(*[task[0] for task in tasks], return_exceptions=True)

            async with lock:
                for (task, indices), result in zip(tasks, results):
                    if isinstance(result, Exception) or result is None:
                        print(f"Batch failed after all attempts, assigning None to labels")
                        for idx in indices:
                            for category in categories:
                                df.at[idx, category] = None
                    else:
                        if len(result) != len(indices):
                            print(f"Mismatch: Expected {len(indices)} labels, got {len(result)}")
                            for idx in indices:
                                for category in categories:
                                    df.at[idx, category] = None
                        else:
                            print(f"Batch labels: {result}")
                            for idx, labels in zip(indices, result):
                                for category_idx, category in enumerate(categories):
                                    df.at[idx, category] = labels[category_idx]

                    processed_reviews += len(indices)
                    print(f"Processed {processed_reviews}/{len(incomplete_reviews)} reviews")

                    if processed_reviews % 50 == 0:
                        try:
                            df.to_excel(temp_file, index=False)
                            print(f"Saved temporary progress to {temp_file} after processing {processed_reviews} reviews")
                        except Exception as e:
                            print(f"Error saving temp file: {e}")

                    if processed_reviews % 100 == 0:
                        try:
                            df.to_excel(output_file, index=False)
                            print(f"Processed {processed_reviews} reviews and saved to {output_file} (checkpoint)")
                        except Exception as e:
                            print(f"Error saving output file: {e}")

    try:
        await process_all_batches()
    except KeyboardInterrupt:
        print("Process interrupted by user. Saving current progress...")
        try:
            df.to_excel(temp_file, index=False)
            print(f"Temporary progress saved to {temp_file}")
            df.to_excel(output_file, index=False)
            print(f"Final progress saved to {output_file}")
        except Exception as e:
            print(f"Error saving files: {e}")
        return

    try:
        df.to_excel(output_file, index=False)
        print(f"Final save to {output_file}")
    except Exception as e:
        print(f"Error saving final output file: {e}")

    for label in categories:
        if label == "emotion":
            counts = df[label].value_counts()
            print(f"{label}: {counts.to_dict()}")
        else:
            n_yes = len(df[df[label] == 'yes'])
            n_no = len(df[df[label] == 'no'])
            n_none = len(df[df[label].isna()])
            print(f"{label}: Yes: {n_yes}, No: {n_no}, None: {n_none}")

    print(f"Đã lưu dataset vào file: {output_file}")
    end_time = time.time()
    print(f"Total processing time: {end_time - start_time:.2f} seconds")

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())



if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

if __name__ == "__main__":
    SCRIPT_DIR = Path(__file__).resolve().parent

    INPUT_DIR = SCRIPT_DIR.parent / "Crawl_and_preprocesing" / "Data" / "preprocessed"

    OUTPUT_DIR = SCRIPT_DIR.parent / "Data"

    input_file  = INPUT_DIR / "combined_data_3.xlsx"
    output_file = OUTPUT_DIR / "data_final.xlsx"
    temp_file   = OUTPUT_DIR / "data_final_temp.xlsx"  
    asyncio.run(categorize_reviews(
        str(input_file),
        str(output_file),
        str(temp_file),
        API_KEYS,
        MODELS
    ))
