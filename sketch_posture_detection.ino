const int ledPin = 13;  // 아두이노 보드 내장 LED 핀

void setup() {
  Serial.begin(9600);    // 시리얼 통신 시작
  pinMode(ledPin, OUTPUT);  // 13번 핀을 출력으로 설정
}

void loop() {
  if (Serial.available() > 0) {  // 데이터 수신 대기
    char data = Serial.read();   // 한 글자 읽기

    if (data == '1') {
      digitalWrite(ledPin, HIGH);  // LED 켜기
    } else if (data == '0') {
      digitalWrite(ledPin, LOW);   // LED 끄기
    }
  }
}
