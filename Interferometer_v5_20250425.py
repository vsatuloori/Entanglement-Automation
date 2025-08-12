import yaml
import numpy as np
import time
import os
import matplotlib.pyplot as plt
import serial

from LADaq_v1 import LADAqBoard
from supportingfunctions import SupportFunc


class InterferometerParams:
    def __init__(self, params, baudrate=9600, timeout=0.5):
        self.com_port = params.get('com_port')
        self.IP = params.get('IP')
        self.baudrate = baudrate
        self.timeout = timeout
        self.device_connected = False
        self.device = self.connect()

        self.minvoltage = 0
        self.amplification = 2
        self.maxvoltage = 4.9

        self.IntName = params.get('IntName')
        self.Out1 = params.get('Out1')
        self.Out2 = params.get('Out2')
        self.Phase0Voltage = params.get('Phase0Voltage')
        self.Phase90Voltage = params.get('Phase90Voltage')
        self.Phase180Voltage = params.get('Phase180Voltage')
        self.Phase270Voltage = params.get('Phase270Voltage')
        self.Phase0power = params.get('Phase0power')
        self.Phase90power = params.get('Phase90power')
        self.Phase180power = params.get('Phase180power')
        self.Phase270power = params.get('Phase270power')
        self.V = params.get('V')
        self.VSrcCh = params.get('VSrcCh')

    def connect(self):
        if not self.device_connected or self.device==None: 
            print("Interferometer is not connected. Connecting now...")
            try:
                self.device = serial.Serial(port=self.com_port, baudrate=self.baudrate, timeout=self.timeout)
                self.device_connected = True
                print(f"INTERFEROMETER: {self.device}")
                print(f"Interferometer is connected at {self.com_port}")
                time.sleep(0.1)  # Give some time for the device to initialize
            except serial.SerialException as e:
                print(f"Failed to connect to Interferometer: {e}")
                self.device = None
        else:
            print("Interferometer is already connected.")
        return self.device
    
    def VsetCh(self, voltage, channel):
            try:
                if not self.device_connected:
                    print("Interferometer not initialized, attempting to connect...")
                    self.device = self.connect()

                if self.device is None:
                    raise RuntimeError("Failed to connect to the Interferometer or Interferometer not initialized")

                if voltage<=self.maxvoltage:
                    DACvoltage = voltage/self.amplification # This is to ensure that volt is in between 0 and self.maxvoltage/amplification factor
                    command = f"Vset {channel} {DACvoltage}\n"
                    start_time = time.time()
                    self._send_command(command, start_time)
                else:
                    print(f"Voltage set to channel {channel} is {voltage}V exceeds the maximum limit of {self.maxvoltage}V \n Not changing the previous voltage")  

            except Exception as e:
                print(e)
                print("Could not set the voltage")

    def _send_command(self, command, start_time):
        self.device.write(bytes(command, 'utf-8'))
        while True:
            data = self.device.readline()
            dataStr = data.decode().strip()
            if dataStr == "+ok":
                # print(f" Applied voltage {self.amplification*float(command.split()[2])}V, Command:{command.strip()}, running time: {time.time() - start_time:.5f}s")
                break
            else:
                print(f"Received data: {dataStr}")
                print(f"Data not received and running time: {time.time() - start_time:.5f} seconds")
                break

