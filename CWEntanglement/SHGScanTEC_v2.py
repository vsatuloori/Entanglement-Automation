import time
import serial
import numpy as np
import matplotlib.pyplot as plt
from ThorlabsPMFunctions import PowerMeter
from supportingfunctions import SupportFunc
import yaml

class SHGController:
    def __init__(self, filename = None, com_port = None, baudrate=9600, timeout=0.5, plotData=False):
        """
        Initialize SHG Voltage Controller.

        Args:
            voltage_source: Instance like LADAqBoard controlling voltage output
            plotData: If True, plot after scan
        """
        self.waveguides = []
        if (filename):
            with open(filename, 'r') as yaml_file:
                settings = yaml.safe_load(yaml_file)
            self.user = None
            for name in ["Alice", "Bob", "Charlie"]:
                if name in settings and "SHGController" in settings[name]:
                    shg_params = settings[name]["SHGController"]
                    self.com_port = shg_params.get("com_port", com_port)
                    self.baudrate = shg_params.get("baudrate", baudrate)
                    self.timeout = shg_params.get("timeout", timeout)
                    # You can set other parameters here as needed
                     # Remove this if you want to process all found controllers
                    if "Wgs" in settings[name]:
                        for wg in settings[name]["Wgs"]:
                            self.waveguides.append(
                                self.WaveGuide(
                                    settings[name]["Wgs"][wg]["id"],
                                    settings[name]["Wgs"][wg]['min_temp'],
                                    settings[name]["Wgs"][wg]['max_temp'],
                                    settings[name]["Wgs"][wg]['curr_temp'],
                                    settings[name]["Wgs"][wg]['beta'],
                                    settings[name]["Wgs"][wg]['VsrcCh']))
                    break

        else:
            ## LADAq params
            self.com_port = com_port
            self.baudrate = baudrate
            self.timeout = timeout

        self.minvoltage = 0
        self.amplification = 1
        self.maxvoltage = 2.5#
        self.device_connected = False
        
        ### SHG params ###   
        self.plotData = plotData
        self.Supportfunctions = SupportFunc()
        self.last_voltage = 0  # Start with 0V internally

        self.device = self.connect()

    def connect(self):
        # if not self.is_device_connected():
        if not self.device_connected or self.device==None: 
            print("SHG TEC Controller is not connected. Connecting now...")
            try:
                self.device = serial.Serial(port=self.com_port, baudrate=self.baudrate, timeout=self.timeout)
                self.device_connected = True
                print("SHG TEC Controller is connected")
                time.sleep(0.1)  # Give some time for the device to initialize
            except serial.SerialException as e:
                print(f"Failed to connect to SHG TEC Controller: {e}")
                self.device = None
        else:
            print("SHG TEC Controller is already connected.")
        return self.device

    def send_command(self, command, expect_response=True):
        """
        Send command over serial and optionally read the response.

        Parameters:
            command (str): The command string to send.
            expect_response (bool): If True, read response.

        Returns:
            str or None: Response string if expected, else None.
        """
        self.device.write((command + '\n').encode())
        if expect_response:
            response = self.device.readline().decode().strip()
            print(f"Response: {response}")
            # if response == "+ok":
            #     print(f"Temperature is set")
            #     break
            # else:
            #     print(f"Could not set the temperature. Received response: {response}")
                

    def SetTemperature(self, channel, temperature):
        command = f"SetT {channel} {temperature:.2f}"
        return self.send_command(command)

    def SetImax(self, channel, current):
        command = f"SetImax {channel} {current:.3f}"
        return self.send_command(command)

    def ReadVoltage(self, channel):
        command = f"ReadVolt {channel}"
        response = self.send_command(command)
        try:
            return float(response)
        except (ValueError, TypeError):
            print("Invalid voltage response:", response)
            return None

    def ReadCurrent(self, channel):
        command = f"ReadCurr {channel}"
        response = self.send_command(command)
        try:
            return float(response)
        except (ValueError, TypeError):
            print("Invalid current response:", response)
            return None

    def ramp_voltage(target_voltage, current_voltage, step_size=0.1, delay = 1):
        
        if target_voltage < current_voltage:
            step_size = - step_size 


        pass
        
    def SHGSetVoltage(self, target_voltage, step_size=0.01, delay=0.1, channel=0):
        """
        Smoothly ramp from last set voltage to target voltage.

        Args:
            target_voltage: Final voltage to reach
            step_size: Voltage step size
            delay: Time delay between steps
            channel: Channel number (default 0)
        Returns:
            final_voltage: The voltage that was reached
        """

        self.SetTemperature(channel, target_voltage)

        # if self.device is None:
        #     raise ValueError("SHG TEC Controller is not connected!")

        # if target_voltage >= self.last_voltage:
        #     voltages = np.arange(self.last_voltage, target_voltage + step_size, step_size)
        # else:
        #     voltages = np.arange(self.last_voltage, target_voltage - step_size, -step_size)

        # for voltage in voltages:
        #     voltage_to_set = min(max(voltage, 0), 5)  # Clamp between 0V and 5V
        #     self.SetTemperature(voltage_to_set, channel)
        #     time.sleep(delay)

        # print(f"Voltage successfully ramped from {self.last_voltage:.3f} V to {target_voltage:.3f} V on channel {channel}")

        # self.last_voltage = target_voltage  # Update memory
        # return self.last_voltage

    def SHGScan(self, measurement_inst, temp_range=(25, 60), step_size=0.5, max_SHG_temp=80, stabilization_time=5.0, channel=0):
        """
        Perform an SHG scan.

        Args:
            measurement_inst: Instance like PowerMeter to measure power
            temp_range: Tuple (start_temp, end_temp)
            step_size: temp step size for scan
            max_SHG_temp: Maximum allowed temp
            stabilization_time: Wait time after setting each temp
            channel: Channel to apply temp (default 0)

        Returns:
            temp_power_data: List of (temp, measured_power) tuples
        """
        start_temp, end_temp = temp_range

        # Apply max temp limit
        if max_SHG_temp is not None:
            end_temp = min(end_temp, max_SHG_temp)
        
        if start_temp > end_temp:
            step_size = -step_size

        temps = np.arange(start_temp, end_temp, step_size)
        temp_power_data = []

        for temp in temps:
            # Smooth ramp to the temp
            self.SetTemperature(
                temperature=temp,
                channel=channel
            )
            time.sleep(stabilization_time)

            measured_power = measurement_inst.measure_power()
            temp_power_data.append((temp, measured_power))

            print(f"temp: {temp} C, Measured Power: {measured_power} mW")

        # Plot if enabled
        if self.plotData:
            self.Supportfunctions.plot_voltage_vs_power(temp_power_data, figSaveName="SHG_scan.png")

        return temp_power_data
    
    class WaveGuide:
        def __init__(self, id, min_temp, max_temp, curr_temp, beta, VsrcCh):
            self.id = id
            self.min_temp = min_temp
            self.max_temp = max_temp
            self.curr_temp = curr_temp
            self.beta = beta
            self.VsrcCh = VsrcCh

