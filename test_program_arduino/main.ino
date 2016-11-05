#include <ADC.h>
#define HWSERIAL Serial1

int baud_rate = 115200;
int led_pin = 2;
ADC *adc = new ADC();

void setup(){
    pinMode(led_pin, OUTPUT);
    Serial.begin(baud_rate);
    Serial1.begin(baud_rate);
    adc->setReference(ADC_REF_EXT);
    adc->setConversionSpeed(ADC_VERY_LOW_SPEED);
    adc->setResolution(16, ADC_0);
}

void loop(){
    int diff = adc->analogReadDifferential(A10, A11, ADC_0);
    
    digitalWrite(led_pin, HIGH);
    delay(100);
    digitalWrite(led_pin, LOW);
    delay(100);
    if(Serial1.available())
    {
        char _next_char = Serial1.read();
        Serial.println(_next_char);
    }
    if(Serial.available())
    {
        char _next_char = Serial.read();
        Serial1.println(_next_char);
    }
}
