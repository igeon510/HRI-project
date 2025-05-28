import cv2
import mediapipe as mp
import sys
import serial
import time
import pygame
import serial.tools.list_ports
import os 


# 포트 자동감지, pyinstaller 혹은 안되면 필요 패키지 설치하도록 readme 추가

# drawio seq1
# ====================== 초기화 함수 ======================

import serial.tools.list_ports

def init_arduino(baudrate=9600):
    ports = serial.tools.list_ports.comports()
    for p in ports:
        if "Arduino" in p.description or "usbmodem" in p.device or "usbserial" in p.device:
            print(f"Found Arduino on {p.device}")
            return serial.Serial(p.device, baudrate)
    raise Exception("Arduino not found. Please check the connection.")


def init_mediapipe():
    mp_pose = mp.solutions.pose
    return mp_pose.Pose(
        static_image_mode=False,
        model_complexity=0,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )
    
def init_camera():
    cap = cv2.VideoCapture(0)
    cv2.namedWindow('Posture Detection', cv2.WINDOW_NORMAL)
    return cap

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
# ====================== 기능 함수 ======================

def get_landmark_positions(pose_landmarks, image_width, image_height):
    # 어깨 중앙점 계산
    left_shoulder = pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.LEFT_SHOULDER]
    right_shoulder = pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER]
    
    # 입 좌표 계산
    mouth_left = pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.MOUTH_LEFT]
    mouth_right = pose_landmarks.landmark[mp.solutions.pose.PoseLandmark.MOUTH_RIGHT]
    
    # 어깨 중앙점 계산
    shoulder_mid_x = (left_shoulder.x + right_shoulder.x) / 2
    shoulder_mid_y = (left_shoulder.y + right_shoulder.y) / 2
    
    # 입 중앙점 계산
    mouth_mid_x = (mouth_left.x + mouth_right.x) / 2
    mouth_mid_y = (mouth_left.y + mouth_right.y) / 2
    
    return {
        'shoulder_mid': (int(shoulder_mid_x * image_width), int(shoulder_mid_y * image_height)),
        'mouth_mid': (int(mouth_mid_x * image_width), int(mouth_mid_y * image_height)),
        'mouth_y': int(mouth_mid_y * image_height),
        'shoulder_mid_y': int(shoulder_mid_y * image_height)
    }

def draw_baseline_guidance(image, font):
    cv2.putText(image, "Please straighten your back and shoulders according to the reference posture and look at the screen. Press 'S' in keyboard.", (20, 60), font, 0.8, (0, 0, 255), 2)
    center_x, center_y = image.shape[1] // 2 + 50, image.shape[0] // 2
    axes_length = (200, 300)
    cv2.ellipse(image, (center_x, center_y), axes_length, 0, 0, 360, (0, 255, 255), 2)


def calculate_score_from_landmarks(baseline, current):
    """
    입과 어깨 중앙점의 상대적 위치 변화로 거북목 점수를 계산.
    - 기준값은 함수 내부에서 설정됨
    - 입과 어깨 사이의 거리 변화를 기반으로 계산
    """
    
    # 기준값 정의
    distance_thresh = 120  # 픽셀 기준 거리 변화 허용치
    
    # 값 추출
    baseline_mouth_y = baseline['mouth_y']
    baseline_shoulder_y = baseline['shoulder_mid_y']
    current_mouth_y = current['mouth_y']
    current_shoulder_y = current['shoulder_mid_y']
    
    
    # 기준 자세에서의 거리
    baseline_distance = abs(baseline_mouth_y - baseline_shoulder_y)
    current_distance = abs(current_mouth_y - current_shoulder_y)
    
    # 거리 변화량 계산
    distance_diff = baseline_distance-current_distance
    
    # 정규화 점수 계산
    score = min(max((distance_diff / distance_thresh) * 100, 0), 100)
    
    return score


def handle_posture_feedback(score, font, image, arduino):
    if score > 80:
        #cv2.putText(image, "Stage 2 Warning: Severe posture issue!", (20, 120), font, 0.8, (0, 0, 255), 2)
        arduino.write(b'4')
        print("serial 4 sent\n")
        # shakeHead() 모션임
    elif score >= 50:
        #cv2.putText(image, "Stage 1 Warning: Please fix your posture!", (20, 120), font, 0.8, (0, 165, 255), 2)
        arduino.write(b'1')
        print("serial 1 sent\n")
    else:
        arduino.write(b'0')
        print("serial 0 sent\n")

def handle_stretch_session(arduino):
    if not pygame.mixer.music.get_busy():
        pygame.mixer.music.play()
    arduino.write(b'3')

# ====================== 메인 ======================

def main():
    pygame.init()
    pygame.mixer.init()
    try:
        pygame.mixer.music.load(resource_path("alpacca_sound.wav"))
    except Exception as e:
        print("사운드 파일 로딩 실패:", e)
        return
        
    arduino = init_arduino()
    pose = init_mediapipe()
    cap = init_camera()
    font = cv2.FONT_HERSHEY_DUPLEX

    baseline_landmarks = None
    measured = False

    last_score_time = 0  # ⬅ 1초 타이머 기준
    last_touch_time = 0  # 터치 반응 시간 초기화

    score=0

    while cap.isOpened():

        #touch 됐으면 효과음 틀기 (touch는 딱 하나만 올 것임)
        if arduino.in_waiting > 0:
            line = arduino.readline().decode('utf-8').strip()
            if line == "TOUCH":
                print("🧤 TOUCH received from Arduino")
                if not pygame.mixer.music.get_busy():
                  pygame.mixer.music.play()

        success, image = cap.read()
        if not success:
            break

        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = pose.process(image_rgb)
        image_height, image_width, _ = image.shape
        key = cv2.waitKey(5)

        if results.pose_landmarks:
            landmarks = get_landmark_positions(results.pose_landmarks, image_width, image_height)

            # 랜드마크 표시
            cv2.circle(image, landmarks['shoulder_mid'], 4, (0, 255, 0), -1)
            cv2.circle(image, landmarks['mouth_mid'], 4, (0, 0, 255), -1)
         

            if not measured:
                draw_baseline_guidance(image, font)
                if key in [ord('s') , ord('m')]:
                    baseline_landmarks = landmarks
                    measured = True
                    #print(" 기준 자세 저장 완료!")
            else:
                current_time=time.time()
                cv2.putText(image, "'M' to stretch, 'R' to reset baseline", (20, 110), font, 0.8, (200, 200, 200), 1)
                cv2.putText(image, f'Turtle Neck Score: {score:.1f}/100', (20, 80), font, 0.8, (0, 100, 255), 2)
                if current_time - last_score_time >= 3.0: # 3초에 한번 score재고, 처리하기
                    score = calculate_score_from_landmarks(baseline_landmarks, landmarks)
                    cv2.putText(image, f'Turtle Neck Score: {score:.1f}/100', (20, 80), font, 0.8, (0, 100, 255), 2)
                    handle_posture_feedback(score, font, image, arduino)
                    if score>=80:
                        last_score_time=current_time+3.0
                    else :
                        last_score_time=current_time
                

        cv2.imshow('Pakapaka', image)

        if key in [ord('m'), ord('M')]:
            handle_stretch_session(arduino)


        if key in [ord('r'), ord('R')]:
            baseline_landmarks = None
            measured = False
            #print("기준 자세 초기화 완료!")

        if key == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
    cv2.waitKey(1)
    sys.exit()

if __name__ == "__main__":
    main()