// 서보모터 2개 연결시 업데이트

#include <Servo.h>

Servo servoLeft;
Servo servoRight;
int input;

void setup() {
  servoLeft.attach(9);   // 왼쪽 서보모터 핀
  servoRight.attach(10); // 오른쪽 서보모터 핀
  Serial.begin(9600);
}



// 고개 기본 위치
void setDefaultPosition() {
  servoLeft.write(0);
  servoRight.write(0);
}

// 고개 숙임 (90도)
void nodDown90() {
  servoLeft.write(90);
  servoRight.write(90);
}

// 고개 숙임 (180도 수준)
void nodDown180() {
  servoLeft.write(180);
  servoRight.write(180);
}

// 교정 알림: 흔들기 동작
void shakeHead() {
  for (int i = 0; i < 3; i++) {
    servoLeft.write(160);
    servoRight.write(20);
    delay(300);
    servoLeft.write(120);
    servoRight.write(60);
    delay(300);
  }
}

// 교정 완수 보상: 끄덕끄덕
void nodYes() {
  for (int i = 0; i < 3; i++) {
    servoLeft.write(45);
    servoRight.write(45);
    delay(400);
    servoLeft.write(135);
    servoRight.write(135);
    delay(400);
  }
}

void loop() {
  if (Serial.available()) {
    input = Serial.read();

    switch (input) {
      case '0':
        setDefaultPosition();  // 기본 자세
        break;

      case '1':
        nodDown90();           // 고개 살짝 숙임
        delay(5000);           // 5초 대기
        break;

      case '2':
        nodDown180();          // 고개 많이 숙임
        shakeHead();           // 교정 알림
        break;

      case '3':
        // 자세 교정 세션 시작 (미구현)

        break;

      case '4':
        nodDown180();          // 고개 많이 숙임
        shakeHead();           // 교정 알림
        delay(500);           // 5초 대기
        break;

      case '5':
        setDefaultPosition();             // 교정 완수 보상 (끄덕끄덕)
        break;

      case '6':
        // 쓰다듬기 모션 (미구현)
        break;

      default:
        break;
    }
  }
}

