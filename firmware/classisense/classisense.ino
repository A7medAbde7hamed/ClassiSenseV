/* ClassiSense protocol v1 / Arduino Uno-Nano, replaces StandardFirmata.
 * Safety loop never waits for the PC or Serial. Active-low MQ-5 on D4.
 * Missing serial host keeps local gas alarm operating; illumination stays ON.
 * Digital DO alone cannot distinguish a disconnected MQ-5 from safe HIGH.
 */
#include <Arduino.h>
const byte LED_PIN=2, BUZZER_PIN=3, GAS_PIN=4, TEMP_PIN=A0;
const unsigned long WARMUP_MS=60000, LIGHT_DELAY_MS=10000, HOST_TIMEOUT_MS=15000;
unsigned long lastPerson=0,lastHost=0,lastSample=0,lastReport=0,lastTick=0;
unsigned long ledMillis=0;
bool lights=false, gas=false, buzzer=false, tempValid=false, hostSeen=false, warmedUp=false;
float temperature=0;
char command[40]; byte commandLength=0;
char telemetry[300]; unsigned int txLength=0,txPosition=0;

void setLights(bool on){lights=on;digitalWrite(LED_PIN,on?HIGH:LOW);}
void receiveCommand(){
  while(Serial.available()){
    char c=Serial.read();
    if(c=='\n'){
      command[commandLength]='\0';
      if(strncmp(command,"OCCUPANCY ",10)==0){
        char *end; long count=strtol(command+10,&end,10);
        if(end!=command+10 && *end=='\0' && count>=0 && count<=10000){
          lastHost=millis();hostSeen=true;
          if(count>0){lastPerson=lastHost;setLights(true);}
        }
      }
      commandLength=0;
    }else if(c!='\r'){
      if(commandLength<sizeof(command)-1) command[commandLength++]=c;
      else commandLength=0;
    }
  }
}
void setup(){
  pinMode(LED_PIN,OUTPUT);pinMode(BUZZER_PIN,OUTPUT);pinMode(GAS_PIN,INPUT_PULLUP);
  digitalWrite(BUZZER_PIN,LOW);setLights(true);Serial.begin(115200);
}
void loop(){
  unsigned long now=millis(), elapsed=now-lastTick;lastTick=now;
  if(lights)ledMillis+=elapsed;
  // Immediate local alarm, including during warmup. No serial command can mute it.
  if(now>=WARMUP_MS)warmedUp=true;
  gas=digitalRead(GAS_PIN)==LOW;
  buzzer=gas;digitalWrite(BUZZER_PIN,buzzer?HIGH:LOW);
  receiveCommand();
  if(!hostSeen || now-lastHost>HOST_TIMEOUT_MS) setLights(true);
  else if(now-lastPerson>=LIGHT_DELAY_MS) setLights(false);
  if(now-lastSample>=500){
    lastSample=now;int raw=analogRead(TEMP_PIN);
    temperature=raw*(5.0/1023.0)*100.0;
    tempValid=raw>1 && raw<1022 && temperature>=-20 && temperature<=120;
  }
  // Drain a bounded chunk; never block the safety loop behind USB telemetry.
  if(txPosition<txLength){
    int available=Serial.availableForWrite();
    if(available>0){
      unsigned int count=min((unsigned int)available,(unsigned int)(txLength-txPosition));
      Serial.write((const uint8_t*)telemetry+txPosition,count);txPosition+=count;
    }
  }
  if(now-lastReport>=500 && txPosition>=txLength){
    lastReport=now;char tempText[16];
    if(tempValid)dtostrf(temperature,1,1,tempText);else strcpy(tempText,"null");
    txLength=snprintf(telemetry,sizeof(telemetry),
      "{\"protocol\":1,\"gas_detected\":%s,\"gas_state\":\"%s\",\"temperature_c\":%s,\"temperature_state\":\"%s\",\"lights_on\":%s,\"buzzer_on\":%s,\"led_on_seconds\":%lu}\n",
      gas?"true":"false",gas?"danger":(!warmedUp?"stale":"healthy"),tempText,
      !tempValid?"disconnected":(temperature>=45?"danger":"healthy"),lights?"true":"false",buzzer?"true":"false",ledMillis/1000);
    if(txLength>=sizeof(telemetry))txLength=0;
    txPosition=0;
  }
}
