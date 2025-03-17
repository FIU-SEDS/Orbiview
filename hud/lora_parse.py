import csv
import serial
import time

#setting up a serial connection (port and baud rate)
# ser = serial.Serial(port='/dev/cu.usbmodem1101', baudrate=9600, timeout=1) # mac
ser = serial.Serial(port='COM13', baudrate=115200, timeout=1) # windows
time.sleep(2)

output_csv = "parsed_data.csv"

with open(output_csv, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["acceleration_x","acceleration_y","acceleration_z","gyro_x","gyro_y","gyro_z","time_elapsed", "rssi", "signal_to_noise"])

print("Waiting for LoRa data...")
#reads the data file and processes each line 
try:
    while True: 
        line = ser.readline().decode('utf-8').strip()  # Read and decode serial data
        if "+RCV=" in line:
            clean_data = line.replace("+RCV=", "")
            data_values = clean_data.split(',')

            acceleration_x = data_values[2]
            acceleration_y = data_values[3]
            acceleration_z = data_values[4]
            gyro_x = data_values[5]
            gyro_y = data_values[6]
            gyro_z = data_values[7]
            time_elapsed = data_values[8]  # Time
            rocket_state = data_values[9]
            rssi = data_values[10]  # RSSI 
            signal_to_noise = data_values[11]  # Signal 

                
            with open(output_csv, mode='a', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow([acceleration_x,acceleration_y,acceleration_z,gyro_x,gyro_y,gyro_z,time_elapsed,rocket_state, rssi, signal_to_noise])

            print(f"Logged data: Acceleration(X,Y,Z)=({acceleration_x},{acceleration_y},{acceleration_z}), Gyroscope(X,Y,Z)=({gyro_x},{gyro_y},{gyro_z}), Time={time_elapsed}, Rocket State={rocket_state}, RSSI={rssi}, Signal={signal_to_noise}, ")   
            time.sleep(0.5)  


except KeyboardInterrupt:
    print("\nStopped receiving data.")
    ser.close()