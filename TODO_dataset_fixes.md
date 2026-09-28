# TODO: แก้ไข Thai Bill/Receipt Dataset Generator (generate_v3.py + ไฟล์ที่เกี่ยวข้อง)

> วิธีใช้ไฟล์นี้: ทำทีละข้อตามลำดับ (บนลงล่างสำคัญกว่า) เมื่อแก้เสร็จและทดสอบผ่านแล้วให้เปลี่ยน `[ ]` เป็น `[x]` ห้ามข้ามขั้น "เกณฑ์ผ่าน" ของแต่ละข้อ

---

## 0. ไฟล์ที่เกี่ยวข้อง
- `generate_v3.py`
- `config.yaml`
- `src/catalog_th.py`
- `src/template_engine_v3.py`
- `src/augmentation_v3.py`
- `src/icon_manager.py`
- `catalog_large.json` ✅ (อัปเดตแล้ว — ดูข้อ 9)

---

## 🔴 Critical

### [x] 1. อ่านค่าจาก `config.yaml` จริง ห้าม hardcode ซ้อน
**ปัญหาเดิม:** `main()` ใน `generate_v3.py` hardcode `num_unique_docs = 5000`, `"dataset"` เป็น output path ตรงๆ ทั้งที่ `config.yaml` มี `num_samples_per_type`, `output_dir`, `doc_types` อยู่แล้ว แต่ไม่เคยถูกอ่านเลย

**สิ่งที่ต้องทำ:**
- [ ] เพิ่ม `import yaml` และโหลด config ตอนต้น `main()`: `cfg = yaml.safe_load(open("config.yaml", encoding="utf-8"))`
- [ ] แทนที่ `num_unique_docs = 5000` ด้วยค่าที่คำนวณจาก config (เช่น `num_samples_per_type * len(doc_types) * len(CATEGORIES)` หรือตามที่ตกลง schema ของ config)
- [ ] แทนที่ `"dataset"` ทุกจุดด้วย `cfg["output_dir"]`
- [ ] ห้ามมี fallback hardcode ค่าอื่นซ่อนอยู่ในโค้ดที่ config ควบคุมได้แล้ว

**เกณฑ์ผ่าน:** แก้ `config.yaml` แล้วรัน `python generate_v3.py` ต้องได้จำนวนไฟล์/output path เปลี่ยนตาม config โดยไม่ต้องแก้โค้ด `.py` เลย

---

### [x] 2. ใช้ seed จาก config จริง (reproducibility)
**ปัญหาเดิม:** `config.yaml` มี `seed: 42` แต่ไม่มีการเรียก `random.seed()` ที่ไหนเลยในทั้งโปรเจกต์

**สิ่งที่ต้องทำ:**
- [ ] เรียก `random.seed(cfg["seed"])` เป็นบรรทัดแรกๆ ใน `main()` ก่อนสร้าง `tasks` ใดๆ

**เกณฑ์ผ่าน:** รัน `python generate_v3.py` สองรอบด้วย seed เดิม → ได้ `metadata.jsonl` และไฟล์ภาพ (เช็คด้วย hash หรือ diff ข้อมูล json) เหมือนกันทุกรอบ

---

### [x] 3. เช็ค assets (fonts, backgrounds) แบบ fail-fast ตอนเริ่มโปรแกรม
**ปัญหาเดิม:**
- `apply_photographed()` เรียก `os.listdir(bg_folder)` โดยไม่เช็คว่าโฟลเดอร์มีอยู่จริงก่อน → ถ้าไม่มี จะ `FileNotFoundError` (ยืนยันแล้วจากการทดสอบจริง) ซึ่งถูกกลืนด้วย `try/except` ใน `main()` ทำให้ **photo variant หายทั้งหมด** แบบเงียบๆ
- ฟอนต์ (Kanit, Sarabun, Itim, Sriracha, Mali) ถ้าหาไม่เจอ จะ fallback ไป `ImageFont.load_default()` ซึ่ง**render ภาษาไทยไม่ได้เลย** (ทดสอบแล้วได้กล่องดำล้วน) โดยไม่มี warning ใดๆ

