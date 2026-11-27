#include <stdbool.h>
#include <stdint.h>

#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(accelerometer_app, LOG_LEVEL_INF);

static const uint8_t pins[] = { 3, 4, 7, 8, 12, 13 };

static const struct device *const gpio0 =
	DEVICE_DT_GET(DT_NODELABEL(gpio0));
static const struct gpio_dt_spec led_red =
	GPIO_DT_SPEC_GET(DT_ALIAS(led_red), gpios);
static const struct gpio_dt_spec led_green =
	GPIO_DT_SPEC_GET(DT_ALIAS(led_green), gpios);

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

static bool contains_pin(uint8_t pin, uint8_t a, uint8_t b,
			 uint8_t c, uint8_t d)
{
	return pin == a || pin == b || pin == c || pin == d;
}

static void set_all_input(void)
{
	for (size_t i = 0; i < 6; i++) {
		gpio_pin_configure(gpio0, pins[i], GPIO_INPUT);
	}
}

static void spi_output(uint8_t pin)
{
	gpio_pin_configure(gpio0, pin, GPIO_OUTPUT_INACTIVE);
}

static uint8_t spi_transfer(uint8_t sck, uint8_t mosi, uint8_t miso,
			    uint8_t cs, uint8_t command)
{
	uint8_t received = 0;

	gpio_pin_set(gpio0, cs, 0);
	k_busy_wait(2);

	for (int bit = 7; bit >= 0; bit--) {
		gpio_pin_set(gpio0, sck, 0);
		gpio_pin_set(gpio0, mosi, (command >> bit) & 1U);
		k_busy_wait(2);
		gpio_pin_set(gpio0, sck, 1);
		k_busy_wait(2);
	}

	for (int bit = 7; bit >= 0; bit--) {
		gpio_pin_set(gpio0, sck, 0);
		k_busy_wait(2);
		gpio_pin_set(gpio0, sck, 1);
		k_busy_wait(2);
		if (gpio_pin_get(gpio0, miso) > 0) {
			received |= (uint8_t)(1U << bit);
		}
	}

	gpio_pin_set(gpio0, cs, 1);
	k_busy_wait(2);
	return received;
}

static void i2c_start(uint8_t scl, uint8_t sda)
{
	gpio_pin_set(gpio0, sda, 1);
	gpio_pin_set(gpio0, scl, 1);
	k_busy_wait(2);
	gpio_pin_set(gpio0, sda, 0);
	k_busy_wait(2);
	gpio_pin_set(gpio0, scl, 0);
	k_busy_wait(2);
}

static void i2c_stop(uint8_t scl, uint8_t sda)
{
	gpio_pin_set(gpio0, sda, 0);
	gpio_pin_set(gpio0, scl, 1);
	k_busy_wait(2);
	gpio_pin_set(gpio0, sda, 1);
	k_busy_wait(2);
}

static bool i2c_write_byte(uint8_t scl, uint8_t sda, uint8_t byte)
{
	for (int bit = 7; bit >= 0; bit--) {
		gpio_pin_set(gpio0, sda, (byte >> bit) & 1U);
		k_busy_wait(2);
		gpio_pin_set(gpio0, scl, 1);
		k_busy_wait(2);
		gpio_pin_set(gpio0, scl, 0);
		k_busy_wait(2);
	}

	gpio_pin_configure(gpio0, sda, GPIO_INPUT | GPIO_PULL_UP);
	for (int attempt = 0; attempt < 20; attempt++) {
		gpio_pin_set(gpio0, scl, 1);
		k_busy_wait(2);
		if (gpio_pin_get(gpio0, sda) == 0) {
			gpio_pin_set(gpio0, scl, 0);
			gpio_pin_configure(gpio0, sda,
					   GPIO_OUTPUT | GPIO_PULL_UP);
			return true;
		}
		gpio_pin_set(gpio0, scl, 0);
		k_busy_wait(2);
	}
	gpio_pin_configure(gpio0, sda, GPIO_OUTPUT | GPIO_PULL_UP);
	return false;
}

static uint8_t i2c_read_byte(uint8_t scl, uint8_t sda)
{
	uint8_t value = 0;

	gpio_pin_configure(gpio0, sda, GPIO_INPUT | GPIO_PULL_UP);
	for (int bit = 7; bit >= 0; bit--) {
		gpio_pin_set(gpio0, scl, 1);
		k_busy_wait(2);
		if (gpio_pin_get(gpio0, sda) > 0) {
			value |= (uint8_t)(1U << bit);
		}
		gpio_pin_set(gpio0, scl, 0);
		k_busy_wait(2);
	}

	gpio_pin_configure(gpio0, sda, GPIO_OUTPUT | GPIO_PULL_UP);
	gpio_pin_set(gpio0, sda, 1);
	gpio_pin_set(gpio0, scl, 1);
	k_busy_wait(2);
	gpio_pin_set(gpio0, scl, 0);
	k_busy_wait(2);
	gpio_pin_set(gpio0, sda, 1);
	return value;
}