if __name__ == "__main__":

    wg_3822991_channel = 0
    wg_3822990_channel = 1 # Using this waveguide for CW entanglement

    wg_3822990_optimal_temp = 46 # in degree celcius

    # Initialize Thorlabs Power Meter
    # power_meter = PowerMeter(power_meter_id='USB0::0x1313::0x8078::P0023583::INSTR', wavelength=770)
    
    # Create an SHG controller instance
    SHGcontroller = SHGController(
        filename = "SHGScanTEC_v2.yaml"
    )

    # # Run the scan

    # SHGcontroller.SetTemperature(channel=wg_3822990_channel, temperature=44.5)
    # time.sleep(10)
    wg1 = SHGcontroller.waveguides[0]
    
    SHGcontroller.SetTemperature(channel=wg1.VsrcCh, temperature=wg1.curr_temp)
    # time.sleep(10)
    # temp_power_data = SHGcontroller.SHGScan(
    #     measurement_inst=power_meter,
    #     temp_range=(25, 60),
    #     channel = wg_3822990_channel,
    #     step_size=1,
    #     max_SHG_temp=80,
    #     stabilization_time=5
    # )

    # plt.figure()
    # temps, powers = zip(*temp_power_data)
    # flat_powers = powers

    # # Create the plot
    # plt.figure()
    # plt.plot(temps, flat_powers, marker='o')
    # plt.title('Temperature vs Power')
    # plt.xlabel('Temperature (\u00b0C)')
    # plt.ylabel('Power (W)')
    # plt.grid(True)
    # plt.show()

    # voltage_1 = 5
    # voltage_2 = 2.6
    # for voltage in np.arange(voltage_1, voltage_2, -0.1):
    #     SHGcontroller.SHGSetVoltage(target_voltage = voltage, step_size=0.01, delay=0.1, channel=3)
    #     print(f"voltage:{voltage}, power:{np.mean(power_meter.measure_power(N=100))}")
    #     time.sleep(2)
    # SHGcontroller.SetTemperature(target_voltage = 1.5, step_size=0.01, delay=0.1, channel=3)
    # SHGcontroller.SetTemperature(channel=wg_3822990_channel, temperature=40)

    # print("SHG scan complete.")
