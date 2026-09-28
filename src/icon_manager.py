import random
from PIL import Image, ImageDraw, ImageFont
import os
from functools import lru_cache

THEMES = {
    "cafe": [("#4A2C2A", "#D4A96A"), ("#6B8E23", "#FFFFFF"), ("#8D6E63", "#FFFFFF")],
    "construction": [("#2C3E50", "#E67E22"), ("#7F8C8D", "#FFFFFF"), ("#34495E", "#F1C40F")],
    "it": [("#1A237E", "#00BCD4"), ("#4A148C", "#FF4081"), ("#000000", "#FFFFFF")],
    "supermarket": [("#1B5E20", "#FDD835"), ("#E65100", "#FFFFFF"), ("#D32F2F", "#FFFFFF")]
}

def get_theme(category):
    if category in THEMES:
        return random.choice(THEMES[category])
    return ("#000000", "#FFFFFF")

@lru_cache(maxsize=32)
def get_font(font_name="Kanit-Bold.ttf", size=20):
    font_path = os.path.join("assets", "fonts", font_name)
    if not os.path.exists(font_path):
        return ImageFont.load_default()
    return ImageFont.truetype(font_path, size)

def get_logo_image(merchant_name, size, primary_color, text_color="white"):
    """สร้างภาพโลโก้สำเร็จรูป โดยใช้อักษรย่อตัวแรกของร้าน"""
    logo = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(logo)
    
    # วาดกรอบโค้ง
    draw.rounded_rectangle([0, 0, size, size], radius=int(size*0.2), fill=primary_color)
    
    # หาย่อตัวอักษรตัวแรก (ตัดคำว่า ร้าน, บริษัท ออกถ้ามี)
    clean_name = merchant_name.replace("บริษัท", "").replace("ร้าน", "").replace("ห้างหุ้นส่วนจำกัด", "").replace("บมจ.", "").strip()
    initial = clean_name[0] if clean_name else "L"
    
    # พิมพ์ตัวอักษรตรงกลาง
    font_size = int(size * 0.6)
    font = get_font("Kanit-Bold.ttf", font_size)
    
    bbox = draw.textbbox((0, 0), initial, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    
    # Offset สำหรับจัดกึ่งกลาง
    offset_x = (size - w) / 2
    offset_y = (size - h) / 2 - (size * 0.1) # ขยับขึ้นนิดหน่อยเพื่อชดเชยสระ
    
    draw.text((offset_x, offset_y), initial, fill=text_color, font=font)
            
    return logo
