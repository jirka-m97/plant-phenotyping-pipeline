#define EN 8

//Direction pin
#define X_DIR 5

//Step pin
#define X_STP 2

//A498
int delayTime = 1810;  //48 s jedna otočka
int scanningTime = 2000;
int total_steps = 13100;
int one_step = total_steps;

void step(bool dir, byte dirPin, byte stepperPin, int steps) {
  digitalWrite(dirPin, dir);
  delay(0);
  for (int i = 0; i< steps; i++) {
    digitalWrite(EN,LOW);
    digitalWrite(stepperPin, HIGH);
    delayMicroseconds(delayTime);
    digitalWrite(stepperPin, LOW);
    delayMicroseconds(delayTime);
  }
}

void setup() {
  pinMode(X_DIR, OUTPUT); pinMode(X_STP,OUTPUT);
  pinMode(EN, OUTPUT);
  digitalWrite(EN,HIGH);
  //delay(2000);
  //digitalWrite(EN,LOW);
}

void loop() {
  while(true) {
    step(true, X_DIR, X_STP, one_step); 
  }
}
