#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/drivers/i2c.h>
#include <zephyr/logging/log.h>
#include <hal/nrf_gpio.h>
#include <hal/nrf_power.h>
#include <nrfx.h>

LOG_MODULE_REGISTER(accel_wake, LOG_LEVEL_INF);

#define LIS2DH_WHO_AM_I_REG      0x0F
#define LIS2DH_CTRL_REG1         0x20
#define LIS2DH_CTRL_REG2         0x21
#define LIS2DH_CTRL_REG3         0x22
#define LIS2DH_CTRL_REG4         0x23
#define LIS2DH_CTRL_REG5         0x24
#define LIS2DH_REFERENCE         0x26
#define LIS2DH_OUT_X_L           0x28
#define LIS2DH_INT1_CFG          0x30
#define LIS2DH_INT1_SRC          0x31
#define LIS2DH_INT1_THS          0x32
#define LIS2DH_INT1_DURATION     0x33
#define LIS2DH_FIFO_CTRL_REG     0x2E
#define LIS2DH_FIFO_SRC_REG      0x2F
#define LIS2DH_ACT_THS           0x3E
#define LIS2DH_ACT_DUR           0x3F
#define LIS2DH_WHO_AM_I_VALUE    0x33

#define LIS2DH_FIFO_BYPASS       0x00
#define LIS2DH_FIFO_STREAM       0xC0
#define LIS2DH_FIFO_DEPTH        32
#define RESETREAS_OFF            NRF_POWER_RESETREAS_OFF_MASK

#define INT1_PIN                 3  /* P0.03, aktywny stanem wysokim */
#define I2C_SDA_PIN              11 /* P0.11 */
#define I2C_SCL_PIN              12 /* P0.12 */
#define BUZZER_A_PIN             5  /* P0.05 */
#define BUZZER_B_PIN             6  /* P0.06 */
#define BUTTON_MINUS_PIN         13 /* P0.13 */
#define BUTTON_PLUS_PIN          14 /* P0.14 */
#define LED_RED_PIN              17 /* P0.17, wspolna anoda */
#define LED_GREEN_PIN            18 /* P0.18, wspolna anoda */
#define LED_BLUE_PIN             19 /* P0.19, wspolna anoda */

static const uint16_t lis2dh_address = 0x19;

static void leds_off(void)
{
	nrf_gpio_pin_set(LED_RED_PIN);
	nrf_gpio_pin_set(LED_GREEN_PIN);
	nrf_gpio_pin_set(LED_BLUE_PIN);
}

static void configure_gpio(void)
{
	nrf_gpio_cfg_output(LED_RED_PIN);
	nrf_gpio_cfg_output(LED_GREEN_PIN);
	nrf_gpio_cfg_output(LED_BLUE_PIN);
	leds_off();

	nrf_gpio_cfg_output(BUZZER_A_PIN);
	nrf_gpio_cfg_output(BUZZER_B_PIN);
	nrf_gpio_pin_clear(BUZZER_A_PIN);
	nrf_gpio_pin_clear(BUZZER_B_PIN);

	nrf_gpio_cfg(BUTTON_PLUS_PIN,
		     NRF_GPIO_PIN_DIR_INPUT,
		     NRF_GPIO_PIN_INPUT_DISCONNECT,
		     NRF_GPIO_PIN_NOPULL,
		     NRF_GPIO_PIN_S0S1,
		     NRF_GPIO_PIN_NOSENSE);
	nrf_gpio_cfg(BUTTON_MINUS_PIN,
		     NRF_GPIO_PIN_DIR_INPUT,
		     NRF_GPIO_PIN_INPUT_DISCONNECT,
		     NRF_GPIO_PIN_NOPULL,
		     NRF_GPIO_PIN_S0S1,
		     NRF_GPIO_PIN_NOSENSE);
}

static void blink_led(uint32_t pin, uint32_t duration_ms)
{
	nrf_gpio_pin_clear(pin);
	k_msleep(duration_ms);
	nrf_gpio_pin_set(pin);
}

static void red_error_blink(void)
{
	for (int i = 0; i < 3; i++) {
		blink_led(LED_RED_PIN, 100);
		k_msleep(100);
	}
}

static int lis2dh_write_reg(const struct device *i2c,
			    uint16_t address,
			    uint8_t reg,
			    uint8_t value)
{
	uint8_t payload[] = { reg, value };

	return i2c_write(i2c, payload, sizeof(payload), address);
}

