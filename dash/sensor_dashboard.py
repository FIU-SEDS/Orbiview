import sys
import numpy as np
import csv
import serial
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QGridLayout)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor
import pyqtgraph as pg
import os

class SerialThread(QThread):
    data_received = pyqtSignal(list)
    
    # change port to /dev/ttyUSB# for linux
    def __init__(self, port='COM13', baudrate=115200):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.running = True
        self.connected = False

        output_dir = "Flight_Logs"
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate a timestamp-based filename
        current_time = time.strftime("%Y-%m-%d_%H-%M-%S")
        self.output_csv = os.path.join(output_dir, f"Flight_Data_{current_time}.csv")
        
        # Initialize CSV file
        with open(self.output_csv, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["acceleration_x", "acceleration_y", "acceleration_z", 
                           "gyro_x", "gyro_y", "gyro_z", 
                           "time_elapsed", "rocket_state", "rssi", "signal_to_noise"])
        
        print(f"Data will be saved to: {self.output_csv}")
        print(f"Attempting to connect to {port} at {baudrate} baud...")
    
    def run(self):
        ser = None
        reconnect_delay = 2  # seconds
        
        while self.running:
            # Try to connect if not connected
            if not self.connected:
                try:
                    # Close previous connection if exists
                    if ser is not None:
                        ser.close()
                    
                    # Open new serial connection
                    ser = serial.Serial(port=self.port, baudrate=self.baudrate, timeout=1)
                    time.sleep(reconnect_delay)  # Allow time for connection to establish
                    self.connected = True
                    print(f"Connected to {self.port}. Waiting for data...")
                except Exception as e:
                    print(f"Connection failed: {e}. Retrying in {reconnect_delay} seconds...")
                    time.sleep(reconnect_delay)
                    continue
            
            # Read data if connected
            try:
                if ser.in_waiting:
                    line = ser.readline().decode('utf-8').strip()  # Read and decode serial data
                    if "+RCV=" in line:
                        clean_data = line.replace("+RCV=", "")  # FOR OLD CODE IT IS Received: +RCV=
                        data_values = clean_data.split(',')
                        
                        # Parse data values
                        if len(data_values) >= 12:  # Ensure we have all expected values
                            acceleration_x = int(data_values[2])
                            acceleration_y = int(data_values[3])
                            acceleration_z = int(data_values[4])
                            gyro_x = int(data_values[5])
                            gyro_y = int(data_values[6])
                            gyro_z = int(data_values[7])
                            time_elapsed = int(data_values[8])
                            rocket_state = data_values[9]
                            rssi = int(data_values[10])
                            signal_to_noise = float(data_values[11])
                            
                            # Save to CSV
                            with open(self.output_csv, mode='a', newline='') as csvfile:
                                writer = csv.writer(csvfile)
                                writer.writerow([
                                    acceleration_x, acceleration_y, acceleration_z,
                                    gyro_x, gyro_y, gyro_z,
                                    time_elapsed, rocket_state, rssi, signal_to_noise
                                ])
                            
                            # Emit signal with parsed data
                            self.data_received.emit([
                                acceleration_x, acceleration_y, acceleration_z,
                                gyro_x, gyro_y, gyro_z,
                                time_elapsed, rocket_state, rssi, signal_to_noise
                            ])
                
                time.sleep(0.05)  # Small delay to prevent CPU hogging
                
            except serial.SerialException as e:
                print(f"Serial connection lost: {e}. Attempting to reconnect...")
                self.connected = False
                time.sleep(reconnect_delay)
            except Exception as e:
                print(f"Error reading data: {e}")
                time.sleep(0.5)  # Brief pause before trying again
        
        # Clean up
        if ser is not None:
            ser.close()
    
    def stop(self):
        self.running = False
        self.wait()

