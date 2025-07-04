#include <Servo.h>

const int servoLeftDefault=165;
const int servoRightDefault=25;
const int servoLeftMax=55;
const int servoRightMax=140;
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

void nodDown45(){
  servoLeft.write(servoLeftDefault+(servoLeftMax-servoLeftDefault)*0.25);
  servoRight.write(servoRightDefault+(servoRightMax-servoRightDefault)*0.25);
}

// 고개 숙임 (90도)
void nodDown90() {
  servoLeft.write((servoLeftDefault+servoLeftMax)/2);
  servoRight.write((servoRightDefault+servoRightMax)/2);
}

void nodDown135() {
  servoLeft.write(servoLeftDefault+(servoLeftMax-servoLeftDefault)*0.75);
  servoRight.write(servoRightDefault+(servoRightMax-servoRightDefault)*0.75);
}


// 고개 숙임 (180도 수준)
void nodDown180() {
  servoLeft.write(servoLeftMax);
  servoRight.write(servoRightMax);
}

// 교정 알림: 흔들기 동작
void shakeHead() {
  for (int i = 0; i < 2; i++) {
    servoLeft.write(servoLeftDefault);
    servoRight.write(servoRightMax);
    delay(500);
    servoLeft.write(servoLeftMax);
    servoRight.write(servoRightDefault);
    delay(500);
  }
  nodDown180();
  delay(3000);
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
  delay(2000);
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

  if (currentState == HIGH) {
    delay(100);  // 50ms 기다린 후
    if (digitalRead(touchPin) == HIGH) {
      touched();  // 진짜 터치라고 판단
      return;
    }
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

      case '5': // 45도
        nodDown45();
        break;
      
      case '6': // 135도
        nodDown135();
        break;
      

      default:
        break;

    }
    
  
  }
}
