#include <Arduino.h>
#include <bluefruit.h>

void setup()
{
    Serial.begin(115200);

    if (!Bluefruit.begin())
    {
        Serial.println("BLE: blad inicjalizacji");
        return;
    }

    Bluefruit.setName("nRF52_Bluefruit");
    Bluefruit.Advertising.addFlags(BLE_GAP_ADV_FLAGS_LE_ONLY_GENERAL_DISC_MODE);
    Bluefruit.Advertising.addName();
    Bluefruit.Advertising.start(0);

    Serial.println("BLE dziala! Szukaj: nRF52_Bluefruit");
}

void loop()
{
}