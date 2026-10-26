#pragma once
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
using byte=uint8_t;
using std::min;
#define A0 14
#define HIGH 1
#define LOW 0
#define OUTPUT 1
#define INPUT_PULLUP 2
extern unsigned long fakeMillis;
extern int pins[20];
extern int adc;
inline unsigned long millis(){return fakeMillis;}
inline void pinMode(int,int){}
inline void digitalWrite(int p,int v){pins[p]=v;}
inline int digitalRead(int p){return pins[p];}
inline int analogRead(int){return adc;}
inline char* dtostrf(double val,signed char width,unsigned char precision,char* out){sprintf(out,"%*.*f",width,precision,val);return out;}
struct FakeSerial {
 std::string input,output;
 int space=64;
 void begin(int){}
 int available(){return input.size();}
 char read(){char c=input[0];input.erase(0,1);return c;}
 int availableForWrite(){return space;}
 void write(const uint8_t* p,unsigned int n){output.append((const char*)p,n);}
};
extern FakeSerial Serial;
