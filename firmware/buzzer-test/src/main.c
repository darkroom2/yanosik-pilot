#include <zephyr/kernel.h>
#include <zephyr/sys/printk.h>
#include <hal/nrf_gpio.h>
#include <stdbool.h>

#define BUZZER_A_PIN          5
#define BUZZER_B_PIN          6
#define BUTTON_PLUS_PIN       14
#define BUTTON_MINUS_PIN      15
#define LED_RED_PIN           17
#define LED_GREEN_PIN         18
#define LED_BLUE_PIN          19

#define FREQ_MIN_HZ           3000U
#define FREQ_MAX_HZ           5000U
#define FREQ_START_HZ         4000U
#define PWM_CLOCK_HZ          16000000UL
#define DEBOUNCE_MS           20U
#define DEBOUNCE_STABLE_READS 3U

/* 4-elementowy bufor w pamięci RAM dla EasyDMA w trybie LOAD_Individual */
static uint16_t pwm_seq[4];
static uint32_t current_frequency = FREQ_START_HZ;
static bool pwm_running = false;

static void configure_gpio(void)
{
	nrf_gpio_cfg_output(LED_RED_PIN);
	nrf_gpio_cfg_output(LED_GREEN_PIN);
	nrf_gpio_cfg_output(LED_BLUE_PIN);
	nrf_gpio_cfg_input(BUTTON_PLUS_PIN, NRF_GPIO_PIN_PULLUP);
	nrf_gpio_cfg_input(BUTTON_MINUS_PIN, NRF_GPIO_PIN_PULLUP);

	/* Wyłączenie wszystkich kanałów RGB (wspólna anoda) */
	nrf_gpio_pin_set(LED_RED_PIN);
	nrf_gpio_pin_set(LED_GREEN_PIN);
	nrf_gpio_pin_set(LED_BLUE_PIN);

	/* Piny buzzera w trybie wysokiej wydajności prądowej H0H1 */
	nrf_gpio_cfg(BUZZER_A_PIN,
		     NRF_GPIO_PIN_DIR_OUTPUT,
		     NRF_GPIO_PIN_INPUT_DISCONNECT,
		     NRF_GPIO_PIN_NOPULL,
		     NRF_GPIO_PIN_H0H1,
		     NRF_GPIO_PIN_NOSENSE);
	nrf_gpio_cfg(BUZZER_B_PIN,
		     NRF_GPIO_PIN_DIR_OUTPUT,
		     NRF_GPIO_PIN_INPUT_DISCONNECT,
		     NRF_GPIO_PIN_NOPULL,
		     NRF_GPIO_PIN_H0H1,
		     NRF_GPIO_PIN_NOSENSE);
}

static void pwm_hw_init(void)
{
	NRF_PWM0->ENABLE = 0;

	NRF_PWM0->PSEL.OUT[0] = (BUZZER_A_PIN << PWM_PSEL_OUT_PIN_Pos) |
				(PWM_PSEL_OUT_CONNECT_Connected << PWM_PSEL_OUT_CONNECT_Pos);
	NRF_PWM0->PSEL.OUT[1] = (BUZZER_B_PIN << PWM_PSEL_OUT_PIN_Pos) |
				(PWM_PSEL_OUT_CONNECT_Connected << PWM_PSEL_OUT_CONNECT_Pos);
	NRF_PWM0->PSEL.OUT[2] = PWM_PSEL_OUT_CONNECT_Disconnected << PWM_PSEL_OUT_CONNECT_Pos;
	NRF_PWM0->PSEL.OUT[3] = PWM_PSEL_OUT_CONNECT_Disconnected << PWM_PSEL_OUT_CONNECT_Pos;

	NRF_PWM0->MODE = PWM_MODE_UPDOWN_Up << PWM_MODE_UPDOWN_Pos;
	NRF_PWM0->PRESCALER = PWM_PRESCALER_PRESCALER_DIV_1 << PWM_PRESCALER_PRESCALER_Pos;
	NRF_PWM0->DECODER = (PWM_DECODER_LOAD_Individual << PWM_DECODER_LOAD_Pos) |
			    (PWM_DECODER_MODE_RefreshCount << PWM_DECODER_MODE_Pos);
	NRF_PWM0->LOOP = 0;

	NRF_PWM0->ENABLE = 1;
}

