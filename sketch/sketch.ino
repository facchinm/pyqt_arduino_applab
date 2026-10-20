#include <Arduino_RouterBridge.h>

void set_led_state(bool state) {
  // Built-in LED on UNO Q is active-low
  digitalWrite(LED_BUILTIN, state ? LOW : HIGH);
}

int read_analog() {
  return analogRead(A0);
}

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);

  Bridge.begin();
  Bridge.provide("set_led_state", set_led_state);
  Bridge.provide("read_analog", read_analog);
}

void loop() {
}
