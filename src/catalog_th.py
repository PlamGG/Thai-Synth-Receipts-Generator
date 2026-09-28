import json
import os
import random

LARGE_CATALOG_PATH = "catalog_large.json"
CATALOG = None
if os.path.exists(LARGE_CATALOG_PATH):
    try:
        with open(LARGE_CATALOG_PATH, "r", encoding="utf-8") as f:
            CATALOG = json.load(f)
    except Exception:
        pass

UNSEEN_CATALOG_PATH = "catalog_unseen.json"
CATALOG_UNSEEN = None
if os.path.exists(UNSEEN_CATALOG_PATH):
    try:
        with open(UNSEEN_CATALOG_PATH, "r", encoding="utf-8") as f:
            CATALOG_UNSEEN = json.load(f)
    except Exception:
        pass

def get_random_address():
    return f"{random.randint(1, 999)}/{random.randint(1, 99)} ถ.{random.choice(['สุขุมวิท', 'เพชรเกษม', 'พหลโยธิน'])} {random.choice(['กรุงเทพมหานคร', 'นนทบุรี', 'เชียงใหม่'])}"

def get_random_phone():
    return f"0{random.randint(2, 9)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}"

def generate_merchant_info(category, split="train"):
    if split in ["validation", "test"] and CATALOG_UNSEEN and "merchants" in CATALOG_UNSEEN and category in CATALOG_UNSEEN["merchants"] and len(CATALOG_UNSEEN["merchants"][category]) > 0:
        return random.choice(CATALOG_UNSEEN["merchants"][category])
        
    if CATALOG and "merchants" in CATALOG and category in CATALOG["merchants"] and len(CATALOG["merchants"][category]) > 0:
        return random.choice(CATALOG["merchants"][category])

    return {
        "name": f"ร้านค้า {category} สำรอง",
        "tax_id": f"010555{random.randint(1000000, 9999999)}",
        "branch": "สำนักงานใหญ่",
        "address": get_random_address(),
        "phone": get_random_phone()
    }

def generate_customer_info(split="train"):
    if split in ["validation", "test"] and CATALOG_UNSEEN and "customers" in CATALOG_UNSEEN and len(CATALOG_UNSEEN["customers"]) > 0:
        return random.choice(CATALOG_UNSEEN["customers"])
        
    if CATALOG and "customers" in CATALOG and len(CATALOG["customers"]) > 0:
        return random.choice(CATALOG["customers"])
        
    return {
        "name": f"ลูกค้าทั่วไป {random.randint(1,99)}",
        "tax_id": f"01044{random.randint(10000000, 99999999)}",
        "branch": "สำนักงานใหญ่",
        "address": get_random_address()
    }

def generate_random_date(doc_type):
    from datetime import datetime, timedelta
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2025, 12, 31)
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    random_date = start_date + timedelta(days=random_days)
    
    date_era = random.choices(["buddhist", "gregorian"], weights=[0.7, 0.3])[0]
    y = random_date.year + 543 if date_era == "buddhist" else random_date.year
    date_str = f"{random_date.day:02d}/{random_date.month:02d}/{y}"
    time_str = f"{random.randint(8,20):02d}:{random.randint(0,59):02d}"
    return date_str, time_str, date_era

def build_document_data(category, doc_type, sample_id, split="train"):
    merchant = generate_merchant_info(category, split=split)
    date_str, extra_date, date_era = generate_random_date(doc_type)
    
    num_items = random.randint(1, 7)
    cat_items = []
    
    if split in ["validation", "test"] and CATALOG_UNSEEN and "items" in CATALOG_UNSEEN and category in CATALOG_UNSEEN["items"] and len(CATALOG_UNSEEN["items"][category]) > 0:
        cat_items = CATALOG_UNSEEN["items"][category]
    elif CATALOG and "items" in CATALOG and category in CATALOG["items"] and len(CATALOG["items"][category]) > 0:
        cat_items = CATALOG["items"][category]
        
    if cat_items:
        selected_raw = random.sample(cat_items, min(num_items, len(cat_items)))
        selected_items = [(i["name"], int(float(i["min_price"])), int(float(i["max_price"]))) for i in selected_raw]
    else:
        available_items = [("สินค้าสำรอง 1", 100, 500), ("สินค้าสำรอง 2", 200, 300)]
        selected_items = random.sample(available_items, min(num_items, len(available_items)))
    
    items_list = []
    subtotal = 0
    for i, (item_name, min_p, max_p) in enumerate(selected_items):
        qty = random.randint(1, 10)
        unit_price = random.randint(min_p, max_p)
        total_price = qty * unit_price
        items_list.append({
            "no": i + 1,
            "name": item_name,
            "qty": qty,
            "unit_price": float(unit_price),
            "price": float(unit_price),
            "total": float(total_price)
        })
        subtotal += total_price
        
    discount = 0
    vatable = subtotal
    tax = round(vatable * 0.07, 2)
    total = vatable + tax
    
    customer = generate_customer_info(split=split)
    
    data = {
        "sample_id": sample_id,
        "split": split,
        "category": category,
        "doc_type": doc_type,
        "lang": "th",
        "merchant_name": merchant.get("name", ""),
        "merchant_tax_id": merchant.get("tax_id", ""),
        "merchant_address": merchant.get("address", ""),
        "merchant_phone": merchant.get("phone", ""),
        "date": date_str,
        "time": extra_date,
        "date_era": date_era,
        "items": items_list,
        "subtotal": float(subtotal),
        "discount": float(discount),
        "vatable": float(vatable),
        "tax": float(tax),
        "vat_7": float(tax),
        "vat_exempt": 0.0,
        "total": float(total),
        "currency": "THB",
        "is_original": True,
        "invoice_number": f"INV-{random.randint(1000,9999)}",
        "customer_name": customer.get("name", ""),
        "customer_tax_id": customer.get("tax_id", ""),
        "customer_address": customer.get("address", ""),
        "code_type": random.choice(["qr", "barcode", "none"])
    }
    return data

def data_to_plain_text(data):
    lines = []
    lines.append(data.get("merchant_name", ""))
    if "merchant_address" in data:
        lines.append(data["merchant_address"])
    if "merchant_tax_id" in data:
        lines.append(f"เลขประจำตัวผู้เสียภาษี: {data['merchant_tax_id']}")
    lines.append(f"วันที่: {data['date']}")
    
    for item in data["items"]:
        lines.append(f"{item['qty']} {item['name']} {item['unit_price']:.2f} {item['total']:.2f}")
    lines.append(f"รวมเงิน: {data['subtotal']:.2f}")
    lines.append(f"ภาษีมูลค่าเพิ่ม: {data.get('tax', data.get('vat_7', 0)):.2f}")
    lines.append(f"ยอดสุทธิ: {data['total']:.2f}")
    
    return "\n".join(lines)
CATEGORIES = ["cafe", "construction", "it", "supermarket"]
DOC_TYPES = ["receipt", "tax_invoice", "thermal_slip", "quotation"]

