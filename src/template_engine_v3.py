import qrcode
import re
import os
import random
from PIL import Image, ImageDraw, ImageFont
from src.icon_manager import get_theme, get_logo_image
from functools import lru_cache

@lru_cache(maxsize=32)
def get_font(font_name="Kanit-Regular.ttf", size=20):
    font_path = os.path.join("assets", "fonts", font_name)
    if not os.path.exists(font_path):
        return ImageFont.load_default()
    return ImageFont.truetype(font_path, size)

def draw_text_with_bbox(draw, x, y, text, font, fill, bboxes_list, label="text", align="left"):
    if not text:
        return 0, 0
    text = str(text)
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    
    if align == "center":
        x = x - (w / 2)
    elif align == "right":
        x = x - w
        
    draw.text((x, y), text, font=font, fill=fill)
    
    padding = 2
    px1, py1 = x - padding, y - padding
    px2, py2 = x + w + padding, y - padding
    px3, py3 = x + w + padding, y + h + padding
    px4, py4 = x - padding, y + h + padding
    
    bboxes_list.append({
        "box": [[px1, py1], [px2, py2], [px3, py3], [px4, py4]],
        "text": text,
        "label": label
    })
    return w, h

def wrap_text_lines(draw, text, font, max_width):
    text = str(text)
    lines = []
    current_line = ""
    # กลุ่มสระบน/ล่าง และวรรณยุกต์ไทยที่ห้ามแยกออกจากพยัญชนะ
    combining_chars = set("ัิีึืฺุู็่้๊๋์ํ")
    
    # ตัดด้วย Space ก่อนเพื่อประหยัดเวลา (Performance Optimization)
    words = text.split(" ")
    for i, word in enumerate(words):
        prefix = " " if i > 0 and current_line else ""
        test_line = current_line + prefix + word
        bbox = draw.textbbox((0, 0), test_line, font=font)
        
        if (bbox[2] - bbox[0]) <= max_width:
            current_line = test_line
        else:
            # ถ้าคำยาวเกิน ค่อย Fallback กลับมาเช็คทีละอักษร (Char-by-char)
            for char in (prefix + word):
                if char in combining_chars:
                    current_line += char  # แปะติดกับพยัญชนะเดิมเสมอ
                    continue
                    
                bbox = draw.textbbox((0, 0), current_line + char, font=font)
                if (bbox[2] - bbox[0]) > max_width and current_line:
                    lines.append(current_line.strip())
                    current_line = char.strip()
                else:
                    current_line += char
                    
    if current_line.strip():
        lines.append(current_line.strip())
    return lines

def get_wrapped_text_height(draw, text, font, max_width, line_spacing=5):
    lines = wrap_text_lines(draw, text, font, max_width)
    if not lines: return 0
    total_h = 0
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        total_h += (bbox[3] - bbox[1]) + line_spacing
    return total_h - line_spacing

def draw_text_wrapped(draw, x, y, text, font, fill, bboxes_list, max_width, label="text", line_spacing=5):
    lines = wrap_text_lines(draw, text, font, max_width)
    if not lines: return 0
    
    current_y = y
    max_w = 0
    
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        draw.text((x, current_y), line, font=font, fill=fill)
        max_w = max(max_w, w)
        current_y += h + line_spacing
        
    total_h = (current_y - line_spacing) - y
    padding = 2
    px1, py1 = x - padding, y - padding
    px2, py2 = x + max_w + padding, y - padding
    px3, py3 = x + max_w + padding, y + total_h + padding
    px4, py4 = x - padding, y + total_h + padding
    
    bboxes_list.append({
        "box": [[px1, py1], [px2, py2], [px3, py3], [px4, py4]],
        "text": str(text).strip(),
        "label": label
    })
    
    return total_h

def draw_fake_barcode(draw, x, y, width, height, bboxes_list):
    curr_x = x
    while curr_x < x + width:
        line_w = random.randint(1, 4)
        if curr_x + line_w > x + width:
            line_w = (x + width) - curr_x
        if random.random() > 0.3:
            draw.rectangle([curr_x, y, curr_x + line_w, y + height], fill="black")
        curr_x += line_w + random.randint(1, 3)
        
    bboxes_list.append({
        "box": [[x, y], [x + width, y], [x + width, y + height], [x, y + height]],
        "text": "<BARCODE>",
        "label": "barcode"
    })

def crc16(data_str: str) -> str:
    crc = 0xFFFF
    for char in data_str:
        crc ^= ord(char) << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
    return f"{crc:04X}"