**สิ่งที่ต้องทำ:**
- [ ] เพิ่มฟังก์ชัน `validate_assets()` เรียกตอนต้น `main()` ก่อน generate ใดๆ:
  - เช็ค `assets/backgrounds/` มีอยู่จริงและมีไฟล์ `.jpg`/`.png` อย่างน้อย 1 ไฟล์ ถ้าไม่มี → `raise FileNotFoundError` พร้อมข้อความชัดเจน
  - เช็คฟอนต์หลักที่ใช้บ่อย (Kanit-Bold.ttf, Kanit-Regular.ttf, Sarabun-Regular.ttf) มีอยู่จริงใน `assets/fonts/` ถ้าไม่มี → `raise FileNotFoundError` เช่นกัน (ห้ามปล่อยให้ fallback ไป default font เงียบๆ)
- [ ] path ของ `assets/` ควรอิงตำแหน่งสคริปต์ (เช่น `os.path.join(os.path.dirname(__file__), "assets")`) ไม่ใช่ relative ต่อ current working directory เพื่อกัน error กรณีรันจากคนละที่

**เกณฑ์ผ่าน:** ลบ/ย้ายโฟลเดอร์ `assets/fonts` หรือ `assets/backgrounds` ออกชั่วคราวแล้วรันสคริปต์ → ต้อง error ทันทีตั้งแต่ต้นโปรแกรมพร้อมข้อความบอกว่าไฟล์/โฟลเดอร์ไหนหาย ไม่ใช่รันไป 5000 docs แล้วค่อยพังทีละตัว

---

### [x] 4. นับจำนวน success/fail จริง และรายงานผลตามจริงตอนจบ
**ปัญหาเดิม:** ข้อความสรุปท้ายโปรแกรม (`print(f"\nDone! Generated {num_unique_docs} unique docs x 3 variations...")`) ใช้ตัวเลขที่ตั้งใจไว้ตอนแรก ไม่ใช่จำนวนที่สำเร็จจริง ถ้ามี doc ที่ error ระหว่างทาง ข้อความนี้จะโกหก

**สิ่งที่ต้องทำ:**
- [ ] เพิ่มตัวนับ `success_count`, `failed_count`, `failed_ids = []`
- [ ] ทุกครั้งที่เข้า `except Exception as e:` ให้ increment `failed_count` และเก็บ `sample_id` ไว้ใน `failed_ids`
- [ ] เปลี่ยนข้อความสรุปท้ายโปรแกรมให้ใช้ `success_count` และ `failed_count` จริง พร้อม list ตัวอย่าง `sample_id` ที่ fail (ถ้ามี) เพื่อ debug ง่าย
- [ ] เขียน `failed_ids` ลงไฟล์ log แยก (เช่น `dataset/generation_errors.log`) ถ้ามี failure

**เกณฑ์ผ่าน:** จำลองให้บาง doc fail (เช่น ลบสินค้าออกจาก catalog บาง category ชั่วคราว) แล้วรัน → ข้อความสรุปท้ายต้องตรงกับจำนวนไฟล์จริงในโฟลเดอร์ output

---

## 🟡 สำคัญสำหรับคุณภาพ dataset

### [x] 5. แก้ mapping category → doc_type ให้ตรงกับ CATEGORIES จริง (ไม่ใช้ list เดา) + สุ่มแบบเฉลี่ย
**ปัญหาเดิม:**
- เงื่อนไข `if cat in ["cafe", "supermarket", "restaurant", "pharmacy", "clothing", "bookstore", "pet_shop"]` มีชื่อ category ที่ไม่มีอยู่จริงใน `CATEGORIES` (`["cafe", "construction", "it", "supermarket"]`) — เป็นโค้ดตกค้าง
- ใช้ `random.choice(...)` เลือก doc_type ต่อ 1 เอกสาร ทำให้จำนวนต่อ doc_type ไม่เท่ากันและไม่ reproducible ตามสัดส่วนที่ตั้งใจ

