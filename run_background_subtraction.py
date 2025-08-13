import cv2
import os
import time

# ==============================================================================
# ⚙️ ส่วนตั้งค่า (CONFIGURATION)
# ==============================================================================

# ระบุตำแหน่งไฟล์วิดีโอ หรือใช้ 0 สำหรับกล้องเว็บแคม
VIDEO_SOURCE = 'IMG_3829.MOV' 

# สร้างโฟลเดอร์สำหรับเก็บภาพ Snapshot
SNAPSHOT_DIR = 'box_snapshots'
if not os.path.exists(SNAPSHOT_DIR):
    os.makedirs(SNAPSHOT_DIR)

# ขนาดพื้นที่ (Area) ขั้นต่ำของวัตถุที่จะถือว่าเป็น "กล่อง" (เพื่อกรอง Noise)
# **ปรับค่านี้ให้เหมาะสมกับขนาดกล่องในวิดีโอของคุณ**
MIN_CONTOUR_AREA = 100000

# ตำแหน่งของเส้น Trigger สำหรับถ่ายภาพ (คิดเป็น % ของความกว้างจอ)
# 0.5 คือกลางจอพอดี
TRIGGER_POSITION_PERCENT = 0.9 

# ==============================================================================
# ✨ ส่วนโปรแกรมหลัก (MAIN PROGRAM)
# ==============================================================================


# Set your desired output size
resize_width = 640
resize_height = 480



def sharpen_image_unsharp_mask(image, kernel_size=(5, 5), sigma=1.0, amount=1.5, threshold=0):
    """
    เพิ่มความคมชัดของภาพด้วยเทคนิค Unsharp Masking
    - image: ภาพที่ต้องการปรับ (ควรเป็นภาพสี BGR)
    - kernel_size: ขนาดของ Gaussian blur kernel
    - sigma: ค่าเบี่ยงเบนมาตรฐานของ Gaussian blur
    - amount: ปริมาณความคมชัดที่จะเพิ่ม (1.0 คือไม่เปลี่ยนแปลง, > 1.0 คือคมขึ้น)
    - threshold: ค่าขีดแบ่งสำหรับ sharpening mask
    """
    # 1. ทำสำเนาภาพต้นฉบับ
    original = image.copy()

    # 2. สร้างเวอร์ชันที่เบลอของภาพ
    blurred = cv2.GaussianBlur(original, kernel_size, sigma)

    # 3. สร้าง "Unsharp Mask" โดยการลบภาพเบลอออกจากภาพต้นฉบับ
    # cv2.addWeighted คือการรวมภาพแบบมีน้ำหนัก: original*amount - blurred*(amount-1)
    sharpened = cv2.addWeighted(original, amount, blurred, - (amount - 1), threshold)
    
    return sharpened


