// =========================================================================
// Turntable Zero Position Control with Hall Sensor (Arduino, en-GB)
// Author: Jiří Mach
// Institution: UCT Prague, Faculty of Food and Biochemical Technology,
//              Laboratory of Bioengineering
// Licence: Apache 2.0
// Date: 2025-09-18
// Description:
//   Arduino sketch to move a stepper-driven turntable to its zero position
//   using an A4988 driver and a Hall effect sensor as a stop signal. The
//   stepper is rotated until the Hall sensor is triggered, after which the
//   motor is disabled to lock the reference position.
// =========================================================================

// Turntable pin definitions
#define EN    8  // enable pin (A4988)
#define X_DIR 5  // direction pin
#define X_STP 2  // step pin

// Hall sensor pin definition
int digitalPin = 7;
int digitalVal;

// A4988 stepper driver — pulse delay in microseconds
int delayTime  = 300;
int one_step   = 13100;  // full rotation step count

// reserved for future use
// int scanningTime = 2000;

// Step function — rotates stepper until Hall sensor is triggered
void step(bool dir, byte dirPin, byte stepperPin, int steps) {
  digitalWrite(dirPin, dir);
  for (int i = 0; i < steps; i++) {
    digitalVal = digitalRead(digitalPin);  // check Hall sensor state
    if (digitalVal == HIGH) {
      break;  // stop if Hall sensor triggered
    }
    digitalWrite(stepperPin, HIGH);
    delayMicroseconds(delayTime);
    digitalWrite(stepperPin, LOW);
    delayMicroseconds(delayTime);
  }
}

void setup() {
  // Turntable pin modes
  pinMode(X_DIR, OUTPUT);
  pinMode(X_STP, OUTPUT);
  pinMode(EN, OUTPUT);
  digitalWrite(EN, HIGH);
  digitalWrite(X_DIR, LOW);
  digitalWrite(X_STP, LOW);

  // Hall sensor pin mode
  pinMode(digitalPin, INPUT);
}

void loop() {
  digitalVal = digitalRead(digitalPin);
  if (digitalVal == LOW) {
    digitalWrite(EN, LOW);
    step(true, X_DIR, X_STP, one_step);
  }
  else {
    digitalWrite(EN, HIGH);
  }
}