def generate_promptpay_payload(target: str, amount: float = 0.0) -> str:
    target = re.sub(r'[^0-9]', '', str(target)) if target else "0000000000"
    if len(target) == 10 and target.startswith('0'):
        target_field = f"01130066{target[1:]}"
    elif len(target) == 13:
        target_field = f"0213{target}"
    else:
        target_field = f"02130000000000000"
        
    tag29 = f"0016A000000677010111{target_field}"
    payload = f"00020101021129{len(tag29):02d}{tag29}5802TH5303764"
    if amount > 0:
        amt_str = f"{amount:.2f}"
        payload += f"54{len(amt_str):02d}{amt_str}"
        
    payload += "6304"
    checksum = crc16(payload)
    return payload + checksum

def draw_real_qr(img, x, y, size, data, bboxes_list):
    target = data.get('merchant_phone') or data.get('merchant_tax_id') or "0812345678"
    amount = data.get('total', 0.0)
    payload = generate_promptpay_payload(target, amount)
    
    qr = qrcode.make(payload)
    qr = qr.resize((size, size))
    img.paste(qr, (int(x), int(y)))
    
    bboxes_list.append({
        "box": [[x, y], [x + size, y], [x + size, y + size], [x, y + size]],
        "text": payload,
        "label": "qrcode"
    })


