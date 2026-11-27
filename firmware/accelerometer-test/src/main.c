#include <math.h>
#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/drivers/sensor.h>
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(accelerometer_app, LOG_LEVEL_INF);

static const struct gpio_dt_spec led_red =
	GPIO_DT_SPEC_GET(DT_ALIAS(led_red), gpios);
static const struct gpio_dt_spec led_green =
	GPIO_DT_SPEC_GET(DT_ALIAS(led_green), gpios);
static const struct gpio_dt_spec led_blue =
	GPIO_DT_SPEC_GET(DT_ALIAS(led_blue), gpios);

static const struct device *const accel =
	DEVICE_DT_GET(DT_ALIAS(accel0));

static void set_led(const struct gpio_dt_spec *led, bool on)
{
	gpio_pin_set_dt(led, on ? 1 : 0);
}

static int configure_led(const struct gpio_dt_spec *led)
{
	if (!gpio_is_ready_dt(led)) {
		return -1;
	}
	return gpio_pin_configure_dt(led, GPIO_OUTPUT_INACTIVE);
}

static void fast_red_blink(void)
{
	while (1) {
		set_led(&led_red, true);
		k_sleep(K_MSEC(100));
		set_led(&led_red, false);
		k_sleep(K_MSEC(100));
	}
}

int main(void)
{
	struct sensor_value xyz[3];
	struct sensor_value odr;
	int rc;
	int log_count = 0;

	LOG_INF("Docelowa aplikacja LIS2DH12TR startuje");

	if (!device_is_ready(accel)) {
		LOG_ERR("Akcelerometr LIS2DH12 nie jest gotowy");
		configure_led(&led_red);
		fast_red_blink();
	}

	if (configure_led(&led_red) != 0 ||
	    configure_led(&led_green) != 0 ||
	    configure_led(&led_blue) != 0) {
		LOG_ERR("Błąd inicjalizacji LED RGB");
		fast_red_blink();
	}

	set_led(&led_red, false);
	set_led(&led_green, false);
	set_led(&led_blue, false);

	sensor_value_from_double(&odr, 50.0);
	rc = sensor_attr_set(accel, SENSOR_CHAN_ACCEL_XYZ,
			     SENSOR_ATTR_SAMPLING_FREQUENCY, &odr);
	if (rc != 0) {
		LOG_ERR("Nie ustawiono ODR 50 Hz (%d)", rc);
		fast_red_blink();
	}

	while (1) {
		rc = sensor_sample_fetch(accel);
		if (rc == 0) {
			rc = sensor_channel_get(accel,
						SENSOR_CHAN_ACCEL_XYZ, xyz);
		}

		if (rc != 0) {
			LOG_ERR("Blad odczytu akcelerometru (%d)", rc);
			set_led(&led_red, true);
			set_led(&led_green, false);
			set_led(&led_blue, false);
		} else {
			double x = sensor_value_to_double(&xyz[0]);
			double y = sensor_value_to_double(&xyz[1]);
			double z = sensor_value_to_double(&xyz[2]);

			set_led(&led_red, fabs(x) > 5.0);
			set_led(&led_green, fabs(y) > 5.0);
			set_led(&led_blue, fabs(z) > 5.0);

			log_count++;
			if (log_count >= 5) {
				LOG_INF("Accel [m/s2]: X=%.2f Y=%.2f Z=%.2f",
					x, y, z);
				log_count = 0;
			}
		}

		k_sleep(K_MSEC(100));
	}
}
