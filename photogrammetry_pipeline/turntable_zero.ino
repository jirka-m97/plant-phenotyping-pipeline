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

// Pins_turntable definition
#define EN 8
#define X_DIR 5
#define X_STP 2

// Pins_Hall definition
int digitalPin = 7;
int digitalVal;

// Set parameters (turntable, A498)
int delayTime = 300;
int scanningTime = 2000;
int total_steps = 13100;
int one_step = total_steps;

// Step function definition (turntable)
void step(bool dir, byte dirPin, byte stepperPin, int steps) {
  int digitalVal;
  
  digitalWrite(dirPin, dir);
  delay(0);
  
  for (int i = 0; i < steps; i++) {
    digitalVal = digitalRead(digitalPin); // Check Hall sensor state
  
    // Stop if either condition is met
    if (digitalVal == HIGH) {
      break;
    }

    digitalWrite(stepperPin, HIGH);
    delayMicroseconds(delayTime);
    digitalWrite(stepperPin, LOW);
    delayMicroseconds(delayTime);
  }
}

void setup() {
  // Turntable pinModes
  pinMode(X_DIR, OUTPUT);
  pinMode(X_STP,OUTPUT);
  pinMode(EN, OUTPUT);
  digitalWrite(EN,HIGH);

  digitalWrite(X_DIR,LOW);
  digitalWrite(X_STP,LOW);
  
  // Hall pinModes
  pinMode(digitalPin, INPUT);
}

void loop() {
  digitalVal = digitalRead(digitalPin);

  if (digitalVal == LOW) {
    digitalWrite(EN,LOW);
    step(true, X_DIR, X_STP, one_step);
  }
  else {
    digitalWrite(EN,HIGH);
  }
}

