import base64
import struct

def parse_packet(data_bytes):
    """Parse binary packet data: 1 byte sensor ID + 4 bytes float value"""
    if len(data_bytes) < 5:  # Need at least 5 bytes (1 for ID + 4 for float)
        print(f"[Error] Packet too short: {len(data_bytes)} bytes, need 5")
        return None
        
    sensor_id = data_bytes[0]
    print(f"[Debug] Sensor ID: {sensor_id}, Data length: {len(data_bytes)} bytes")

    try:
        # Unpack the float value from bytes 1-4
        float_value = struct.unpack_from('f', data_bytes, offset=1)[0]
        
        # Map sensor IDs to sensor names
        sensor_names = {
            0: "Pressure",
            1: "Altitude", 
            2: "Acceleration_X",
            3: "Acceleration_Y",
            4: "Acceleration_Z",
            5: "Gyro_X",
            6: "Gyro_Y", 
            7: "Gyro_Z",
            8: "Magnetometer_X",
            9: "Magnetometer_Y",
            10: "Magnetometer_Z",
            11: "Temperature",
            12: "Humidity",
            13: "GPS_Latitude",
            14: "GPS_Longitude",
            15: "GPS_Altitude"
        }
        
        sensor_name = sensor_names.get(sensor_id, f"Unknown_Sensor_{sensor_id}")
        
        print(f"[{sensor_name}] Value: {float_value:.6f}")
        
        return {
            'sensor_id': sensor_id,
            'sensor_name': sensor_name,
            'value': float_value
        }
            
    except struct.error as e:
        print(f"[Struct Error] Failed to unpack sensor ID {sensor_id}: {e}")
        return None

def process_serial_line(line):
    """Process a single line from serial input in format: RCV+=[address],[length],[data],[rssi],[snr]"""
    print(f"[Input] Processing line: {line}")
    
    try:
        if "+RCV=" in line:
            # Remove the RCV+= prefix and split by commas
            data_part = line.replace("+RCV=", "")
            parts = data_part.split(',')
            print(f"[Debug] Split into {len(parts)} parts: {parts}")
            
            if len(parts) >= 5:
                address = parts[0].strip()
                length = parts[1].strip()
                b64_data = parts[2].strip()  # The Base64 encoded data
                rssi = parts[3].strip()
                snr = parts[4].strip()
                
                print(f"[Debug] Address: {address}")
                print(f"[Debug] Reported Length: {length}")
                print(f"[Debug] RSSI: {rssi}")
                print(f"[Debug] SNR: {snr}")
                print(f"[Debug] Base64 data: '{b64_data}'")
                
                try:
                    # Decode Base64 to binary data
                    raw_data = base64.b64decode(b64_data)
                    actual_length = len(raw_data)
                    print(f"[Debug] Actual decoded length: {actual_length} bytes")
                    print(f"[Debug] Raw bytes: {[hex(b) for b in raw_data]}")
                    
                    # Check if reported length matches actual length
                    try:
                        reported_length_int = int(length)
                        if reported_length_int != actual_length:
                            print(f"[Warning] Length mismatch! Reported: {reported_length_int}, Actual: {actual_length}")
                    except ValueError:
                        print(f"[Warning] Could not parse reported length: '{length}'")
                    
                    # Parse the packet
                    parsed_data = parse_packet(raw_data)
                   
                    if parsed_data:
                        # Add the metadata
                        parsed_data['address'] = address
                        parsed_data['reported_length'] = length
                        parsed_data['actual_length'] = actual_length
                        parsed_data['rssi'] = rssi
                        parsed_data['snr'] = snr
                    
                    return parsed_data
                    
                except Exception as e:
                    print(f"[Decode Error] {e}")
                    return None
            else:
                print(f"[Error] Invalid RCV format, expected 5 parts, got {len(parts)}")
                return None
        else:
            print("[Error] Line doesn't contain 'RCV+='")
            return None
    except Exception as e:
        print(f"[Serial Error] {e}")
        return None

def decode_raw_base64(b64_string):
    """Helper function to decode and inspect any Base64 string"""
    print(f"\n[Base64 Decode] Input: '{b64_string}'")
    try:
        raw_data = base64.b64decode(b64_string)
        print(f"[Base64 Decode] Decoded {len(raw_data)} bytes: {[hex(b) for b in raw_data]}")
        
        if len(raw_data) >= 5:
            sensor_id = raw_data[0]
            float_val = struct.unpack_from('f', raw_data, offset=1)[0]
            print(f"[Base64 Decode] Sensor ID: {sensor_id}, Float value: {float_val}")
        elif len(raw_data) >= 1:
            print(f"[Base64 Decode] Only {len(raw_data)} bytes - not enough for sensor+float format")
            print(f"[Base64 Decode] First byte (sensor ID?): {raw_data[0]}")
        else:
            print("[Base64 Decode] No data decoded")
            
    except Exception as e:
        print(f"[Base64 Decode] Error: {e}")

def interactive_test():
    print("=" * 60)
    print("INTERACTIVE BASE64 SENSOR PACKET PARSER")
    print("=" * 60)
    print("Format: RCV+=[address],[length],[data],[rssi],[snr]")
    print("Enter 'quit' to exit")
    print("Enter 'b64:yourbase64string' to decode just Base64 data")
    print("=" * 60)
    
    while True:
        try:
            user_input = input("\nEnter RCV line: ").strip()
            
            if user_input.lower() == 'quit':
                break
            
            if user_input.startswith('b64:'):
                # Just decode the Base64 part
                b64_part = user_input[4:]
                decode_raw_base64(b64_part)
                continue
                
            if not user_input:
                print("Please enter a valid RCV line or 'quit'")
                continue
            
            print("\n" + "-" * 50)
            result = process_serial_line(user_input)
            
            if result:
                print(f"\n[SUCCESS] Parsed Data:")
                print(f"  Sensor: {result['sensor_name']} (ID: {result['sensor_id']})")
                print(f"  Value: {result['value']:.6f}")
                print(f"  Address: {result['address']}")
                print(f"  Length: {result['reported_length']} (actual: {result['actual_length']})")
                print(f"  RSSI: {result['rssi']}")
                print(f"  SNR: {result['snr']}")
            else:
                print("\n[FAILED] Could not parse the input")
            
            print("-" * 50)
            
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    interactive_test()