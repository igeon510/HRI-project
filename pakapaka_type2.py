# -*- coding: utf-8 -*-
import cv2
import sys
import serial
import time
import pygame
import serial.tools.list_ports
import os
import numpy as np
import mediapipe as mp
import random

from mediapipe.tasks import python
from mediapipe.tasks.python import vision


# 포트 자동감지, pyinstaller 혹은 안되면 필요 패키지 설치하도록 readme 추가

# drawio seq1
# ====================== 초기화 함수 ======================

import serial.tools.list_ports

music_files = [
    "sound/sound1.wav",
    "sound/sound2.wav",
    "sound/sound3.wav",
    "sound/sound4.wav",
    "sound/sound5.wav",
    "sound/sound6.wav",
    "sound/sound7.wav"
    ]    

sound_on = False  # 초기 상태: Off

def init_arduino(baudrate=9600):
    ports = serial.tools.list_ports.comports()
    for p in ports:
        if "Arduino" in p.description or "usbmodem" in p.device or "usbserial" in p.device:
            print(f"Found Arduino on {p.device}")
            try:
                return serial.Serial(p.device, baudrate, timeout=0.1)  # timeout을 짧게 설정
            except serial.SerialException as e:
                print(f"포트 {p.device} 연결 실패: {e}")
                continue
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
    image_bottom_y = image_height - 1

    # 입 중앙 계산
    mouth_left = landmarks[9]
    mouth_right = landmarks[10]
    mouth_mid_x = (mouth_left.x + mouth_right.x) / 2
    mouth_mid_y = (mouth_left.y + mouth_right.y) / 2

    # 어깨 감지 가능한 경우
    try:
        left_shoulder = landmarks[11]
        right_shoulder = landmarks[12]
        shoulder_mid_x = (left_shoulder.x + right_shoulder.x) / 2
        shoulder_mid_y = (left_shoulder.y + right_shoulder.y) / 2
        shoulder_mid = (int(shoulder_mid_x * image_width), int(shoulder_mid_y * image_height))
        shoulder_mid_y_px = int(shoulder_mid_y * image_height)
    except:
        # fallback: 입 중앙 X좌표, 이미지 아래쪽 Y좌표를 어깨로 간주
        shoulder_mid = (int(mouth_mid_x * image_width), image_bottom_y)
        shoulder_mid_y_px = image_bottom_y

    return {
        'shoulder_mid': shoulder_mid,
        'mouth_mid': (int(mouth_mid_x * image_width), int(mouth_mid_y * image_height)),
        'mouth_y': int(mouth_mid_y * image_height),
        'shoulder_mid_y': shoulder_mid_y_px
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
    if score > 90:
        #cv2.putText(image, "Stage 2 Warning: Severe posture issue!", (20, 120), font, 0.8, (0, 0, 255), 2)
        arduino.write(b'4')
        print("serial 4 sent means phase 5 and shake\n")
        if sound_on and not pygame.mixer.music.get_busy():
                    pygame.mixer.music.load(resource_path("sound/sound_shake.wav"))
                    pygame.mixer.music.play()  
        return True
        
        # shakeHead() 모션임
    elif score >= 75:
        #cv2.putText(image, "Stage 1 Warning: Please fix your posture!", (20, 120), font, 0.8, (0, 165, 255), 2)
        arduino.write(b'6')
        print("serial 6 sent means phase 4\n")
        return False

    elif score >= 50:
        #cv2.putText(image, "Stage 1 Warning: Please fix your posture!", (20, 120), font, 0.8, (0, 165, 255), 2)
        arduino.write(b'1')
        print("serial 1 sent means phase 3\n")
        return False

    elif score >= 25:
        #cv2.putText(image, "Stage 1 Warning: Please fix your posture!", (20, 120), font, 0.8, (0, 165, 255), 2)
        arduino.write(b'5')
        print("serial 5 sent means phase 2\n")
        return False

    else:
        arduino.write(b'0')
        print("serial 0 sent means phase 1\n")
        return False

def handle_stretch_session(arduino, sound_on):
    if sound_on and not pygame.mixer.music.get_busy():
        selected_music = resource_path(random.choice(music_files))
        pygame.mixer.music.load(selected_music)
        pygame.mixer.music.play()       
    arduino.write(b'3')

def draw_landmarks_on_image(rgb_image, detection_result):
    annotated_image = np.copy(rgb_image)
    if detection_result.pose_landmarks and len(detection_result.pose_landmarks) > 0:
        landmarks = detection_result.pose_landmarks[0]
        image_height, image_width, _ = annotated_image.shape

        # 입 중앙 계산 (노랑)
        mouth_left = landmarks[9]
        mouth_right = landmarks[10]
        mouth_mid_x = (mouth_left.x + mouth_right.x) / 2
        mouth_mid_y = (mouth_left.y + mouth_right.y) / 2
        mouth_mid = (int(mouth_mid_x * image_width), int(mouth_mid_y * image_height))
        cv2.circle(annotated_image, mouth_mid, 10, (0, 255, 255), -1)

        # 어깨 중앙 계산 (파랑)
        try:
            left_shoulder = landmarks[11]
            right_shoulder = landmarks[12]
            shoulder_mid_x = (left_shoulder.x + right_shoulder.x) / 2
            shoulder_mid_y = (left_shoulder.y + right_shoulder.y) / 2
            shoulder_mid = (int(shoulder_mid_x * image_width), int(shoulder_mid_y * image_height))
        except:
            # 어깨 감지 실패 시: 입 중앙 x + 프레임 하단
            shoulder_mid = (mouth_mid[0], image_height - 1)

        cv2.circle(annotated_image, shoulder_mid, 10, (255, 0, 0), -1)

    return annotated_image


# ====================== 메인 ======================

def main():
    pygame.init()
    pygame.mixer.init()
    global sound_on
        
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

        #touch 됐으면 효과음 틀기 (touch는 딱 하나만 올 것임)
        if arduino.in_waiting > 0:
            line = arduino.readline().decode('utf-8').strip()
            if line == "TOUCH":
                print("🧤 TOUCH received from Arduino")
                if sound_on and not pygame.mixer.music.get_busy():
                    selected_music = resource_path(random.choice(music_files))
                    pygame.mixer.music.load(selected_music)
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
                if key in [ord('s')]:
                    baseline_landmarks = landmarks
                    measured = True
            else:
                current_time = time.time()
                cv2.putText(image, "''R' to reset baseline, 'P' to turn on/off the sound", (20, 110), font, 0.8, (200, 200, 200), 1)
                cv2.putText(image, f'Turtle Neck Score: {score:.1f}/100', (20, 80), font, 0.8, (0, 100, 255), 2)
                cv2.putText(
                    image,
                    f"Sound: {'ON' if sound_on else 'OFF'}",
                    (image.shape[1] - 200, 30),
                    font,
                    0.8,
                    (0, 255, 0) if sound_on else (50, 50, 50),
                    2
                )

                if current_time - last_score_time >= 3.0:
                    prev_score = score
                    score = calculate_score_from_landmarks(baseline_landmarks, landmarks)

                    if prev_score >= 80 and score < 30:
                        if sound_on:# and not pygame.mixer.music.get_busy():
                            pygame.mixer.music.load(resource_path("sound/positive.wav"))  # 하락 알림용 효과음 파일
                            pygame.mixer.music.play()

                    cv2.putText(image, f'Turtle Neck Score: {score:.1f}/100', (20, 80), font, 0.8, (0, 100, 255), 2)
                    if(handle_posture_feedback(score, font, image, arduino)):
                        last_score_time=current_time+4.5
                    else:
                        last_score_time=current_time
                    

        cv2.imshow('Pakapaka', image)

        if key in [ord('r'), ord('R')]:
            baseline_landmarks = None
            measured = False
            #print("기준 자세 초기화 완료!")

        if key in [ord('p'), ord('P')]:
            sound_on = not sound_on
            print(f"{'🔊 Sound ON' if sound_on else '🔇 Sound OFF'}")

        if key == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
    cv2.waitKey(1)
    sys.exit()

if __name__ == "__main__":
    main()