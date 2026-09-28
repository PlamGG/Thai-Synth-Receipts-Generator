import json
import sys
import cv2
import numpy as np

def verify_image(image_path, json_path):
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error loading {image_path}")
        return
        
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    # Draw polygons
    for item in data['ocr_boxes']:
        pts = np.array(item['box'], np.int32)
        pts = pts.reshape((-1, 1, 2))
        
        # วาดกรอบสีแดง
        cv2.polylines(img, [pts], isClosed=True, color=(0, 0, 255), thickness=2)
        
        # ดึงจุดซ้ายบนเพื่อเขียน Label
        x, y = pts[0][0]
        # ใส่พื้นหลังสีดำให้ตัวหนังสือ
        cv2.putText(img, item['label'], (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 3)
        cv2.putText(img, item['label'], (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        
    out_path = image_path.replace(".jpg", "_verified.jpg")
    cv2.imwrite(out_path, img)
    print(f"Verified image saved to {out_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python verify_dataset.py <image.jpg> <data.json>")
    else:
        verify_image(sys.argv[1], sys.argv[2])