class Interferometer:
    def __init__(self, data=None):
        # self.filename = filename
        self.Interferometers = {}
        self.LADAqs = {}
        self.Connection = {}

        if data:
            self.load_data(data)
        else:
            print("No YAML file provided!")

    def load_data(self, data):
        # with open(filename, 'r') as yaml_file:
        #     data = yaml.safe_load(yaml_file)

        # Load interferometers
        for intf_name, params in data['Interferometers'].items():
            intf_obj = InterferometerParams(params)
            self.Interferometers[intf_name] = intf_obj
            setattr(self, intf_name, intf_obj)   # <<<<<< this is needed ✅

        # Load LADAqs
        # for ladaq_name, params in data['LADAqs'].items():
        #     self.LADAqs[ladaq_name] = {
        #         "com_port": params['com_port'],
        #         "device": None
        #     }

        # Load connection
        # self.Connection = data['Connection']

    def save_yaml(self, filename):
        """Update only Interferometers, LADAqs, and Connection sections back to YAML file, without touching other sections."""
        try:
            # Load existing YAML
            with open(filename, 'r') as file:
                data = yaml.safe_load(file)
        except Exception as e:
            print(f"Error loading existing YAML in save_yaml: {e}")
            data = {}

        # Update only LADAqs
        # data['LADAqs'] = {}
        # for ladaq_name, info in self.LADAqs.items():
        #     data['LADAqs'][ladaq_name] = {
        #         'com_port': info['com_port']
        #     }

        # Update Connection section
        data['Connection'] = self.Connection


        # Update only Interferometers
        data['Interferometers'] = {}
        for intf_name, params in self.Interferometers.items():
            data['Interferometers'][intf_name] = {
                'IntName': params.IntName,
                'Out1': params.Out1,
                'Out2': params.Out2,
                'Phase0Voltage': float(params.Phase0Voltage),
                'Phase90Voltage': float(params.Phase90Voltage),
                'Phase180Voltage': float(params.Phase180Voltage),
                'Phase270Voltage': float(params.Phase270Voltage),
                'Phase0power': float(params.Phase0power),
                'Phase90power': float(params.Phase90power),
                'Phase180power': float(params.Phase180power),
                'Phase270power': float(params.Phase270power),
                'V': float(params.V),
                'VSrcCh': params.VSrcCh
            }

        # Write back full YAML
        try:
            with open(filename, 'w') as file:
                yaml.dump(data, file, default_flow_style=False)
            # print(f"Interferometer settings updated successfully in {filename}")
        except Exception as e:
            print(f"Error saving YAML file: {e}")

    def connect_LADAqs(self):
        """Connect all LADAqs mentioned in YAML."""
        for ladaq_name, info in self.LADAqs.items():
            com_port = info['com_port']
            if com_port is None:
                print(f"Skipping connection for {ladaq_name} (com_port is None)")
                continue
            try:
                self.LADAqs[ladaq_name]['device'] = LADAqBoard(com_port)
                print(f"Connected to {ladaq_name} at {com_port}")
            except Exception as e:
                print(f"Failed to connect to {ladaq_name}: {e}")
   
    def get_LADAq_for_interferometer(self, interferometer_name):
        """Return LADAqBoard object for a given interferometer name or object."""
        # If it's an object, find the label
        if isinstance(interferometer_name, InterferometerParams):
            for name, obj in self.__dict__.items():
                if obj is interferometer_name:
                    interferometer_name = name
                    break

        for ladaq_name, intf_list in self.Connection.items():
            if interferometer_name in intf_list:
                return self.LADAqs[ladaq_name]['device']
        return None

    
    def SetIntPhase(self, interferometer_name, voltage_source= None, voltage= None, sleep_time = 0.1):
        """Set the voltage of the specified interferometer."""
        # If given an object, find its label
        if isinstance(interferometer_name, InterferometerParams):
            # Search for the label
            interferometer_label = None
            for name, obj in self.__dict__.items():
                if obj is interferometer_name:
                    interferometer_label = name
                    break
            if interferometer_label is None:
                raise ValueError("Interferometer object not recognized!")
        else:
            interferometer_label = interferometer_name

        interferometer = self.Interferometers[interferometer_label]

        if voltage_source is None:
            voltage_source = self.Interferometers[interferometer_name]

        try:
            Vmaxstep = 0.005

            if (voltage - interferometer.V) == 0:
                Vstep = 0
            else:
                Vstep = Vmaxstep * (voltage - interferometer.V) / abs(voltage - interferometer.V)

            # Gradually adjust voltage
            while abs(np.round(voltage - interferometer.V, 3)) > Vmaxstep:
                voltage_source.VsetCh(interferometer.V, interferometer.VSrcCh)
                print(f"Interferometer voltage is set to:{interferometer.V}")
                interferometer.V += Vstep
                time.sleep(sleep_time)

            interferometer.V = voltage
            voltage_source.VsetCh(voltage, interferometer.VSrcCh)
            time.sleep(sleep_time)
            self.save_yaml(self.filename)

            # print(f"Set voltage {interferometer.V}V on {interferometer_name}")
            voltageSetStatus = True

        except Exception as e:
            voltageSetStatus = False
            print(f"Could not set the voltage for {interferometer_name}: {e}")

        return voltageSetStatus

    # def feedbackSignal(self, Measurement_Inst, *args, **kwargs):
    #     try:
    #         if hasattr(Measurement_Inst, 'measure_power'):
    #             power_measured = np.mean(Measurement_Inst.measure_power(N=100))
    #             return power_measured
            
    #         elif hasattr(Measurement_Inst, 'getChannelCounts'):
    #             counts = float(Measurement_Inst.getChannelCounts(*args, **kwargs))
    #             return counts
            
    #         elif hasattr(Measurement_Inst, 'histogram_between_channels'):
    #             hist_data, bin_centers, selected_counts = Measurement_Inst.histogram_between_channels(*args, **kwargs)
    #             if selected_counts is not None:
    #                 return selected_counts
    #             else:
    #                 return np.sum(hist_data)

        # except Exception as e:
        #     print(f"Error during feedback signal measurement: {e}")
        #     return None
    
    def feedbackSignal(self, Measurement_Inst, *args, **kwargs):
        """
        Get feedback signal by calling a specific function on the measurement instrument.

        Expects 'measurement_function' to be provided in kwargs.
        """
        try:
            measurement_function = kwargs.pop('measurement_function', None)

            if measurement_function is None:
                raise ValueError("No 'measurement_function' specified in kwargs for feedbackSignal.")

            # Get the function from Measurement_Inst
            func = getattr(Measurement_Inst, measurement_function, None)

            if func is None:
                raise AttributeError(f"The Measurement_Inst does not have function '{measurement_function}'.")

            # Now handle based on measurement_function
            if measurement_function == 'histogram_between_channels':
                # Special case: histogram returns (hist_data, bin_centers, selected_counts)
                hist_data, bin_centers, selected_counts = func(*args, **kwargs)
                if selected_counts is not None:
                    return selected_counts
                else:
                    return np.sum(hist_data)

            elif measurement_function in ['measure_power', 'getChannelCountRates']:
                # For PowerMeter and Countrate, take mean if array/list is returned
                result = func(*args, **kwargs)
                if isinstance(result, (list, np.ndarray)):
                    return np.mean(result)
                else:
                    return float(result)

            elif measurement_function == 'getChannelCounts':
                # For getChannelCounts, return total counts (sum if multiple channels)
                result = func(*args)
                if isinstance(result, (list, np.ndarray)):
                    return np.sum(result)
                else:
                    return float(result)

            else:
                # Default: call normally
                result = func(*args, **kwargs)
                return float(result)

        except Exception as e:
            print(f"Error during feedback signal measurement: {e}")
            return None

        
    def sweep_voltage_and_measure_power(self, voltage_range, voltage_source, Interferometer_name, Measurement_Inst, step_size=0.02, *args, **kwargs):
        voltage_power_data = []

        plot_live = kwargs.pop('plot_live', False)
        sleep_time = kwargs.pop('sleep_time', 5)

        # Set up live plotting
        if plot_live:
            plt.ion()
            fig, ax = plt.subplots()
            line, = ax.plot([], [], 'bo-')
            ax.set_title(f"Voltage vs Feedback for {Interferometer_name.IntName}")
            ax.set_xlabel("Voltage (V)")
            ax.set_ylabel("Feedback Value")
            ax.grid(True)

        for voltage in np.arange(voltage_range[0], voltage_range[1], step_size):
            self.SetIntPhase(Interferometer_name, voltage_source, voltage, sleep_time)
            time.sleep(0.3)
            feedback_value = self.feedbackSignal(Measurement_Inst, *args, **kwargs)
            voltage_power_data.append((voltage, feedback_value))
            print(f"Voltage: {voltage:.3f}V, Feedback value: {feedback_value:.6f}")


            if plot_live:
                voltages, powers = zip(*voltage_power_data)
                line.set_data(voltages, powers)
                ax.relim()
                ax.autoscale_view()
                plt.pause(0.01)

        if plot_live:
            plt.ioff()
            plt.show()

        return voltage_power_data

    def CharaterizeInterferometers(self, SupportingFuncs, interferometer_list, voltage_range=(0, 5), voltage_source=None, Measurement_Inst=None, step_size=0.02, tolerance=0.01, UpdateVoltage=True, plotVoltagePower=True,  *args, **kwargs):
        """
        Optimize interferometer phase by sweeping through a voltage range.

        Parameters:
            SupportingFuncs: Supporting functions object (for finding extrema, etc.)
            interferometer_list: Single InterferometerParams object OR list of InterferometerParams objects
            voltage_range (tuple): Voltage range to sweep (start, stop)
            voltage_source: Voltage source object
            Measurement_Inst: Measurement instrument (power meter or time tagger)
            step_size (float): Step size for sweeping voltage
            tolerance (float): Tolerance used when finding extrema
            UpdateVoltage (bool): Whether to update the interferometer voltages
            plotVoltagePower (bool): Whether to plot voltage vs power
        """
        # If a single interferometer object is passed, wrap it in a list
        if not isinstance(interferometer_list, (list, tuple)):
            interferometer_list = [interferometer_list]

        for interferometer_obj in interferometer_list:
            try:
                # Find the label dynamically for printing
                interferometer_label = None
                for name, obj in self.__dict__.items():
                    if obj is interferometer_obj:
                        interferometer_label = name
                        break

                if interferometer_label is None:
                    interferometer_label = str(interferometer_obj)  # fallback to object print

                print(f"\n--- Starting optimization for {interferometer_label} ---")

                # Sweep voltage and measure power
                voltage_power_data = self.sweep_voltage_and_measure_power(
                    voltage_range=voltage_range,
                    step_size=step_size,
                    voltage_source=voltage_source,
                    Interferometer_name=interferometer_obj,
                    Measurement_Inst=Measurement_Inst,
                    *args, **kwargs
                )

                # Find the extrema
                # supportfunc = SupportingFuncs()  # Instantiate
                min_voltages, max_voltages = SupportingFuncs.find_extrema(voltage_power_data, tolerance)

                # Print results
                print(f"Results for {interferometer_label}:")
                print(f"Min Voltages: {min_voltages}")
                print(f"Max Voltages: {max_voltages}")

                # Update the interferometer voltages based on the extrema
                if UpdateVoltage:
                    self.UpdateIntVoltages(voltage_power_data, min_voltages, max_voltages, interferometer_obj)

                # Save after each optimization
                self.save_yaml(self.filename)

                # Plot the scan
                if plotVoltagePower:
                    self.plot_voltage_vs_power(voltage_power_data)

                print(f"--- Finished Characterization for {interferometer_label} ---\n")

            except Exception as e:
                print(f"Error during Characterization for {interferometer_label}: {e}")

    def UpdateIntVoltages(self, voltage_power_data, min_voltages, max_voltages, interferometer_obj):
        """Update the voltages for Phase0, Phase90, Phase180, and Phase270 based on the optimization."""
        try:
            voltages, powers = zip(*voltage_power_data)
            min_power = min(powers)
            max_power = max(powers)
            power_range = max_power - min_power
            avg_power = min_power + power_range / 2

            Phase0Voltage, Phase0power = [], []
            Phase90Voltage, Phase90power = [], []
            Phase180Voltage, Phase180power = [], []
            Phase270Voltage, Phase270power = [], []

            tolerance = 0.05  # Adjustable if needed

            # Find the label of the interferometer (IntE, IntF, etc.)
            interferometer_label = None
            for name, obj in self.__dict__.items():
                if obj is interferometer_obj:
                    interferometer_label = name
                    break

            if interferometer_label is None:
                raise ValueError("Interferometer object not found for UpdateIntVoltages.")
            
            for min_voltage in min_voltages:
                for max_voltage in max_voltages:
                    if min_voltage > max_voltage:
                        mid_voltage = (min_voltage + max_voltage) / 2
                        phase270_voltage = min_voltage + abs((min_voltage - max_voltage) / 2)

                        if mid_voltage and max_voltage < 4.8 and phase270_voltage < 4.8:
                            for voltage, power in voltage_power_data:
                                if np.isclose(voltage, max_voltage, atol=tolerance):
                                    Phase0Voltage.append(voltage)
                                    Phase0power.append(power)
                                if np.isclose(voltage, min_voltage, atol=tolerance):
                                    Phase180Voltage.append(voltage)
                                    Phase180power.append(power)

                                # Phase90Voltage.append(mid_voltage)
                                Phase90power.append(avg_power)

                                # Phase270Voltage.append(phase270_voltage)
                                Phase270power.append(avg_power)
                                
                                if np.isclose(power, avg_power, atol=tolerance * avg_power):
                                    if max_voltage < voltage < min_voltage:
                                        Phase90Voltage.append(voltage)
                                        # Phase90power.append(power)
                                    if min_voltage < voltage < phase270_voltage:
                                        Phase270Voltage.append(voltage)
                                        # Phase270power.append(power)

                            def mean_if_not_empty(values, label):
                                if values:
                                    return np.mean(values)
                                else:
                                    print(f"{label} is empty")
                                    return 0

                            # Save back into the interferometer object
                            interferometer_obj.Phase0Voltage = mean_if_not_empty(Phase0Voltage, 'Phase0Voltage')
                            interferometer_obj.Phase0power = mean_if_not_empty(Phase0power, 'Phase0power')

                            interferometer_obj.Phase90Voltage = mean_if_not_empty(Phase90Voltage, 'Phase90Voltage')
                            interferometer_obj.Phase90power = mean_if_not_empty(Phase90power, 'Phase90power')

                            interferometer_obj.Phase180Voltage = mean_if_not_empty(Phase180Voltage, 'Phase180Voltage')
                            interferometer_obj.Phase180power = mean_if_not_empty(Phase180power, 'Phase180power')

                            interferometer_obj.Phase270Voltage = mean_if_not_empty(Phase270Voltage, 'Phase270Voltage')
                            interferometer_obj.Phase270power = mean_if_not_empty(Phase270power, 'Phase270power')

                            print(f"Updated Voltages for {interferometer_label}:")
                            print(f"Phase0: {interferometer_obj.Phase0Voltage}")
                            print(f"Phase90: {interferometer_obj.Phase90Voltage}")
                            print(f"Phase180: {interferometer_obj.Phase180Voltage}")
                            print(f"Phase270: {interferometer_obj.Phase270Voltage}")
                            return  # Exit after updating

            # If no valid points found
            print(f"No suitable voltage combination found for {interferometer_label}. Setting defaults.")
            interferometer_obj.Phase0Voltage = 0.1
            interferometer_obj.Phase90Voltage = 0.1
            interferometer_obj.Phase180Voltage = 0.1
            interferometer_obj.Phase270Voltage = 0.1

        except Exception as e:
            print(f"Error during UpdateIntVoltages: {e}")

    def _gradient_descent(
        self,
        initial_voltage,
        target_power,
        mode,
        voltage_source,
        interferometer_obj,
        Measurement_Inst,
        measurement_function,
        initial_learning_rate,
        tolerance,
        power_tolerance,
        max_iterations,
        min_step_size,
        *args,
        **kwargs
        ):
        
        """
        Slope‐based gradient descent engine.
        mode: 'target' (drive to numeric target_power),
            'minimize' (drive power down),
            'maximize' (drive power up).
        Returns the final voltage.
        """
        import numpy as np, time

        # unpack Phase0/180 for bounds
        V0, P0     = interferometer_obj.Phase0Voltage,  interferometer_obj.Phase0power
        V180, P180 = interferometer_obj.Phase180Voltage, interferometer_obj.Phase180power
        Vmin = min(V0, V180) - 0.25
        Vmax = max(V0, V180) + 0.5

        curV = float(np.clip(initial_voltage, Vmin, Vmax))
        lr   = initial_learning_rate
        delta = 0.05#min_step_size

        kwargs.setdefault("measurement_function", measurement_function)

        # helper to measure stabilized power
        def measure_stable():
            while True:
                p1 = self.feedbackSignal(Measurement_Inst, *args, **kwargs)
                time.sleep(1)
                p2 = self.feedbackSignal(Measurement_Inst, *args, **kwargs)
                if p1 and p1>0 and abs(p2-p1)/p1 < 0.05:
                    return p2

        P_prev = measure_stable()

        for it in range(1, max_iterations+1):
            # 1) slope estimate
            v_test = float(np.clip(curV + delta, Vmin, Vmax))
            self.SetIntPhase(interferometer_obj, voltage_source, v_test)
            P_test = measure_stable()
            slope = (P_test - P_prev)/(v_test - curV) if abs(v_test - curV)>1e-8 else 0.0

            # 2) compute raw step
            if mode == 'minimum':
                raw_step = - lr * slope
            elif mode == 'maximum':
                raw_step =   lr * slope
            else:  # numeric target
                err_rel = (P_prev - target_power) / target_power
                if abs(slope) > 1e-8:
                    raw_step = (target_power - P_prev)/slope
                else:
                    raw_step = - err_rel * lr

            # 3) enforce minimum step size
            if abs(raw_step) < min_step_size:
                step = np.sign(raw_step or slope) * min_step_size
            else:
                step = raw_step

            # 4) propose & clamp
            proposed = curV + step
            newV     = float(np.clip(proposed, Vmin, Vmax))
            print(f"[GD {it}] proposed={proposed:.4f}, clamped→{newV:.4f}, slope={slope:.4e}")

            # 5) apply & measure new
            self.SetIntPhase(interferometer_obj, voltage_source, newV)
            P_new = measure_stable()

            # 6) decide accept/reject
            if mode == 'minimum':
                improved = (P_new < P_prev)
                new_err_rel = P_new - P_prev
            elif mode == 'maximum':
                improved = (P_new > P_prev)
            else:
                new_err_rel = (P_new - target_power)/target_power
                improved = (abs(new_err_rel) < abs(err_rel))

            if improved:
                curV   = newV
                P_prev = P_new
                print(f"[GD {it}] improved voltage:{curV} V, power:{P_prev} ")
                if mode == 'target':
                    err_rel = new_err_rel
            else:
                print(f"[GD {it}] no improvement, halving lr")
                lr *= 0.5

            # 7) convergence?
            # if mode == 'target' and (abs(err_rel) < tolerance or (abs(err_rel)*target_power < power_tolerance)) :
            #     print(f"[GD] converged at {curV:.4f} V (rel_err={err_rel*100:.2f}%)")
            #     return curV
            # if mode is ('minimum','maximum') and (abs(err_rel) < tolerance or (abs(err_rel)*target_power < power_tolerance)):
            #     print(f"[GD] extremum found at {curV:.4f} V, P={P_prev:.6f}")
            #     return curV

            if (abs(err_rel) < tolerance or (abs(err_rel)*target_power < power_tolerance)):
                print(f"[GD] converged at {curV:.4f} V (rel_err={err_rel*100:.2f}%)")
                return curV



        print(f"[GD] max_iters reached; V={curV:.4f}, P={P_prev:.6f}")
        return curV


    def OptimizeIntPhase(
        self,
        target_power,
        voltage_source,
        interferometer_obj,
        Measurement_Inst=None,
        approx_voltage=None,
        initial_learning_rate=0.01,
        tolerance=0.01,
        power_tolerance = 1e-5, 
        max_iterations=100,
        min_step_size=0.005,
        *args,
        **kwargs
    ):
        """
        Dispatch to gradient‐descent for:
        - numeric target_power (mode='target')
        - 'minimum'       (mode='minimize')
        - 'maximum'/'maximize' (mode='maximize')
        """
        # pick mode
        if isinstance(target_power, str) and target_power.lower() in ('minimum','maximum'):
            mode = target_power.lower()
            numeric_target = None
        else:
            mode = 'target'
            numeric_target = float(target_power)

        # initial voltage
        if approx_voltage is not None:
                    initV = approx_voltage
        else:
            if mode == 'minimum':
                # pick the voltage at the lower‐power fringe
                if interferometer_obj.Phase0power <= interferometer_obj.Phase180power:
                    initV = interferometer_obj.Phase0Voltage
                else:
                    initV = interferometer_obj.Phase180Voltage

            elif mode == 'maximum':
                # pick the voltage at the higher‐power fringe
                if interferometer_obj.Phase0power >= interferometer_obj.Phase180power:
                    initV = interferometer_obj.Phase0Voltage
                else:
                    initV = interferometer_obj.Phase180Voltage

            else:
                # for numeric targets, start in the middle
                initV = 0.5 * (
                    interferometer_obj.Phase0Voltage 
                    + interferometer_obj.Phase180Voltage
                )

        # call GD engine
        return self._gradient_descent(
            initial_voltage=initV,
            target_power=numeric_target,
            mode=mode,
            voltage_source=voltage_source,
            interferometer_obj=interferometer_obj,
            Measurement_Inst=Measurement_Inst,
            measurement_function=kwargs.pop('measurement_function', 'measure_power'),
            initial_learning_rate=initial_learning_rate,
            tolerance=tolerance,
            power_tolerance = power_tolerance,
            max_iterations=max_iterations,
            min_step_size=min_step_size,
            *args,
            **kwargs
        )

    def calculate_visibility(self, interferometer_name):
        """
        Calculate visibility for the given interferometer.
        
        Visibility = (Phase0power - Phase180power) / (Phase0power + Phase180power)
        
        Parameters:
            interferometer_name: InterferometerParams object OR string name like 'IntE'
        
        Returns:
            visibility (float)
        """
        # Handle if an object is passed instead of string
        if isinstance(interferometer_name, InterferometerParams):
            # Find the label (e.g., 'IntE')
            for name, obj in self.__dict__.items():
                if obj is interferometer_name:
                    interferometer_name = name
                    break
            else:
                raise ValueError("Provided interferometer object not found in Interferometer class.")

        # Now interferometer_name is string
        if interferometer_name not in self.Interferometers:
            raise ValueError(f"Interferometer {interferometer_name} not found.")

        interferometer = self.Interferometers[interferometer_name]

        try:
            phase0_power = interferometer.Phase0power
            phase180_power = interferometer.Phase180power

            visibility = (phase0_power - phase180_power) / (phase0_power + phase180_power)
            print(f"Visibility for {interferometer_name}: {visibility:.4f}")
            return visibility

        except Exception as e:
            print(f"Error calculating visibility for {interferometer_name}: {e}")
            return None


    def plot_voltage_vs_power(self, voltage_power_data):
        """Plot voltage vs. power."""
        voltages, powers = zip(*voltage_power_data)
        plt.figure()
        plt.plot(voltages, powers, marker='o')
        plt.title('Voltage vs Power')
        plt.xlabel('Voltage (V)')
        plt.ylabel('Power (a.u.)')
        plt.grid(True)
        plt.show()

    def InterferometerRepeatabilityTest(
        self,
        interferometer_obj,
        voltage_source,
        Measurement_Inst,
        cycles=1,
        measurement_function="measure_power",
        wait_time=0.5,
        *args,
        **kwargs
    ):
        """
        Cycle between Phase0Voltage and Phase180Voltage to test repeatability.
        
        For each cycle:
        1. Set to Phase0Voltage, wait, measure power.
        2. Set to Phase180Voltage, wait, measure power.
        3. Return to Phase0Voltage, wait, measure power again.
        
        Parametersinterferometer_name
        ----------
        interferometer_obj : InterferometerParams
            The interferometer to test (e.g., self.IntE).
        voltage_source : object
            The LADAqBoard channel for setting voltages.
        Measurement_Inst : object
            The measurement instrument (power meter, time tagger, etc.).
        cycles : int, default=1
            Number of back-and-forth cycles to perform.
        measurement_function : str, default="measure_power"
            Name of the method on Measurement_Inst to call for feedbackSignal.
        wait_time : float, default=0.5
            Seconds to wait after setting each voltage before measuring.
        *args, **kwargs
            Additional arguments (e.g., N=30) passed to feedbackSignal.
        
        Returns
        -------
        list of dict
            One entry per cycle with keys:
            'cycle', 'P0_initial', 'P180', 'P0_return'
        """
        import time
        
        # ensure feedbackSignal knows which method to call
        kwargs.setdefault("measurement_function", measurement_function)
        
        results = []
        for cycle in range(1, cycles + 1):
            # 1) Phase0 initial
            self.SetIntPhase(interferometer_obj, voltage_source, interferometer_obj.Phase0Voltage)
            time.sleep(wait_time)
            P0_initial = self.feedbackSignal(Measurement_Inst, *args, **kwargs)
            
            # 2) Phase180
            self.SetIntPhase(interferometer_obj, voltage_source, interferometer_obj.Phase180Voltage)
            time.sleep(wait_time)
            P180 = self.feedbackSignal(Measurement_Inst, *args, **kwargs)
            
            # 3) Return to Phase0
            self.SetIntPhase(interferometer_obj, voltage_source, interferometer_obj.Phase0Voltage)
            time.sleep(wait_time)
            P0_return = self.feedbackSignal(Measurement_Inst, *args, **kwargs)
            
            results.append({
                "cycle": cycle,
                "P0_initial": P0_initial,
                "P180": P180,
                "P0_return": P0_return
            })
            
            print(
                f"[Cycle {cycle}] "
                f"P0_initial={P0_initial:.6f}, "
                f"P180={P180:.6f}, "
                f"P0_return={P0_return:.6f}"
            )
        
        return results


    def monitor_stability(
        self,
        interferometer_obj,
        power_meter,
        voltage=None,
        duration_minutes=60,
        interval_seconds=5,
        N=100,
        save_data=True,
        plot_live=True
    ):
        """
        Monitor interferometer stability by locking to a fixed phase voltage and logging power.

        Parameters
        ----------
        interferometer_obj : InterferometerParams
            The interferometer to monitor (e.g., self.IntD).
        power_meter : PowerMeter object
            Instance with a measure_power(N=...) method.
        voltage : float
            Voltage to set and hold constant during monitoring.
        duration_minutes : int
            Duration for monitoring (in minutes).
        interval_seconds : int
            Time between successive power readings (in seconds).
        N : int
            Number of power samples to average per reading.
        save_data : bool
            Save time and power arrays to an .npz file if True.
        plot_live : bool
            Show a live plot during the measurement.
        """
        import numpy as np
        import matplotlib.pyplot as plt
        import time
        from datetime import datetime

        # Set voltage
        voltage_source = self.get_LADAq_for_interferometer(interferometer_obj)
        if voltage is not None:
          self.SetIntPhase(interferometer_obj, voltage_source=voltage_source, voltage=voltage)
          print(f"\n--- Starting stability monitoring for {interferometer_obj.IntName} at {voltage:.2f} V ---")
        else:
          print(f"\n--- Starting stability monitoring for {interferometer_obj.IntName} at previously applied voltage ---")

        times = []
        powers = []

        if plot_live:
            plt.ion()
            fig, ax = plt.subplots()
            power_line, = ax.plot([], [], 'b.-', label="Power (dBm)")
            mean_line, = ax.plot([], [], 'g--', label="Mean")
            std_upper, = ax.plot([], [], 'r--', label="Mean ± Std")
            std_lower, = ax.plot([], [], 'r--')
            ax.set_title(f"Stability of {interferometer_obj.IntName}")
            ax.set_xlabel("Time (min)")
            ax.set_ylabel("Power (dBm)")
            ax.grid(True)
            ax.legend()

        start_time = time.time()
        end_time = start_time + duration_minutes * 60

        try:
            while time.time() < end_time:
                elapsed_min = (time.time() - start_time) / 60
                power = np.mean(power_meter.measure_power(N=N))/1e-3 # Converting W to mW

                times.append(elapsed_min)
                powers.append(power)

                mean_p = np.mean(powers)
                std_p = np.std(powers)

                if plot_live:
                    power_line.set_data(times, powers)
                    mean_line.set_data(times, [mean_p] * len(times))
                    std_upper.set_data(times, [mean_p + std_p] * len(times))
                    std_lower.set_data(times, [mean_p - std_p] * len(times))
                    ax.relim()
                    ax.autoscale_view()
                    plt.pause(0.01)

                try:
                    print(f"[{elapsed_min:.2f} min] Power: {power:.3f} mW | Mean: {mean_p:.3f} mW| Std: {std_p:.6f} mW")
                except Exception as e:
                    print(f"[{elapsed_min:.2f} min] Power reading error: {e}")
                time.sleep(interval_seconds)

        except KeyboardInterrupt:
            print("Monitoring interrupted.")

        if plot_live:
            plt.ioff()
            plt.show()

        print(f"\n--- Summary for {interferometer_obj.IntName} ---")
        print(f"Mean Power: {np.mean(powers):.3f} dBm")
        print(f"Std Dev:    {np.std(powers):.3f} dB")
        print(f"Drift:      {powers[-1] - powers[0]:.3f} dB")

        if save_data:
            filename = f"stability_{interferometer_obj.IntName}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.npz"
            np.savez(filename, time=np.array(times), power=np.array(powers))
            print(f"Data saved to {filename}")


