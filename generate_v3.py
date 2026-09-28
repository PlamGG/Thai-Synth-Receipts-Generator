from collections import defaultdict
import os
import json
import yaml
import random
import cv2
import numpy as np
from src.catalog_th import CATEGORIES, build_document_data, data_to_plain_text
from src.template_engine_v3 import generate_template_v3
from src.augmentation_v3 import apply_printer_error, apply_photographed, apply_signature

def setup_folders(output_dir, splits=("train", "validation", "test")):
    dirs = []
    for split in splits:
        for variant in ["clean", "error", "photo"]:
            for sub in ["images", "json", "text"]:
                dirs.append(f"{output_dir}/{split}/{variant}/{sub}")
    dirs.append(f"{output_dir}/spot_checks")
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def save_variant(base_id, variant, split, img, bboxes, data, plain_text, output_dir):
    img_path = f"{output_dir}/{split}/{variant}/images/{base_id}_{variant}.jpg"
    json_path = f"{output_dir}/{split}/{variant}/json/{base_id}_{variant}.json"
    txt_path = f"{output_dir}/{split}/{variant}/text/{base_id}_{variant}.txt"
    
    img.save(img_path, quality=90)
    
    output_data = data.copy()
    output_data["image_width"] = img.width
    output_data["image_height"] = img.height
    output_data["ocr_boxes"] = bboxes
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
        
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(plain_text)
        
    # คืนค่าเป็น dict สำหรับบันทึกลง metadata.jsonl
    return {
        "file_name": f"{variant}/images/{base_id}_{variant}.jpg",
        "ground_truth": json.dumps(output_data, ensure_ascii=False)
    }

def do_spot_check(img_path, json_path, out_path):
    img = cv2.imread(img_path)
    if img is None: return
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    for item in data['ocr_boxes']:
        pts = np.array(item['box'], np.int32).reshape((-1, 1, 2))
        cv2.polylines(img, [pts], isClosed=True, color=(0, 0, 255), thickness=2)
    cv2.imwrite(out_path, img)


