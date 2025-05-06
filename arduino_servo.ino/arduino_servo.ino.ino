#include <Servo.h>

Servo myServo;
int input;

void setup() {
  myServo.attach(9);  // SG90 모터 핀
  Serial.begin(9600);
}

void loop() {
  if (Serial.available()) {
    input = Serial.read();

    if (input == '0') {
      myServo.write(0);  // 정지 또는 기본 자세
    } else if (input == '1') {
      myServo.write(90);  // 1단계 경고
    } else if (input == '2') {
      myServo.write(180);  // 2단계 심각
    }
  }
}