static int lis2dh_read_reg(const struct device *i2c,
			   uint16_t address,
			   uint8_t reg,
			   uint8_t *value)
{
	return i2c_write_read(i2c, address, &reg, 1, value, 1);
}

static bool lis2dh_probe(const struct device *i2c)
{
	uint8_t who_am_i;

	if (lis2dh_read_reg(i2c, lis2dh_address,
			    LIS2DH_WHO_AM_I_REG, &who_am_i) == 0 &&
	    who_am_i == LIS2DH_WHO_AM_I_VALUE) {
		LOG_INF("LIS2DH WHO_AM_I=0x%02X pod adresem 0x19",
			who_am_i);
		return true;
	}

	return false;
}

static int lis2dh_configure_motion_wake(const struct device *i2c,
					uint16_t address)
{
	int rc;

	rc = lis2dh_write_reg(i2c, address, LIS2DH_CTRL_REG1, 0x57);
	if (rc != 0) return rc;

	rc = lis2dh_write_reg(i2c, address, LIS2DH_CTRL_REG2, 0x09);
	if (rc != 0) return rc;

	rc = lis2dh_write_reg(i2c, address, LIS2DH_CTRL_REG3, 0x40);
	if (rc != 0) return rc;

	rc = lis2dh_write_reg(i2c, address, LIS2DH_CTRL_REG4, 0x80);
	if (rc != 0) return rc;

	rc = lis2dh_write_reg(i2c, address, LIS2DH_CTRL_REG5, 0x40);
	if (rc != 0) return rc;

	rc = lis2dh_write_reg(i2c, address, LIS2DH_FIFO_CTRL_REG,
			      LIS2DH_FIFO_STREAM);
	if (rc != 0) return rc;

	rc = lis2dh_write_reg(i2c, address, LIS2DH_ACT_THS, 0x08);
	if (rc != 0) return rc;
	rc = lis2dh_write_reg(i2c, address, LIS2DH_ACT_DUR, 0x26);
	if (rc != 0) return rc;

	rc = lis2dh_write_reg(i2c, address, LIS2DH_INT1_THS, 0x08);
	if (rc != 0) return rc;
	rc = lis2dh_write_reg(i2c, address, LIS2DH_INT1_DURATION, 0x02);
	if (rc != 0) return rc;
	rc = lis2dh_write_reg(i2c, address, LIS2DH_INT1_CFG, 0x2A);
	if (rc != 0) return rc;

	uint8_t reference;
	rc = lis2dh_read_reg(i2c, address, LIS2DH_REFERENCE, &reference);
	if (rc != 0) return rc;
	LOG_INF("LIS2DH REFERENCE=0x%02X", reference);

	uint8_t src;
	rc = lis2dh_read_reg(i2c, address, LIS2DH_INT1_SRC, &src);
	if (rc != 0) return rc;
	LOG_INF("LIS2DH INT1_SRC=0x%02X", src);

	return lis2dh_read_reg(i2c, address, LIS2DH_INT1_SRC, &src);
}

static int lis2dh_read_fifo(const struct device *i2c, uint16_t address)
{
	uint8_t fifo_src;
	int rc = lis2dh_read_reg(i2c, address,
				 LIS2DH_FIFO_SRC_REG, &fifo_src);
	if (rc != 0) {
		return rc;
	}

	uint32_t fss = fifo_src & 0x1F;
	if (fss > LIS2DH_FIFO_DEPTH) {
		fss = LIS2DH_FIFO_DEPTH;
	}

	LOG_INF("LIS2DH FIFO FSS=%u FIFO_SRC=0x%02X", fss, fifo_src);
	if (fss == 0) {
		return 0;
	}

	uint8_t burst[LIS2DH_FIFO_DEPTH * 6];
	uint8_t burst_reg = LIS2DH_OUT_X_L | 0x80;
	rc = i2c_write_read(i2c, address, &burst_reg, 1,
			     burst, fss * 6);
	if (rc != 0) {
		LOG_ERR("FIFO burst read failed: %d", rc);
		return rc;
	}

	for (uint32_t i = 0; i < fss; i++) {
		uint8_t *sample = &burst[i * 6];
		int16_t x_raw = (int16_t)((uint16_t)sample[0] |
					   ((uint16_t)sample[1] << 8));
		int16_t y_raw = (int16_t)((uint16_t)sample[2] |
					   ((uint16_t)sample[3] << 8));
		int16_t z_raw = (int16_t)((uint16_t)sample[4] |
					   ((uint16_t)sample[5] << 8));

		int16_t x = x_raw >> 6;
		int16_t y = y_raw >> 6;
		int16_t z = z_raw >> 6;

		if (i < 5) {
			LOG_INF("FIFO[%u] X=%d Y=%d Z=%d", i, x, y, z);
		}
	}

	return 0;
}