**สิ่งที่ต้องทำ:**
- [ ] ประกาศ mapping ตรงๆ ให้ตรงกับ 4 categories จริง:
  ```python
  CATEGORY_DOC_TYPES = {
      "cafe":         ["receipt", "thermal_slip"],
      "supermarket":  ["receipt", "thermal_slip"],
      "construction": ["tax_invoice", "quotation", "receipt"],
      "it":           ["tax_invoice", "quotation", "receipt"],
  }
  ```
- [ ] เขียนฟังก์ชันแบ่งจำนวนเอกสารต่อ doc_type แบบ**หารเท่ากันก่อน แล้วแจกเศษแบบสุ่ม** (ไม่ใช่ `random.choice` อิสระทีละตัว) ตัวอย่าง logic:
  ```python
  def build_tasks(category_doc_types, num_per_category, seed):
      rng = random.Random(seed)
      tasks = []
      for cat, doc_types in category_doc_types.items():
          base = num_per_category // len(doc_types)
          remainder = num_per_category % len(doc_types)
          counts = {dt: base for dt in doc_types}
          for dt in rng.sample(doc_types, remainder):
              counts[dt] += 1
          for dt, cnt in counts.items():
              tasks.extend([(cat, dt)] * cnt)
      rng.shuffle(tasks)
      return tasks
  ```
- [ ] ลบ list เงื่อนไข category เดิมทิ้งทั้งหมด

**เกณฑ์ผ่าน:** หลัง generate เสร็จ, group `metadata.jsonl` (หรือ log ระหว่าง generate) ตาม `(category, doc_type)` แล้วนับจำนวน — ต้องเท่ากันหรือต่างกันไม่เกิน 1 ภายในหมวดเดียวกัน

---

### [x] 6. ลบโค้ด reassignment ตัวแปรที่ไม่จำเป็น
**ปัญหาเดิม:**
```python
data = build_document_data(category, doc_type, sample_id)
...
try:
    clean_img, clean_bboxes = generate_template_v3(data)
    doc_type = data.get("doc_type", "receipt")   # <-- บรรทัดนี้ไม่จำเป็น เขียนทับตัวแปร loop เดิม
```

**สิ่งที่ต้องทำ:**
- [ ] ลบบรรทัด `doc_type = data.get("doc_type", "receipt")` ทิ้ง (ค่าที่ได้เหมือนเดิมอยู่แล้วจาก tuple ของ loop)

**เกณฑ์ผ่าน:** โค้ดรันได้ผลลัพธ์เหมือนเดิมทุกอย่าง (regression test เทียบ output ก่อน/หลังแก้ด้วย seed เดียวกัน)

---

### [x] 7. เพิ่ม train/val/test split ตอน generate — แยกโฟลเดอร์จริง (group by sample_id + stratify)
**เหตุผล:** clean/error/photo ของ `sample_id` เดียวกันมีเนื้อหาเอกสารเหมือนกันทุกตัวเลข ถ้าปล่อยให้คนโหลดไปสุ่ม split เองทีหลัง (แบบสุ่มทีละแถว/รูป) จะเกิด **data leakage** — variant ของเอกสารเดียวกันหลุดไปอยู่คนละ split

**สำคัญ:** ต้อง**แยกเป็นโฟลเดอร์จริง** ไม่ใช่แค่ใส่ field `"split"` ในไฟล์ เพราะ HF `load_dataset("imagefolder", ...)` auto-detect split ได้จาก**ชื่อโฟลเดอร์บนสุด**เท่านั้น (`train`/`validation`/`test`) การใส่แค่ field ในไฟล์แล้วให้คนอื่น filter เองจะสร้างภาระ/ผิดพลาดง่ายกว่า