def draw_layout_a(data, primary_color, secondary_color):
    f_title = get_font("Kanit-Bold.ttf", 32)
    f_h2 = get_font("Kanit-Bold.ttf", 20)
    f_body = get_font("Sarabun-Regular.ttf", 20)
    
    temp_img = Image.new('RGB', (1, 1))
    temp_draw = ImageDraw.Draw(temp_img)
    items_h = 0
    for item in data['items']:
        th = get_wrapped_text_height(temp_draw, item['name'], f_body, 330)
        items_h += max(45, th + 20)
        
    img_h = max(1050, 700 + int(items_h))
    img = Image.new('RGB', (800, img_h), color='white')
    draw = ImageDraw.Draw(img)
    bboxes = []
    
    # Sidebar
    draw.rectangle([0, 0, 40, img_h], fill=primary_color)
    
    # Logo & Name
    logo = get_logo_image(data['merchant_name'], 70, primary_color)
    img.paste(logo, (70, 40), logo)
    draw_text_wrapped(draw, 160, 50, data['merchant_name'], f_title, primary_color, bboxes, max_width=400, label="merchant_name")
    
    doc_title_map = {"receipt": "RECEIPT", "tax_invoice": "TAX INVOICE", "quotation": "QUOTATION", "thermal_slip": "RECEIPT"}
    title = doc_title_map.get(data['doc_type'], "INVOICE")
    draw_text_with_bbox(draw, 750, 40, title, f_title, primary_color, bboxes, "doc_title", align="right")
    
    if data.get('is_original'):
        draw_text_with_bbox(draw, 750, 80, "(ต้นฉบับ / ORIGINAL)", f_h2, "#E74C3C", bboxes, "is_original", align="right")
    elif data.get('doc_type') == "tax_invoice":
        draw_text_with_bbox(draw, 750, 80, "(สำเนา / COPY)", f_h2, "#E74C3C", bboxes, "is_original", align="right")
    
    y_info = 140
    if "merchant_address" in data:
        draw_text_with_bbox(draw, 70, y_info, data["merchant_address"], f_body, "#555555", bboxes, "merchant_address")
        y_info += 35
    if "merchant_phone" in data:
        draw_text_with_bbox(draw, 70, y_info, f"โทร: {data['merchant_phone']}", f_body, "#555555", bboxes, "merchant_phone")
        y_info += 35
    if "merchant_tax_id" in data:
        draw_text_with_bbox(draw, 70, y_info, f"เลขประจำตัวผู้เสียภาษี: {data['merchant_tax_id']}", f_body, "#555555", bboxes, "merchant_tax_id")
        
    # Date Box
    draw.rounded_rectangle([480, 130, 750, 240], radius=10, outline=primary_color, width=2)
    draw_text_with_bbox(draw, 490, 145, f"วันที่ / Date:", f_h2, primary_color, bboxes, "date_label")
    draw_text_with_bbox(draw, 740, 145, data['date'], f_h2, "black", bboxes, "date", align="right")
    
    if data['doc_type'] == "tax_invoice" and "invoice_number" in data:
        draw_text_with_bbox(draw, 490, 190, f"เลขที่ / No:", f_h2, primary_color, bboxes, "inv_no_label")
        draw_text_with_bbox(draw, 740, 190, data['invoice_number'], f_h2, "black", bboxes, "invoice_number", align="right")
    elif data['doc_type'] == "quotation" and "quotation_number" in data:
        draw_text_with_bbox(draw, 490, 190, f"เลขที่ / No:", f_h2, primary_color, bboxes, "quo_no_label")
        draw_text_with_bbox(draw, 740, 190, data['quotation_number'], f_h2, "black", bboxes, "quotation_number", align="right")
        
    # Customer Info
    y = 260
    if "customer_name" in data:
        draw_text_with_bbox(draw, 70, y, "ลูกค้า / Customer:", f_h2, primary_color, bboxes, "cust_label")
        draw_text_with_bbox(draw, 260, y, data['customer_name'], f_h2, "black", bboxes, "customer_name")
        y += 35
    if "customer_tax_id" in data and data["customer_tax_id"]:
        draw_text_with_bbox(draw, 70, y, f"เลขผู้เสียภาษี: {data['customer_tax_id']} ({data.get('customer_branch', '')})", f_body, "#555555", bboxes, "customer_tax")
        y += 35
    if "billing_address" in data:
        draw_text_with_bbox(draw, 70, y, data['billing_address'], f_body, "#555555", bboxes, "billing_address")
        y += 45
        
    # Table Header
    y = 360
    table_top_y = y
    draw.rectangle([70, y, 750, y+45], fill=primary_color)
    draw_text_with_bbox(draw, 90, y+8, "ลำดับ", f_h2, "white", bboxes, "th_no")
    draw_text_with_bbox(draw, 150, y+8, "รายการ / Description", f_h2, "white", bboxes, "th_desc")
    draw_text_with_bbox(draw, 500, y+8, "จำนวน", f_h2, "white", bboxes, "th_qty", align="center")
    draw_text_with_bbox(draw, 600, y+8, "ราคา", f_h2, "white", bboxes, "th_price", align="center")
    draw_text_with_bbox(draw, 720, y+8, "รวม", f_h2, "white", bboxes, "th_total", align="center")
    
    y += 55
    draw_grid = random.choice([True, False])
    
    for item in data['items']:
        draw_text_with_bbox(draw, 90, y, str(item.get('no', '')), f_body, "black", bboxes, "item_no")
        
        # Wrapped text for description
        text_h = draw_text_wrapped(draw, 150, y, item['name'], f_body, "black", bboxes, max_width=330, label="item_name")
        
        draw_text_with_bbox(draw, 500, y, str(item['qty']), f_body, "black", bboxes, "item_qty", align="center")
        draw_text_with_bbox(draw, 600, y, f"{item['unit_price']:,.2f}", f_body, "black", bboxes, "item_price", align="center")
        draw_text_with_bbox(draw, 720, y, f"{item['total']:,.2f}", f_body, "black", bboxes, "item_total", align="center")
        
        row_h = max(45, text_h + 20)
        y += row_h
        
        if draw_grid:
            draw.line([70, y, 750, y], fill="#DDDDDD", width=1)
            
    table_bottom_y = y
    draw.line([70, table_bottom_y, 750, table_bottom_y], fill=primary_color, width=2)
    
    if draw_grid:
        for line_x in [70, 135, 460, 540, 660, 750]:
            draw.line([line_x, table_top_y, line_x, table_bottom_y], fill="#DDDDDD", width=1)
            
    y += 20
    
    # Totals
    sub_y = y
    draw_text_with_bbox(draw, 480, sub_y, "รวมเป็นเงิน:", f_body, "black", bboxes, "label_subtotal")
    draw_text_with_bbox(draw, 745, sub_y, f"{data['subtotal']:,.2f}", f_body, "black", bboxes, "subtotal", align="right")
    sub_y += 35
    
    if data.get('discount', 0) > 0:
        draw_text_with_bbox(draw, 480, sub_y, "ส่วนลด:", f_body, "black", bboxes, "label_discount")
        draw_text_with_bbox(draw, 745, sub_y, f"{data['discount']:,.2f}", f_body, "red", bboxes, "discount", align="right")
        sub_y += 35
        
    if data.get('vat_7', 0) > 0:
        draw_text_with_bbox(draw, 480, sub_y, f"ภาษีมูลค่าเพิ่ม (7%):", f_body, "black", bboxes, "label_tax")
        draw_text_with_bbox(draw, 745, sub_y, f"{data['vat_7']:,.2f}", f_body, "black", bboxes, "tax", align="right")
        sub_y += 35
        
    draw.rectangle([480, sub_y, 750, sub_y+55], fill=primary_color)
    draw_text_with_bbox(draw, 490, sub_y+15, "ยอดรวมสุทธิ", f_h2, "white", bboxes, "label_total")
    draw_text_with_bbox(draw, 745, sub_y+15, f"{data['total']:,.2f}", f_h2, "white", bboxes, "total", align="right")
    
    # Barcode / QR
    if data.get('code_type') == 'barcode':
        draw_fake_barcode(draw, 70, sub_y, 200, 50, bboxes)
    elif data.get('code_type') == 'qr':
        draw_real_qr(img, 70, sub_y, 60, data, bboxes)
        
    # Signature Blocks
    if data.get('has_signature_block'):
        sig_y = sub_y + 100
        draw.line([100, sig_y, 300, sig_y], fill="black", width=1)
        draw_text_with_bbox(draw, 200, sig_y+10, "ผู้รับเงิน / ผู้รับมอบอำนาจ", f_body, "black", bboxes, "sig_label_1", align="center")
        draw_text_with_bbox(draw, 200, sig_y+40, "วันที่ ____/____/____", f_body, "black", bboxes, "sig_date_1", align="center")
        
        draw.line([500, sig_y, 700, sig_y], fill="black", width=1)
        draw_text_with_bbox(draw, 600, sig_y+10, "ผู้อนุมัติ / ผู้มีอำนาจลงนาม", f_body, "black", bboxes, "sig_label_2", align="center")
        draw_text_with_bbox(draw, 600, sig_y+40, "วันที่ ____/____/____", f_body, "black", bboxes, "sig_date_2", align="center")
        
    return img, bboxes