def main():
    # 1. โหลดวิดีโอและเตรียมการ
    cap = cv2.VideoCapture(VIDEO_SOURCE)
    if not cap.isOpened():
        print(f"Error: ไม่สามารถเปิดไฟล์วิดีโอหรือกล้องที่ {VIDEO_SOURCE}")
        return

    # สร้าง Background Subtractor แบบ MOG2
    # history: จำนวนเฟรมที่ใช้เรียนรู้ background
    # varThreshold: ค่าความแปรปรวน, ยิ่งสูงยิ่งตรวจจับการเปลี่ยนแปลงได้ยาก (ลด false positive)
    # detectShadows=True: ให้ระบบพยายามแยกแยะและกำจัดเงา (เงาจะเป็นสีเทาใน mask)
    bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=50, detectShadows=True)

    # 2. ตัวแปรสำหรับจัดการสถานะ
    snapshot_counter = 0
    can_take_snapshot = True # สถานะที่บอกว่าพร้อมถ่ายภาพกล่องใบใหม่หรือไม่

    while True:
        # 3. อ่านเฟรมจากวิดีโอ
        ret, frame = cap.read()

        

        if not ret:
            print("วิดีโอจบแล้ว หรือไม่สามารถอ่านเฟรมได้")
            break

        # Resize the frame
        frame = cv2.resize(frame, (resize_width, resize_height))

        frame_height, frame_width, _ = frame.shape
        
        # คำนวณตำแหน่งเส้น Trigger
        trigger_line_x = int(frame_width * TRIGGER_POSITION_PERCENT)

        # 4. ประมวลผลภาพ
        # 4.1. ใช้ Background Subtractor เพื่อหา Foreground Mask
        fg_mask = bg_subtractor.apply(frame)
        
        # 4.2. MOG2 จะสร้างเงาเป็นสีเทา (ค่า 127) เราจะตั้งให้เป็นสีดำ (0) เพื่อให้เหลือแค่วัตถุ
        _, fg_mask = cv2.threshold(fg_mask, 254, 255, cv2.THRESH_BINARY)
        
        # 4.3. กำจัด Noise ใน Mask
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel, iterations=2)

        # 5. ค้นหาวัตถุ (Contours)
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        found_box_in_frame = False

        for contour in contours:
            # 5.1. กรองวัตถุขนาดเล็ก (Noise) ออกไป
            if cv2.contourArea(contour) < MIN_CONTOUR_AREA:
                continue

            found_box_in_frame = True # เจอกล่องในเฟรมแล้ว

            # 5.2. หาตำแหน่งและขนาดของกล่อง
            (x, y, w, h) = cv2.boundingRect(contour)
            
            # วาดกรอบสี่เหลี่ยมรอบกล่องที่เจอ (สีเขียว)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # 6. Logic การตัดสินใจถ่ายภาพ (Triggering)
            # เช็คว่า "ขอบหน้า" ของกล่องผ่านเส้น Trigger ไปแล้ว และ "ขอบหลัง" ยังไม่ผ่าน
            # และต้องอยู่ในสถานะที่พร้อมถ่ายภาพ
            if x < trigger_line_x < x + w and can_take_snapshot:
                
                # --- SNAPSHOT! ---
                # ตัดภาพกล่องจากเฟรมสีต้นฉบับ
                # snapshot = frame[y:y+h, x:x+w]
                snapshot_original = frame[y:y+h, x:x+w]
    
                # =========================================================
                # ✨ ขั้นตอนใหม่: นำภาพที่ได้ไปเพิ่มความคมชัด ✨
                # =========================================================
                if snapshot_original.size > 0: # ตรวจสอบว่าภาพไม่ว่างเปล่า
                    snapshot_sharpened = sharpen_image_unsharp_mask(snapshot_original, amount=2.0)
                else:
                    snapshot_sharpened = snapshot_original # ถ้าภาพว่างเปล่าก็ใช้ภาพเดิม
                # =========================================================
                
                # สร้างชื่อไฟล์ที่ไม่ซ้ำกัน
                timestamp = int(time.time())
                filename = os.path.join(SNAPSHOT_DIR, f'box_{timestamp}_{snapshot_counter}.png')
                
                # # บันทึกภาพ
                # cv2.imwrite(filename, snapshot)
                # บันทึกภาพ "เวอร์ชันที่คมชัดขึ้น"
                cv2.imwrite(filename, snapshot_sharpened) 
                print(f"✅ Snapshot taken: {filename}")
                
                snapshot_counter += 1
                can_take_snapshot = False # ตั้งค่าว่าถ่ายไปแล้ว จะไม่ถ่ายซ้ำจนกว่ากล่องใบนี้จะผ่านไป

        # 7. รีเซ็ตสถานะ
        # ถ้าไม่เจอกล่องใดๆ ในเฟรมเลย แสดงว่ากล่องใบเก่าผ่านไปแล้ว ให้รีเซ็ตสถานะเพื่อรอถ่ายใบใหม่
        if not found_box_in_frame:
            can_take_snapshot = True

        # 8. แสดงผลลัพธ์ (สำหรับ Debug)
        # วาดเส้น Trigger (สีแดง)
        cv2.line(frame, (trigger_line_x, 0), (trigger_line_x, frame_height), (0, 0, 255), 2)
        cv2.putText(frame, 'Trigger Line', (trigger_line_x + 5, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        
        # แสดงสถานะปัจจุบันบนจอ
        status_text = "Status: READY" if can_take_snapshot else "Status: WAITING FOR NEXT BOX"
        cv2.putText(frame, status_text, (10, frame_height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)

        cv2.imshow('Original Frame', frame)
        cv2.imshow('Foreground Mask', fg_mask)

        # กด 'q' เพื่อออกจากโปรแกรม
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # 9. คืนทรัพยากร
    cap.release()
    cv2.destroyAllWindows()
    print("Program finished.")


if __name__ == '__main__':
    main()
