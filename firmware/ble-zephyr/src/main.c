#include <zephyr/kernel.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(ble_zephyr, LOG_LEVEL_INF);

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
    LOG_INF("nRF52 Zephyr BLE starting");

    const struct device *gpio = DEVICE_DT_GET(DT_NODELABEL(gpio0));
    if (gpio_pin_configure(gpio, LED_PIN, GPIO_OUTPUT_ACTIVE) != 0) {
        LOG_ERR("LED GPIO configuration failed");
    }

    if (bt_enable(NULL) != 0) {
        LOG_ERR("bt_enable failed");
        blink_error(gpio, 2);
    }

    if (bt_le_adv_start(BT_LE_ADV_NCONN, ad, ARRAY_SIZE(ad), NULL, 0) != 0) {
        LOG_ERR("bt_le_adv_start failed");
        blink_error(gpio, 3);
    }

    LOG_INF("BLE advertising started");

    while (1) {
        gpio_pin_toggle(gpio, LED_PIN);
        k_sleep(K_SECONDS(1));
    }
}
