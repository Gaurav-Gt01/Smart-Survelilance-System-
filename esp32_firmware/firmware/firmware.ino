#define PIR_PIN    13
#define GREEN_PIN  26
#define RED_PIN    27
#define BUZZER_PIN 14

bool motionActive = false;

void setup() {
  Serial.begin(115200);
  pinMode(PIR_PIN, INPUT);
  pinMode(GREEN_PIN, OUTPUT);
  pinMode(RED_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);

  digitalWrite(GREEN_PIN, HIGH);
  digitalWrite(RED_PIN, LOW);
}

void buzzFor3Seconds() {
  unsigned long start = millis();
  while (millis() - start < 3000) {
    digitalWrite(BUZZER_PIN, HIGH);
    delayMicroseconds(500);
    digitalWrite(BUZZER_PIN, LOW);
    delayMicroseconds(500);
  }
}

void loop() {
  int motion = digitalRead(PIR_PIN);

  if (motion == HIGH && !motionActive) {
    motionActive = true;

    digitalWrite(GREEN_PIN, LOW);
    digitalWrite(RED_PIN, HIGH);

    Serial.println("MOTION");

    buzzFor3Seconds();

    digitalWrite(GREEN_PIN, HIGH);
    digitalWrite(RED_PIN, LOW);
  }

  if (motion == LOW && motionActive) {
    motionActive = false;
    Serial.println("CLEAR");
  }

  delay(200);
}