if __name__ == "__main__":
    from ThorlabsPMFunctions import PowerMeter
    from supportingfunctions import SupportFunc

    # Initialize
    # interferometer = Interferometer(filename='IntParams.yaml')
    interferometer = Interferometer(filename='IntParams.yaml')

    # # Connect all LADAQs
    interferometer.connect_LADAqs()

    # # Connect PowerMeter
    # pm = PowerMeter('USB0::0x1313::0x8078::P0023583::INSTR')
    # # print(f"voltage_source:{interferometer.get_LADAq_for_interferometer(interferometer.IntE)}")

    interferometer_obj = interferometer.IntE
    interferometer.SetIntPhase(interferometer_name=interferometer_obj, voltage=interferometer_obj.Phase90Voltage)
    # # interferometer.SetIntPhase(interferometer_name=interferometer.IntD, voltage=2.8)
    # print(f"Measured_power: {pm.measure_power(N=10)}")


    # Characterize a single interferometer (e.g., IntE)
    # interferometer.CharaterizeInterferometers(
    #     SupportingFuncs=SupportFunc(),
    #     interferometer_list=[interferometer.IntE],   # <<<< clean access ✅
    #     voltage_range=[2.75, 3.8],
    #     voltage_source=interferometer.get_LADAq_for_interferometer('IntE'),
    #     Measurement_Inst=pm,
    #     step_size=0.005,
    #     tolerance=0.05,
    #     UpdateVoltage=True,
    #     plotVoltagePower=True,
    #     measurement_function = "measure_power",
    #     plot_live = True,
    #     sleep_time = 1
    # )

    # Characterize multiple interferometers together (e.g., IntE and IntF)
    # interferometer.CharaterizeInterferometers(
    #     SupportingFuncs=SupportFunc,
    #     interferometer_list=[interferometer.IntE, interferometer.IntF],
    #     voltage_range=(2, 5),
    #     voltage_source=None,
    #     Measurement_Inst=pm,
    #     step_size=0.05,
    #     tolerance=0.01,
    #     UpdateVoltage=True,
    #     plotVoltagePower=False
    # )
    # vis = interferometer.calculate_visibility(interferometer.IntE)

    # # Using Time tagger for optimizing interferometer
    # from TimeTaggerFunctions import TT  # Import your TT class

    # # Initialize TimeTagger (TT)
    # tt = TT(filename="TimeTaggerConfig.yaml")  # Use your YAML config for TT
    # time.sleep(0.5)
    # tt.initTTChs()  # Initialize channels
    # Measurement_Inst = tt 

    # interferometer.CharaterizeInterferometers(
    #     SupportingFuncs=SupportFunc(),
    #     interferometer_list=[interferometer.IntF],
    #     voltage_range=(2, 5),
    #     voltage_source=interferometer.get_LADAq_for_interferometer('IntF'),
    #     Measurement_Inst=Measurement_Inst,  # This is your TimeTaggerFunctions object
    #     step_size=0.01,
    #     tolerance=0.05,
    #     UpdateVoltage=True,
    #     plotVoltagePower=True,
    #     measurement_function='histogram_between_channels',
    #     ch_click=3,
    #     ch_start=5,
    #     measurement_time=1,
    #     binwidth_ps=1,
    #     n_bins=1000,
    #     end_bins=[270, 310],
    #     plotHistogram = True
    # )
    # vis = interferometer.calculate_visibility(interferometer.IntE)
    # vis = interferometer.calculate_visibility(interferometer.IntF)



    ##### ===== Optimizing interferometers to a target power ===== #####
    # intferferometer_obj = interferometer.IntE
    # target_power = interferometer_obj.Phase180power

    # optimal_voltage = interferometer.OptimizeIntPhase(
    #     target_power="maximum",
    #     voltage_source=interferometer.get_LADAq_for_interferometer(intferferometer_obj),
    #     interferometer_obj=intferferometer_obj,
    #     Measurement_Inst=pm,
    #     measurement_function='measure_power',  # tells feedbackSignal which method to call
    #     N=100,                                   # passed through to measure_power(N=...)
    #     initial_learning_rate=0.1,
    #     tolerance=0.03,
    #     power_tolerance = 1e-5,
    #     max_iterations=50
    # )

    # print(f"Reached {target_power:.3f} at V = {optimal_voltage:.4f} V")


    #==================================================================#

    ## Stability checking of the interferometer 

    # interferometer.SetIntPhase(interferometer_name=interferometer_obj, voltage=interferometer_obj.Phase90Voltage, sleep_time = 0.5)
    # time.sleep(30)
    # interferometer.monitor_stability(
    #     interferometer_obj=interferometer.IntE,
    #     power_meter=pm,
    #     voltage=None,
    #     duration_minutes=1,
    #     interval_seconds=0.1,
    #     N=100,
    #     save_data=True,
    #     plot_live=True  # <- enable or disable live plot
    # )


    ### Interferometer repeatability test ###
    # inside your main script


    # results = interferometer.InterferometerRepeatabilityTest(
    #     interferometer_obj=interferometer.IntE,
    #     voltage_source=interferometer.get_LADAq_for_interferometer('IntE'),
    #     Measurement_Inst=pm,
    #     cycles=5,
    #     measurement_function="measure_power",
    #     N=30,
    #     wait_time=1.0
    # )


    # Save updated parameters
    # interferometer.save_yaml(interferometer.filename)

