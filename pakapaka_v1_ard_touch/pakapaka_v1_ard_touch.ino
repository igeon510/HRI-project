#include <Servo.h>

const int servoLeftDefault=180;
const int servoRightDefault=0;
const int servoLeftMax=90;
const int servoRightMax=120;
const int touchPin=4;


Servo servoLeft;
Servo servoRight;
int input;
int lastTouchState=LOW;


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

// 고개 숙임 (90도)
void nodDown90() {
  servoLeft.write((servoLeftDefault+servoLeftMax)/2);
  servoRight.write((servoRightDefault+servoRightMax)/2);
}


// 고개 숙임 (180도 수준)
void nodDown180() {
  servoLeft.write(servoLeftMax);
  servoRight.write(servoRightMax);
}

// 교정 알림: 흔들기 동작
void shakeHead() {
  for (int i = 0; i < 3; i++) {
    servoLeft.write(servoLeftDefault);
    servoRight.write(servoRightMax);
    delay(500);
    servoLeft.write(servoLeftMax);
    servoRight.write(servoRightDefault);
    delay(500);
  }
  nodDown180();
  delay(8000);
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
  setDefaultPosition();
  delay(8000);
}

// touch쓰고 끄덕끄덕 모션
// 일단은 nodYes를 가져다 쓰지만, 다른거 써도 됨.
void touched(){
  Serial.println("TOUCH");
  setDefaultPosition();
  delay(100);
  nodYes();
}

void loop() {

  int currentState=digitalRead(touchPin);
  if (currentState==HIGH){
    touched();
    // 이게 불려지는 순간 사실 touched에서 nodYes가 불려지면서 딜레이가 꽤 길어짐, 따라서 그동안은 아두이노 코드 진행 x
    return;
  }

  if (Serial.available()) {
    input = Serial.read();
  

    switch (input) {
      case '0':
        setDefaultPosition();  // 기본 자세
        break;

      case '1':
        nodDown90();          // 고개 살짝 숙임, 대기
        break;

      case '2':
        nodDown180();          // 고개 많이 숙임
        break;

      case '3':
        setDefaultPosition();
        delay(100);
        nodYes();
        break;

      case '4':
        shakeHead();           // 교정 알림
        break;

      case '5':
        setDefaultPosition();
        delay(100);
        nodYes();             // 교정 완수 보상 (끄덕끄덕)
        break;

      case '6':
        // 쓰다듬기 모션 (미구현)
        break;

      default:
        break;

    }
    
  
  }
}
