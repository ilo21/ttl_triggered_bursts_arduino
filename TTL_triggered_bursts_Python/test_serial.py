import serial
import serial.tools.list_ports
from struct import pack
import time

BAUDRATE = 115200
COM = "COM5"

HOW_MANY_TIMES = 10

FREQ = 100
HIGH_WIDTH = 5
SEC = 2

RESET_CHAR = 'R'
QUIT_CHAR = 'Q'

arduino = serial.Serial(COM, baudrate= BAUDRATE, write_timeout = 1,timeout = 1)
ctr = 0
received = False

while ctr < HOW_MANY_TIMES and received == False:
    time.sleep(1)
    ctr+=1
    # send end of message
    message = str(FREQ)+","+str(HIGH_WIDTH)+","+str(SEC)
    arduino.flushInput()
    arduino.flushOutput()
    print(f"{ctr}. Sending {message}")
    arg = bytes(message, 'utf-8','ignore') + b'\n'
    try:
        arduino.write(arg)
        time.sleep(0.5)
        line = arduino.readline()
        # line = arduino.read(100)
        try:
            data=line[0:][:-2].decode("utf-8") 
            data_list = data.split(",")
            print(f"Received {data}")
            if len(data_list) == 3: # wait until arduino confimrs that it has set all 3 values
                if data_list[0] == str(FREQ) and data_list[1] == str(HIGH_WIDTH) and data_list[2] == str(SEC):
                    try:
                        next_ctr = 0
                        while next_ctr < HOW_MANY_TIMES:
                            next_ctr+=1
                            arduino.write(bytes(RESET_CHAR, 'utf-8','ignore')) # then send Reset character to confirm to arduino
                            time.sleep(0.3)
                            line = arduino.readline()
                            try:
                                data=line[0:][:-2].decode("utf-8")   
                                if data == RESET_CHAR:
                                    print(data)
                                    received = True
                                    break
                            except:
                                print("Could not decode")
                    except:
                        print("Write confirmation timeout")
        except:
            print("Could not decode")
    except:
        print("Write parameters timeout")
     
time.sleep(10)
ctr = 0
while ctr < HOW_MANY_TIMES:
    time.sleep(1)
    ctr +=1
    try:
        arduino.write(bytes(QUIT_CHAR, 'utf-8','ignore'))
    except:
        print("Could not send quit")
    time.sleep(0.5)
    line = arduino.readline()
    try:
        data=line[0:][:-2].decode("utf-8")   
        if data == QUIT_CHAR:
            print(data)
            break
    except:
        print("Could not decode")
arduino.close()
print("Done")