static void all_leds_off(void)
{
	nrf_gpio_pin_set(LED_RED_PIN);
	nrf_gpio_pin_set(LED_GREEN_PIN);
	nrf_gpio_pin_set(LED_BLUE_PIN);
}

static void set_led_for_frequency(uint32_t frequency)
{
	all_leds_off();

	if (frequency < 3900U) {
		nrf_gpio_pin_clear(LED_BLUE_PIN);
	} else if (frequency <= 4100U) {
		nrf_gpio_pin_clear(LED_GREEN_PIN);
	} else {
		nrf_gpio_pin_clear(LED_RED_PIN);
	}
}

static void flash_white_limit(void)
{
	nrf_gpio_pin_clear(LED_RED_PIN);
	nrf_gpio_pin_clear(LED_GREEN_PIN);
	nrf_gpio_pin_clear(LED_BLUE_PIN);
	k_msleep(100);
	set_led_for_frequency(current_frequency);
}

static void update_buzzer(uint32_t frequency)
{
	uint32_t countertop = PWM_CLOCK_HZ / frequency;
	uint32_t half = countertop / 2U;

	/* Zatrzymujemy tylko wtedy, gdy PWM już wcześniej pracował */
	if (pwm_running) {
		NRF_PWM0->EVENTS_STOPPED = 0;
		NRF_PWM0->TASKS_STOP = 1;
		while (NRF_PWM0->EVENTS_STOPPED == 0) {
		}
		NRF_PWM0->EVENTS_STOPPED = 0;
	}

	pwm_seq[0] = (uint16_t)half;
	pwm_seq[1] = (uint16_t)(half | 0x8000U); /* Przeciwfaza 180 stopni */
	pwm_seq[2] = 0;
	pwm_seq[3] = 0;

	NRF_PWM0->COUNTERTOP = countertop;
	NRF_PWM0->SEQ[0].PTR = (uint32_t)pwm_seq;
	NRF_PWM0->SEQ[0].CNT = 4;
	NRF_PWM0->SEQ[0].REFRESH = 0;
	NRF_PWM0->SEQ[0].ENDDELAY = 0;

	NRF_PWM0->TASKS_SEQSTART[0] = 1;
	pwm_running = true;

	set_led_for_frequency(frequency);
	printk("Buzzer frequency: %u Hz\n", frequency);
}

static void change_frequency(int32_t delta_hz)
{
	int32_t new_frequency = (int32_t)current_frequency + delta_hz;

	if (new_frequency < (int32_t)FREQ_MIN_HZ) {
		new_frequency = (int32_t)FREQ_MIN_HZ;
	} else if (new_frequency > (int32_t)FREQ_MAX_HZ) {
		new_frequency = (int32_t)FREQ_MAX_HZ;
	}

	if ((uint32_t)new_frequency == current_frequency) {
		return;
	}

	current_frequency = (uint32_t)new_frequency;
	update_buzzer(current_frequency);

	if (current_frequency == FREQ_MIN_HZ ||
	    current_frequency == FREQ_MAX_HZ) {
		flash_white_limit();
	}
}

int main(void)
{
	configure_gpio();

	/* Natychmiastowa sygnalizacja startu aplikacji */
	set_led_for_frequency(current_frequency);
	printk("System uruchomiony, start PWM...\n");

	pwm_hw_init();
	update_buzzer(current_frequency);

	uint32_t plus_low_reads = 0;
	uint32_t minus_low_reads = 0;
	bool plus_pressed = false;
	bool minus_pressed = false;

	while (1) {
		uint32_t plus_now = nrf_gpio_pin_read(BUTTON_PLUS_PIN);
		uint32_t minus_now = nrf_gpio_pin_read(BUTTON_MINUS_PIN);

		if (plus_now == 0) {
			if (plus_low_reads < DEBOUNCE_STABLE_READS) {
				plus_low_reads++;
			} else if (!plus_pressed) {
				plus_pressed = true;
				change_frequency(50);
			}
		} else {
			plus_low_reads = 0;
			plus_pressed = false;
		}

		if (minus_now == 0) {
			if (minus_low_reads < DEBOUNCE_STABLE_READS) {
				minus_low_reads++;
			} else if (!minus_pressed) {
				minus_pressed = true;
				change_frequency(-50);
			}
		} else {
			minus_low_reads = 0;
			minus_pressed = false;
		}

		k_msleep(DEBOUNCE_MS);
	}
}
