# 🇹🇭 Thai-Synth-Receipts-Generator

A robust, highly realistic synthetic dataset generator for Thai commercial documents. Designed specifically for training and evaluating state-of-the-art Document AI and OCR models (e.g., Donut, LayoutLM, TrOCR).

## 🎯 เป้าหมายและสถาปัตยกรรม (Architecture & Features)
โปรเจกต์นี้ถูกออกแบบมาเพื่อแก้ปัญหาการขาดแคลนข้อมูลเอกสารภาษาไทยคุณภาพสูง (Research-grade) โดยเน้นที่ความสมจริง ความหลากหลาย และความทนทาน (Robustness) สำหรับนำไปทดสอบโมเดล:
- **6 Diverse Layouts:** รองรับเทมเพลต 6 รูปแบบ ได้แก่ ใบเสร็จมาตรฐาน, ใบกำกับภาษีเต็มรูป, สลิปเทอร์มอล, สลิปมินิมอลคาเฟ่, บิลแบบตารางตีเส้นกริด, และบิลเงินสดสไตล์จดด้วยมือ
- **Zero-shot Evaluation:** แบ่งกลุ่มข้อมูลอย่างรัดกุมผ่าน `catalog_unseen.json` แยกคำศัพท์ ชื่อสินค้า และชื่อบริษัทในโฟลเดอร์ Test ออกจาก Train 100% เพื่อทดสอบว่า AI "อ่าน" ได้จริง ไม่ได้แค่จำคำศัพท์ได้
- **Advanced Augmentations:** ประมวลผลเอกสารแต่ละใบแยกเป็น 3 สภาพแวดล้อม:
    - `clean`: ภาพต้นฉบับดิจิทัลสมบูรณ์แบบ
    - `error`: จุดบกพร่องจากเครื่องพิมพ์ (หมึกจาง, เส้นคาด, สีเลอะ, กระดาษยับ/ฉีกขาด, เงาซ้อน)
    - `photo`: ภาพถ่ายจากกล้องมือถือ (แสงแฟลร์, แสงหลอดไฟนีออน/ทังสเตน, ภาพสั่นไหว Motion Blur, แสงมืดสว่างไม่เท่ากัน)
- **Rich Annotations:** บันทึก Ground Truth ลงในฟอร์แมต `metadata.jsonl` มาตรฐาน HuggingFace พร้อมเก็บพิกัด Bounding Box ทุกตัวอักษร

## 🚀 วิธีรัน (Reproducibility & Installation)
**1. ติดตั้ง Dependencies**
```bash
pip install Pillow opencv-python qrcode numpy pyyaml
```

**2. ตั้งค่าข้อมูล (Configuration)**
ปรับแก้ไฟล์ `config.yaml` เพื่อตั้งจำนวนเอกสารที่ต้องการสร้าง หรืออัตราส่วน Train/Val/Test:
```yaml
num_samples_per_type: 312
split_ratio:
  train: 0.8
  validation: 0.1
  test: 0.1
```

**3. สั่ง Generate Dataset**
```bash
python generate_v3.py
```

## 📊 ผลลัพธ์และสถิติชุดข้อมูล (Dataset Output)
สถิติการสร้างชุดข้อมูลล่าสุด (Production Run):
- **Total Unique Documents:** 4,992 เอกสาร
- **Total Generated Images:** 14,976 ภาพ (4,992 × 3 Styles)
- โครงสร้างโฟลเดอร์:
  ```text
  dataset/
  ├── train/ (80%)
  ├── validation/ (10%)
  └── test/ (10%)
      ├── clean/
      ├── error/
      └── photo/
  ```
ผลลัพธ์สามารถบีบอัดไฟล์และนำขึ้น **Kaggle / HuggingFace** ได้ทันทีโดยไม่ต้องผ่านกระบวนการทำความสะอาดเพิ่มเติม

