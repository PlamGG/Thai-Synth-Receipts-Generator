import os
import requests

def download_file(url, path):
    if not os.path.exists(path):
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            with open(path, 'wb') as f:
                f.write(r.content)
            print(f"Downloaded: {path}")
        except Exception as e:
            print(f"Failed to download {url}: {e}")

# ฉากหลังที่เหมือนการถ่ายรูปเอกสารวางบนพื้น
backgrounds = {
    # พื้นไม้ / โต๊ะไม้
    "wood_desk.jpg": "https://images.unsplash.com/photo-1550684848-fac1c5b4e853?w=1000&q=80",
    "wood_floor.jpg": "https://images.unsplash.com/photo-1581428982868-e410dd047a90?w=1000&q=80",
    # กำแพงขาว / พื้นขาว
    "white_wall.jpg": "https://images.unsplash.com/photo-1513694203232-719a280e022f?w=1000&q=80",
    "white_paper.jpg": "https://images.unsplash.com/photo-1586075010923-2dd4570fb338?w=1000&q=80",
    # พื้นกระเบื้อง (Tile)
    "tile_floor_1.jpg": "https://images.unsplash.com/photo-1516888693095-f0e05366ddc6?w=1000&q=80",
    "tile_floor_2.jpg": "https://images.unsplash.com/photo-1523399732811-5b4ff8bcbe14?w=1000&q=80"
}

# ฟอนต์มาตรฐานที่ใช้ในไทย
fonts = {
    # TH Sarabun New (มาตรฐานเอกสารราชการ/บริษัท)
    "THSarabunNew.ttf": "https://raw.githubusercontent.com/wutipong/thaifonts/master/fonts/THSarabunNew/THSarabunNew.ttf",
    "THSarabunNew-Bold.ttf": "https://raw.githubusercontent.com/wutipong/thaifonts/master/fonts/THSarabunNew/THSarabunNew%20Bold.ttf",
    # Dot Matrix (สำหรับสลิป 7-11 / Thermal slip)
    "DotMatrix.ttf": "https://raw.githubusercontent.com/wutipong/thaifonts/master/fonts/TlwgTypo/TlwgTypo.ttf" # ใช้ TlwgTypo แทนเพื่อให้มีลักษณะเหลี่ยมๆ คล้าย Thermal
}

# Download Backgrounds
for filename, url in backgrounds.items():
    download_file(url, os.path.join("assets", "backgrounds", filename))

# Download Fonts
for filename, url in fonts.items():
    download_file(url, os.path.join("assets", "fonts", filename))

print("Assets setup complete!")