static int lis2dh_rearm_fifo(const struct device *i2c, uint16_t address)
{
	int rc = lis2dh_write_reg(i2c, address, LIS2DH_FIFO_CTRL_REG,
				  LIS2DH_FIFO_BYPASS);
	if (rc != 0) return rc;

	return lis2dh_write_reg(i2c, address, LIS2DH_FIFO_CTRL_REG,
				LIS2DH_FIFO_STREAM);
}

static void wait_for_int1_low(void)
{
	for (int i = 0; i < 500 &&
	     nrf_gpio_pin_read(INT1_PIN) != 0; i++) {
		k_msleep(50);
	}
}

static void disable_i2c_and_inputs(void)
{
	NRF_TWIM0->TASKS_STOP = 1;
	k_busy_wait(20);
	NRF_TWIM0->ENABLE = 0;

	nrf_gpio_cfg(I2C_SDA_PIN,
		     NRF_GPIO_PIN_DIR_INPUT,
		     NRF_GPIO_PIN_INPUT_DISCONNECT,
		     NRF_GPIO_PIN_PULLUP,
		     NRF_GPIO_PIN_S0S1,
		     NRF_GPIO_PIN_NOSENSE);
	nrf_gpio_cfg(I2C_SCL_PIN,
		     NRF_GPIO_PIN_DIR_INPUT,
		     NRF_GPIO_PIN_INPUT_DISCONNECT,
		     NRF_GPIO_PIN_PULLUP,
		     NRF_GPIO_PIN_S0S1,
		     NRF_GPIO_PIN_NOSENSE);
}

static void enter_system_off(void)
{
	disable_i2c_and_inputs();
	nrf_gpio_cfg_sense_input(INT1_PIN,
				 NRF_GPIO_PIN_NOPULL,
				 NRF_GPIO_PIN_SENSE_HIGH);
	NRF_POWER->SYSTEMOFF = 1;

	__DSB();
	while (1) {
		__WFE();
	}
}

int main(void)
{
	uint32_t resetreas = NRF_POWER->RESETREAS;
	NRF_POWER->RESETREAS = resetreas;

	configure_gpio();

	/* Wlacz wewnetrzna przetwornice DC/DC nRF52832. */
	NRF_POWER->DCDCEN = 1;

	const bool cold_start =
		(resetreas & RESETREAS_OFF) == 0;
	const bool system_off_wake =
		(resetreas & RESETREAS_OFF) != 0;

	const struct device *i2c = DEVICE_DT_GET(DT_NODELABEL(i2c0));
	if (!device_is_ready(i2c)) {
		LOG_ERR("I2C0 (P0.12/P0.11) nie jest gotowe");
		red_error_blink();
		enter_system_off();
	}

	if (!lis2dh_probe(i2c)) {
		LOG_ERR("LIS2DH nie odpowiada pod adresem 0x19");
		red_error_blink();
		enter_system_off();
	}

	if (cold_start || !system_off_wake) {
		LOG_INF("START: zimny start/reset (RESETREAS=0x%08X)",
			resetreas);
		if (lis2dh_configure_motion_wake(i2c,
						 lis2dh_address) != 0) {
			LOG_ERR("Blad konfiguracji rejestrow LIS2DH");
			red_error_blink();
			enter_system_off();
		}

		blink_led(LED_GREEN_PIN, 10);
		enter_system_off();
	}

	LOG_INF("START: wybudzenie RESETREAS_OFF (RESETREAS=0x%08X)",
		resetreas);
	blink_led(LED_BLUE_PIN, 5);

	if (lis2dh_read_fifo(i2c, lis2dh_address) != 0) {
		LOG_ERR("Nie udalo sie odczytac FIFO LIS2DH");
	}
	if (lis2dh_rearm_fifo(i2c, lis2dh_address) != 0) {
		LOG_ERR("Nie udalo sie ponownie uzbroic FIFO");
	}

	uint8_t src;
	lis2dh_read_reg(i2c, lis2dh_address, LIS2DH_INT1_SRC, &src);
	wait_for_int1_low();
	enter_system_off();

	return 0;
}
