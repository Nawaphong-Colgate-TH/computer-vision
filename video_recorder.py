import cv2
import datetime
import os

# --- การตั้งค่า ---
output_folder = "video_recordings"

if not os.path.exists(output_folder):
    os.makedirs(output_folder)
    print(f"สร้างโฟลเดอร์ '{output_folder}' สำหรับเก็บวิดีโอเรียบร้อยแล้ว")

# เริ่มต้นการจับภาพวิดีโอจากกล้อง
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("ข้อผิดพลาด: ไม่สามารถเปิดกล้องได้")
    exit()

# --- ส่วนของการตั้งค่ากล้องเพื่อให้ได้คุณภาพสูงสุด ---
print("กำลังพยายามตั้งค่าความละเอียดกล้องเป็น 1920x1080...")
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cap.get(cv2.CAP_PROP_FPS)

if fps == 0:
    print("ไม่สามารถดึงค่า FPS จากกล้องได้, ใช้ค่าเริ่มต้น 25 FPS")
    fps = 25.0

print(f"-> กล้องกำลังทำงานที่ความละเอียด: {frame_width}x{frame_height} @ {fps:.2f} FPS")
# -----------------------------------------------------

is_recording = False
video_writer = None
recording_start_time = None # ตัวแปรสำหรับเก็บเวลาที่เริ่มบันทึก

print("\n--- การควบคุม ---")
print("กด 's' เพื่อ เริ่ม/หยุด การบันทึกวิดีโอ")
print("กด 'q' เพื่อออกจากโปรแกรม")
print("--------------------")

while True:
    ret, frame = cap.read()
    if not ret:
        print("ไม่สามารถรับเฟรมภาพได้... กำลังออกจากโปรแกรม")
        break

    # เขียนเฟรมต้นฉบับลงไฟล์วิดีโอ หากกำลังบันทึก
    if is_recording and video_writer:
        video_writer.write(frame)

    # สร้างสำเนาของเฟรมขึ้นมาเพื่อใช้ในการแสดงผล
    display_frame = frame.copy()

    # --- ส่วนของการวาดบนหน้าจอ (จะไม่ถูกบันทึกลงวิดีโอ) ---

    # 1. วาดสัญลักษณ์ REC และตัวนับเวลา (ถ้ากำลังบันทึก)
    if is_recording:
        # วาดวงกลมสีแดง
        cv2.circle(display_frame, (30, 30), 10, (0, 0, 255), -1)
        # วาดข้อความ REC
        cv2.putText(display_frame, "REC", (50, 37), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        # คำนวณและแสดงตัวนับเวลา
        if recording_start_time:
            elapsed_time = datetime.datetime.now() - recording_start_time
            total_seconds = int(elapsed_time.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            time_string = f"{hours:02}:{minutes:02}:{seconds:02}"
            
            # วาดข้อความตัวนับเวลาข้างๆ REC
            cv2.putText(display_frame, time_string, (110, 37), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    # 2. วาดแถบพื้นหลังและข้อความแนะนำที่ด้านล่าง
    alpha = 0.6
    bar_height = 60
    overlay = display_frame.copy()
    cv2.rectangle(overlay, (0, frame_height - bar_height), (frame_width, frame_height), (0, 0, 0), -1)
    cv2.addWeighted(overlay, alpha, display_frame, 1 - alpha, 0, display_frame)
    text1 = "S : Start/Stop Recording"
    text2 = "Q : Quit"
    cv2.putText(display_frame, text1, (10, frame_height - 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(display_frame, text2, (10, frame_height - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    # --- จบส่วนของการวาดบนหน้าจอ ---

    cv2.imshow('Live Video', display_frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord('s'):
        is_recording = not is_recording
        if is_recording:
            print("-> เริ่มการบันทึก...")
            # เริ่มจับเวลาเมื่อการบันทึกเริ่มต้น
            recording_start_time = datetime.datetime.now()
            current_time = recording_start_time.strftime("%Y-%m-%d_%H-%M-%S")
            filename = f'recording_{current_time}.avi'
            full_path = os.path.join(output_folder, filename)
            
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            video_writer = cv2.VideoWriter(full_path, fourcc, fps, (frame_width, frame_height))
            
            print(f"บันทึกเป็นไฟล์ AVI: {full_path}")
        else:
            print("-> หยุดการบันทึก")
            # รีเซ็ตเวลาเมื่อหยุดบันทึก
            recording_start_time = None
            if video_writer:
                video_writer.release()
                video_writer = None
                print("บันทึกวิดีโอเรียบร้อยแล้ว")

    elif key == ord('q'):
        print("กำลังออกจากโปรแกรม...")
        break

if is_recording and video_writer:
    print("กำลังบันทึกไฟล์ส่วนที่เหลือ...")
    video_writer.release()

cap.release()
cv2.destroyAllWindows()
