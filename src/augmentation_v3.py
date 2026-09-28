_VIGNETTE_CACHE = {}
import cv2
import numpy as np
import random
import os
from PIL import Image, ImageDraw, ImageFont

_BG_CACHE = {}

def warp_point(pt, matrix):
    px = (matrix[0][0]*pt[0] + matrix[0][1]*pt[1] + matrix[0][2]) / ((matrix[2][0]*pt[0] + matrix[2][1]*pt[1] + matrix[2][2]))
    py = (matrix[1][0]*pt[0] + matrix[1][1]*pt[1] + matrix[1][2]) / ((matrix[2][0]*pt[0] + matrix[2][1]*pt[1] + matrix[2][2]))
    return [round(px, 2), round(py, 2)]

def warp_bboxes(bboxes, matrix):
    new_bboxes = []
    for item in bboxes:
        new_box = []
        for pt in item["box"]:
            new_box.append(warp_point(pt, matrix))
        new_bboxes.append({
            "box": new_box,
            "text": item["text"],
            "label": item["label"]
        })
    return new_bboxes

def apply_signature(img_pil, bboxes, doc_type):
    """วาดลายเซ็นจำลอง และ ตราประทับวันที่ (เฉพาะบางบิล)"""
    w, h = img_pil.size
    draw = ImageDraw.Draw(img_pil)
    
    # 1. วาดลายเซ็น (ปากกาลูกลื่นสีน้ำเงิน) 
    # หาตำแหน่งลายเซ็นจาก bboxes
    sig_box = next((b for b in bboxes if b['label'].startswith('sig_label')), None)
    if sig_box:
        # วาดตรงจุดที่มีเส้นลายเซ็น
        sx = int((sig_box['box'][0][0] + sig_box['box'][1][0]) / 2) + random.randint(-50, 50)
        sy = int(sig_box['box'][0][1]) - random.randint(20, 50)
    else:
        sx = random.randint(w - 300, w - 150)
        sy = random.randint(h - 200, h - 80)
    
    pen_color = (0, 0, random.randint(150, 200)) # น้ำเงินเข้ม
    
    pts = [(sx, sy)]
    curr_x, curr_y = sx, sy
    for _ in range(random.randint(6, 12)):
        curr_x += random.randint(10, 40)
        curr_y += random.randint(-30, 30)
        pts.append((curr_x, curr_y))
        
    draw.line(pts, fill=pen_color, width=random.randint(2, 4), joint="curve")
    
    # 2. ตราประทับวันที่
    font_choices = []
    if os.path.exists("assets/fonts/Itim-Regular.ttf"): font_choices.append("Itim-Regular.ttf")
    if os.path.exists("assets/fonts/Sriracha-Regular.ttf"): font_choices.append("Sriracha-Regular.ttf")
    if os.path.exists("assets/fonts/Mali-Regular.ttf"): font_choices.append("Mali-Regular.ttf")
    
    if random.random() > 0.3:
        if font_choices:
            font_name = random.choice(font_choices)
            font = ImageFont.truetype(os.path.join("assets", "fonts", font_name), 28)
        else:
            font = ImageFont.load_default()
            
        stamp_text = "Approved / ตรวจแล้ว" if doc_type in ["quotation", "tax_invoice"] else "Paid / รับเงินแล้ว"
        draw.text((sx - 50, sy + 40), stamp_text, fill=(200, 30, 30), font=font)
        
    return img_pil, bboxes