def draw_layout_b(data, primary_color, secondary_color):
    f_title = get_font("Kanit-Bold.ttf", 28)
    f_h2 = get_font("Kanit-Bold.ttf", 20)
    f_body = get_font("Sarabun-Regular.ttf", 20)
    
    temp_img = Image.new('RGB', (1, 1))
    temp_draw = ImageDraw.Draw(temp_img)
    items_h = 0
    for item in data['items']:
        th = get_wrapped_text_height(temp_draw, item['name'], f_body, 460)
        items_h += max(45, th + 20)
        
    img_h = max(1050, 700 + int(items_h))
    img = Image.new('RGB', (800, img_h), color='white')
    draw = ImageDraw.Draw(img)
    bboxes = []
    
    draw.rectangle([0, 0, 800, 180], fill=primary_color)
    logo = get_logo_image(data['merchant_name'], 60, primary_color)
    img.paste(logo, (400 - 30, 20), logo)
    draw_text_with_bbox(draw, 400, 90, data['merchant_name'], f_title, "white", bboxes, "merchant_name", align="center")
    
    doc_title = "ใบเสร็จรับเงิน (RECEIPT)" if data['doc_type'] == "receipt" else "เอกสารการชำระเงิน"
    draw_text_with_bbox(draw, 400, 140, doc_title, f_h2, "white", bboxes, "doc_title", align="center")
    
    y_info = 210
    draw_text_with_bbox(draw, 50, y_info, f"วันที่: {data['date']}", f_body, "black", bboxes, "date")
    if 'time' in data:
        draw_text_with_bbox(draw, 250, y_info, f"เวลา: {data['time']}", f_body, "black", bboxes, "time")
        
    if 'payment_method' in data:
        draw_text_with_bbox(draw, 750, y_info, f"ชำระโดย: {data['payment_method']}", f_h2, primary_color, bboxes, "payment_method", align="right")
        
    if 'cashier' in data:
        y_info += 40
        draw_text_with_bbox(draw, 50, y_info, data['cashier'], f_body, "black", bboxes, "cashier")
        
    y = 310
    draw.line([50, y, 750, y], fill=primary_color, width=3)
    y += 10
    draw_text_with_bbox(draw, 50, y, "ลำดับ", f_h2, "black", bboxes, "th_no")
    draw_text_with_bbox(draw, 120, y, "รายการ", f_h2, "black", bboxes, "th_desc")
    draw_text_with_bbox(draw, 600, y, "จำนวน", f_h2, "black", bboxes, "th_qty", align="right")
    draw_text_with_bbox(draw, 750, y, "รวม (บาท)", f_h2, "black", bboxes, "th_total", align="right")
    y += 45
    draw.line([50, y, 750, y], fill=primary_color, width=1)
    y += 10
    
    for i, item in enumerate(data['items']):
        text_h = get_wrapped_text_height(draw, item['name'], f_body, 460)
        row_h = max(45, text_h + 20)
        
        if i % 2 == 1:
            draw.rectangle([50, y-5, 750, y-5 + row_h], fill="#F9F9F9")
            
        draw_text_with_bbox(draw, 50, y, str(item.get('no', '')), f_body, "black", bboxes, "item_no")
        draw_text_wrapped(draw, 120, y, item['name'], f_body, "black", bboxes, max_width=460, label="item_name")
        draw_text_with_bbox(draw, 600, y, str(item['qty']), f_body, "black", bboxes, "item_qty", align="right")
        draw_text_with_bbox(draw, 750, y, f"{item['total']:,.2f}", f_body, "black", bboxes, "item_total", align="right")
        
        y += row_h
        
    y += 20
    draw.line([50, y, 750, y], fill=primary_color, width=3)
    y += 25
    
    draw_text_with_bbox(draw, 480, y, "รวมสุทธิ", f_title, primary_color, bboxes, "label_total")
    draw_text_with_bbox(draw, 750, y, f"{data['total']:,.2f}", f_title, primary_color, bboxes, "total", align="right")
    
    if data.get('code_type') == 'barcode':
        draw_fake_barcode(draw, 50, y, 150, 40, bboxes)
    elif data.get('code_type') == 'qr':
        draw_real_qr(img, 50, y, 50, data, bboxes)
        
    return img, bboxes

