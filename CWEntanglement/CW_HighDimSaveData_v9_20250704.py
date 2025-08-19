import os
import time
import yaml
import math
import TimeTagger
import datetime
import shutil
from time import sleep
import numpy as np
from LADaq_v1 import LADAqBoard
from Interferometer_v2_20250425 import Interferometer  # Import the Interferometer class
from supportingfunctions import GenerateUniqueFilename
from TimeTaggerFunctions import TT
from ThorlabsPMFunctions import PowerMeter  # Import PowerMeter class
import matplotlib.pyplot as plt
from supportingfunctions import SupportFunc
from OpticalSwitch import OpticalSwitchDriver   
import yoAQ2212 as yoko


class HighDim:

    def __init__(self):
        self.SuFunc = SupportFunc()
        self.yamlfile = "CW_HighDimExptSettings_20250704.yaml"
        
        # Load YAML once
        with open(self.yamlfile, 'r') as f:
            yaml_data = yaml.safe_load(f)

        # Extract important sections
        self.channel_mappings = yaml_data.get('ChannelMappings', {})
        self.interferometer_settings = yaml_data.get('InterferometerSettings', {})
        self.timetagger_channels = yaml_data.get('TimeTagger', {}).get('Channels', {})


        # Initialize Timetagger
        self.TT = TT(filename=self.yamlfile)

        # Initialize Interferometer
        self.interferometer = Interferometer(filename=self.yamlfile)

        # Dynamically load all interferometers
        self.interferometer_list = list(self.interferometer.Interferometers.values())
        self.interferometer_dict = {intf.IntName: intf for intf in self.interferometer_list}

        # Generate filenames
        bases = ['ZZ', 'XX', 'ZX', 'XZ', 'YY', 'ZY', 'YZ']
        basefilename = 'data1'
        self.filename_generator = GenerateUniqueFilename(basefilename, bases)
        filenames = self.filename_generator.get_filenames()
        for basis, full_filename in filenames.items():
            setattr(self, basis, type(basis, (), {'basisId': basis, 'filename': full_filename})())
            
    def initDevices(self):
        try:
            # Initialize the Time Tagger channels
            self.TT.initTTChs()
            print("Timetagger is initialized")
        except Exception as e:
            print(f"Error in initializing Timetagger. Error: {e}")

        ## I am going to take measurement of single dataset myself. so not connecting
        # try:
        #     self.LADAqs = self.interferometer.LADAqs  # Copy LADAqs dictionary from interferometer
        #     for ladaq_name, info in self.LADAqs.items():
        #         com_port = info['com_port']
        #         if com_port is None:
        #             print(f"Skipping connection for {ladaq_name} (com_port is None)")
        #             continue
        #         try:
        #             self.LADAqs[ladaq_name]['device'] = LADAqBoard(com_port)
        #             print(f"Connected to {ladaq_name} at {com_port}")
        #         except Exception as e:
        #             print(f"Failed to connect to {ladaq_name}: {e}")
        # except Exception as e:
        #     print(f"Error in initializing LADAqs. Error: {e}")

        from types import SimpleNamespace
        try:
            with open(self.yamlfile, 'r') as file:
                yaml_data = yaml.safe_load(file)

            powermeter_settings = yaml_data.get('Powermeters', {})
            self.Powermeters = SimpleNamespace()

            for pm_name, params in powermeter_settings.items():
                resource = params.get('power_meter_id', None)
                wavelength = params.get('wavelength', None)

                if resource is not None and wavelength is not None:
                    try:
                        setattr(self.Powermeters, pm_name, PowerMeter(power_meter_id=resource, wavelength=wavelength))
                        print(f"Powermeter {pm_name} connected successfully with resource {resource} at {wavelength} nm")
                    except Exception as e:
                        print(f"Failed to connect Powermeter {pm_name}: {e}")
                else:
                    print(f"Skipping {pm_name} due to missing parameters.")

        except Exception as e:
            print(f"Error in initializing Powermeters. Error: {e}")

        try:
            # Load the OSW part from YAML manually
            with open(self.yamlfile, 'r') as file:
                yaml_data = yaml.safe_load(file)

            OSW_settings = yaml_data.get('OSW', {})
            com_port = OSW_settings.get('com_port', None)
            print(f"Loaded com_port: {com_port}, type: {type(com_port)}")

            if com_port is not None:
                self.OSW = OpticalSwitchDriver(com_port, filename=self.yamlfile)
                print(f"OSW connected successfully at {com_port}")
            else:
                print("No valid OSW com_port specified. OSW driver not initialized.")

        except Exception as e:
            print(f"Error initializing OSW driver. e: {e}")

        try:
            self.yokoframe = yoko.yoAQ2212_frame_controller(ipAddress="10.7.0.30", port=50000, timeout=5)
            print(f"Yokoframe is connected successfully: {self.yokoframe}")
        except Exception as e:
            print(f"Error in initializing Yokoframe. e: {e}")
            
    def disconnectDevices(self):
        try:
            TimeTagger.freeTimeTagger(self.TT.Inst)
            print("TT is disconnected")
        except:
            print("Could not disconnect TT")
        # self.IntVSrc.disconnect()
        try:
            self.SaveHighDimSettings()
            print(f" Experiment settings are saved")
        except Exception as e:
            print(f"!! Experiment settings are NOT saved !!! Error {e}")

    def SaveHighDimSettings(self):
        """Save the updated Interferometer, TimeTagger, OSW, and Powermeter configurations back to the YAML file."""

        try:
            # Load existing YAML first
            with open(self.yamlfile, 'r') as file:
                params_to_save = yaml.safe_load(file)
        except Exception as e:
            print(f"Error loading existing YAML file: {e}")
            params_to_save = {}

        # ==== Save updated Interferometer data ====
        params_to_save['Interferometers'] = {}

        for intf_name, interferometer in self.interferometer.Interferometers.items():
            params_to_save['Interferometers'][intf_name] = {
                'IntName': interferometer.IntName,
                'Out1': interferometer.Out1,
                'Out2': interferometer.Out2,
                'VSrcCh': interferometer.VSrcCh,
                'Phase0Voltage': float(interferometer.Phase0Voltage),
                'Phase90Voltage': float(interferometer.Phase90Voltage),
                'Phase180Voltage': float(interferometer.Phase180Voltage),
                'Phase270Voltage': float(interferometer.Phase270Voltage),
                'Phase0power': float(interferometer.Phase0power),
                'Phase90power': float(interferometer.Phase90power),
                'Phase180power': float(interferometer.Phase180power),
                'Phase270power': float(interferometer.Phase270power),
                'V': float(interferometer.V)
            }



        # ==== Save updated TimeTagger data ====
        params_to_save['TimeTagger'] = {
            'Channels': {
                f'Ch{i+1}': {
                    'ChannelID': channel,
                    'TriggerLevel': self.TT.TriggerLevels[i],
                    'Deadtime': self.TT.Deadtimes[i],
                    'DelayTime': self.TT.DelayTimes[i]
                } for i, channel in enumerate(self.TT.Chlist)
            },
            'DataAcquisitionTime': self.TT.DataAcquisitionTime
        }
        print("TimeTagger parameters saved successfully.")

        # ==== Save updated OSW settings ====
        # Save OSW section only if OSW exists
        if hasattr(self, 'OSW'):
            params_to_save['OSW'] = {
                'com_port' : self. OSW.com_port,
                'SW1Status': self.OSW.SW1Status,
                'SW2Status': self.OSW.SW2Status,
                'SW3Status': self.OSW.SW3Status,
                'SW4Status': self.OSW.SW4Status,
                'com_port': self.OSW.com_port if hasattr(self.OSW, 'com_port') else None
            }
            print("OSW settings are saved")
        else:
            print("OSW not available, skipping OSW settings.")


        # # ==== Save updated Powermeter settings (if any Powermeter connected) ====
        """ Whenever powermeters parameter gets saved, it gives me empty dictionary. need to debug
        """
        # if hasattr(self, 'Powermeters'):
        #     params_to_save['Powermeters'] = {}
        #     powermeter_objects = vars(self.Powermeters)

        #     for pm_name, pm_obj in powermeter_objects.items():
        #         if pm_obj is not None:
        #             power_meter_id = getattr(pm_obj, 'power_meter_id', None)
        #             wavelength = getattr(pm_obj, 'wavelength', None)

        #             if power_meter_id is not None and wavelength is not None:
        #                 params_to_save['Powermeters'][pm_name] = {
        #                     'power_meter_id': power_meter_id,
        #                     'wavelength': wavelength
        #                 }
        #     print("Powermeter settings saved successfully.")

        # ==== Write the updated YAML back ====
        try:
            with open(self.yamlfile, 'w') as yaml_file:
                yaml.dump(params_to_save, yaml_file, default_flow_style=False, sort_keys=False, allow_unicode=True, indent=2)
            print(f"Settings successfully saved to {self.yamlfile}")
        except Exception as e:
            print(f"Error saving settings: {e}")


    def parse_channel(self, ch_key):
        """
        Given 'Ch1', return its corresponding ChannelID from TimeTagger settings.
        If already integer, return as is.
        """
        if isinstance(ch_key, str) and ch_key.startswith('Ch'):
            channel_info = self.timetagger_channels.get(ch_key, None)
            if channel_info is not None:
                return channel_info['ChannelID']
            else:
                raise ValueError(f"Channel {ch_key} not found in TimeTagger settings.")
        else:
            return ch_key  # Already integer fallback

    def loadBasisMeasurementSettings(self, basis_name):
        """
        Set interferometer phases based on basis (Alice/Bob) settings, and return the list of ChannelIDs.
        (Does NOT run acquisition.)
        """
        print(f"\n--- Loading settings for basis {basis_name} ---")

        alice_basis = basis_name[0]  # First letter: Alice basis
        bob_basis = basis_name[1]    # Second letter: Bob basis

        # Get settings
        alice_info = self.channel_mappings.get('Alice', {}).get(alice_basis, {})
        bob_info = self.channel_mappings.get('Bob', {}).get(bob_basis, {})
        clk_info = self.channel_mappings.get('Clk', [])

        # Build channel list
        Chlist = [self.parse_channel(ch) for ch in clk_info]
        Chlist += [self.parse_channel(ch) for ch in alice_info.get('Channels', [])]
        Chlist += [self.parse_channel(ch) for ch in bob_info.get('Channels', [])]
        Chlist = sorted(set(Chlist))

        # Set interferometer phases if needed: 
        # This need to be changed to optimize the phase based on the power or counts
        # Need to use this function to optimize
            # interferometer.OptimizeIntPhase(
    #     SupportingFuncs=SupportFunc(),
    #     interferometer_list=[interferometer.IntF],
    #     voltage_range=(2, 5),
    #     voltage_source=interferometer.get_LADAq_for_interferometer('IntD'),
    #     Measurement_Inst=Measurement_Inst,  # This is your TimeTaggerFunctions object
    #     step_size=0.01,
    #     tolerance=0.05,
    #     UpdateVoltage=True,
    #     plotVoltagePower=True,
    #     measurement_function='histogram_between_channels',
    #     ch_click=2,
    #     ch_start=5,
    #     measurement_time=1,
    #     binwidth_ps=1,
    #     n_bins=1000,
    #     end_bins=[270, 310],
    #     plotHistogram = False
    # # )
    #     for user_info in [alice_info, bob_info]:
    #         intf_name = user_info.get('IntName')
    #         voltage_attr = user_info.get('IntVoltage') ## This should be phase

    #         if intf_name is not None and voltage_attr is not None:
    #             intf_obj = getattr(self.interferometer, intf_name)
    #             voltage = getattr(intf_obj, voltage_attr)
    #             self.interferometer.SetIntPhase(
    #                 interferometer_name=intf_obj,
    #                 voltage_source=self.interferometer.get_LADAq_for_interferometer(intf_obj.IntName),
    #                 voltage=voltage
    #             )

        print(f"Channels selected for {basis_name}: {Chlist}")
        print(f"--- Settings loaded for basis {basis_name} ---\n")

        return Chlist


        
    def updateRunLog(self, selected_basis, attenuation_dB, notes=""):
        # Use the same DataFolder where the data files are saved
        folder_path = self.filename_generator.DataFolder
        os.makedirs(folder_path, exist_ok=True)

        runlog_filename = os.path.join(folder_path, "CW_HighDimRunLog.yaml")
        exptsettings_copy_filename = os.path.join(folder_path, "CW_HighDimExptSettings_copy.yaml")

        # Save a copy of CW_HighDimExptSettings.yaml into today's folder (only once)
        if not os.path.exists(exptsettings_copy_filename):
            try:
                shutil.copy(self.yamlfile, exptsettings_copy_filename)
                print(f"Copied experiment settings to {exptsettings_copy_filename}")
            except Exception as e:
                print(f"Error copying experiment settings: {e}")

        # Read existing runlog (if any)
        try:
            if os.path.exists(runlog_filename):
                with open(runlog_filename, 'r') as f:
                    runlog_data = yaml.safe_load(f) or []
            else:
                runlog_data = []
        except Exception as e:
            print(f"Error reading existing runlog: {e}")
            runlog_data = []

        # Determine next run number
        run_number = len(runlog_data) + 1

        # Read the full CW_HighDimExptSettings.yaml (current)
        try:
            with open(self.yamlfile, 'r') as f:
                full_expt_settings = yaml.safe_load(f)
        except Exception as e:
            print(f"Error reading experiment settings for runlog: {e}")
            full_expt_settings = {}

        # Prepare run information
        run_entry = {
            'run_number': run_number,
            'datetime': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'selected_basis': selected_basis,
            'attenuation_dB': attenuation_dB,
            'filenames': {basis: getattr(self, basis).filename for basis in ['ZZ', 'XX', 'ZX', 'XZ', 'YY', 'ZY', 'YZ']},
            'interferometers': {
                intf.IntName: {
                    'Phase0Voltage': float(intf.Phase0Voltage),
                    'Phase90Voltage': float(intf.Phase90Voltage),
                    'Phase180Voltage': float(intf.Phase180Voltage),
                    'Phase270Voltage': float(intf.Phase270Voltage),
                    'V': float(intf.V)
                } for intf in self.interferometer_list
            },
            'notes': notes,
            'full_experiment_settings': full_expt_settings
        }

        # Append the new entry
        runlog_data.append(run_entry)

        # Write back updated runlog
        try:
            with open(runlog_filename, 'w') as f:
                yaml.dump(runlog_data, f, default_flow_style=False)
            print(f"RunLog updated successfully in {folder_path} (Run {run_number})")
        except Exception as e:
            print(f"Error writing runlog: {e}")

    def setAttenuation(self, attenuation):
        try:
            att1= yoko.yoAQ2212_Attenuator(frame_cont=self.yokoframe, slot=2)
            att1.setAtten(attenuation)
            print(f"Attenuation set:{att1.getAtten()}")
        except Exception as e:
            print(f"Could not set the attenuation. e:{e}")

