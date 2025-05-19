import cv2
import mediapipe as mp
import sys
import serial
import time

arduino = serial.Serial('/dev/tty.usbmodem11101', 9600)

arduino_cooldown_until = 0  # 5초 쿨다운


# MediaPipe 초기화
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh()

# 웹캠 켜기, 프레임 수신용 객체 생성
cap = cv2.VideoCapture(0)

# 창 이름 설정
window_name = 'Posture Detection'
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL) # 창 이름, 속성 정의

# 폰트 설정
font = cv2.FONT_HERSHEY_DUPLEX

baseline_chin_y = None
baseline_eye_z = None
measured = False

# 튜닝 가능한 값
chin_y_threshold = 200  # 턱 Y좌표 기준 변화량
eye_z_threshold = 0.02  # 귀 Z좌표 기준 변화량
while cap.isOpened():
    success, image = cap.read() # 웹 캠에서 프레임 받아오기
    if not success:
        break

    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(image_rgb)
    image_height, image_width, _ = image.shape

    key = cv2.waitKey(5)

    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            # 랜드마크 추출
            left_eye = face_landmarks.landmark[33]
            right_eye = face_landmarks.landmark[263]
            chin = face_landmarks.landmark[152]

            # 좌표 변환
            left_eye_pos = (int(left_eye.x * image_width), int(left_eye.y * image_height))
            right_eye_pos = (int(right_eye.x * image_width), int(right_eye.y * image_height))
            chin_pos = (int(chin.x * image_width), int(chin.y * image_height))

            chin_y = chin_pos[1]
            eye_z = (left_eye.z + right_eye.z) / 2  # 양쪽 귀 평균 z값

            # 얼굴 랜드마크 표시
            cv2.circle(image, left_eye_pos, 4, (0, 255, 0), -1)
            cv2.circle(image, right_eye_pos, 4, (0, 255, 0), -1)
            cv2.circle(image, chin_pos, 4, (0, 0, 255), -1)
            if not measured:
                cv2.putText(image, "Sit upright and press 'S' to save baseline", (20, 60),
                font, 0.8, (0, 0, 255), 2)

                # 타원 그리기
                center_x, center_y = image.shape[1] // 2, image.shape[0] // 2
                center_x=center_x+50
                axes_length = (200, 300)  # (가로 반지름, 세로 반지름)
            
                cv2.ellipse(image, (center_x, center_y), axes_length,
                            angle=0, startAngle=0, endAngle=360,
                            color=(0, 255, 255), thickness=2)

                if key == ord('s'):
                    baseline_chin_y = chin_y
                    baseline_eye_z = eye_z
                    measured = True
                    print("✅ 기준 자세 저장 완료!")
            else:
                    chin_y_diff = chin_y - baseline_chin_y
                    eye_z_diff = baseline_eye_z - eye_z

                    chin_score = min(max((chin_y_diff / chin_y_threshold) * 100, 0), 100)
                    eye_score = min(max((eye_z_diff / eye_z_threshold) * 100, 0), 100)

                    score = max(chin_score, eye_score)

                    cv2.putText(image, f'Turtle Neck Score: {score:.1f}/100', (20, 80),
                                font, 0.8, (0, 100, 255), 2)
                    
                    cv2.putText(image, f'Chin Score: {chin_score:.1f}/100', (20, 110),
                                font, 0.8, (0, 150, 255), 2)
                    
                    cv2.putText(image, f'Eye Score: {eye_score:.1f}/100', (20, 140),
                                font, 0.8, (0, 200, 255), 2)

                    current_time = time.time()
                    if current_time >= arduino_cooldown_until:
                        if score > 90:
                            cv2.putText(image, "Stage 2 Warning: Severe posture issue!", (20, 120),
                                        font, 0.8, (0, 0, 255), 2)
                            arduino.write(b'2')
                            arduino_cooldown_until = current_time + 5
                        elif score >= 50:
                            cv2.putText(image, "Stage 1 Warning: Please fix your posture!", (20, 120),
                                        font, 0.8, (0, 165, 255), 2)
                            arduino.write(b'1')
                            arduino_cooldown_until = current_time + 5
                        elif score < 50:
                            arduino.write(b'0')
                            arduino_cooldown_until = current_time + 5



    # 화면 출력
    cv2.imshow(window_name, image) # 받은 이미지를 창에 띄움

    if key == 27:  # ESC 누르면 종료
        break

# 종료 처리
cap.release()
cv2.destroyWindow(window_name)
cv2.waitKey(1)
sys.exit()
