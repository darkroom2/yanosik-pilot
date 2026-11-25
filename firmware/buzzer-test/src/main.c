#include <zephyr/kernel.h>
#include <zephyr/drivers/pwm.h>

static const struct pwm_dt_spec pwm_a =
    PWM_DT_SPEC_GET(DT_ALIAS(buzzer_pwm_a));
static const struct pwm_dt_spec pwm_b =
    PWM_DT_SPEC_GET(DT_ALIAS(buzzer_pwm_b));

void buzzer_tone(uint32_t freq_hz, uint32_t duration_ms)
{
    uint32_t period_ns = 1000000000U / freq_hz;
    uint32_t pulse_ns = period_ns / 2U;

    pwm_set_dt(&pwm_a, period_ns, pulse_ns);
    pwm_set_dt(&pwm_b, period_ns, pulse_ns);

    k_msleep(duration_ms);

    pwm_set_dt(&pwm_a, period_ns, 0);
    pwm_set_dt(&pwm_b, period_ns, period_ns);
}

int main(void)
{
    if (!device_is_ready(pwm_a.dev) || !device_is_ready(pwm_b.dev)) {
        return 0;
    }

    while (1) {
        buzzer_tone(2000, 500);
        k_msleep(1000);
    }

    return 0;
}
