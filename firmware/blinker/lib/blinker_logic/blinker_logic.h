#ifndef BLINKER_LOGIC_H
#define BLINKER_LOGIC_H

#include <stdint.h>

enum class BlinkerColor : uint8_t
{
    red,
    green,
    blue
};

class BlinkerLogic
{
public:
    void update(uint32_t nowMs, bool nextColorPressed, bool pausePressed);

    BlinkerColor color() const { return color_; }
    bool paused() const { return paused_; }
    bool ledOn() const { return ledOn_; }

private:
    struct ButtonState
    {
        bool readingPressed = false;
        bool stablePressed = false;
        uint32_t lastChangeMs = 0;
    };

    static bool updateButton(ButtonState& button, bool pressed, uint32_t nowMs);
    void nextColor();

    static constexpr uint32_t blinkIntervalMs = 500;
    static constexpr uint32_t debounceIntervalMs = 25;

    BlinkerColor color_ = BlinkerColor::red;
    bool paused_ = false;
    bool ledOn_ = false;
    uint32_t lastBlinkMs_ = 0;
    ButtonState nextColorButton_;
    ButtonState pauseButton_;
};

#endif