**โครงสร้างโฟลเดอร์ที่ต้องได้ (split อยู่นอกสุด, variant อยู่ข้างใน):**
```
dataset/
├── train/
│   ├── clean/{images,json,text}
│   ├── error/{images,json,text}
│   ├── photo/{images,json,text}
│   └── metadata.jsonl        ← รวมทุก variant เฉพาะของ split นี้
├── validation/
│   ├── clean/{images,json,text}
│   ├── error/{images,json,text}
│   ├── photo/{images,json,text}
│   └── metadata.jsonl
├── test/
│   └── ... (โครงสร้างเหมือนกัน)
└── spot_checks/               ← เก็บรวมที่เดียว ไม่ต้องแยก split (ใช้ QC เฉยๆ)
```
> ใช้ชื่อโฟลเดอร์ `validation` ไม่ใช่ `val` เพื่อให้ HF auto-map ชัดเจนไม่ต้องเดา

**สิ่งที่ต้องทำ:**
- [ ] ใส่สัดส่วน split เป็นค่าตั้งใน `config.yaml` เช่น:
  ```yaml
  split_ratio:
    train: 0.9
    validation: 0.05
    test: 0.05
  ```
- [ ] ก่อน generate เอกสาร ให้สร้าง `split_map: {sample_id: "train"/"validation"/"test"}` โดย:
  - Group ตาม `(category, doc_type)` ก่อน (stratify)
  - Shuffle ด้วย seed เดียวกับข้อ 2 แล้วแบ่งตามสัดส่วนจาก config
  - ทุก `sample_id` ต้องได้ split เดียวตลอด (clean/error/photo ของ id เดียวกันอยู่ split เดียวกันเสมอ)
  - ตัวอย่าง logic:
    ```python
    from collections import defaultdict

    def make_splits(tasks, split_ratio, seed):
        rng = random.Random(seed)
        groups = defaultdict(list)
        for cat, dtype, sid in tasks:
            groups[(cat, dtype)].append(sid)

        split_map = {}
        for key, ids in groups.items():
            rng.shuffle(ids)
            n = len(ids)
            n_train = int(n * split_ratio["train"])
            n_val = int(n * split_ratio["validation"])
            for sid in ids[:n_train]:
                split_map[sid] = "train"
            for sid in ids[n_train:n_train + n_val]:
                split_map[sid] = "validation"
            for sid in ids[n_train + n_val:]:
                split_map[sid] = "test"
        return split_map
    ```
- [ ] แก้ `setup_folders()` ให้สร้างโฟลเดอร์ตาม split ก่อน variant:
  ```python
  def setup_folders(output_dir, splits=("train", "validation", "test")):
      dirs = []
      for split in splits:
          for variant in ["clean", "error", "photo"]:
              for sub in ["images", "json", "text"]:
                  dirs.append(f"{output_dir}/{split}/{variant}/{sub}")
      dirs.append(f"{output_dir}/spot_checks")
      for d in dirs:
          os.makedirs(d, exist_ok=True)
  ```
- [ ] แก้ `save_variant()` ให้รับ `split` เพิ่ม แล้วปรับ path ทั้ง `img_path`, `json_path`, `txt_path` ให้มี `{split}/` นำหน้า `{variant}/`:
  ```python
  def save_variant(base_id, variant, split, img, bboxes, data, plain_text, output_dir):
      img_path = f"{output_dir}/{split}/{variant}/images/{base_id}_{variant}.jpg"
      json_path = f"{output_dir}/{split}/{variant}/json/{base_id}_{variant}.json"
      txt_path = f"{output_dir}/{split}/{variant}/text/{base_id}_{variant}.txt"
      ...
      return {
          # file_name ต้อง relative จากตำแหน่ง metadata.jsonl ของ split นั้นๆ (ไม่มี {split}/ นำหน้า)
          "file_name": f"{variant}/images/{base_id}_{variant}.jpg",
          "ground_truth": json.dumps(output_data, ensure_ascii=False)
      }
  ```
