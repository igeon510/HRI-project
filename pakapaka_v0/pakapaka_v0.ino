// 서보모터 1개 버전입니다.

#include <Servo.h>

Servo servoLeft;
int input;

bool isWaitingAfterDown = false;
bool isWaitingAfterStretch = false;
unsigned long waitStartTime = 0;

void setup() {
  servoLeft.attach(9);
  Serial.begin(9600);
}

void setDefaultAndWait(){
  servoLeft.write(0);
  waitStartTime=millis();
  isWaitingAfterStretch=true;
}

void setDefaultPosition() {
  servoLeft.write(0);
}

void nodDown90() {
  servoLeft.write(90);
  waitStartTime = millis();
  isWaitingAfterDown = true;
}

void nodDown180() {
  servoLeft.write(180);
}

void loop() {
  // ✅ 대기 중이면 아무것도 안 하고 시리얼도 무시
  if (isWaitingAfterDown) {
    if (millis() - waitStartTime >= 1000) {
      isWaitingAfterDown = false;
    }
    return; // 여기서 완전히 loop 나감
  }
  if (isWaitingAfterStretch) {
    if (millis() - waitStartTime >= 5000) {
      isWaitingAfterStretch = false;
    }
    return; // 여기서 완전히 loop 나감
  }

  // ✅ 시리얼 입력 수신
  if (Serial.available()) {
    input = Serial.read();

    switch (input) {
      case '0':
        setDefaultPosition();
        break;
      case '1':
        nodDown90();  // 90도 숙이고 5초 대기 시작
        break;
      case '2':
        nodDown180(); // 즉시 180도 숙임
        break;
      case '3':
        setDefaultAndWait(); // 디폴트로 가서 5초 대기 시작.
        break;
      default:
        break;
    }
  }
}