class SensorDashboard(QMainWindow):
    def __init__(self, serial_port='COM13', baudrate=115200):
        super().__init__()
        
        # Set window title and size
        self.setWindowTitle("Sensor Dashboard")
        self.setGeometry(100, 100, 1200, 800)
        
        # Setup serial communication thread
        self.serial_thread = SerialThread(port=serial_port, baudrate=baudrate)
        self.serial_thread.data_received.connect(self.update_with_serial_data)
        
        # Set dark theme colors
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #0D0D0D;
                color: #FFFFFF;
            }
            QLabel {
                color: #FFFFFF;
                font-weight: bold;
            }
        """)
        
        # Create main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        # Create top layout for graphs (2x2 grid)
        graphs_widget = QWidget()
        graphs_layout = QGridLayout()
        graphs_widget.setLayout(graphs_layout)
        
        # Create the four graph panels
        self.accel_graph = self.create_graph_panel("Acceleration")
        self.gyro_graph = self.create_graph_panel("Gyroscope")
        self.rssi_graph = self.create_graph_panel("RSSI")
        self.snr_graph = self.create_graph_panel("Signal To Noise")
        
        # Add graph panels to the grid layout
        graphs_layout.addWidget(self.accel_graph, 0, 0)
        graphs_layout.addWidget(self.gyro_graph, 0, 1)
        graphs_layout.addWidget(self.rssi_graph, 1, 0)
        graphs_layout.addWidget(self.snr_graph, 1, 1)
        
        # Create bottom telemetry panel
        telemetry_widget = QWidget()
        telemetry_layout = QVBoxLayout()
        telemetry_widget.setLayout(telemetry_layout)
        
        # Create telemetry title & ON/OFF label
        telemetry_title = QLabel("Telemetry")
        telemetry_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        telemetry_title.setFont(QFont("Arial", 14))
        self.OnOrOff = QLabel("🔴⚪")
        self.OnOrOff.setAlignment(Qt.AlignmentFlag.AlignCenter)
        telemetry_layout.addWidget(telemetry_title)
        telemetry_layout.addWidget(self.OnOrOff)
        
        # Create telemetry values display
        telemetry_values = QWidget()
        values_layout = QHBoxLayout()
        telemetry_values.setLayout(values_layout)
        
        # Create each telemetry value display
        self.accel_x = self.create_telemetry_value("Acceleration X", "--")
        self.accel_y = self.create_telemetry_value("Acceleration Y", "--")
        self.accel_z = self.create_telemetry_value("Acceleration Z", "--")
        self.gyro_x = self.create_telemetry_value("Gyro X", "--")
        self.gyro_y = self.create_telemetry_value("Gyro Y", "--")
        self.gyro_z = self.create_telemetry_value("Gyro Z", "--")
        self.time = self.create_telemetry_value("Time", "--")
        self.state = self.create_telemetry_value("State", "--")
        
        # Add telemetry values to layout
        values_layout.addWidget(self.accel_x)
        values_layout.addWidget(self.accel_y)
        values_layout.addWidget(self.accel_z)
        values_layout.addWidget(self.gyro_x)
        values_layout.addWidget(self.gyro_y)
        values_layout.addWidget(self.gyro_z)
        values_layout.addWidget(self.time)
        values_layout.addWidget(self.state)
        
        telemetry_layout.addWidget(telemetry_values)
        
        # Add widgets to main layout
        main_layout.addWidget(graphs_widget, 4)  # 80% of height
        main_layout.addWidget(telemetry_widget, 1)  # 20% of height
        
        # Setup data and timers
        self.setup_graph_data()
        self.setup_timers()
        
        # Start serial thread
        self.serial_thread.start()
    
    def create_graph_panel(self, title):
        # Create widget for the graph panel
        panel = QWidget()
        panel.setStyleSheet("border: 1px solid #333333; border-radius: 10px;")
        layout = QVBoxLayout()
        panel.setLayout(layout)
        
        # Add title
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Arial", 12))
        layout.addWidget(title_label)
        
        # Create PyQtGraph plot widget
        plot_widget = pg.PlotWidget()
        plot_widget.setBackground('#0D0D0D')
        plot_widget.showGrid(x=True, y=True, alpha=0.3)
        
        # Configure axes
        plot_widget.getAxis('bottom').setPen(pg.mkPen(color='#FFFFFF', width=1))
        plot_widget.getAxis('left').setPen(pg.mkPen(color='#FFFFFF', width=1))
        plot_widget.getAxis('bottom').setTextPen(pg.mkPen(color='#FFFFFF', width=1))
        plot_widget.getAxis('left').setTextPen(pg.mkPen(color='#FFFFFF', width=1))
        
        layout.addWidget(plot_widget)
        
        # Store the plot widget for later access
        panel.plot_widget = plot_widget
        
        return panel
    
    def create_telemetry_value(self, title, value):
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Arial", 8))
        
        value_label = QLabel(value)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        
        # Store the value label for later updates
        widget.value_label = value_label
        
        return widget
    
    def setup_graph_data(self):
        # Generate x-axis data (time points)
        self.x_data = np.arange(500)
        
        # Initialize empty data arrays
        self.accel_x_data = np.zeros(0)
        self.accel_y_data = np.zeros(0)
        self.accel_z_data = np.zeros(0)
        self.gyro_x_data = np.zeros(0)
        self.gyro_y_data = np.zeros(0)
        self.gyro_z_data = np.zeros(0)
        self.rssi_data = np.zeros(0)
        self.snr_data = np.zeros(0)
        
        # Create acceleration plot lines
        self.accel_x_line = self.accel_graph.plot_widget.plot(
            self.x_data, self.accel_x_data, pen=pg.mkPen(color='#3498db', width=2), name="acceleration_x"
        )
        self.accel_y_line = self.accel_graph.plot_widget.plot(
            self.x_data, self.accel_y_data, pen=pg.mkPen(color='#2ecc71', width=2), name="acceleration_y"
        )
        self.accel_z_line = self.accel_graph.plot_widget.plot(
            self.x_data, self.accel_z_data, pen=pg.mkPen(color='#e74c3c', width=2), name="acceleration_z"
        )
        
        # Create gyroscope plot lines
        self.gyro_x_line = self.gyro_graph.plot_widget.plot(
            self.x_data, self.gyro_x_data, pen=pg.mkPen(color='#3498db', width=2), name="gyro_x"
        )
        self.gyro_y_line = self.gyro_graph.plot_widget.plot(
            self.x_data, self.gyro_y_data, pen=pg.mkPen(color='#e74c3c', width=2), name="gyro_y"
        )
        self.gyro_z_line = self.gyro_graph.plot_widget.plot(
            self.x_data, self.gyro_z_data, pen=pg.mkPen(color='#f1c40f', width=2), name="gyro_z"
        )
        
        # Create RSSI plot line
        self.rssi_line = self.rssi_graph.plot_widget.plot(
            self.x_data, self.rssi_data, pen=pg.mkPen(color='#FFFFFF', width=2), name="rssi"
        )
        
        # Create SNR plot line
        self.snr_line = self.snr_graph.plot_widget.plot(
            self.x_data, self.snr_data, pen=pg.mkPen(color='#3498db', width=2), name="snr"
        )
        
        # Set y-axis ranges
        self.accel_graph.plot_widget.setYRange(-1000, 1500)
        self.gyro_graph.plot_widget.setYRange(-150000, 150000)
        self.rssi_graph.plot_widget.setYRange(-50, 0)
        self.snr_graph.plot_widget.setYRange(0, 12)
        
        # Set initial connection state
        self.is_connected = False
        self.state.value_label.setText("CONNECT RECIEVER")
        
        # Create legends
        self.create_legend(self.accel_graph, ["accel_x", "accel_y", "accel_z"])
        self.create_legend(self.gyro_graph, ["gyro_x", "gyro_y", "gyro_z"])
    
    def create_legend(self, graph_panel, items):
        legend = pg.LegendItem(offset=(70, 30))
        legend.setParentItem(graph_panel.plot_widget.graphicsItem())
        
        if "accel_x" in items:
            legend.addItem(self.accel_x_line, "acceleration_x")
            legend.addItem(self.accel_y_line, "acceleration_y")
            legend.addItem(self.accel_z_line, "acceleration_z")
        elif "gyro_x" in items:
            legend.addItem(self.gyro_x_line, "gyro_x")
            legend.addItem(self.gyro_y_line, "gyro_y")
            legend.addItem(self.gyro_z_line, "gyro_z")
    
    def setup_timers(self):
        # Create a timer to check connection status
        self.connection_timer = QTimer()
        self.connection_timer.timeout.connect(self.check_connection)
        self.connection_timer.start(2000)  # Check every 2 seconds
        
        # Last data timestamp to check for connection status
        self.last_data_time = 0
    
    def check_connection(self):
        # If no data received for 5 seconds, consider disconnected
        current_time = time.time()
        if hasattr(self, 'last_data_time') and (current_time - self.last_data_time) > 5:
            if self.is_connected:
                self.is_connected = False
                self.state.value_label.setText("CONNECT RECIEVER")
                
                # Reset values when disconnected
                self.accel_x.value_label.setText("--")
                self.accel_y.value_label.setText("--")
                self.accel_z.value_label.setText("--")
                self.gyro_x.value_label.setText("--")
                self.gyro_y.value_label.setText("--")
                self.gyro_z.value_label.setText("--")
                self.time.value_label.setText("--")
                
                print("Connection lost. Waiting for data...")
        
        # On first run, set initial timestamp
        if not hasattr(self, 'last_data_time'):
            self.last_data_time = current_time
    
    # Removed update_telemetry method as it's no longer needed
                
    def update_with_serial_data(self, data):
        """Update dashboard with real data received from serial port"""
        # Extract data values
        accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z, time_value, state, rssi, snr = data
        
        # Mark as connected and update last data time
        if not self.is_connected:
            self.is_connected = True
            print("Connection established! Receiving data...")
        
        self.last_data_time = time.time()
        
        # Update acceleration data
        self.accel_x_data = np.roll(self.accel_x_data, -1)
        self.accel_x_data[-1] = accel_x
        
        self.accel_y_data = np.roll(self.accel_y_data, -1)
        self.accel_y_data[-1] = accel_y
        
        self.accel_z_data = np.roll(self.accel_z_data, -1)
        self.accel_z_data[-1] = accel_z
        
        # Update gyroscope data
        self.gyro_x_data = np.roll(self.gyro_x_data, -1)
        self.gyro_x_data[-1] = gyro_x
        
        self.gyro_y_data = np.roll(self.gyro_y_data, -1)
        self.gyro_y_data[-1] = gyro_y
        
        self.gyro_z_data = np.roll(self.gyro_z_data, -1)
        self.gyro_z_data[-1] = gyro_z
        
        # Update RSSI data
        self.rssi_data = np.roll(self.rssi_data, -1)
        self.rssi_data[-1] = rssi
        
        # Update SNR data
        self.snr_data = np.roll(self.snr_data, -1)
        self.snr_data[-1] = snr
        
        # Update plot data
        self.accel_x_line.setData(self.x_data, self.accel_x_data)
        self.accel_y_line.setData(self.x_data, self.accel_y_data)
        self.accel_z_line.setData(self.x_data, self.accel_z_data)
        
        self.gyro_x_line.setData(self.x_data, self.gyro_x_data)
        self.gyro_y_line.setData(self.x_data, self.gyro_y_data)
        self.gyro_z_line.setData(self.x_data, self.gyro_z_data)
        
        self.rssi_line.setData(self.x_data, self.rssi_data)
        self.snr_line.setData(self.x_data, self.snr_data)
        
        # Update telemetry display
        self.accel_x.value_label.setText(str(accel_x))
        self.accel_y.value_label.setText(str(accel_y))
        self.accel_z.value_label.setText(str(accel_z))
        self.gyro_x.value_label.setText(str(gyro_x))
        self.gyro_y.value_label.setText(str(gyro_y))
        self.gyro_z.value_label.setText(str(gyro_z))
        self.time.value_label.setText(str(time_value))

        # Update state display
        if(state == "1"):
            self.state.value_label.setText("INIT")
        elif(state == "2"):
            self.state.value_label.setText("IDLE")
        elif(state == "3"):
            self.state.value_label.setText("BOOST")
        elif(state == "4"):
            self.state.value_label.setText("APOGEE")
        elif(state == "5"):
            self.state.value_label.setText("DROGUE")
        elif(state == "6"):
            self.state.value_label.setText("MAIN")
        elif(state == "7"):
            self.state.value_label.setText("LAND")

        #Update ON/OFF label
        self.OnOrOff.setText("⚪🟢")
        

    def closeEvent(self, event):
        """Handle window close event to clean up resources"""
        print("Shutting down...")
        if hasattr(self, 'serial_thread'):
            self.serial_thread.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Change this to match your serial port
    # window = SensorDashboard(serial_port='/dev/ttyUSB0', baudrate=115200) # linux
    window = SensorDashboard(serial_port='COM13', baudrate=115200) # windows
    
    window.show()
    
    sys.exit(app.exec())