def draw_layout_c(data, primary_color, secondary_color):
    f_title = get_font("Kanit-Bold.ttf", 26)
    f_body = get_font("Sarabun-Regular.ttf", 20)
    
    temp_img = Image.new('RGB', (1, 1))
    temp_draw = ImageDraw.Draw(temp_img)
    items_h = 0
    for item in data['items']:
        th = get_wrapped_text_height(temp_draw, item['name'], f_body, 410)
        items_h += th + 60
        
    img_h = max(800, 600 + int(items_h))
    img = Image.new('RGB', (450, img_h), color='white')
    draw = ImageDraw.Draw(img)
    bboxes = []
    
    logo = get_logo_image(data['merchant_name'], 50, "#000000")
    img.paste(logo, (200, 20), logo)
    
    draw_text_with_bbox(draw, 225, 80, data['merchant_name'], f_title, "black", bboxes, "merchant_name", align="center")
    
    y_info = 125
    if 'merchant_address' in data:
        draw_text_wrapped(draw, 20, y_info, data['merchant_address'], f_body, "#333333", bboxes, max_width=410, label="merchant_address")
        th = get_wrapped_text_height(draw, data['merchant_address'], f_body, 410)
        y_info += th + 15
        
    if 'merchant_tax_id' in data:
        draw_text_with_bbox(draw, 225, y_info, f"TAX ID: {data['merchant_tax_id']}", f_body, "#333333", bboxes, "merchant_tax", align="center")
        y_info += 35
        
    if 'pos_id' in data:
        draw_text_with_bbox(draw, 225, y_info, f"POS: {data['pos_id']} / {data.get('cashier', '')}", f_body, "#333333", bboxes, "pos_info", align="center")
        
    draw.line([20, y_info+40, 430, y_info+40], fill="black", width=2)
    
    draw_text_with_bbox(draw, 20, y_info+55, f"วันที่: {data['date']}  เวลา: {data.get('time', '12:00')}", f_body, "black", bboxes, "datetime")
        
    draw.line([20, y_info+95, 430, y_info+95], fill="black", width=1)
    
    y = y_info + 115
    for item in data['items']:
        text_h = draw_text_wrapped(draw, 20, y, item['name'], f_body, "black", bboxes, max_width=410, label="item_name")
        y += text_h + 10
        draw_text_with_bbox(draw, 50, y, f"{item['qty']} x {item['unit_price']:,.2f}", f_body, "black", bboxes, "item_qty_price")
        draw_text_with_bbox(draw, 430, y, f"{item['total']:,.2f}", f_body, "black", bboxes, "item_total", align="right")
        y += 45
        
    draw.line([20, y, 430, y], fill="black", width=1)
    y += 20
    
    draw_text_with_bbox(draw, 20, y, "ยอดรวมสุทธิ", f_title, "black", bboxes, "label_total")
    draw_text_with_bbox(draw, 430, y, f"{data['total']:,.2f}", f_title, "black", bboxes, "total", align="right")
    
    y += 50
    # VAT Breakdown (Only show if Vatable > 0)
    if 'vatable' in data and data['vatable'] > 0:
        draw_text_with_bbox(draw, 20, y, "Vatable:", f_body, "black", bboxes, "label_vatable")
        draw_text_with_bbox(draw, 430, y, f"{data['vatable']:,.2f}", f_body, "black", bboxes, "val_vatable", align="right")
        y += 30
        draw_text_with_bbox(draw, 20, y, "VAT 7%:", f_body, "black", bboxes, "label_vat")
        draw_text_with_bbox(draw, 430, y, f"{data.get('vat_7', 0):,.2f}", f_body, "black", bboxes, "val_vat", align="right")
        y += 30
        
    if 'payment_method' in data:
        draw_text_with_bbox(draw, 20, y, f"ชำระด้วย: {data['payment_method']}", f_body, "black", bboxes, "payment_method")
        
    draw.line([20, y+45, 430, y+45], fill="black", width=2)
    
    y_footer = y + 65
    draw_text_with_bbox(draw, 225, y_footer, "THANK YOU", f_title, "black", bboxes, "footer", align="center")
    
    # Barcode
    y_code = y_footer + 50
    if data.get('code_type') == 'barcode':
        draw_fake_barcode(draw, 125, y_code, 200, 50, bboxes)
    elif data.get('code_type') == 'qr':
        draw_real_qr(img, 195, y_code, 60, data, bboxes)
    
    return img, bboxes