def validate_assets():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(base_dir, "assets")
    bg_dir = os.path.join(assets_dir, "backgrounds")
    fonts_dir = os.path.join(assets_dir, "fonts")
    
    if not os.path.exists(bg_dir):
        raise FileNotFoundError(f"Backgrounds folder not found: {bg_dir}")
    
    bg_files = [f for f in os.listdir(bg_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    if not bg_files:
        raise FileNotFoundError(f"No image files found in backgrounds folder: {bg_dir}")
        
    required_fonts = ["Kanit-Bold.ttf", "Kanit-Regular.ttf", "Sarabun-Regular.ttf"]
    for font in required_fonts:
        font_path = os.path.join(fonts_dir, font)
        if not os.path.exists(font_path):
            raise FileNotFoundError(f"Required font not found: {font_path}")


CATEGORY_DOC_TYPES = {
    "cafe":         ["receipt", "thermal_slip"],
    "supermarket":  ["receipt", "thermal_slip"],
    "construction": ["tax_invoice", "quotation", "receipt"],
    "it":           ["tax_invoice", "quotation", "receipt"],
}

def build_tasks(category_doc_types, num_per_category, seed):
    rng = random.Random(seed)
    tasks = []
    for cat, doc_types in category_doc_types.items():
        if cat not in CATEGORIES:
            continue
        base = num_per_category // len(doc_types)
        remainder = num_per_category % len(doc_types)
        counts = {dt: base for dt in doc_types}
        for dt in rng.sample(doc_types, remainder):
            counts[dt] += 1
        for dt, cnt in counts.items():
            tasks.extend([(cat, dt)] * cnt)
    rng.shuffle(tasks)
    return tasks

def make_splits(tasks, split_ratio, seed):
    rng = random.Random(seed)
    groups = defaultdict(list)
    for idx, (cat, dtype) in enumerate(tasks, 1):
        doc_prefix = {"receipt": "RCT", "tax_invoice": "INV", "quotation": "QUO", "thermal_slip": "THM"}[dtype]
        sample_id = f"TH-{doc_prefix}-{idx:06d}"
        groups[(cat, dtype)].append(sample_id)

    split_map = {}
    for key, ids in groups.items():
        rng.shuffle(ids)
        n = len(ids)
        n_train = int(n * split_ratio.get("train", 0.9))
        n_val = int(n * split_ratio.get("validation", 0.05))
        for sid in ids[:n_train]:
            split_map[sid] = "train"
        for sid in ids[n_train:n_train + n_val]:
            split_map[sid] = "validation"
        for sid in ids[n_train + n_val:]:
            split_map[sid] = "test"
    return split_map

def main():
    validate_assets()
    cfg = yaml.safe_load(open("config.yaml", encoding="utf-8"))
    enabled_augmentations = cfg.get("augmentations", ["fade", "streaks", "blur", "artifacts", "skew", "fold", "broken"])
    output_dir = cfg.get("output_dir", "dataset")
    
    seed = cfg.get("seed", 42)
    random.seed(seed)
    np.random.seed(seed)
    
    setup_folders(output_dir)
    
    # Calculate docs based on config
    num_samples_per_type = cfg.get("num_samples_per_type", 10)
    doc_types = cfg.get("doc_types", ["tax_invoice", "receipt"])
    num_unique_docs = num_samples_per_type * len(doc_types) * len(CATEGORIES)
    
    num_per_category = num_unique_docs // len(CATEGORIES)
    tasks = build_tasks(CATEGORY_DOC_TYPES, num_per_category, seed)
    
    split_ratio = cfg.get("split_ratio", {"train": 0.9, "validation": 0.05, "test": 0.05})
    split_map = make_splits(tasks, split_ratio, seed)
    metadata_by_split = defaultdict(list)
    
    success_count = 0
    failed_count = 0
    failed_ids = []

    for doc_count, (category, doc_type) in enumerate(tasks, 1):
        doc_prefix = {"receipt": "RCT", "tax_invoice": "INV", "quotation": "QUO", "thermal_slip": "THM"}[doc_type]
        sample_id = f"TH-{doc_prefix}-{doc_count:06d}"
        
        split = split_map.get(sample_id, "train")
        data = build_document_data(category, doc_type, sample_id, split=split)
        plain_text = data_to_plain_text(data)
        
        try:
            clean_img, clean_bboxes = generate_template_v3(data)
            
            if doc_type in ["tax_invoice", "quotation"] or random.random() > 0.7:
                clean_img, clean_bboxes = apply_signature(clean_img, clean_bboxes, doc_type)
            
            # 1. Clean
            meta_c = save_variant(sample_id, "clean", split, clean_img, clean_bboxes, data, plain_text, output_dir)
            
            # 2. Error
            error_img, error_bboxes = apply_printer_error(clean_img, clean_bboxes, enabled_effects=enabled_augmentations)
            meta_e = save_variant(sample_id, "error", split, error_img, error_bboxes, data, plain_text, output_dir)
            
            # 3. Photo
            photo_img, photo_bboxes = apply_photographed(clean_img, clean_bboxes, data, difficulty="random")
            meta_p = save_variant(sample_id, "photo", split, photo_img, photo_bboxes, data, plain_text, output_dir)
            
            metadata_by_split[split].append(meta_c)
            metadata_by_split[split].append(meta_e)
            metadata_by_split[split].append(meta_p)
            
            
            success_count += 1
            if doc_count % 10 == 0:
                print(f"Generated {doc_count}/{num_unique_docs} unique docs...")
        except Exception as e:
            print(f"Error generating {sample_id}: {e}")
            failed_count += 1
            failed_ids.append(sample_id)
            
    # Save metadata.jsonl for each split
    for split_name, lines in metadata_by_split.items():
        with open(f"{output_dir}/{split_name}/metadata.jsonl", "w", encoding="utf-8") as f:
            for line_dict in lines:
                f.write(json.dumps(line_dict, ensure_ascii=False) + "\n")
            
    # --- Stratified Spot Checks (ขั้นต่ำ 1 ภาพ / doc_type x variant) ---
    print("Doing Stratified Spot Checks...")
    seen_combos = set()
    spot_checks_done = 0
    
    # เรามี generated_photos เป็น list ของ (dtype, variant, img_path, json_path, out_path)
    # แต่โค้ดเดิมไม่ได้เก็บ dtype กับ variant ไว้ใน tuple 
    # เดี๋ยวเราแก้ให้ loop จาก metadata_lines แทน หรือทำตอนเซฟก็ได้
    # เอาแบบง่ายสุดคือ loop จาก generated_photos ที่จะบันทึก combo เข้าไปด้วย
    # แต่เพื่อให้แก้โค้ดน้อยที่สุด ขอเปลี่ยนแค่ส่วนท้าย
    
    # สุ่มรูปมาตรวจให้ครอบคลุม (เราจะดึงชื่อไฟล์มา parse หา combo)
    # ไฟล์ชื่อ: variant/images/TH-RCT-000001_variant.jpg
    for split_name, lines in metadata_by_split.items():
        for line_dict in lines:
            file_name = line_dict["file_name"]
            parts = file_name.split('/')
            variant = parts[0]
            base_name = parts[-1].split('_')[0]
            doc_prefix = base_name.split('-')[1]
            
            combo = (doc_prefix, variant)
            if combo not in seen_combos:
                seen_combos.add(combo)
                img_path = f"{output_dir}/{split_name}/{variant}/images/{base_name}_{variant}.jpg"
                json_path = f"{output_dir}/{split_name}/{variant}/json/{base_name}_{variant}.json"
                out_path = f"{output_dir}/spot_checks/chk_{doc_prefix}_{variant}.jpg"
                do_spot_check(img_path, json_path, out_path)
                spot_checks_done += 1
            
    print(f"Saved {spot_checks_done} stratified spot checks (covering all doc_types x variants).")
        
    print(f"\nDone! Successfully generated {success_count} unique docs x 3 variations = {success_count*3} images total.")
    if failed_count > 0:
        print(f"Failed to generate {failed_count} docs.")
        print(f"Sample failed IDs: {failed_ids[:5]}")
        error_log_path = f"{output_dir}/generation_errors.log"
        with open(error_log_path, "w", encoding="utf-8") as err_f:
            for fid in failed_ids:
                err_f.write(f"{fid}\n")
        print(f"Full list of failed IDs saved to {error_log_path}")
    print(f"Metadata saved to {output_dir}/metadata.jsonl (HuggingFace format).")

if __name__ == "__main__":
    main()
