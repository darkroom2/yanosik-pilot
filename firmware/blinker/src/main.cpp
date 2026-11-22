#include <Arduino.h>

#include "blinker_logic.h"

// nRF52DK Arduino pin indices: D2/D3 are P0.13/P0.14, D6-D8 are P0.17-P0.19.
constexpr uint8_t buttonNextColorPin = 2;
constexpr uint8_t buttonPausePin = 3;
constexpr uint8_t redLedPin = 6;
constexpr uint8_t greenLedPin = 7;
constexpr uint8_t blueLedPin = 8;

BlinkerLogic blinker;

void writeLedChannel(uint8_t pin, BlinkerColor channel)
{
    const bool channelOn = blinker.ledOn() && blinker.color() == channel;
    digitalWrite(pin, channelOn ? LOW : HIGH);
}

void setup()
{
    pinMode(buttonNextColorPin, INPUT_PULLUP);
    pinMode(buttonPausePin, INPUT_PULLUP);
    pinMode(redLedPin, OUTPUT);
    pinMode(greenLedPin, OUTPUT);
    pinMode(blueLedPin, OUTPUT);

    digitalWrite(redLedPin, HIGH);
    digitalWrite(greenLedPin, HIGH);
    digitalWrite(blueLedPin, HIGH);
}

void loop()
{
    blinker.update(
        millis(),
        digitalRead(buttonNextColorPin) == LOW,
        digitalRead(buttonPausePin) == LOW);

    writeLedChannel(redLedPin, BlinkerColor::red);
    writeLedChannel(greenLedPin, BlinkerColor::green);
    writeLedChannel(blueLedPin, BlinkerColor::blue);
}