- [ ] เขียน `metadata.jsonl` **แยกไฟล์ต่อ split** (ไม่รวมเป็นไฟล์เดียวเหมือนโค้ดเดิมที่เขียน `dataset/metadata.jsonl` ไฟล์เดียว):
  ```python
  metadata_by_split = defaultdict(list)  # เก็บระหว่าง generate loop ตาม split ของแต่ละ sample_id

  for split in ["train", "validation", "test"]:
      with open(f"{output_dir}/{split}/metadata.jsonl", "w", encoding="utf-8") as f:
          for line_dict in metadata_by_split[split]:
              f.write(json.dumps(line_dict, ensure_ascii=False) + "\n")
  ```
- [ ] (ทางเลือกเสริม ไม่บังคับ) ใส่ field `"split"` ใน `output_data` (json ต่อรูป) ไว้ด้วยเผื่อใครเอาไฟล์ json ไปใช้แยกจากโครงสร้างโฟลเดอร์

**เกณฑ์ผ่าน:**
- โครงสร้างโฟลเดอร์จริงต้องเป็น `dataset/{train,validation,test}/{clean,error,photo}/...` ตามที่ระบุ ไม่ใช่ `dataset/{clean,error,photo}/...` แบบเดิม
- รัน `load_dataset("imagefolder", data_dir="dataset")` แล้วต้องได้ `DatasetDict` ที่มี key `train`, `validation`, `test` ครบ โดยไม่ต้องเขียนโค้ด filter เพิ่มเอง
- ไม่มี `sample_id` ใดปรากฏมากกว่า 1 split
- นับจำนวนต่อ `(category, doc_type, split)` แล้วสัดส่วนใกล้เคียงกับที่ตั้งไว้ในทุกกลุ่มย่อย (ไม่ใช่แค่ภาพรวม)

---

### [x] 8. ลบ import ที่ไม่ได้ใช้
**ปัญหาเดิม:** `from src.catalog_th import CATEGORIES, DOC_TYPES, ...` — `DOC_TYPES` ไม่เคยถูกใช้ใน `generate_v3.py`

**สิ่งที่ต้องทำ:**
- [ ] ลบ `DOC_TYPES` ออกจาก import (หรือใช้งานจริงถ้ามีเหตุผลใหม่)

**เกณฑ์ผ่าน:** รันแล้วไม่มี unused-import warning (เช่นจาก `pyflakes`/`ruff`)

---

## ✅ เสร็จแล้ว

### [x] 9. ขยาย `catalog_large.json` ให้มีสินค้าเพียงพอ
**ปัญหาเดิม:** item pool บางเกินไป (cafe=28, construction=30, supermarket=32, it=40) ทำให้สินค้าแต่ละชิ้นถูกใช้ซ้ำเฉลี่ย **150-183 ครั้ง** ทั่ว dataset (จำลองแล้ว) เสี่ยงให้โมเดล generalize ได้ไม่ดีกับชื่อสินค้าที่ไม่เคยเห็น

**สิ่งที่ทำไปแล้ว:**
- รวม fallback `PRODUCTS` จาก `catalog_th.py` + เขียนรายการใหม่เพิ่มเข้าไป (มีความหลากหลายของ size/สี/รุ่น)
- ผลลัพธ์: cafe 90, construction 90, supermarket 91, it 90 รายการ (ไม่มีชื่อซ้ำ, ราคาไม่ผิดปกติ — ตรวจสอบแล้ว)
- reuse rate เฉลี่ยลดลงจาก ~150-180x เหลือ **~55x** ต่อชิ้น

**ไฟล์ผลลัพธ์:** `catalog_large.json` (แทนที่ไฟล์เดิม)

