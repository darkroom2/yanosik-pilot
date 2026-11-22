#include "blinker_logic.h"

bool BlinkerLogic::updateButton(ButtonState& button, bool pressed, uint32_t nowMs)
{
    if (pressed != button.readingPressed)
    {
        button.readingPressed = pressed;
        button.lastChangeMs = nowMs;
    }

    if (button.readingPressed != button.stablePressed &&
        static_cast<uint32_t>(nowMs - button.lastChangeMs) >= debounceIntervalMs)
    {
        button.stablePressed = button.readingPressed;
        return button.stablePressed;
    }

    return false;
}

void BlinkerLogic::nextColor()
{
    switch (color_)
    {
    case BlinkerColor::red:
        color_ = BlinkerColor::green;
        break;
    case BlinkerColor::green:
        color_ = BlinkerColor::blue;
        break;
    case BlinkerColor::blue:
        color_ = BlinkerColor::red;
        break;
    }
}

void BlinkerLogic::update(uint32_t nowMs, bool nextColorPressed, bool pausePressed)
{
    if (updateButton(nextColorButton_, nextColorPressed, nowMs))
    {
        nextColor();
    }

    if (updateButton(pauseButton_, pausePressed, nowMs))
    {
        paused_ = !paused_;
        ledOn_ = false;
        lastBlinkMs_ = nowMs;
    }

    if (!paused_ &&
        static_cast<uint32_t>(nowMs - lastBlinkMs_) >= blinkIntervalMs)
    {
        ledOn_ = !ledOn_;
        lastBlinkMs_ = nowMs;
    }
}
