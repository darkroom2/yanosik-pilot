#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/drivers/sensor.h>
#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(yanosik_main, LOG_LEVEL_INF);

static const struct gpio_dt_spec led_r =
	GPIO_DT_SPEC_GET(DT_ALIAS(led_red), gpios);
static const struct gpio_dt_spec led_g =
	GPIO_DT_SPEC_GET(DT_ALIAS(led_green), gpios);
static const struct gpio_dt_spec led_b =
	GPIO_DT_SPEC_GET(DT_ALIAS(led_blue), gpios);

static void set_rgb(bool r, bool g, bool b)
{
	gpio_pin_set_dt(&led_r, r ? 1 : 0);
	gpio_pin_set_dt(&led_g, g ? 1 : 0);
	gpio_pin_set_dt(&led_b, b ? 1 : 0);
}

int main(void)
{
	k_msleep(300);

	if (!gpio_is_ready_dt(&led_r) ||
	    !gpio_is_ready_dt(&led_g) ||
	    !gpio_is_ready_dt(&led_b)) {
		LOG_ERR("Blad inicjalizacji LED RGB");
		return 0;
	}

	gpio_pin_configure_dt(&led_r, GPIO_OUTPUT_INACTIVE);
	gpio_pin_configure_dt(&led_g, GPIO_OUTPUT_INACTIVE);
	gpio_pin_configure_dt(&led_b, GPIO_OUTPUT_INACTIVE);

	const struct device *accel = DEVICE_DT_GET(DT_ALIAS(accel0));
	if (!device_is_ready(accel)) {
		LOG_ERR("LIS2DH12TR (0x19) nie jest gotowy!");
		set_rgb(true, false, false);
		return 0;
	}

	struct sensor_value odr = {
		.val1 = 50,
		.val2 = 0,
	};
	if (sensor_attr_set(accel, SENSOR_CHAN_ACCEL_XYZ,
			    SENSOR_ATTR_SAMPLING_FREQUENCY, &odr) != 0) {
		LOG_WRN("Nie udalo sie ustawic ODR LIS2DH12 na 50 Hz");
	}

	LOG_INF("LIS2DH12TR zainicjalizowany na I2C0 "
		"(SCL=P0.12, SDA=P0.11, ADDR=0x19)");

	struct sensor_value val[3];

	while (1) {
		if (sensor_sample_fetch(accel) == 0) {
			if (sensor_channel_get(accel, SENSOR_CHAN_ACCEL_XYZ,
					       val) == 0) {
				double x = sensor_value_to_double(&val[0]);
				double y = sensor_value_to_double(&val[1]);
				double z = sensor_value_to_double(&val[2]);

				LOG_INF("X: %6.2f | Y: %6.2f | Z: %6.2f [m/s2]",
					x, y, z);

				double ax = x < 0 ? -x : x;
				double ay = y < 0 ? -y : y;
				double az = z < 0 ? -z : z;

				if (ax > ay && ax > az) {
					set_rgb(true, false, false);
				} else if (ay > ax && ay > az) {
					set_rgb(false, true, false);
				} else {
					set_rgb(false, false, true);
				}
			} else {
				LOG_WRN("Blad odczytu osi I2C z LIS2DH12");
			}
		} else {
			LOG_WRN("Blad odczytu probki I2C z LIS2DH12");
		}

		k_msleep(150);
	}

	return 0;
}
