import cv2

# แทนที่ด้วย RTSP URL ของคุณ
rtsp_url = "rtsp://admin:password123@192.168.1.108:554/stream1"

# สร้าง object VideoCapture
cap = cv2.VideoCapture(0)

# ตรวจสอบว่าเปิดกล้องได้สำเร็จหรือไม่
if not cap.isOpened():
    print("ไม่สามารถเปิดกล้องได้")
    exit()

# วนลูปเพื่ออ่านเฟรมจากวิดีโอ
while True:
    # อ่านเฟรม
    ret, frame = cap.read()

    # ตรวจสอบว่าอ่านเฟรมได้สำเร็จหรือไม่
    if not ret:
        print("ไม่สามารถรับเฟรมได้ (อาจสิ้นสุดสตรีมแล้ว?)")
        break

    # แสดงผลเฟรม
    cv2.imshow('CCTV Stream', frame)

    # กด 'q' เพื่อออกจากโปรแกรม
    if cv2.waitKey(1) == ord('q'):
        break

# ปิดการเชื่อมต่อและหน้าต่างทั้งหมด
cap.release()
cv2.destroyAllWindows()
