import sys
import numpy as np
import csv
import serial
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QGridLayout, QComboBox, QPushButton,
                            QDialog, QDialogButtonBox)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor
import pyqtgraph as pg
import os
from serial.tools import list_ports

class PortSelectionDialog(QDialog):
    """Dialog for selecting a serial port"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Serial Port")
        self.resize(400, 200)
        
        # Set dark theme
        self.setStyleSheet("""
            QDialog, QWidget {
                background-color: #0D0D0D;
                color: #FFFFFF;
            }
            QLabel {
                color: #FFFFFF;
                font-weight: bold;
            }
            QComboBox {
                background-color: #222222;
                color: #FFFFFF;
                border: 1px solid #555555;
                padding: 5px;
                min-height: 25px;
            }
            QPushButton {
                background-color: #FFFFFF;
                color: #0D0D0D;
                border: none;
                padding: 8px 16px;
                min-height: 30px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #E0E0E0;
            }
            QPushButton:pressed {
                background-color: #CCCCCC;
            }
        """)
        
        layout = QVBoxLayout()
        
        # Label
        self.label = QLabel("Reciever Serial Port:")
        self.label.setFont(QFont("Arial", 11))
        layout.addWidget(self.label)
        
        # Port selection dropdown
        self.port_combo = QComboBox()
        self.port_combo.setFont(QFont("Arial", 10))
        layout.addWidget(self.port_combo)
        
        # Baud rate selection dropdown
        baud_layout = QHBoxLayout()
        self.baud_label = QLabel("Baud Rate:")
        self.baud_label.setFont(QFont("Arial", 11))
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.baud_combo.setCurrentText("115200")  # Default to 115200
        baud_layout.addWidget(self.baud_label)
        baud_layout.addWidget(self.baud_combo)
        layout.addLayout(baud_layout)
        
        # Refresh button
        self.refresh_button = QPushButton("Refresh Ports")
        self.refresh_button.clicked.connect(self.populate_ports)
        layout.addWidget(self.refresh_button)
        
        # OK/Cancel buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | 
                                           QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
        
        self.setLayout(layout)
        
        # Populate ports initially
        self.populate_ports()
    
    def populate_ports(self):
        """Find all available serial ports and add them to the combo box"""
        self.port_combo.clear()
        ports = self.get_serial_ports()
        
        if not ports:
            self.port_combo.addItem("No ports found")
            self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
        else:
            for port, desc, hwid in ports:
                self.port_combo.addItem(f"{port} - {desc}")
            self.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)
    
    def get_serial_ports(self):
        """Get a list of available serial ports"""
        return sorted(list_ports.comports())
    
    def get_selected_port(self):
        """Return the currently selected port"""
        if self.port_combo.currentText() == "No ports found":
            return None
        
        # Extract just the port name before the dash
        port_text = self.port_combo.currentText()
        return port_text.split(" - ")[0]
    
    def get_selected_baudrate(self):
        """Return the selected baud rate as an integer"""
        return int(self.baud_combo.currentText())


class SerialThread(QThread):
    data_received = pyqtSignal(list)
    connection_status_changed = pyqtSignal(bool, str)  # Signal for connection status
    
    def __init__(self, port=None, baudrate=115200):
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
        
        # Initialize CSV file with new data fields
        with open(self.output_csv, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["tilt_angle", "z_axis_g_force", "linear_accel_x", "linear_accel_y", "linear_accel_z",
                           "linear_velocity_x", "linear_velocity_y", "linear_velocity_z", 
                           "altitude", "pressure", "heading", "temperature", "humidity", 
                           "longitude", "latitude", "time_elapsed", "rocket_state"])
        
        print(f"Data will be saved to: {self.output_csv}")
        if self.port:
            print(f"Attempting to connect to {port} at {baudrate} baud...")
    
    def set_port(self, port, baudrate=None):
        """Update the port and optionally the baudrate"""
        self.port = port
        if baudrate:
            self.baudrate = baudrate
        
        # Reset connection
        self.connected = False
        print(f"Port updated to {port}, baudrate {self.baudrate}")
    
    def run(self):
        ser = None
        reconnect_delay = 2  # seconds
        
        while self.running:
            # Skip connection attempts if no port is specified
            if not self.port:
                time.sleep(1)
                continue
                
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
                    
                    # Emit signal instead of directly accessing UI elements
                    self.connection_status_changed.emit(True, "WAITING FOR SIGNAL")

                except Exception as e:
                    print(f"Connection failed: {e}. Retrying in {reconnect_delay} seconds...")
                    self.connection_status_changed.emit(False, f"CONNECTION FAILED: {str(e)[:20]}")
                    time.sleep(reconnect_delay)
                    continue
            
            # Read data if connected
            try:
                if ser.in_waiting:
                    line = ser.readline().decode('utf-8').strip()  # Read and decode serial data
                    if "+RCV=" in line:
                        clean_data = line.replace("+RCV=", "")  # FOR OLD CODE IT IS Received: Recieved+RCV=
                        data_values = clean_data.split(',')
                        
                        # Parse new data values - expecting 17 values now
                        if len(data_values) >= 17:  # Updated for new data structure
                            tilt_angle = float(data_values[0])
                            z_axis_g_force = float(data_values[1])
                            linear_accel_x = float(data_values[2])
                            linear_accel_y = float(data_values[3])
                            linear_accel_z = float(data_values[4])
                            linear_velocity_x = float(data_values[5])
                            linear_velocity_y = float(data_values[6])
                            linear_velocity_z = float(data_values[7])
                            altitude = float(data_values[8])
                            pressure = float(data_values[9])
                            heading = float(data_values[10])
                            temperature = float(data_values[11])
                            humidity = float(data_values[12])
                            longitude = float(data_values[13])
                            latitude = float(data_values[14])
                            time_elapsed = int(data_values[15])
                            rocket_state = data_values[16]
                            
                            # Save to CSV
                            with open(self.output_csv, mode='a', newline='') as csvfile:
                                writer = csv.writer(csvfile)
                                writer.writerow([
                                    tilt_angle, z_axis_g_force, linear_accel_x, linear_accel_y, linear_accel_z,
                                    linear_velocity_x, linear_velocity_y, linear_velocity_z,
                                    altitude, pressure, heading, temperature, humidity,
                                    longitude, latitude, time_elapsed, rocket_state
                                ])
                            
                            # Emit signal with parsed data
                            self.data_received.emit([
                                tilt_angle, z_axis_g_force, linear_accel_x, linear_accel_y, linear_accel_z,
                                linear_velocity_x, linear_velocity_y, linear_velocity_z,
                                altitude, pressure, heading, temperature, humidity,
                                longitude, latitude, time_elapsed, rocket_state
                            ])
                
                time.sleep(0.05)  # Small delay to prevent CPU hogging
                
            except serial.SerialException as e:
                print(f"Serial connection lost: {e}. Attempting to reconnect...")
                self.connected = False
                
                # Emit signal instead of directly accessing UI elements
                self.connection_status_changed.emit(False, "RECONNECT RECEIVER")
                
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
    def __init__(self):
        super().__init__()
        
        # Set window title and size
        self.setWindowTitle("Sensor Dashboard")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create the UI elements
        self.init_ui()
        
        # Setup serial thread initially with no port
        self.serial_thread = SerialThread()
        self.serial_thread.data_received.connect(self.update_with_serial_data)
        self.serial_thread.connection_status_changed.connect(self.update_connection_status)
        
        # Start serial thread
        self.serial_thread.start()
        
        # Show port selection dialog on startup
        self.show_port_selection()
    
    def init_ui(self):
        """Initialize all UI elements"""
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
            QPushButton {
                background-color: #FFFFFF;
                color: #0D0D0D;
                border: none;
                padding: 8px 16px;
                min-height: 30px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #E0E0E0;
            }
            QPushButton:pressed {
                background-color: #CCCCCC;
            }
        """)
        
        # Create main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        # Create port selection button
        port_button_layout = QHBoxLayout()
        self.port_button = QPushButton("Change Port")
        self.port_button.clicked.connect(self.show_port_selection)
        port_button_layout.addWidget(self.port_button)
        port_button_layout.addStretch()  # Push button to the left
        
        # Create top layout for graphs (2x2 grid)
        graphs_widget = QWidget()
        graphs_layout = QGridLayout()
        graphs_widget.setLayout(graphs_layout)
        
        # Create the four graph panels with new titles
        self.linear_accel_graph = self.create_graph_panel("Linear Acceleration")
        self.barometer_graph = self.create_graph_panel("Barometer")
        self.z_gforce_graph = self.create_graph_panel("Z-Axis G-Force")
        self.temperature_graph = self.create_graph_panel("Temperature")
        
        # Add graph panels to the grid layout
        graphs_layout.addWidget(self.linear_accel_graph, 0, 0)
        graphs_layout.addWidget(self.barometer_graph, 0, 1)
        graphs_layout.addWidget(self.z_gforce_graph, 1, 0)
        graphs_layout.addWidget(self.temperature_graph, 1, 1)
        
        # Create bottom telemetry panel
        telemetry_widget = QWidget()
        telemetry_layout = QVBoxLayout()
        telemetry_widget.setLayout(telemetry_layout)
        
        # Create telemetry title & ON/OFF label
        telemetry_title = QLabel("Telemetry")
        telemetry_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        telemetry_title.setFont(QFont("Arial", 14))
        self.OnOrOff = QLabel("🔴⚪Receiver          🔴⚪Signal")
        self.OnOrOff.setAlignment(Qt.AlignmentFlag.AlignCenter)
        telemetry_layout.addWidget(telemetry_title)
        telemetry_layout.addWidget(self.OnOrOff)
        
        # Create telemetry values display
        telemetry_values = QWidget()
        values_layout = QHBoxLayout()
        telemetry_values.setLayout(values_layout)
        
        # Create each telemetry value display with new labels
        self.linear_vel_z = self.create_telemetry_value("Linear Velocity Z", "--")
        self.altitude = self.create_telemetry_value("Altitude", "--")
        self.pressure = self.create_telemetry_value("Pressure", "--")
        self.temperature = self.create_telemetry_value("Temperature", "--")
        self.heading = self.create_telemetry_value("Heading", "--")
        self.longitude = self.create_telemetry_value("Longitude", "--")
        self.latitude = self.create_telemetry_value("Latitude", "--")
        self.time = self.create_telemetry_value("Time", "--")
        self.state = self.create_telemetry_value("State", "--", small_font=True)
        
        # Add telemetry values to layout
        values_layout.addWidget(self.linear_vel_z)
        values_layout.addWidget(self.altitude)
        values_layout.addWidget(self.pressure)
        values_layout.addWidget(self.temperature)
        values_layout.addWidget(self.heading)
        values_layout.addWidget(self.longitude)
        values_layout.addWidget(self.latitude)
        values_layout.addWidget(self.time)
        values_layout.addWidget(self.state)
        
        telemetry_layout.addWidget(telemetry_values)
        
        # Add port button to main layout
        main_layout.addLayout(port_button_layout)
        
        # Add widgets to main layout
        main_layout.addWidget(graphs_widget, 4)  # 80% of height
        main_layout.addWidget(telemetry_widget, 1)  # 20% of height
        
        # Setup data and timers
        self.setup_graph_data()
        self.setup_timers()
    
    def show_port_selection(self):
        """Show the port selection dialog"""
        dialog = PortSelectionDialog(self)
        if dialog.exec():
            selected_port = dialog.get_selected_port()
            selected_baudrate = dialog.get_selected_baudrate()
            
            if selected_port:
                # Update the serial thread with new port/baudrate
                self.serial_thread.set_port(selected_port, selected_baudrate)
                self.state.value_label.setText(f"CONNECTING TO {selected_port}...")
    
    def update_connection_status(self, is_connected, status_message):
        """Handler for connection status changes"""
        if is_connected:
            self.state.value_label.setText(status_message)
            self.OnOrOff.setText("⚪🟢Receiver          🔴⚪Signal")
        else:
            self.state.value_label.setText(status_message)
            self.OnOrOff.setText("🔴⚪Receiver          🔴⚪Signal")
    
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
    
    def create_telemetry_value(self, title, value, small_font=False):
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Arial", 8))
        
        value_label = QLabel(value)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if small_font:
            value_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))  # Smaller font for State
        else:
            value_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        
        # Store the value label for later updates
        widget.value_label = value_label
        
        return widget
    
    def setup_graph_data(self):
        # Create empty lists to store new data
        self.linear_accel_x_data = []
        self.linear_accel_y_data = []
        self.linear_accel_z_data = []
        self.altitude_data = []
        self.z_gforce_data = []
        self.temperature_data = []
        self.time_data = []  
        
        # Create variable to track if received enough data to start plotting
        self.has_data = False
        self.max_points = 500  # Maximum number of points to display
        
        # Create plot lines with empty data initially
        self.linear_accel_x_line = self.linear_accel_graph.plot_widget.plot(
            [], [], pen=pg.mkPen(color='#3498db', width=2), name="linear_accel_x"
        )
        self.linear_accel_y_line = self.linear_accel_graph.plot_widget.plot(
            [], [], pen=pg.mkPen(color='#2ecc71', width=2), name="linear_accel_y"
        )
        self.linear_accel_z_line = self.linear_accel_graph.plot_widget.plot(
            [], [], pen=pg.mkPen(color='#e74c3c', width=2), name="linear_accel_z"
        )
        
        self.altitude_line = self.barometer_graph.plot_widget.plot(
            [], [], pen=pg.mkPen(color='#3498db', width=2), name="altitude"
        )
        
        self.z_gforce_line = self.z_gforce_graph.plot_widget.plot(
            [], [], pen=pg.mkPen(color='#FFFFFF', width=2), name="z_gforce"
        )
        
        self.temperature_line = self.temperature_graph.plot_widget.plot(
            [], [], pen=pg.mkPen(color='#f39c12', width=2), name="temperature"
        )
        
        # Set y-axis ranges for new graphs
        self.linear_accel_graph.plot_widget.setYRange(-50, 50)
        self.barometer_graph.plot_widget.setYRange(0, 5000)  # Altitude range
        self.z_gforce_graph.plot_widget.setYRange(-10, 10)   # G-force range
        self.temperature_graph.plot_widget.setYRange(-20, 80)  # Temperature range
        
        # Set initial connection state
        self.is_connected = False
        self.state.value_label.setText("SELECT PORT")
        
        # Create legends
        self.create_legend(self.linear_accel_graph, ["linear_accel_x", "linear_accel_y", "linear_accel_z"])
    
    def create_legend(self, graph_panel, items):
        legend = pg.LegendItem(offset=(70, 30))
        legend.setParentItem(graph_panel.plot_widget.graphicsItem())
        
        if "linear_accel_x" in items:
            legend.addItem(self.linear_accel_x_line, "linear_accel_x")
            legend.addItem(self.linear_accel_y_line, "linear_accel_y")
            legend.addItem(self.linear_accel_z_line, "linear_accel_z")
    
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
                self.state.value_label.setText("CONNECTION LOST")
                self.OnOrOff.setText("⚪🟢Receiver          🔴⚪Signal")
                
                # Reset values when disconnected
                self.linear_vel_z.value_label.setText("--")
                self.altitude.value_label.setText("--")
                self.pressure.value_label.setText("--")
                self.temperature.value_label.setText("--")
                self.heading.value_label.setText("--")
                self.longitude.value_label.setText("--")
                self.latitude.value_label.setText("--")
                self.time.value_label.setText("--")

                # Clear all graph data
                self.time_data = []
                self.linear_accel_x_data = []
                self.linear_accel_y_data = []
                self.linear_accel_z_data = []
                self.altitude_data = []
                self.z_gforce_data = []
                self.temperature_data = []
                
                # Update plots with empty data
                self.linear_accel_x_line.setData([], [])
                self.linear_accel_y_line.setData([], [])
                self.linear_accel_z_line.setData([], [])
                self.altitude_line.setData([], [])
                self.z_gforce_line.setData([], [])
                self.temperature_line.setData([], [])
                
                print("Connection lost. Waiting for data...")
        
        # On first run, set initial timestamp
        if not hasattr(self, 'last_data_time'):
            self.last_data_time = current_time
                
    def update_with_serial_data(self, data):
        """Update dashboard with real data received from serial port"""
        # Extract new data values
        (tilt_angle, z_axis_g_force, linear_accel_x, linear_accel_y, linear_accel_z,
         linear_velocity_x, linear_velocity_y, linear_velocity_z,
         altitude, pressure, heading, temperature, humidity,
         longitude, latitude, time_value, state) = data
        
        # Mark as connected and update last data time
        if not self.is_connected:
            self.is_connected = True
            print("Connection established! Receiving data...")
        
        self.last_data_time = time.time()
        
        # Add the new time value to our time_data array
        self.time_data.append(time_value)
        
        # Add data to lists for new graphs
        self.linear_accel_x_data.append(linear_accel_x)
        self.linear_accel_y_data.append(linear_accel_y)
        self.linear_accel_z_data.append(linear_accel_z)
        self.altitude_data.append(altitude)
        self.z_gforce_data.append(z_axis_g_force)
        self.temperature_data.append(temperature)
        
        # Trim lists to max_points if they get too long
        if len(self.time_data) > self.max_points:
            self.time_data = self.time_data[-self.max_points:]
            self.linear_accel_x_data = self.linear_accel_x_data[-self.max_points:]
            self.linear_accel_y_data = self.linear_accel_y_data[-self.max_points:]
            self.linear_accel_z_data = self.linear_accel_z_data[-self.max_points:]
            self.altitude_data = self.altitude_data[-self.max_points:]
            self.z_gforce_data = self.z_gforce_data[-self.max_points:]
            self.temperature_data = self.temperature_data[-self.max_points:]
        
        # Update plot data using time_data for x-axis
        self.linear_accel_x_line.setData(self.time_data, self.linear_accel_x_data)
        self.linear_accel_y_line.setData(self.time_data, self.linear_accel_y_data)
        self.linear_accel_z_line.setData(self.time_data, self.linear_accel_z_data)
        
        self.altitude_line.setData(self.time_data, self.altitude_data)
        self.z_gforce_line.setData(self.time_data, self.z_gforce_data)
        self.temperature_line.setData(self.time_data, self.temperature_data)
        
        # Update telemetry display with new values
        self.linear_vel_z.value_label.setText(f"{linear_velocity_z:.2f}")
        self.altitude.value_label.setText(f"{altitude:.1f}")
        self.pressure.value_label.setText(f"{pressure:.2f}")
        self.temperature.value_label.setText(f"{temperature:.1f}°C")
        self.heading.value_label.setText(f"{heading:.1f}°")
        self.longitude.value_label.setText(f"{longitude:.6f}")
        self.latitude.value_label.setText(f"{latitude:.6f}")
        self.time.value_label.setText(str(time_value))

        # Update state display
         # Update state display
        if(state == "1"):
            self.state.value_label.setText("INIT")
        elif(state == "2"):
            self.state.value_label.setText("IDLE")
        elif(state == "3"):
            self.state.value_label.setText("BOOST")
        elif(state == "4"):
            self.state.value_label.setText("BURNOUT")
        elif(state == "5"):
            self.state.value_label.setText("COAST")
        elif (state == "6"):
            self.state.value_label.setText("APOGEE")
        elif(state == "7"):
            self.state.value_label.setText("DROGUE")
        elif(state == "8"):
            self.state.value_label.setText("MAIN")
        elif(state == "9"):
            self.state.value_label.setText("LAND")

        # Update ON/OFF label
        self.OnOrOff.setText("⚪🟢Receiver          ⚪🟢Signal")
        

    def closeEvent(self, event):
        """Handle window close event to clean up resources"""
        print("Shutting down...")
        if hasattr(self, 'serial_thread'):
            self.serial_thread.stop()