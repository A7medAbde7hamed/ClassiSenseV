#include "Arduino.h"
#include <cassert>
#include <iostream>
unsigned long fakeMillis=0;
int pins[20]={};
int adc=51;
FakeSerial Serial;
#include "../firmware/classisense/classisense.ino"
int main(){
 pins[4]=HIGH;setup();
 fakeMillis=1000;loop();assert(!buzzer);
 // Alarm responds without a video loop, serial host or writable TX buffer.
 Serial.space=0;pins[4]=LOW;fakeMillis=65000;loop();assert(buzzer && pins[3]==HIGH);
 pins[4]=HIGH;fakeMillis=65500;loop();assert(!buzzer);
 Serial.input="OCCUPANCY 3\n";fakeMillis=66000;loop();assert(lights);
 Serial.input="OCCUPANCY 0\n";fakeMillis=70000;loop();assert(lights);
 fakeMillis=77000;loop();assert(!lights);
 fakeMillis=90000;loop();assert(lights); // Host timeout: lighting fail-safe.
 adc=0;fakeMillis=91000;loop();assert(!tempValid);
 adc=51;fakeMillis=92000;loop();assert(tempValid && temperature>24 && temperature<26);
 Serial.space=64;for(int i=0;i<15;i++){fakeMillis+=501;loop();}
 assert(Serial.output.find("\"protocol\":1")!=std::string::npos);
 std::cout<<"Firmware simulation: independent gas alarm, no-host lighting, sensor rails, telemetry PASS\n";
}
