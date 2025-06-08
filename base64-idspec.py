import base64
import struct

def parse_packets(data_bytes):
    """Parse binary packet data: variable-length sensors based on sensor ID"""
    if len(data_bytes) < 1:
        print(f"[Error] Packet too short: {len(data_bytes)} bytes")
        return None
        
    print(f"[Debug] Total data length: {len(data_bytes)} bytes")
    
    # Define sensor configurations: ID -> (name, num_floats, field_names)
    sensor_configs = {
        0: ("Barometer", 2, ["altitude", "pressure"]),
        1: ("IMU", 8, ["tilt_angle", "g_force_z", "linear_accel_x", "linear_accel_y", 
                      "linear_accel_z", "linear_velo_x", "linear_velo_y", "linear_velo_z"]),
        2: ("Magnetometer", 1, ["heading"]),
        3: ("Real_Time_Clock", 0, []),  # Not specified yet
        4: ("Temp_Humid", 2, ["humidity", "temperature"]),
        5: ("GPS", 2, ["latitude", "longitude"]),
        6: ("Time", 0, [])  # Not specified yet
    }
    
    sensors = []
    offset = 0
    sensor_count = 0
    
    while offset < len(data_bytes):
        if offset >= len(data_bytes):
            break
            
        sensor_id = data_bytes[offset]
        sensor_count += 1
        offset += 1
        
        if sensor_id not in sensor_configs:
            print(f"[Error] Unknown sensor ID: {sensor_id}")
            return None
        
        sensor_name, num_floats, field_names = sensor_configs[sensor_id]
        expected_bytes = num_floats * 4  # 4 bytes per float
        
        if offset + expected_bytes > len(data_bytes):
            print(f"[Error] Not enough data for {sensor_name}: need {expected_bytes} bytes, have {len(data_bytes) - offset}")
            return None
        
        print(f"[Sensor {sensor_count}] {sensor_name} (ID: {sensor_id}) - reading {num_floats} float(s)")
        
        try:
            # Read the floats for this sensor
            float_values = []
            sensor_data = {'sensor_id': sensor_id, 'sensor_name': sensor_name}
            
            for i in range(num_floats):
                float_value = struct.unpack_from('f', data_bytes, offset=offset)[0]
                float_values.append(float_value)
                
                # Add named field
                if i < len(field_names):
                    field_name = field_names[i]
                    sensor_data[field_name] = float_value
                    print(f"  {field_name}: {float_value:.6f}")
                else:
                    print(f"  value_{i}: {float_value:.6f}")
                
                offset += 4
            
            sensor_data['values'] = float_values
            sensor_data['num_values'] = num_floats
            sensors.append(sensor_data)
                
        except struct.error as e:
            print(f"[Struct Error] Failed to unpack {sensor_name}: {e}")
            return None
    
    print(f"[Debug] Successfully parsed {len(sensors)} sensor(s)")
    return sensors

def process_serial_line(line):
    """Process a single line from serial input in format: +RCV=[address],[length],[data],[rssi],[snr]"""
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
                    
                    # Parse the packets (could be multiple sensors)
                    parsed_sensors = parse_packets(raw_data)
                    
                    if parsed_sensors:
                        # Add metadata to the result
                        parsed_data = {
                            'sensors': parsed_sensors,
                            'address': address,
                            'reported_length': length,
                            'actual_length': actual_length,
                            'rssi': rssi,
                            'snr': snr,
                            'num_sensors': len(parsed_sensors)
                        }
                        return parsed_data
                    else:
                        return None
                    
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
        
        # Try to parse as sensor data
        if len(raw_data) >= 1:
            print(f"[Base64 Decode] Attempting to parse as sensor data...")
            sensors = parse_packets(raw_data)
            if sensors:
                print(f"[Base64 Decode] Successfully parsed {len(sensors)} sensor(s)")
            else:
                print(f"[Base64 Decode] Failed to parse as sensor data")
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
                print(f"  Number of sensors: {result['num_sensors']}")
                print(f"  Address: {result['address']}")
                print(f"  Length: {result['reported_length']} (actual: {result['actual_length']})")
                print(f"  RSSI: {result['rssi']}")
                print(f"  SNR: {result['snr']}")
                print(f"  Sensors:")
                
                for i, sensor in enumerate(result['sensors']):
                    print(f"    {i+1}. {sensor['sensor_name']} (ID: {sensor['sensor_id']}):")
                    
                    # Print individual fields if they exist
                    if sensor['num_values'] > 0:
                        for key, value in sensor.items():
                            if key not in ['sensor_id', 'sensor_name', 'values', 'num_values'] and isinstance(value, (int, float)):
                                print(f"       {key}: {value:.6f}")
                    else:
                        print(f"       No data fields")
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