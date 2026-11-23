#include <Arduino.h>
#include <BLEPeripheral.h>

// Tworzymy obiekt urządzenia BLE
BLEPeripheral blePeripheral = BLEPeripheral();

void setup() {
  // Nazwa widoczna na telefonie (max ok. 20 znaków)
  blePeripheral.setLocalName("nRF52_Test_BLE");
  blePeripheral.setDeviceName("nRF52_Test_BLE");

  // Uruchomienie stosu BLE i rozpoczęcie rozgłaszania (advertising)
  blePeripheral.begin();
}

void loop() {
  // Obsługa zdarzeń Bluetooth w tle
  blePeripheral.poll();
}