def generate_template_v3(data):
    primary, secondary = get_theme(data['category'])
    doc_type = data['doc_type']
    
    if doc_type in ["tax_invoice", "quotation"]:
        return draw_layout_a(data, primary, secondary)
        
    if doc_type == "thermal_slip":
        return draw_layout_c(data, "#000000", "#FFFFFF")
    
    if doc_type == "receipt":
        if random.random() > 0.5:
            return draw_layout_b(data, primary, secondary)
        else:
            return draw_layout_c(data, "#000000", "#FFFFFF")
            
    return draw_layout_a(data, primary, secondary)

def draw_layout_d(data, primary_color, secondary_color):
    f_title = get_font("Kanit-Bold.ttf", 36)
    f_body = get_font("Sarabun-Regular.ttf", 22)
    f_body_bold = get_font("Kanit-Bold.ttf", 22)
    f_large = get_font("Kanit-Bold.ttf", 30)
    
    temp_img = Image.new('RGB', (1, 1))
    temp_draw = ImageDraw.Draw(temp_img)
    items_h = 0
    for item in data['items']:
        items_h += 75
        
    img_h = max(800, 500 + int(items_h))
    img = Image.new('RGB', (450, img_h), color='white')
    draw = ImageDraw.Draw(img)
    bboxes = []
    
    y = 30
    draw_text_with_bbox(draw, 225, y, data['merchant_name'], f_title, "black", bboxes, "merchant_name", align="center")
    y += 50
    draw_text_wrapped(draw, 225, y, data.get('merchant_address', ''), f_body, "black", bboxes, 400, "merchant_address", align="center")
    y += 70
    draw_text_with_bbox(draw, 225, y, f"TAX ID: {data.get('merchant_tax_id', '')}", f_body, "black", bboxes, "merchant_tax_id", align="center")
    y += 50
    
    draw_text_with_bbox(draw, 30, y, data.get('date', ''), f_body, "black", bboxes, "date", align="left")
    draw_text_with_bbox(draw, 420, y, data.get('time', ''), f_body, "black", bboxes, "time", align="right")
    y += 40
    
    draw.line([(30, y), (420, y)], fill="black", width=2)
    y += 20
    
    for i, item in enumerate(data['items']):
        draw_text_wrapped(draw, 30, y, item['name'], f_body, "black", bboxes, 250, f"item_name_{i}")
        draw_text_with_bbox(draw, 420, y, f"{item['total']:,.2f}", f_body_bold, "black", bboxes, f"item_total_{i}", align="right")
        y += 30
        draw_text_with_bbox(draw, 50, y, f"{item['qty']} x {item['price']:,.2f}", f_body, "#555555", bboxes, f"item_qty_price_{i}", align="left")
        y += 40
        
    y += 20
    draw.line([(30, y), (420, y)], fill="black", width=2)
    y += 20
    
    draw_text_with_bbox(draw, 30, y, "TOTAL", f_large, "black", bboxes, "label_total", align="left")
    draw_text_with_bbox(draw, 420, y, f"{data['total']:,.2f}", f_large, "black", bboxes, "total", align="right")
    y += 70
    
    if data.get('code_type') == 'barcode':
        draw_fake_barcode(draw, 125, y, 200, 50, bboxes)
    elif data.get('code_type') == 'qr':
        draw_real_qr(img, 195, y, 60, data, bboxes)
        
    return img, bboxes

