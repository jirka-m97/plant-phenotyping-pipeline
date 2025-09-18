// =========================================================================
// Turntable Continuous Rotation Control (Arduino, en-GB)
// Author: Jiří Mach
// Institution: UCT Prague, Faculty of Food and Biochemical Technology,
//              Laboratory of Bioengineering
// Licence: Apache 2.0
// Date: 2025-09-18
// Description:
//   Arduino sketch for continuous rotation of a stepper-driven turntable
//   using an A4988 driver. The EN, DIR, and STEP pins are configured to
//   generate pulses with a fixed delay time, driving the table to rotate
//   endlessly in one direction.
// =========================================================================

#define EN 8

//Direction pin
#define X_DIR 5

//Step pin
#define X_STP 2

//A498
int delayTime = 1810;  
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
}

void loop() {
  while(true) {
    step(true, X_DIR, X_STP, one_step); 
  }
}
