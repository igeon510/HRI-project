#include <Servo.h>

const int servoLeftDefault=180;
const int servoRightDefault=0;
const int servoLeftMax=80;
const int servoRightMax=120;


Servo servoLeft;
Servo servoRight;
int input;

bool isWaitingAfterDown = false;
bool isWaitingAfterStretch = false;
unsigned long waitStartTime = 0;

void setup() {
  servoLeft.attach(9);   // 왼쪽 서보모터 핀
  servoRight.attach(11); // 오른쪽 서보모터 핀
  Serial.begin(9600);
}



// 고개 기본 위치
void setDefaultPosition() {
  servoLeft.write(servoLeftDefault);
  servoRight.write(servoRightDefault);
}

void setDefaultAndWait(){
  servoLeft.write(servoLeftDefault);
  servoRight.write(servoRightDefault);
  waitStartTime=millis();
  isWaitingAfterStretch=true;
}

// 고개 숙임 (90도)
void nodDown90() {
  servoLeft.write((servoLeftDefault+servoLeftMax)/2);
  servoRight.write((servoRightDefault+servoRightMax)/2);
}

void nodDown90AndWait() {
  servoLeft.write((servoLeftDefault+servoLeftMax)/2);
  servoRight.write((servoRightDefault+servoRightMax)/2);
  waitStartTime = millis();
  isWaitingAfterDown = true;
}

// 고개 숙임 (180도 수준)
void nodDown180() {
  servoLeft.write(servoLeftMax);
  servoRight.write(servoRightMax);
}

// 교정 알림: 흔들기 동작
void shakeHead() {
  for (int i = 0; i < 3; i++) {
    servoLeft.write((servoLeftDefault+servoLeftMax)/3);
    servoRight.write((servoRightDefault+servoRightMax)/2);
    delay(500);
    servoLeft.write((servoLeftDefault+servoLeftMax)/2);
    servoRight.write((servoRightDefault+servoRightMax)/3);
    delay(500);
  }
}

// 교정 완수 보상: 끄덕끄덕
void nodYes() {
  for (int i = 0; i < 3; i++) {
    servoLeft.write((servoLeftDefault+servoLeftMax)/2);
    servoRight.write((servoRightDefault+servoRightMax)/2);
    delay(300);
    servoLeft.write(servoLeftDefault);
    servoRight.write(servoRightDefault);
    delay(300);
  }
}

void loop() {

  if (isWaitingAfterDown) {
    if (millis() - waitStartTime >= 5000) {
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


  if (Serial.available()) {
    input = Serial.read();
  

    switch (input) {
      case '0':
        setDefaultPosition();  // 기본 자세
        break;

      case '1':
        nodDown90AndWait();          // 고개 살짝 숙임, 대기
        break;

      case '2':
        nodDown180();          // 고개 많이 숙임
        break;

      case '3':
        setDefaultAndWait();
        nodYes();
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