def draw_layout_e(data, primary_color, secondary_color):
    f_title = get_font("Kanit-Bold.ttf", 32)
    f_h2 = get_font("Kanit-Bold.ttf", 20)
    f_body = get_font("Sarabun-Regular.ttf", 20)
    
    temp_img = Image.new('RGB', (1, 1))
    temp_draw = ImageDraw.Draw(temp_img)
    items_h = 0
    for item in data['items']:
        _, th = get_text_dimensions(item['name'], f_body, temp_draw)
        items_h += max(40, th + 20)
        
    img_h = max(1000, 700 + int(items_h))
    img = Image.new('RGB', (800, img_h), color='white')
    draw = ImageDraw.Draw(img)
    bboxes = []
    
    doc_title_map = {"receipt": "ใบเสร็จรับเงิน", "tax_invoice": "ใบกำกับภาษี", "quotation": "ใบเสนอราคา", "thermal_slip": "ใบเสร็จรับเงินย่อ"}
    title_text = doc_title_map.get(data['doc_type'], "ใบกำกับภาษี")
    draw_text_with_bbox(draw, 400, 40, title_text, f_title, primary_color, bboxes, "doc_title", align="center")
    
    y = 100
    draw.rectangle([40, y, 390, y+150], outline="black", width=2)
    draw.rectangle([410, y, 760, y+150], outline="black", width=2)
    
    draw_text_with_bbox(draw, 50, y+10, "ผู้ขาย (Seller):", f_h2, "black", bboxes, "label_seller")
    draw_text_with_bbox(draw, 50, y+40, data['merchant_name'], f_body, "black", bboxes, "merchant_name")
    draw_text_wrapped(draw, 50, y+70, data.get('merchant_address', ''), f_body, "black", bboxes, 330, "merchant_address")
    
    draw_text_with_bbox(draw, 420, y+10, "ลูกค้า (Buyer):", f_h2, "black", bboxes, "label_buyer")
    draw_text_with_bbox(draw, 420, y+40, data.get('customer_name', '-'), f_body, "black", bboxes, "customer_name")
    draw_text_wrapped(draw, 420, y+70, data.get('customer_address', '-'), f_body, "black", bboxes, 330, "customer_address")
    
    y += 180
    
    draw.rectangle([40, y, 760, y+40], fill=primary_color, outline="black")
    draw_text_with_bbox(draw, 70, y+10, "ลำดับ", f_h2, "white", bboxes, "th_no")
    draw_text_with_bbox(draw, 250, y+10, "รายการ", f_h2, "white", bboxes, "th_desc")
    draw_text_with_bbox(draw, 500, y+10, "จำนวน", f_h2, "white", bboxes, "th_qty")
    draw_text_with_bbox(draw, 580, y+10, "ราคา", f_h2, "white", bboxes, "th_price")
    draw_text_with_bbox(draw, 680, y+10, "จำนวนเงิน", f_h2, "white", bboxes, "th_total")
    
    y += 40
    start_y_table = y
    
    for i, item in enumerate(data['items']):
        draw_text_with_bbox(draw, 70, y+10, str(i+1), f_body, "black", bboxes, f"item_no_{i}")
        draw_text_wrapped(draw, 140, y+10, item['name'], f_body, "black", bboxes, 320, f"item_name_{i}")
        draw_text_with_bbox(draw, 510, y+10, str(item['qty']), f_body, "black", bboxes, f"item_qty_{i}")
        draw_text_with_bbox(draw, 620, y+10, f"{item['price']:,.2f}", f_body, "black", bboxes, f"item_price_{i}", align="right")
        draw_text_with_bbox(draw, 750, y+10, f"{item['total']:,.2f}", f_body, "black", bboxes, f"item_total_{i}", align="right")
        
        _, th = get_text_dimensions(item['name'], f_body, temp_draw)
        row_h = max(40, th + 20)
        draw.line([(40, y+row_h), (760, y+row_h)], fill="black")
        y += row_h
        
    draw.rectangle([40, start_y_table-40, 760, y], outline="black", width=2)
    draw.line([(120, start_y_table-40), (120, y)], fill="black", width=2)
    draw.line([(480, start_y_table-40), (480, y)], fill="black", width=2)
    draw.line([(550, start_y_table-40), (550, y)], fill="black", width=2)
    draw.line([(650, start_y_table-40), (650, y)], fill="black", width=2)
    
    draw.rectangle([480, y, 760, y+90], outline="black", width=2)
    draw.line([(480, y+30), (760, y+30)], fill="black")
    draw.line([(480, y+60), (760, y+60)], fill="black")
    draw.line([(650, y), (650, y+90)], fill="black", width=2)
    
    draw_text_with_bbox(draw, 490, y+5, "มูลค่ารวม", f_body, "black", bboxes, "label_subtotal")
    draw_text_with_bbox(draw, 750, y+5, f"{data.get('subtotal', 0):,.2f}", f_body, "black", bboxes, "subtotal", align="right")
    
    draw_text_with_bbox(draw, 490, y+35, "ภาษีมูลค่าเพิ่ม 7%", f_body, "black", bboxes, "label_tax")
    draw_text_with_bbox(draw, 750, y+35, f"{data.get('tax', 0):,.2f}", f_body, "black", bboxes, "tax", align="right")
    
    draw_text_with_bbox(draw, 490, y+65, "ยอดเงินสุทธิ", f_h2, "black", bboxes, "label_total")
    draw_text_with_bbox(draw, 750, y+65, f"{data['total']:,.2f}", f_h2, "black", bboxes, "total", align="right")
    
    return img, bboxes

