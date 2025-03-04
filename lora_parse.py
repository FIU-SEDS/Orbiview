import csv
import serial
import time

#setting up a serial connection (port and baud rate)
ser = serial.Serial(port='/dev/cu.usbmodem1101', baudrate=9600, timeout=1)
time.sleep(2)

output_csv = "parsed_data.csv"

with open(output_csv, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Altitude", "Acceleration", "Time", "RSSI", "Signal-to-Noise"])

print("Waiting for LoRa data...")
#reads the data file and processes each line 
try:
    while True: 
        line = ser.readline().decode('utf-8').strip()  # Read and decode serial data
        if "Received: +RCV=" in line:
            clean_data = line.replace("Received: +RCV=", "")
            data_values = clean_data.split(',')

            altitude = data_values[2]  # Altitude
            accelerometer = data_values[3] 
            time_elapsed = data_values[4]  # Time
            rssi = data_values[5]  # RSSI 
            signal_to_noise = data_values[6]  # Signal 

                
            with open(output_csv, mode='a', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow([altitude, accelerometer,time_elapsed, rssi, signal_to_noise])

            print(f"Logged data: Altitude={altitude}, Accelerometer={accelerometer}, Time={time_elapsed}, RSSI={rssi}, Signal={signal_to_noise}, ")   
            time.sleep(0.5)  


except KeyboardInterrupt:
    print("\nStopped receiving data.")
    ser.close()