static bool i2c_read_who(uint8_t scl, uint8_t sda, uint8_t addr,
			 uint8_t *who)
{
	i2c_start(scl, sda);
	if (!i2c_write_byte(scl, sda, (uint8_t)(addr << 1))) {
		i2c_stop(scl, sda);
		return false;
	}
	if (!i2c_write_byte(scl, sda, 0x0F)) {
		i2c_stop(scl, sda);
		return false;
	}

	i2c_start(scl, sda);
	if (!i2c_write_byte(scl, sda, (uint8_t)((addr << 1) | 1U))) {
		i2c_stop(scl, sda);
		return false;
	}
	*who = i2c_read_byte(scl, sda);
	i2c_stop(scl, sda);
	return true;
}

int main(void)
{
	int hits = 0;

	if (!device_is_ready(gpio0) ||
	    !gpio_is_ready_dt(&led_red) ||
	    !gpio_is_ready_dt(&led_green)) {
		return 0;
	}

	configure_led(&led_red);
	configure_led(&led_green);
	set_led(&led_red, false);
	set_led(&led_green, false);
	set_all_input();

	LOG_INF("Start skanu LIS2DH12TR");

	/* Faza 1: 6 * 5 * 4 * 3 = 360 permutacji. */
	for (size_t si = 0; si < 6; si++) {
		for (size_t mi = 0; mi < 6; mi++) {
			if (mi == si) continue;
			for (size_t ii = 0; ii < 6; ii++) {
				if (ii == si || ii == mi) continue;
				for (size_t ci = 0; ci < 6; ci++) {
					if (ci == si || ci == mi || ci == ii) continue;

					set_all_input();
					uint8_t sck = pins[si];
					uint8_t mosi = pins[mi];
					uint8_t miso = pins[ii];
					uint8_t cs = pins[ci];

					for (size_t pi = 0; pi < 6; pi++) {
						if (!contains_pin(pins[pi],
								  sck, mosi, miso, cs)) {
							gpio_pin_configure(
								gpio0, pins[pi],
								GPIO_INPUT);
						}
					}

					gpio_pin_configure(gpio0, miso,
							    GPIO_INPUT | GPIO_PULL_DOWN);
					spi_output(sck);
					spi_output(mosi);
					spi_output(cs);
					gpio_pin_set(gpio0, sck, 1);
					gpio_pin_set(gpio0, mosi, 0);
					gpio_pin_set(gpio0, cs, 1);

					uint8_t who = spi_transfer(
						sck, mosi, miso, cs, 0x8F);
					if (who == 0x33) {
						gpio_pin_set(gpio0, cs, 0);
						k_busy_wait(2);
						/* Zapis 0x57 do CTRL_REG1. */
						uint8_t write[] = { 0x20, 0x57 };
						for (size_t n = 0; n < 2; n++) {
							for (int bit = 7; bit >= 0; bit--) {
								gpio_pin_set(gpio0, sck, 0);
								gpio_pin_set(gpio0, mosi,
									     (write[n] >> bit) & 1U);
								k_busy_wait(2);
								gpio_pin_set(gpio0, sck, 1);
								k_busy_wait(2);
							}
						}
						gpio_pin_set(gpio0, cs, 1);

						uint8_t ctrl1 = spi_transfer(
							sck, mosi, miso, cs, 0xA0);
						hits++;
						LOG_INF("SPI HIT! SCK=P0.%02d, MOSI=P0.%02d, MISO=P0.%02d, CS=P0.%02d -> WHO=0x%02X, CTRL1=0x%02X",
							sck, mosi, miso, cs, who, ctrl1);
						k_msleep(10);
					}

					set_all_input();
				}
			}
		}
	}

	/* Faza 2: 6 * 5 = 30 uporządkowanych par. */
	for (size_t si = 0; si < 6; si++) {
		for (size_t di = 0; di < 6; di++) {
			if (si == di) continue;

			uint8_t scl = pins[si];
			uint8_t sda = pins[di];
			if (sda == 0 || scl == 0) continue;

			set_all_input();
			for (size_t pi = 0; pi < 6; pi++) {
				uint8_t pin = pins[pi];
				if (pin == scl || pin == sda) continue;
				gpio_pin_configure(gpio0, pin,
						   GPIO_INPUT | GPIO_PULL_UP);
			}
			gpio_pin_configure(gpio0, scl,
					   GPIO_OUTPUT | GPIO_PULL_UP);
			gpio_pin_configure(gpio0, sda,
					   GPIO_OUTPUT | GPIO_PULL_UP);
			gpio_pin_set(gpio0, scl, 1);
			gpio_pin_set(gpio0, sda, 1);

			for (uint8_t addr = 0x18; addr <= 0x19; addr++) {
				uint8_t who = 0;
				if (i2c_read_who(scl, sda, addr, &who) &&
				    who == 0x33) {
					hits++;
					LOG_INF("I2C HIT! SCL=P0.%02d, SDA=P0.%02d, ADDR=0x%02X -> WHO=0x33",
						scl, sda, addr);
				}
			}

			set_all_input();
		}
	}

	LOG_INF("Koniec skanu. Trafienia: %d", hits);
	if (hits > 0) {
		set_led(&led_green, true);
	} else {
		while (1) {
			set_led(&led_red, true);
			k_msleep(100);
			set_led(&led_red, false);
			k_msleep(100);
		}
	}

	while (1) {
		k_sleep(K_SECONDS(1));
	}
}
