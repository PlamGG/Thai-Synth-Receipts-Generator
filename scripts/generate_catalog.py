import os
import json
import time
from google import genai
from google.genai import types

# เอา API Key ของคุณมาใส่ตรงนี้ได้เลย (วิธีที่ 1)
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.environ.get("GEMINI_API_KEY")

try:
    if API_KEY:
        client = genai.Client(api_key=API_KEY)
    else:
        # ถ้าไม่ใส่ในโค้ด จะพยายามดึงจาก Environment (วิธีที่ 2)
        client = genai.Client()
except Exception as e:
    print("Error: ไม่สามารถเชื่อมต่อกับ Gemini API ได้")
    print("กรุณาใส่ API Key ในบรรทัดที่ 7 ของไฟล์นี้ หรือตั้งค่า Environment Variable: GEMINI_API_KEY")
    print(e)
    exit(1)

CATEGORIES = ['restaurant', 'cafe', 'supermarket', 'it', 'pharmacy', 'construction', 'clothing', 'clinic', 'auto_parts', 'bookstore', 'home_appliances', 'pet_shop']

def generate_items(category, num_items=50):
    prompt = f"""
    สร้างรายการสินค้าภาษาไทยสำหรับหมวดหมู่ '{category}' จำนวน {num_items} รายการ
    สินค้าต้องมีความหลากหลาย สมจริง มีสเปคหรือรายละเอียดในชื่อสินค้า (เช่น มีความยาวปะปนกัน เพื่อทดสอบระบบ Text-wrapping)
    ส่งกลับมาเป็น JSON Array ของ Object ที่มีโครงสร้างดังนี้:
    [
        {{"name": "ชื่อสินค้าอย่างละเอียด", "min_price": 100.0, "max_price": 500.0}}
    ]
    * ข้อควรระวัง: 
    - ราคา (price) ให้สมเหตุสมผลกับประเภทสินค้า
    - ห้ามมีคำอธิบายอื่น ให้ตอบเป็น JSON เท่านั้น
    """
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"Failed to generate items for {category}: {e}")
        return []

def generate_merchants(category, num_merchants=15):
    prompt = f"""
    สร้างข้อมูลร้านค้า/บริษัทภาษาไทยสำหรับหมวดหมู่ '{category}' จำนวน {num_merchants} รายการ
    ส่งกลับมาเป็น JSON Array ของ Object ที่มีโครงสร้างดังนี้:
    [
        {{
            "name": "ชื่อบริษัท หรือ ชื่อร้านค้า",
            "tax_id": "เลขประจำตัวผู้เสียภาษี 13 หลัก (ตัวเลขสุ่มสมจริง)",
            "address": "ที่อยู่ภาษาไทยแบบเต็ม (เลขที่ ซอย ถนน ตำบล อำเภอ จังหวัด รหัสไปรษณีย์)",
            "phone": "เบอร์โทรศัพท์ (เช่น 02-XXX-XXXX หรือ 08X-XXX-XXXX)"
        }}
    ]
    ห้ามมีคำอธิบายอื่น ให้ตอบเป็น JSON เท่านั้น
    """
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"Failed to generate merchants for {category}: {e}")
        return []
        
def generate_customers(num_customers=30):
    prompt = f"""
    สร้างข้อมูลลูกค้า (บริษัทจำกัด / ห้างหุ้นส่วนจำกัด / นิติบุคคล / บุคคลธรรมดา) ภาษาไทย จำนวน {num_customers} รายการ
    ส่งกลับมาเป็น JSON Array ของ Object ที่มีโครงสร้างดังนี้:
    [
        {{
            "name": "ชื่อบริษัท หรือ ชื่อนามสกุลบุคคล",
            "tax_id": "เลขประจำตัวผู้เสียภาษี 13 หลัก",
            "branch": "สำนักงานใหญ่ หรือ สาขาที่ 00001",
            "address": "ที่อยู่ภาษาไทยแบบเต็ม"
        }}
    ]
    ห้ามมีคำอธิบายอื่น ให้ตอบเป็น JSON เท่านั้น
    """
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"Failed to generate customers: {e}")
        return []

def main():
    print("Starting Catalog Generation via Gemini LLM...")
    catalog = {
        "merchants": {},
        "items": {},
        "customers": []
    }
    
    # 1. Generate Customers
    print("-> Generating 30 Customers...")
    catalog["customers"] = generate_customers(30)
    time.sleep(2)
    
    # 2. Generate Merchants & Items per category
    for cat in CATEGORIES:
        print(f"\n-> Processing Category: [{cat.upper()}]")
        print(f"   Generating Merchants...")
        catalog["merchants"][cat] = generate_merchants(cat, 15)
        time.sleep(2)
        
        # ปั๊มสินค้า 100 ชิ้น (แบ่งยิง 2 รอบ รอบละ 50 เพื่อไม่ให้ LLM ตัดจบก่อน)
        cat_items = []
        for batch in range(2):
            print(f"   Generating Items (Batch {batch+1}/2)...")
            cat_items.extend(generate_items(cat, 50))
            time.sleep(2) # กัน Rate Limit
        catalog["items"][cat] = cat_items
        
    # Save to file
    with open("catalog_large.json", "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)
        
    print(f"\nGenerated catalog_large.json successfully!")
    print(f"Total Customers: {len(catalog['customers'])}")
    for cat in CATEGORIES:
        print(f"[{cat.upper()}] Merchants: {len(catalog['merchants'].get(cat, []))} | Items: {len(catalog['items'].get(cat, []))}")

if __name__ == "__main__":
    main()
