import cv2
import sys
import serial
import time
import pygame
import serial.tools.list_ports
import os
import numpy as np
import mediapipe as mp
from mediapipe import solutions
from mediapipe.framework.formats import landmark_pb2

from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# ====================== 초기화 함수 ======================

def init_arduino(baudrate=9600):
    ports = serial.tools.list_ports.comports()
    for p in ports:
        if "Arduino" in p.description or "usbmodem" in p.device or "usbserial" in p.device:
            print(f"Found Arduino on {p.device}")
            return serial.Serial(p.device, baudrate)
    raise Exception("Arduino not found. Please check the connection.")

def init_pose_landmarker(model_path):
    base_options = python.BaseOptions(model_asset_path=model_path)
    options = vision.PoseLandmarkerOptions(
        base_options=base_options,
        output_segmentation_masks=False,
        num_poses=1,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    return vision.PoseLandmarker.create_from_options(options)

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

def get_landmark_positions(landmarks, image_width, image_height):
    left_shoulder = landmarks[11]
    right_shoulder = landmarks[12]
    mouth_left = landmarks[9]
    mouth_right = landmarks[10]

    shoulder_mid_x = (left_shoulder.x + right_shoulder.x) / 2
    shoulder_mid_y = (left_shoulder.y + right_shoulder.y) / 2
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
    distance_thresh = 120
    baseline_mouth_y = baseline['mouth_y']
    baseline_shoulder_y = baseline['shoulder_mid_y']
    current_mouth_y = current['mouth_y']
    current_shoulder_y = current['shoulder_mid_y']
    baseline_distance = abs(baseline_mouth_y - baseline_shoulder_y)
    current_distance = abs(current_mouth_y - current_shoulder_y)
    distance_diff = baseline_distance - current_distance
    score = min(max((distance_diff / distance_thresh) * 100, 0), 100)
    return score

def handle_posture_feedback(score, font, image, arduino):
    if score > 80:
        arduino.write(b'2')
        print("serial 2 sent\n")
    elif score >= 50:
        arduino.write(b'1')
        print("serial 1 sent\n")
    else:
        arduino.write(b'0')
        print("serial 0 sent\n")

def handle_stretch_session(arduino):
    if not pygame.mixer.music.get_busy():
        pygame.mixer.music.play()
    arduino.write(b'3')

def draw_landmarks_on_image(rgb_image, detection_result):
    annotated_image = np.copy(rgb_image)
    if detection_result.pose_landmarks and len(detection_result.pose_landmarks) > 0:
        landmarks = detection_result.pose_landmarks[0]
        image_height, image_width, _ = annotated_image.shape

        # 어깨(11, 12): 파란색, 입(9, 10): 빨간색
        for idx, color, radius in [
            (11, (0, 0, 255), 8),   # 왼쪽 어깨(파랑)
            (12, (255, 0, 0), 8),   # 오른쪽 어깨(빨강)
            (9, (0, 255, 255), 8),  # 왼쪽 입(노랑)
            (10, (0, 255, 255), 8)  # 오른쪽 입(노랑)
        ]:
            x = int(landmarks[idx].x * image_width)
            y = int(landmarks[idx].y * image_height)
            cv2.circle(annotated_image, (x, y), radius, color, -1)
    return annotated_image

# ====================== 메인 ======================

def main():
    pygame.init()
    pygame.mixer.init()
    try:
        pygame.mixer.music.load(resource_path("alpacca_sound.wav"))
    except Exception as e:
        print("사운드 파일 로딩 실패:", e)
        return

    model_path = resource_path("pose_landmarker_lite.task")
    pose_landmarker = init_pose_landmarker(model_path)
    arduino = init_arduino()
    cap = init_camera()
    font = cv2.FONT_HERSHEY_DUPLEX

    baseline_landmarks = None
    measured = False
    last_score_time = 0
    score = 0

    while cap.isOpened():
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
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
        detection_result = pose_landmarker.detect(mp_image)
        image_height, image_width, _ = image.shape
        key = cv2.waitKey(5)

        if detection_result.pose_landmarks and len(detection_result.pose_landmarks) > 0:
            # 시각화
            annotated_image = draw_landmarks_on_image(image_rgb, detection_result)
            image = cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR)

            landmarks = get_landmark_positions(
                detection_result.pose_landmarks[0],
                image_width,
                image_height
            )

            if not measured:
                draw_baseline_guidance(image, font)
                if key in [ord('s'), ord('m')]:
                    baseline_landmarks = landmarks
                    measured = True
            else:
                current_time = time.time()
                cv2.putText(image, "'M' to stretch, 'R' to reset baseline", (20, 110), font, 0.8, (200, 200, 200), 1)
                cv2.putText(image, f'Turtle Neck Score: {score:.1f}/100', (20, 80), font, 0.8, (0, 100, 255), 2)
                if current_time - last_score_time >= 3.0:
                    score = calculate_score_from_landmarks(baseline_landmarks, landmarks)
                    cv2.putText(image, f'Turtle Neck Score: {score:.1f}/100', (20, 80), font, 0.8, (0, 100, 255), 2)
                    handle_posture_feedback(score, font, image, arduino)
                    last_score_time = current_time

        cv2.imshow('Pakapaka', image)

        if key in [ord('m'), ord('M')]:
            handle_stretch_session(arduino)

        if key in [ord('r'), ord('R')]:
            baseline_landmarks = None
            measured = False

        if key == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
    cv2.waitKey(1)
    sys.exit()

if __name__ == "__main__":
    main()