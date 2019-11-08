#define POT_PIN A0
void setup() {
  Serial.begin(9600);
}

void loop() {
  int pot_value = analogRead(POT_PIN);
  Serial.println(pot_value);
  delay(300);
}