**สิ่งที่ควรทำต่อ (ไม่บังคับ, เก็บไว้ทำทีหลัง):**
- [ ] (ไม่บังคับ) ขยาย customers (ปัจจุบัน 180) เพิ่มอีก ถ้าต้องการลด reuse ของลูกค้าใน tax_invoice ให้ต่ำลงอีก

---

### [x] 10. ขยาย merchant pool ในทุกหมวด
**ปัญหาเดิม:** merchant pool 90/หมวด ทำให้ชื่อร้านถูกใช้ซ้ำเฉลี่ย ~14 ครั้ง/ร้าน (ยอมรับได้แต่ไม่ optimal)

**สิ่งที่ทำไปแล้ว:** generate ชื่อร้านใหม่ด้วย name-template เดิมใน `catalog_th.py` (combinatorial, ไม่ใช่ list ตายตัว) จนชนเพดานคอมบิเนชัน ผลลัพธ์: it=300, construction=300, cafe=188, supermarket=174 (ไม่มีชื่อ/tax_id ซ้ำ) reuse เฉลี่ยลดเหลือ **4-7x**

**ไฟล์ผลลัพธ์:** `catalog_large.json` (รวมทั้ง item pool ข้อ 9 และ merchant pool ข้อนี้ไว้ในไฟล์เดียวแล้ว)

**สิ่งที่ควรทำต่อ (ไม่บังคับ):**
- [ ] (ไม่บังคับ) cafe/supermarket ชนเพดานคอมบิเนชันของ template ชื่อร้าน (~98/84 แบบ) ถ้าอยากได้มากกว่า 188/174 ต้องเพิ่มคำใน `NICKNAMES`/`AUSPICIOUS` หรือเพิ่ม pattern ชื่อใหม่ในฟังก์ชัน `generate_merchant_info()` ก่อน

---

### [x] 11. แก้ `config.yaml` augmentations ให้ตรงกับโค้ดจริง (ตอนนี้ชื่อไม่ตรงกันเลย)
**ปัญหาเดิม:** `config.yaml` ระบุ `augmentations: ["blur", "fold", "fade", "broken"]` แต่ `apply_printer_error()` ใน `augmentation_v3.py` **ไม่เคยอ้างอิงชื่อเหล่านี้เลย** ใช้เลข `1-5` hardcode แทน และ **ไม่มี effect "fold" (รอยพับ/ยับ) กับ "broken" (มุม/ขอบขาด) อยู่จริงในโค้ด** ทั้งที่ config ระบุว่ามี — เป็นช่องว่างระหว่างสิ่งที่ config บอกกับสิ่งที่ระบบทำจริง

**สิ่งที่ต้องทำ:**
- [ ] เปลี่ยน `apply_printer_error()` ให้รับ list ของ effect name จาก config แทนเลข 1-5 เช่น `apply_printer_error(img, bboxes, enabled_effects=cfg["augmentations"])`
- [ ] เขียน effect ใหม่ 2 ตัวที่ config อ้างถึงแต่ยังไม่มีจริง:
  - `"fold"` — จำลองรอยพับกระดาษ (เช่น เส้นตรง 1-2 เส้นพาดขวาง/แนวตั้ง พร้อมแถบเงา/สว่างบางๆ ตัดผ่านเส้นนั้น)
  - `"broken"` — จำลองมุมกระดาษขาด/ขอบกระดาษหาย (เช่น ตัดมุมหนึ่งของภาพเป็นรูปสามเหลี่ยม/ไม่เป็นระเบียบ แล้วเติมพื้นหลังสีขาวหรือโปร่งใสแทน)
- [ ] map ชื่อ effect เดิมที่มีอยู่แล้วเข้ากับชื่อใน config: `"fade"` → effect 1 (super faded), `"blur"` → effect 3 (blur/noise), effect 2 (streaks) และ 5 (skew) เดิมที่ไม่มีชื่อใน config ให้ตั้งชื่อเพิ่มใน config ด้วย (เช่น `"streaks"`, `"skew"`) เพื่อให้ config ครอบคลุมทุก effect ที่โค้ดทำได้จริง

