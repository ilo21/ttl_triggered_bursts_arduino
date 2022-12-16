
#include <Wire.h>
// About serial communication:
// https://forum.arduino.cc/t/serial-input-basics-updated/382007
// Make Serial Monitor compatible for all TinyCircuits processors
#if defined(ARDUINO_ARCH_AVR)
  #define SerialMonitorInterface Serial
#elif defined(ARDUINO_ARCH_SAMD)
  #define SerialMonitorInterface SerialUSB
#endif


int TTL_PIN = A0; // input for TTL trigger
int BURST_OUT_PIN = A2; //pulse output for bursts

// values
int TARGET_FREQ_Hz = 1;
int HIGH_PULSE_WIDTH_MS = 0;
int HOW_LONG_SEC = 0;
int TTL_PIN_STATE = LOW; //defines TTL_PIN state state

int cycle_ms = int(1000/TARGET_FREQ_Hz);
int low_pulse_width_ms = cycle_ms - HIGH_PULSE_WIDTH_MS;
int num_of_cycles = HOW_LONG_SEC/cycle_ms;

int ctr = 0;
int readValue;
bool valuesReceived = false;
bool receivedNewChar = false;
bool armed = false;


const byte numChars = 32;
char receivedChars[numChars];   // an array to store the received data
char singleChar;
char resetChar = 'R';
char quitChar = 'Q';


void setup() {

  // start serial communication
  SerialMonitorInterface.begin(115200);
  Wire.begin();			


  // set pins to in and out
  pinMode(TTL_PIN, INPUT); //TTL trigger
  pinMode(BURST_OUT_PIN, OUTPUT); // bursts
} // end setup

void loop() {

  if (receivedNewChar == false) {
    // listen for comma separated values
    recvWithEndMarker();
    assignValues();
    // wait for confirmation
    recvOneChar();

  } // end if values were not received 
    //int current_time = millis();
    // run for x time
     //if (millis() < current_time + HOW_LONG_SEC*1000) { // Returns the number of milliseconds passed since the Arduino board began running the current program. Will go back to zero after approximately 50 days.
   // } // end running for x time
  if (armed == true) {
    TTL_PIN_STATE = digitalRead(TTL_PIN);
    if (TTL_PIN_STATE == HIGH) {
      for (int i=0; i < num_of_cycles; i++) {
        sendBurst();
      } // end running for x time
      receivedNewChar = false;
    }
  } // end if was received
  
} // end loop

void sendBurst() {
    digitalWrite(BURST_OUT_PIN, 1);       
    delay(HIGH_PULSE_WIDTH_MS);               // high pulse width delay 
    digitalWrite(BURST_OUT_PIN, 0);
    delay(low_pulse_width_ms);                // low pulse width delay  
} // end sendBurst

// function to read bytes until newline character
void recvWithEndMarker() {
    static byte ndx = 0;
    char endMarker = '\n';
    char rc;
    
    while (SerialMonitorInterface.available() > 0 && valuesReceived == false) {
        rc = SerialMonitorInterface.read();     
        if (rc != endMarker) {
            receivedChars[ndx] = rc;
            ndx++;
            if (ndx >= numChars) {
                ndx = numChars - 1;
            }
        }
        else {
            receivedChars[ndx] = '\0'; // terminate the string
            ndx = 0;
            valuesReceived = true;
        }
    }
    
} // end recvWithEndMarker

// function that reads 3 comma separated ints and assigns them to frequency and pulse duration, burst duration
void assignValues() { 
  if (valuesReceived == true) {
    int len = sizeof(receivedChars)/sizeof(char);
    String my_int_str = ""; // string to convert to int
    bool first = false;
    bool second = false;
    for (int i=0;i<len;i++) {
      if (receivedChars[i]==','){
        if (first == false) { // that will be the first received int
          first = true;
          TARGET_FREQ_Hz = my_int_str.toInt();
          my_int_str = ""; // clear for next int
        }
        else if (first == true && second == false) {
          second = true;
          HIGH_PULSE_WIDTH_MS = my_int_str.toInt();
          my_int_str = ""; // clear for next int
        }
      } // end if comma
      else {
        my_int_str.concat(receivedChars[i]);
      }
    } // end for
    // check last int
    HOW_LONG_SEC = my_int_str.toInt();
    cycle_ms = int(1000/TARGET_FREQ_Hz);
    low_pulse_width_ms = cycle_ms - HIGH_PULSE_WIDTH_MS;
    num_of_cycles = HOW_LONG_SEC*1000/cycle_ms;

    SerialMonitorInterface.print(TARGET_FREQ_Hz);
    SerialMonitorInterface.print(",");
    SerialMonitorInterface.print(HIGH_PULSE_WIDTH_MS);
    SerialMonitorInterface.print(",");
    SerialMonitorInterface.println(HOW_LONG_SEC);

    // clear character array
    for( int i = 0; i < sizeof(receivedChars);  ++i ) {
        receivedChars[i] = (char)0;
    }
   
  } // end if valuesReceived true
}

void recvOneChar() {
    if (SerialMonitorInterface.available() > -1) {
        singleChar = Serial.read();
        if (singleChar == resetChar) {
          SerialMonitorInterface.println(singleChar);
          armed = true;
          receivedNewChar = true;
          valuesReceived = false;
        }
        else if (singleChar == quitChar) {
          SerialMonitorInterface.println(singleChar);
          armed = false;
          valuesReceived = false;
          digitalWrite(BURST_OUT_PIN, 0);
          TARGET_FREQ_Hz = 1;
          HIGH_PULSE_WIDTH_MS = 0;
          HOW_LONG_SEC = 0;
        }
        else {
          valuesReceived = false;
        }
      // clear character array
        for( int i = 0; i < sizeof(receivedChars);  ++i ) {
              receivedChars[i] = (char)0;
        }
    }
} // end recvOneChar