if __name__ == "__main__":

    try: 
        
        HD = HighDim()
        HD.initDevices()

        SingleBasisDataAcquisition = True  # Set this to True for single basis mode

        SingleBasisDataAcquisition = True  # Set to True for manual run

        if SingleBasisDataAcquisition:
            # --- Manual configuration ---
            HD.TT.DataAcquisitionTime = 10  # Set measurement time
            manual_run_number = 3  # Set your run number here
            manual_basis = 'XX'    # Set the basis you're measuring
            manual_filename = f"data_highmu_max_50ns_{manual_basis}_{HD.TT.DataAcquisitionTime}.ttbin"  # Your filename

            # Generate today's folder (same logic as filename_generator)
            today_folder = HD.filename_generator.DataFolder
            run_folder_name = f"Run{manual_run_number}"
            run_folder_path = os.path.join(today_folder, run_folder_name)

            # Create run folder if not existing
            os.makedirs(run_folder_path, exist_ok=True)

            # Apply to HD object
            HD.current_run_number = manual_run_number
            HD.current_run_folder = run_folder_path
            HD.bases_to_measure = [manual_basis]
            HD.manual_filename_map = {
                manual_basis: os.path.join(run_folder_path, manual_filename)
            }

            print(f"Manual mode: Run {manual_run_number} in {run_folder_path}")
            print(f"Filename for basis {manual_basis}: {HD.manual_filename_map[manual_basis]}")

        else:
            # Automatic folder creation
            today_folder = HD.filename_generator.DataFolder
            HD.current_run_folder, HD.current_run_number = HD.filename_generator.MakeRunFolder()
            HD.bases_to_measure = ['ZZ', 'XX', 'ZX', 'XZ', 'YY', 'ZY', 'YZ']


        # # Create a new run folder at the start of each run
        # today_folder = HD.filename_generator.DataFolder
        # HD.current_run_folder, HD.current_run_number = HD.filename_generator.MakeRunFolder()
        
        # -------------------- SHG SCANNING -------------------------
        SHGScanStatus = False  # <--- Add this line
        from SHGScanTEC_v1 import SHG  # Import SHG class only if needed


        # SHGscan.SHGSetVoltage(target_voltage = 0.32, step_size=0.1, delay=0.1, channel=3)

        if SHGScanStatus:
            # Create an SHG instance
            SHGscan = SHG(
                voltage_source=HD.LADAqs['LADAqSHG']['device'],
                plotData=True  # Optional: Enable plotting inside SHGScan
            )

            # Run the SHG Scan
            SHG_voltage_power_data = SHGscan.SHGScan(
                measurement_inst=HD.Powermeters.PM1,
                voltage_range=(2.0, 5),   # Define your voltage range
                step_size=0.05,          # Define your step size
                max_SHG_voltage=5,    # Define your max SHG voltage
                stabilization_time=5.0,  # Optional wait after each voltage set
                channel = 3
            )

            print("SHG Scan complete.")

            # 1. Save the SHG voltage vs power data
            shg_data_filename = os.path.join(HD.current_run_folder, "SHG_voltage_power_data.npy")
            clean_voltage_power_data = np.array([
                (v, p if np.isscalar(p) else p[0]) for v, p in SHG_voltage_power_data])

            # 2. Save it
            np.save(shg_data_filename, clean_voltage_power_data)
            print(f"Saved SHG voltage-power data to: {shg_data_filename}")
            
            # 2. Plot and Save using SupportFunctions

            shg_plot_filename = os.path.join(HD.current_run_folder, "SHGscan1536.png")
            HD.SuFunc.plot_voltage_vs_power(clean_voltage_power_data, figSaveName=shg_plot_filename)

            print(f"Saved SHG scan plot to: {shg_plot_filename}")
        # ------------------------------------------------------------

        
        
        ########################## Interferometer functions #########################
        # Sweep voltage manually and measure feedback signal (example scan)
        voltages = []
        powers = []

        start_time = time.time()
        ### Changing the voltage and measuring the power
        # for volt in np.arange(2, 4, 0.05):
        #     HD.interferometer.SetIntPhase(
        #         interferometer_name=HD.interferometer.IntA,
        #         voltage_source=HD.interferometer.get_LADAq_for_interferometer(HD.interferometer.IntA.IntName),
        #         voltage=volt
        #     )
        #     voltages.append(volt)

        #     power_measured = HD.interferometer.feedbackSignal(
        #         Measurement_Inst=HD.TT,
        #         Chlist=HD.TT.Chlist[0:1],
        #         measurement_time=0.1
        #     )
        #     powers.append(power_measured)

        #     print(f"Voltage: {volt:.3f} V, Power: {power_measured:.6f}, Time elapsed: {time.time() - start_time:.2f} seconds")

        # After sweep, reset to Phase180Voltage
        # HD.interferometer.SetIntPhase(
        #     interferometer_name=HD.interferometer.IntA,
        #     voltage_source=HD.interferometer.get_LADAq_for_interferometer(HD.interferometer.IntA.IntName),
        #     voltage=3
        # )

        # Run optimization of Interferometers
        # HD.interferometer.OptimizeIntPhase(
        #     SupportingFuncs=HD.SuFunc,
        #     interferometer_list=[HD.interferometer.IntE], # HD.interferometer.IntF],
        #     voltage_range=[1, 4.5],
        #     step_size=0.1,
        #     voltage_source=HD.interferometer.get_LADAq_for_interferometer(HD.interferometer.IntE.IntName),
        #     Measurement_Inst=HD.Powermeters.PM1,
        #     UpdateVoltage=True,
        #     plotVoltagePower=True
        # )

        ########### Optimizing interferometer phase for any power ###########
        # HD.interferometer.OptimizeIntPhaseTarget(target_power=1.4e-3, voltage_source=HD.IntVSrc, Interferometer_name=HD.IntA, Measurement_Inst=HD.PM)

        ########################## Time tagger functions ####################

        HD.TT.getChannelCountRate(Chlist=[1, 2, 3, 4, 5, 6, 7])
        StartDataAcquisition = True
        
        if StartDataAcquisition == True:
            # Enable Test Signals on all channels
            test_channels = [HD.parse_channel('Ch1'), HD.parse_channel('Ch2'), HD.parse_channel('Ch3'),
                            HD.parse_channel('Ch4'), HD.parse_channel('Ch5'), HD.parse_channel('Ch6'), HD.parse_channel('Ch7')]
            
            # HD.TT.enableTestSignals(Chlist=test_channels)
            print("Test signals enabled on Ch1-Ch7")
                    
            # bases_to_measure = ['ZZ', 'XX', 'ZX', 'XZ', 'YY', 'ZY', 'YZ']  # List of bases
            # bases_to_measure = ['XX']  # List of bases

            for basis in HD.bases_to_measure:
                # 1. Set interferometers and get channels
                Chlist = HD.loadBasisMeasurementSettings(basis_name=basis)
               
                # 2. Get filename (manual or auto)
                if SingleBasisDataAcquisition:
                    filenameWrite = HD.manual_filename_map[basis]
                else:
                    filenameWrite = getattr(HD, basis).filename
                    filenameWrite = os.path.join(HD.current_run_folder, os.path.basename(filenameWrite))

                # 3. Run TimeTagger acquisition
                HD.TT.TTSyncMeasure(filenameWrite=filenameWrite, Chlist=Chlist)

                # 4. Save data
                HD.TT.npSaveData(filenameRead=filenameWrite, ShowDataTable=True)
        else:
            print(f"Data Acqusition is not intiated")

        # HD.setAttenuation(10)
        HD.updateRunLog(selected_basis=HD.bases_to_measure, attenuation_dB=0, notes="Nice optimized run, Without DWDMs")
        HD.disconnectDevices()

        # print("Measuring counts on channels...")
        # HD.TT.getChannelCounts(Chlist=HD.TT.Chlist[0:3], measurement_time=HD.TT.DataAcquisitionTime) #measurement_time sets the time for measurement runs
        # HD.TT.getChannelCountRate(Chlist=HD.TT.Chlist[0:3], measurement_time=HD.TT.DataAcquisitionTime) #always /s. For better accuracy can use longer measurement time
        
        # Disable test signals after testing
        # HD.TT.disableTestSignals(Chlist=HD.TT.Chlist[0:3])

    except KeyboardInterrupt:
        HD.disconnectDevices()    
        print("error")