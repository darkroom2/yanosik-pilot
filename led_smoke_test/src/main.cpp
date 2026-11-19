#include <Arduino.h>

namespace {
constexpr uint8_t kRedLedPin = 17;
constexpr uint8_t kLed18Pin = 18;
constexpr uint8_t kLed19Pin = 19;

void pulseLed(uint8_t pin) {
  digitalWrite(pin, LOW);
  delay(1000);
  digitalWrite(pin, HIGH);
  delay(300);
}
} // namespace

void setup() {
  pinMode(kRedLedPin, OUTPUT);
  pinMode(kLed18Pin, OUTPUT);
  pinMode(kLed19Pin, OUTPUT);

  digitalWrite(kRedLedPin, HIGH);
  digitalWrite(kLed18Pin, HIGH);
  digitalWrite(kLed19Pin, HIGH);
  delay(500);
}

void loop() {
  pulseLed(kLed18Pin);
  pulseLed(kLed19Pin);
}