**เกณฑ์ผ่าน:** ลบชื่อ effect ใดออกจาก `augmentations` ใน config แล้วรัน generate ใหม่ → effect นั้นต้องไม่ปรากฏในภาพผลลัพธ์เลย (พิสูจน์ว่า config ควบคุมโค้ดจริง ไม่ใช่แค่ตกแต่ง)

---

### [x] 12. เพิ่มความสมจริงของวันที่ (ปี พ.ศ. / ค.ศ.)
**ปัญหาเดิม:** `generate_random_date()` ใน `catalog_th.py` ใช้ `strftime("%d/%m/%Y")` แบบ ค.ศ. เท่านั้น ทั้งที่เอกสารไทยจริง (โดยเฉพาะใบกำกับภาษี/ใบเสร็จ) นิยมใช้ปี **พ.ศ.** เป็นส่วนใหญ่

**สิ่งที่ต้องทำ:**
- [ ] สุ่มเลือกรูปแบบปีระหว่าง ค.ศ. กับ พ.ศ. ต่อเอกสาร (เช่น 70% พ.ศ., 30% ค.ศ. ให้ใกล้เคียงสัดส่วนจริง) โดย พ.ศ. = ปี ค.ศ. + 543
- [ ] เก็บ field บอกด้วยว่าเอกสารนั้นใช้ปีแบบไหน (เช่น `"date_era": "buddhist"` หรือ `"gregorian"`) ใน output json เพื่อให้โมเดลที่เทรนสามารถแยกแยะ/normalize ได้ภายหลัง

**เกณฑ์ผ่าน:** สุ่มดูตัวอย่างเอกสารหลังแก้ ต้องเจอทั้งวันที่แบบ พ.ศ. (เช่น 15/03/2568) และ ค.ศ. (15/03/2025) ปนกันในชุดข้อมูล

---

## 🔵 ทำเพิ่มได้ถ้าอยากทำ (ไม่บังคับ — เก็บไว้เป็นไอเดียสำหรับรอบถัดไป)

> หมวดนี้คือของที่ "ดีถ้ามี" แต่ไม่ใช่เงื่อนไขที่ต้องทำก่อนปล่อย dataset จริง ทำได้เมื่อมีเวลา/ต้องการยกระดับคุณภาพเพิ่ม

### [x] 13. เพิ่ม layout ใหม่ให้หลากหลายกว่าเดิม (ปัจจุบันมีแค่ 3 แบบ: a/b/c)
ตัวอย่าง layout ที่แนะนำเพิ่ม:
- **Layout D — Modern POS minimalist:** โลโก้กลมกลางบน ไม่มี sidebar สีพื้นเทา/ขาว ตัวหนังสือบาง QR code เด่นมุมล่างขวา (สไตล์ใบเสร็จแอปส่งของยุคใหม่) → เหมาะกับ cafe/supermarket
- **Layout E — Formal bordered tax form:** ตีตารางเส้นกรอบทุกช่องแบบฟอร์มบัญชีทางการ หัวตารางเส้นคู่ตัวหนา มีกล่อง "ตราประทับ" ระบุชัดเจน → เหมาะกับ tax_invoice/quotation บริษัทใหญ่
- **Layout F — Casual handwritten-style:** ไม่มีกรอบ/ตาราง ใช้ font แนวลายมือ จัดวางไม่เป๊ะ → เหมาะกับ receipt ร้านเล็ก
- **Layout G — Bilingual letterhead (B2B):** โลโก้ชิดซ้าย บล็อกข้อมูลบริษัทชิดขวา แถบหัวหนา ภาษาไทย-อังกฤษคู่กัน → เหมาะกับ construction/it tax_invoice ขนาดใหญ่

