#include <zephyr/kernel.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/bluetooth/bluetooth.h>

#define LED_PIN 17

static const struct bt_data ad[] = {
    BT_DATA_BYTES(BT_DATA_FLAGS, BT_LE_AD_NO_BREDR),
    BT_DATA(BT_DATA_NAME_COMPLETE, CONFIG_BT_DEVICE_NAME, sizeof(CONFIG_BT_DEVICE_NAME) - 1),
};

static void blink_error(const struct device *gpio, int count)
{
    while (1) {
        for (int i = 0; i < count; i++) {
            gpio_pin_set(gpio, LED_PIN, 1);
            k_sleep(K_MSEC(150));
            gpio_pin_set(gpio, LED_PIN, 0);
            k_sleep(K_MSEC(150));
        }
        k_sleep(K_MSEC(1500));
    }
}

int main(void)
{
    const struct device *gpio = DEVICE_DT_GET(DT_NODELABEL(gpio0));
    gpio_pin_configure(gpio, LED_PIN, GPIO_OUTPUT_ACTIVE);

    if (bt_enable(NULL) != 0) {
        blink_error(gpio, 2);
    }

    if (bt_le_adv_start(BT_LE_ADV_NCONN, ad, ARRAY_SIZE(ad), NULL, 0) != 0) {
        blink_error(gpio, 3);
    }

    while (1) {
        gpio_pin_toggle(gpio, LED_PIN);
        k_sleep(K_SECONDS(1));
    }
}