def apply_printer_error(img_pil, bboxes, enabled_effects=None):
    img_cv = np.array(img_pil)
    h, w = img_cv.shape[:2]
    
    if enabled_effects is None:
        enabled_effects = ["fade", "streaks", "blur", "artifacts", "skew", "fold", "broken"]
    num_to_apply = min(random.randint(2, 4), len(enabled_effects))
    effects = random.sample(enabled_effects, num_to_apply) if enabled_effects else []
    
    # 1. หมึกจางมากๆ (Super Faded)
    if "fade" in effects:
        alpha = random.uniform(0.3, 0.6)
        beta = random.randint(70, 130)
        img_cv = cv2.convertScaleAbs(img_cv, alpha=alpha, beta=beta)
        
    # 2. เส้นหัวพิมพ์แตก (Streaks)
    if "streaks" in effects:
        for _ in range(random.randint(5, 15)):
            y = random.randint(0, h)
            x_start = random.randint(0, w//2)
            x_end = x_start + random.randint(50, 200)
            thickness = random.randint(1, 2)
            cv2.line(img_cv, (x_start, y), (x_end, y), (200, 200, 200), thickness)
            
    # 3. เบลอ และ จุดกวนภาพ (Blur & Noise)
    if "blur" in effects:
        if random.random() > 0.5:
            img_cv = cv2.GaussianBlur(img_cv, (3, 3), 0)
        else:
            noise = np.random.normal(0, 15, img_cv.shape).astype(np.float32)
            img_cv = np.clip(img_cv + noise, 0, 255).astype(np.uint8)
            
    # 4. ภาพแตก (JPEG Artifacts)
    if "artifacts" in effects:
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), random.randint(10, 30)]
        _, encimg = cv2.imencode('.jpg', img_cv, encode_param)
        img_cv = cv2.imdecode(encimg, 1)
        
    # 5. เอียง (Skew)
    if "skew" in effects:
        angle = random.uniform(-4, 4)
        M = cv2.getRotationMatrix2D((w/2, h/2), angle, 1.0)
        img_cv = cv2.warpAffine(img_cv, M, (w, h), borderValue=(255, 255, 255))
        
        # Transform BBoxes
        new_bboxes = []
        for b in bboxes:
            pts = np.array(b['box'], dtype=np.float32).reshape(-1, 1, 2)
            pts_rot = cv2.transform(pts, M)
            b_new = b.copy()
            b_new['box'] = pts_rot.reshape(4, 2).tolist()
            new_bboxes.append(b_new)
        bboxes = new_bboxes
        

    # Fold (รอยพับ)
    if "fold" in effects:
        fold_y = random.randint(h//4, h*3//4)
        cv2.line(img_cv, (0, fold_y), (w, fold_y), (180, 180, 180), 2)
        cv2.line(img_cv, (0, fold_y-1), (w, fold_y-1), (255, 255, 255), 1)
        overlay = img_cv.copy()
        cv2.rectangle(overlay, (0, fold_y), (w, min(h, fold_y+15)), (100, 100, 100), -1)
        cv2.addWeighted(overlay, 0.1, img_cv, 0.9, 0, img_cv)

    # Broken (มุมขาด)
    if "ghosting" in effects:
        shift_x, shift_y = random.randint(2, 4), random.randint(2, 4)
        M = np.float32([[1, 0, shift_x], [0, 1, shift_y]])
        shifted = cv2.warpAffine(img_cv, M, (w, h), borderValue=(255,255,255))
        img_cv = cv2.addWeighted(img_cv, 0.7, shifted, 0.3, 0)
        
    if "blob" in effects:
        overlay = img_cv.copy()
        for _ in range(random.randint(1, 3)):
            bx, by = random.randint(0, w), random.randint(0, h)
            radius = random.randint(15, 30)
            cv2.circle(overlay, (bx, by), radius, (80, 80, 80), -1)
        overlay = cv2.GaussianBlur(overlay, (21, 21), 0)
        img_cv = cv2.addWeighted(img_cv, 0.8, overlay, 0.2, 0)
        
    if "warp" in effects:
        x, y = np.meshgrid(np.arange(w), np.arange(h))
        map_x = (x + 2 * np.sin(y / 20.0)).astype(np.float32)
        map_y = (y + 2 * np.cos(x / 20.0)).astype(np.float32)
        img_cv = cv2.remap(img_cv, map_x, map_y, cv2.INTER_LINEAR, borderValue=(255,255,255))
        
    if "broken" in effects:
        corner = random.choice([(0,0), (w,0), (0,h), (w,h)])
        size = random.randint(40, 100)
        
        def in_triangle(pt, corner_pt, size_val):
            cx, cy = corner_pt
            dx, dy = abs(pt[0] - cx), abs(pt[1] - cy)
            return (dx + dy) <= size_val
            
        if corner == (0,0):
            pts = np.array([[0,0], [size,0], [0,size]])
        elif corner == (w,0):
            pts = np.array([[w,0], [w-size,0], [w,size]])
        elif corner == (0,h):
            pts = np.array([[0,h], [size,h], [0,h-size]])
        else:
            pts = np.array([[w,h], [w-size,h], [w,h-size]])
        cv2.fillPoly(img_cv, [pts], (255, 255, 255))
        
        valid_bboxes = []
        for b in bboxes:
            box_pts = b['box']
            center_x = sum(p[0] for p in box_pts) / 4.0
            center_y = sum(p[1] for p in box_pts) / 4.0
            if not in_triangle((center_x, center_y), corner, size):
                valid_bboxes.append(b)
        bboxes = valid_bboxes

    return Image.fromarray(img_cv), bboxes

def apply_paper_texture(img_cv, doc_type):
    h, w = img_cv.shape[:2]
    
    # Determine paper style based on doc_type
    styles = ["plain"]
    if doc_type == "thermal_slip":
        styles = ["thermal", "crumpled"]
    elif doc_type == "receipt":
        styles = ["thermal", "crumpled", "plain"]
    elif doc_type == "tax_invoice":
        styles = ["carbon", "crumpled", "plain"]
    elif doc_type == "quotation":
        styles = ["plain", "crumpled"]
        
    style = random.choice(styles)
    
    if style == "thermal":
        # Vignette effect for thermal paper
        if (h, w) not in _VIGNETTE_CACHE:
            X_kernel = cv2.getGaussianKernel(w, w/1.5)
            Y_kernel = cv2.getGaussianKernel(h, h/1.5)
            kernel = Y_kernel * X_kernel.T
            _VIGNETTE_CACHE[(h, w)] = kernel / kernel.max()
            
        mask = _VIGNETTE_CACHE[(h, w)]
        img_cv = (img_cv * (mask[..., np.newaxis] * 0.2 + 0.8)).astype(np.uint8)
        # Slight bluish/grayish tint
        img_cv = cv2.addWeighted(img_cv, 0.95, np.full_like(img_cv, (240, 240, 250)), 0.05, 0)
        
    elif style == "carbon":
        # Carbon copy: Dark text becomes bluish/purple
        # img_cv is RGB
        mask_black = cv2.inRange(img_cv, np.array([0, 0, 0]), np.array([120, 120, 120]))
        img_cv[mask_black > 0] = [60, 40, 150] # RGB purple/blue
        
        # Add carbon dot noise (light blue/purple dots)
        noise = np.random.rand(h, w)
        img_cv[noise > 0.99] = [180, 180, 220]
        
    elif style == "crumpled":
        # Random crease lines
        for _ in range(random.randint(4, 10)):
            x1, y1 = random.randint(0, w), random.randint(0, h)
            x2 = x1 + random.randint(-w//2, w//2)
            y2 = y1 + random.randint(-h//2, h//2)
            cv2.line(img_cv, (x1, y1), (x2, y2), (210, 210, 210), random.randint(1, 3))
            cv2.line(img_cv, (x1+1, y1+1), (x2+1, y2+1), (255, 255, 255), random.randint(1, 3))
            
    return img_cv

def apply_photographed(img_pil, bboxes, data, bg_folder="assets/backgrounds", difficulty="random"):
    # ป้องกันการแก้ไขภาพต้นฉบับ (In-place Mutation) เผื่อมีการนำภาพเดิมไปใช้ต่อในอนาคต
    img_pil = img_pil.copy()
    
    if difficulty == "random":
        difficulty = random.choice(["easy", "hard"])
        
    img_cv = np.array(img_pil)
    
    # --- ADDED: Apply Paper Texture ---
    doc_type_for_texture = data.get("doc_type", "receipt")
    img_cv = apply_paper_texture(img_cv, doc_type_for_texture)
    
    doc_h, doc_w = img_cv.shape[:2]
    
    # คำนวณขนาดฉากหลังให้สัมพันธ์กับความสูงกระดาษ ป้องกันสัดส่วนภาพบิดเบี้ยว
    bg_w = int(doc_w * 1.5)
    bg_h = int(doc_h * 1.5)
    
    bg_files = [f for f in os.listdir(bg_folder) if f.endswith(('.jpg', '.png'))]
    if bg_files:
        bg_name = random.choice(bg_files)
        # โหลดภาพผ่าน Cache (Memory)
        if bg_name not in _BG_CACHE:
            bg_path = os.path.join(bg_folder, bg_name)
            img_read = cv2.imread(bg_path)
            if img_read is not None:
                _BG_CACHE[bg_name] = cv2.cvtColor(img_read, cv2.COLOR_BGR2RGB)
            else:
                _BG_CACHE[bg_name] = np.ones((100, 100, 3), dtype=np.uint8) * 150
                
        bg = _BG_CACHE[bg_name].copy()
        bg = cv2.resize(bg, (bg_w, bg_h))
    else:
        bg = np.ones((bg_h, bg_w, 3), dtype=np.uint8) * 150
        
    pts_src = np.float32([[0, 0], [doc_w, 0], [doc_w, doc_h], [0, doc_h]])
    
    margin_x = random.randint(50, 200)
    margin_y = random.randint(50, 200)
    
    if difficulty == "easy":
        pt1 = [margin_x + random.randint(-20, 20), margin_y + random.randint(-20, 20)]
        pt2 = [bg_w - margin_x + random.randint(-20, 20), margin_y + random.randint(-20, 30)]
        pt3 = [bg_w - margin_x + random.randint(-30, 10), bg_h - margin_y + random.randint(-10, 30)]
        pt4 = [margin_x + random.randint(-30, 20), bg_h - margin_y + random.randint(-10, 20)]
    else:
        pt1 = [margin_x + random.randint(-50, 200), margin_y + random.randint(-50, 200)]
        pt2 = [bg_w - margin_x + random.randint(-200, 50), margin_y + random.randint(0, 250)]
        pt3 = [bg_w - margin_x + random.randint(-250, 50), bg_h - margin_y + random.randint(-250, 50)]
        pt4 = [margin_x + random.randint(-50, 250), bg_h - margin_y + random.randint(-250, 50)]
        
    pts_dst = np.float32([pt1, pt2, pt3, pt4])
    M = cv2.getPerspectiveTransform(pts_src, pts_dst)
    
    warped_doc = cv2.warpPerspective(img_cv, M, (bg_w, bg_h), borderMode=cv2.BORDER_CONSTANT, borderValue=(0,0,0))
    new_bboxes = warp_bboxes(bboxes, M)
    
    mask = cv2.warpPerspective(np.ones_like(img_cv)*255, M, (bg_w, bg_h))
    gray_mask = cv2.cvtColor(mask, cv2.COLOR_RGB2GRAY)
    _, binary_mask = cv2.threshold(gray_mask, 1, 255, cv2.THRESH_BINARY)
    
    warped_doc_fg = cv2.bitwise_and(warped_doc, warped_doc, mask=binary_mask)
    inv_mask = cv2.bitwise_not(binary_mask)
    bg_bg = cv2.bitwise_and(bg, bg, mask=inv_mask)
    
    final_img = cv2.add(bg_bg, warped_doc_fg)
    
    if difficulty == "hard":
        # Add shadow
        shadow = np.ones_like(final_img, dtype=np.float32)
        # Fix: ป้องกัน error กรณี bg_h เล็กกว่า 200
        sy = random.randint(min(100, bg_h//2), max(101, bg_h-200))
        shadow[sy:, :] = random.uniform(0.6, 0.8) 
        final_img = cv2.multiply(final_img.astype(np.float32), shadow).astype(np.uint8)
        
        if random.random() > 0.5:
            final_img = cv2.GaussianBlur(final_img, (3,3), 0)
            
    return Image.fromarray(final_img), new_bboxes
