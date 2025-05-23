#include <Servo.h>

const int servoLeftDefault=180;
const int servoRightDefault=0;
const int servoLeftMax=80;
const int servoRightMax=120;


Servo servoLeft;
Servo servoRight;

// left, 9번
// right, 11번




void setup() {
  servoLeft.attach(9);   // 왼쪽 서보모터 핀
  servoRight.attach(11); // 오른쪽 서보모터 핀
  Serial.begin(9600);

}

void setDefaultPosition() {
  servoLeft.write(servoLeftDefault);
  servoRight.write(servoRightDefault);
  Serial.print("default\n");
}

void moveForward() {
  servoLeft.write(servoLeftMax);
  servoRight.write(servoRightMax); 
  Serial.print("forward\n");
}


void shake(){
  for(int i=0;i<5;i++){
  servoLeft.write(servoLeftDefault);
  servoRight.write(servoRightDefault);
  servoLeft.write(servoLeftMax/2);
  servoRight.write(servoRightMax/2);
  }
}
void loop() {
  // put your main code here, to run repeatedly:
  setDefaultPosition();
  delay(3000);
  moveForward();
  delay(3000);

}