### [x] 14. เพิ่มความสมจริงเชิงพื้นผิว/แสง (ต่อยอดจาก domain gap)
- [ ] เพิ่มสีพื้นกระดาษให้มีหลายเฉด (ไม่ใช่ขาวล้วนทุกใบ) เช่น กระดาษความร้อน (thermal) สีออกเหลืองอ่อน, กระดาษรีไซเคิลสีครีม
- [ ] (ขั้นสูง) สร้าง QR PromptPay แบบ payload ถูกต้องตามมาตรฐาน EMVCo เพื่อให้ scan/decode ได้จริง เพิ่มความสมจริงสำหรับงานที่ต้องอ่าน QR ด้วย

### [ ] 15. เพิ่มความหลากหลายของ augmentation (ต่อยอดจากข้อ 11)
**Printer/scan error เพิ่มได้:** รอยยับ/พับกระดาษแบบ mesh warp (ไม่ใช่แค่เส้นตรง), รอยเปื้อนหมึก/คราบกาแฟ (blob สีน้ำตาลโปร่งแสง), พิมพ์ซ้อน/เหลื่อม (ghosting แบบเครื่องพิมพ์เก่า)

**Photographed เพิ่มได้:** สีเพี้ยนจากแสงไฟ (fluorescent เขียว / tungsten เหลืองส้ม), motion blur ตามทิศทาง (ต่างจาก Gaussian blur เดิม), ภาพมืด/สว่างเกิน (ปรับ gamma), lens distortion โค้งขอบภาพแบบกล้องมือถือจริง

### [x] 16. Unseen-item holdout สำหรับวัด generalization
กันสินค้าบางส่วน (~15-20% ของ catalog) ไว้ไม่ให้โผล่ใน train เลย ใส่เฉพาะใน test split เพื่อทดสอบว่าโมเดล generalize ไปยังชื่อสินค้าที่ไม่เคยเห็นตอนเทรนได้จริงไหม — มีประโยชน์ถ้าต้องการทำ dataset เป็น benchmark วัด generalization โดยเฉพาะ แต่ถ้าจุดประสงค์หลักคือเทรนโมเดลใช้งานทั่วไป ไม่ทำก็ได้ไม่เสียหาย

---

## ลำดับการทำงานแนะนำสำหรับ AI

1. ทำข้อ 1-4 ก่อน (Critical) — ทำให้ pipeline ไม่พังเงียบๆ และ reproducible
2. ทำข้อ 5-6 (ความถูกต้องของข้อมูล + code cleanup)
3. ทำข้อ 7 (train/val/test split) — สำคัญมากถ้าจะปล่อยเป็น public dataset
4. ทำข้อ 8 (cleanup เล็กน้อย)
5. ข้อ 9-10 เสร็จแล้ว — แค่แทนที่ไฟล์ `catalog_large.json` เดิมด้วยไฟล์ใหม่ที่แนบมา (มีทั้ง item pool และ merchant pool ที่ขยายแล้วในไฟล์เดียว)
6. ทำข้อ 11-12 (แก้ config augmentation ให้ตรงกับโค้ดจริง + เพิ่มความสมจริงวันที่ พ.ศ.) — เป็น bug ที่ควรแก้ก่อนปล่อยจริง ไม่ใช่แค่ nice-to-have
7. รัน generate จริงแบบเต็มจำนวน (5000 docs x 3 variants) แล้วสุ่มตรวจด้วย `verify_dataset.py` อย่างน้อย 10-20 ภาพต่อ (category, doc_type, variant) ก่อนอัปโหลดขึ้น Kaggle/HF จริง
8. ข้อ 13-16 (🔵 หมวดไม่บังคับ) — ทำในรอบถัดไปถ้ามีเวลา/อยากยกระดับคุณภาพเพิ่ม ไม่ใช่เงื่อนไขต้องทำก่อนปล่อย v1










