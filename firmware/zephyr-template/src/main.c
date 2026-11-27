#include <zephyr/kernel.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(template, LOG_LEVEL_INF);

static const struct gpio_dt_spec led =
    GPIO_DT_SPEC_GET(DT_ALIAS(led0), gpios);

int main(void)
{
    LOG_INF("Zephyr template starting");

    if (!gpio_is_ready_dt(&led)) {
        LOG_ERR("LED GPIO device is not ready");
        return 0;
    }

    if (gpio_pin_configure_dt(&led, GPIO_OUTPUT_ACTIVE) != 0) {
        LOG_ERR("LED GPIO configuration failed");
        return 0;
    }

    while (1) {
        gpio_pin_toggle_dt(&led);
        k_sleep(K_SECONDS(1));
    }
}