def draw_layout_f(data, primary_color, secondary_color):
    import random
    f_title = get_font("Kanit-Bold.ttf", 28)
    f_label = get_font("Sarabun-Bold.ttf", 20)
    
    try:
        f_hw = get_font("Mali-Regular.ttf", 22)
    except:
        f_hw = get_font("Sarabun-Regular.ttf", 22)
        
    temp_img = Image.new('RGB', (1, 1))
    temp_draw = ImageDraw.Draw(temp_img)
    items_h = 0
    for item in data['items']:
        _, th = get_text_dimensions(item['name'], f_hw, temp_draw)
        items_h += max(40, th + 20)
        
    img_h = max(800, 600 + int(items_h))
    img = Image.new('RGB', (600, img_h), color='#F9F9F9')
    draw = ImageDraw.Draw(img)
    bboxes = []
    
    draw_text_with_bbox(draw, 450, 30, f"เล่มที่ {random.randint(1,50)}", f_label, "black", bboxes, "book_no")
    draw_text_with_bbox(draw, 450, 60, f"เลขที่ {random.randint(1,9999)}", f_label, "black", bboxes, "receipt_no")
    
    draw_text_with_bbox(draw, 300, 40, "บิลเงินสด", f_title, "black", bboxes, "doc_title", align="center")
    
    y = 120
    draw_text_with_bbox(draw, 30, y, "นาม (Name):", f_label, "black", bboxes, "label_buyer")
    draw_text_with_bbox(draw, 140, y-5, data.get('customer_name', '-'), f_hw, "blue", bboxes, "customer_name")
    
    y += 40
    draw_text_with_bbox(draw, 30, y, "วันที่ (Date):", f_label, "black", bboxes, "label_date")
    draw_text_with_bbox(draw, 140, y-5, data.get('date', '-'), f_hw, "blue", bboxes, "date")
    
    y += 60
    
    draw.rectangle([30, y, 570, y+40], fill="#EEEEEE", outline="black")
    draw_text_with_bbox(draw, 40, y+10, "จำนวน", f_label, "black", bboxes, "th_qty")
    draw_text_with_bbox(draw, 130, y+10, "รายการ", f_label, "black", bboxes, "th_desc")
    draw_text_with_bbox(draw, 400, y+10, "หน่วยละ", f_label, "black", bboxes, "th_price")
    draw_text_with_bbox(draw, 500, y+10, "จำนวนเงิน", f_label, "black", bboxes, "th_total")
    
    y += 40
    start_table = y
    
    for i, item in enumerate(data['items']):
        draw_text_with_bbox(draw, 55, y+5, str(item['qty']), f_hw, "blue", bboxes, f"item_qty_{i}")
        draw_text_wrapped(draw, 120, y+5, item['name'], f_hw, "blue", bboxes, 250, f"item_name_{i}")
        draw_text_with_bbox(draw, 450, y+5, f"{item['price']:,.2f}", f_hw, "blue", bboxes, f"item_price_{i}", align="right")
        draw_text_with_bbox(draw, 560, y+5, f"{item['total']:,.2f}", f_hw, "blue", bboxes, f"item_total_{i}", align="right")
        
        _, th = get_text_dimensions(item['name'], f_hw, temp_draw)
        row_h = max(40, th + 20)
        draw.line([(30, y+row_h), (570, y+row_h)], fill="gray", width=1)
        y += row_h
        
    draw.rectangle([30, start_table-40, 570, y], outline="black", width=2)
    draw.line([(110, start_table-40), (110, y)], fill="black", width=2)
    draw.line([(380, start_table-40), (380, y)], fill="black", width=2)
    draw.line([(480, start_table-40), (480, y)], fill="black", width=2)
    
    draw.rectangle([380, y, 570, y+50], outline="black", width=2)
    draw.line([(480, y), (480, y+50)], fill="black", width=2)
    
    draw_text_with_bbox(draw, 390, y+10, "รวมเงิน", f_label, "black", bboxes, "label_total")
    draw_text_with_bbox(draw, 560, y+10, f"{data['total']:,.2f}", f_hw, "blue", bboxes, "total", align="right")
    
    return img, bboxes
