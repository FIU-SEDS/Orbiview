import serial # install pyserial for reading serial port
import pandas as pd

arduino = serial.Serial(port=' ', baudrate = 115200, timeout = 0.1)

arduino.open() # open serial port to listen in for any incoming data

while True:
    if arduino.in_waiting: # returns the number of bytes available to read in the serial ports recieve buffer
        packet = arduino.readline()
        print(packet.decode('utf-8'))
        # removes extra newline
        # print(packet.decode('utf-8').rstrip('\n'))