#include <unity.h>

#include "blinker_logic.h"

void setUp(void) {}
void tearDown(void) {}

void test_button_cycles_through_colors_once_per_press()
{
    BlinkerLogic logic;
    logic.update(0, false, false);

    logic.update(1, true, false);
    logic.update(26, true, false);
    TEST_ASSERT_EQUAL(static_cast<int>(BlinkerColor::green), static_cast<int>(logic.color()));
    logic.update(100, true, false);
    TEST_ASSERT_EQUAL(static_cast<int>(BlinkerColor::green), static_cast<int>(logic.color()));

    logic.update(101, false, false);
    logic.update(126, false, false);
    logic.update(127, true, false);
    logic.update(152, true, false);
    TEST_ASSERT_EQUAL(static_cast<int>(BlinkerColor::blue), static_cast<int>(logic.color()));

    logic.update(153, false, false);
    logic.update(178, false, false);
    logic.update(179, true, false);
    logic.update(204, true, false);
    TEST_ASSERT_EQUAL(static_cast<int>(BlinkerColor::red), static_cast<int>(logic.color()));
}

void test_bouncing_button_does_not_repeat_color_change()
{
    BlinkerLogic logic;
    logic.update(0, false, false);
    logic.update(1, true, false);
    logic.update(6, false, false);
    logic.update(11, true, false);
    logic.update(36, true, false);
    TEST_ASSERT_EQUAL(static_cast<int>(BlinkerColor::green), static_cast<int>(logic.color()));

    logic.update(100, true, false);
    TEST_ASSERT_EQUAL(static_cast<int>(BlinkerColor::green), static_cast<int>(logic.color()));
}

void test_led_toggles_at_blink_interval()
{
    BlinkerLogic logic;
    logic.update(0, false, false);
    logic.update(499, false, false);
    TEST_ASSERT_FALSE(logic.ledOn());

    logic.update(500, false, false);
    TEST_ASSERT_TRUE(logic.ledOn());

    logic.update(1000, false, false);
    TEST_ASSERT_FALSE(logic.ledOn());
}

void test_pause_turns_led_off_and_resume_keeps_selected_color()
{
    BlinkerLogic logic;
    logic.update(0, false, false);
    logic.update(500, false, false);
    TEST_ASSERT_TRUE(logic.ledOn());

    logic.update(501, false, true);
    logic.update(526, false, true);
    TEST_ASSERT_TRUE(logic.paused());
    TEST_ASSERT_FALSE(logic.ledOn());

    logic.update(527, false, false);
    logic.update(552, false, false);
    logic.update(553, false, true);
    logic.update(578, false, true);
    TEST_ASSERT_FALSE(logic.paused());
    TEST_ASSERT_FALSE(logic.ledOn());
    TEST_ASSERT_EQUAL(static_cast<int>(BlinkerColor::red), static_cast<int>(logic.color()));
}

int main()
{
    UNITY_BEGIN();
    RUN_TEST(test_button_cycles_through_colors_once_per_press);
    RUN_TEST(test_bouncing_button_does_not_repeat_color_change);
    RUN_TEST(test_led_toggles_at_blink_interval);
    RUN_TEST(test_pause_turns_led_off_and_resume_keeps_selected_color);
    return UNITY_END();
}
