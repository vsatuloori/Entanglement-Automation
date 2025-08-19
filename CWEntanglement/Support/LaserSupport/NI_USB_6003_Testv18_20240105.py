import nidaqmx
from nidaqmx.constants import TerminalConfiguration, Edge, AcquisitionType, VoltageUnits
import matplotlib.pyplot as plt
import time
import numpy as np
# import Multimeter_Automation_Testv3 as DCPS 
from datetime import datetime
import os
import Gradient_Descent as GD
from scipy import signal
# import NI_USB_6003_Example as NIAO

current_date = datetime.now().date()
# current_date = current_date.replace("-", "_")

isSaved = False

class NIDAQ_USB:
    def __init__(self, devID, aiNoSamples, aiSamplingRate, aiNoChannels, incr=1,
                 aoNoSamples=None, aoSamplingRate=None, aoNoChannels=1, aoData=None) -> None:
        """
        Setup NIDAQ_USB device for Analog Input (AI) and Analog Output (AO)

        Arguments:
        devID = Device number given in serial connection (ex. 'Dev1')
        aiNoSamples = Total number of AI samples per collection run
        aiSamplingRate = AI sampling rate
        aiNoChannels = AI number of channels

        incr = Number of AI samples per AO sample (defaults to 1)

        aoNoSamples = Total number of AO samples per collection run (defaults to None)
        aoSamplingRate = AO sampling rate (defaults to None)
        aoNoChannels = AO number of channels (defaults to None)
        """
        self.devID = devID
        self.aiNoSamples = aiNoSamples
        self.aiSamplingRate = aiSamplingRate
        self.aiNoChannels = aiNoChannels
        self.incr = incr

        self.aoNoSamples = aoNoSamples
        self.aoSamplingRate = aoSamplingRate
        self.aoNoChannels = aoNoChannels
        self.min_v = 0
        self.max_v = 1.5

        self.aiTask = None
        self.aoTask = None

        self.aiCurrentIdx = 0 # current index of the AI data
        # NUM_MEASUREMENTS = aiNoSamples//incr
        # if NUM_MEASUREMENTS == aiNoSamples/incr:
        #     self.NUM_MEASUREMENTS = NUM_MEASUREMENTS
        # else: 
        #     raise Exception("Invalid increment value: number of measurements is not an integer")
        self.NUM_MEASUREMENTS = aiNoSamples//incr
        self.dataDict = {}
        # self.dataDict["AI Calibration"] = None
        # self.dataDict["AO Calibration"] = None
        self.dataDict["AI Data"] = np.zeros([self.aiNoChannels+1,self.aiNoSamples])
        self.dataDict["AO Data"] = np.zeros([self.aoNoChannels+1,self.aoNoSamples]) # Still need to figure out how to do this
    def __str__(self):
        return (f"<NIDAQ USB>:\n"
                + "Analog Input parameters"
                + f"\n\tnumber of samples: {self.aiNoSamples}\n\tsampling rate: {self.aiSamplingRate}\n\tnumber of channels: {self.aiNoChannels}\n\tincrement: {incr}")
    
    # Task funcitons
    def setup_ai_task(self, spc): # add task argument to use in MasterFile?
        """
        Setup Analog Input nidaqmx.Task() object self.aiTask

        Arguments:
        spc = samples per channel
        """
        self.aiTask = nidaqmx.Task() # <- check if can be outside
        self.aiTask.ai_channels.add_ai_voltage_chan(f"{self.devID}/ai0:{self.aiNoChannels-1}", terminal_config=TerminalConfiguration.RSE) #initialize data acquisition task
        self.aiTask.timing.cfg_samp_clk_timing(rate=self.aiSamplingRate, source="", active_edge=Edge.RISING, sample_mode=AcquisitionType.FINITE, samps_per_chan=spc)#=incr)

    def setup_ao_task(self, spc=2): # add task argument to use in MasterFile?
        """
        Setup Analog Output nidaqmx.Task() object self.aoTask

        Arguments:
        spc = samples per channel
        """
        self.aoTask2 = nidaqmx.Task() # <- check if can be outside
        self.aoTask2.ao_channels.add_ao_voltage_chan(f"{self.devID}/ao0", min_val=min_v, max_val=max_v, units=VoltageUnits.VOLTS)  # Replace with your AO channel
        self.aoTask2.timing.cfg_samp_clk_timing(rate=aoSamplingRate, source="", active_edge=Edge.RISING, sample_mode=AcquisitionType.FINITE, samps_per_chan=spc)#=numParam

    def start_ai_task(self):
        self.aiTask.start()
    def stop_ai_task(self):
        self.aiTask.stop()
    def close_ai_task(self):
        self.aiTask.close()

    def start_ao_task(self):
        self.aoTask.start()
    def stop_ao_task(self):
        self.aoTask.stop()
    def close_ao_task(self):
        self.aoTask.close()

    def close_all_tasks(self):
        self.aiTask.close()
        self.aoTask.close()
    
    def ai_measurment_incr(self):
        """ Runs single AI measurement with number of samples incr and returns the data as an np array """
        data_values = np.zeros([self.aiNoChannels + 1, self.incr])

        # AI
        ai_start = time.perf_counter()
        self.start_ai_task()
        data0 = self.aiTask.read(number_of_samples_per_channel=incr) # reads incr number of samples
        # time.sleep(0.0005)
        self.stop_ai_task()
        data1 = np.array(data0) # reads from channel every loop

        ai_end = time.perf_counter()
        ai_time = ai_end - ai_start

        print(f"Elapsed time to run the AI task is = {ai_time} s")

        data_values[0,:] = ai_time
        data_values[1:,:] = data1

        self.aiMeasTracker += incr

        return data_values
        
    def ai_measurment(self):
        """ Runs single AI measurement with number of samples incr and returns the data as an np array """
        data_values = np.zeros([self.aiNoChannels + 1, self.incr])
        # AI
        ai_start = time.perf_counter()
        for _ in range(1000):
            self.start_ai_task()
            data0 = self.aiTask.read(number_of_samples_per_channel=incr) # Read incr number of samples
            # time.sleep(0.0005)
            self.stop_ai_task()
            data1 = np.array(data0) #reads from channel every loop
            # data = data1
        ai_end = time.perf_counter()
        ai_time = ai_end - ai_start

        print(f"Elapsed time to run the AI task is = {ai_time} s")

        data_values[0,:] = ai_time
        data_values[1:,:] = data1

        return data_values
    
    def calibration(self, CaliFunction):
        pass

    def measurement(self, MeasFunction):
        pass

    def save_ai_data(self):
        pass
        # TODO save AI data to .pkl dictionary

# Define constants
NoSamples = int(5e3)#int(150e3) # <- check this
SamplingRate = 25e3 # Even though sampling rate is high, python exec limits total data acquisition rate to 10kHz
duration = NoSamples / SamplingRate
NoChannels = 4
incr = 10 # averaging increment (for 4 channels use 10, for 3 use 12)
numThetaValues = int(NoSamples/incr)
data_values = np.zeros([NoChannels+1,NoSamples])
theta = np.zeros([2,numThetaValues])
ratio_12 = np.zeros([2,numThetaValues])
maxima = np.zeros([2,numThetaValues])
minima = np.zeros([2,numThetaValues])
maximum = 3.8
minimum = -3.8
max_attempts = 5
th_t = 45
# a = -0.006
# b = 1.79
# c = 0.002
# d = 1.02

# a,b,c,d values for 8dBm, 1/5/24
a = 0.00565
b = 0.375
c = 0.00285
d = 0.215

"""
# # a,b,c,d values for 8dBm, 1/3/24
# a = 0.00395
# b = 0.562
# c = -0.000695
# d = 0.315

# a,b,c,d values for 8dBm, 1/4/24
a=-0.00365
b=0.578
c=-0.000542
d=0.330
"""
"""
# a=0.49829264276195328
# b=3.22345330263488
# c=0.03219871927285567
# d=3.887665377056692
"""
"""
# # 8/16 PS4 a,b,c and d values
# a=0.020421337336301804
# b=0.019360079895704985
# c=-0.01749215245945379
# d=0.009841373946983367
"""

####  DC power supply parameters 
v = 0
min_v = 0
max_v = 1.5 # DCPS is not used here
GAIN = 5

# sample_rate = 5000  # Sample rate in samples per second for AO
# print(DCPS.sample_rate)
# print(sample_rate)
# duration = 60
# frequency = 10
# aoSamples =50#int(sample_rate * duration)
# aoSamples = 2
voltage_range = (max_v - min_v)
# time_axis = np.linspace(0, duration, aoSamples, endpoint=False)
# aoData = voltage_range * np.linspace(0, 1, aoSamples, endpoint=False) # ramp
aoSamplingRate = 5000
aoFreq = 20#20#100
aoSamples = int(aoSamplingRate*duration)
numParam = 2#aoSamples
numSamplesPerCycle = aoSamplingRate/aoFreq
ramp_function = ((np.linspace(0, aoSamples, aoSamples, endpoint=False)) % (numSamplesPerCycle)) * (max_v - min_v)/(numSamplesPerCycle)  # Iraj ramp


######### Triangular function ##############
t_linspace = np.linspace(0, duration, aoSamples, endpoint=False)
aoDataOffset = 0#0.1 
TriangularWave = voltage_range/2 * signal.sawtooth(2*np.pi*aoFreq * t_linspace, 1)  + voltage_range/2 + aoDataOffset
SineWave = voltage_range/2 * np.sin(2*np.pi * aoFreq * t_linspace) + voltage_range/2
ZeroWave = 0 * t_linspace
FixedVoltage = np.copy(ZeroWave)
FixedVoltage[1000:] = 1
aoData = TriangularWave #TriangularWave

# voltages =  ((np.linspace(0, NoSamples, NoSamples, endpoint=False)) % SamplingRate)*(max_v - min_v)/SamplingRate 
voltages = aoData
print(np.shape(voltages))
# sine_wave = voltage_range * np.sNumin(frequency * time_axis)/2 + voltage_range/2 # actually a sine wave
# sine_wave = np.zeros(2)
# sine_wave[1] = voltage_range # switching between two values
# print(sine_wave[0:10])
if np.any(aoData > 2) or np.any(aoData < 0):
    raise Exception(f"Voltage range is too high!")
# sinesamples = 10
# aoData = np.linspace(0, 5, sinesamples)
# filename = f""
print(voltages)

# Task funcitons
def start_ai_task(spc=incr): # add task argument to use in MasterFile?
    global task1
    task1 = nidaqmx.Task() # <- check if can be outside
    task1.ai_channels.add_ai_voltage_chan(f"Dev1/ai0:{NoChannels-1}", terminal_config=TerminalConfiguration.RSE) #initialize data acquisition task
    task1.timing.cfg_samp_clk_timing(rate=SamplingRate,  source="", active_edge=Edge.RISING, sample_mode=AcquisitionType.FINITE, samps_per_chan=spc)#=incr)
    # task1.start()
    # time.sleep(1)

def setup_ao_task(spc=numParam): # add task argument to use in MasterFile?
    global task2
    task2 = nidaqmx.Task() # <- check if can be outside
    task2.ao_channels.add_ao_voltage_chan("Dev1/ao0", min_val=0.0, max_val=max_v, units=VoltageUnits.VOLTS)  # Replace with your AO channel
    task2.timing.cfg_samp_clk_timing(rate=aoSamplingRate,  source="", active_edge=Edge.RISING, sample_mode=AcquisitionType.FINITE, samps_per_chan=spc)#=numParam
    # task2.write(aoData, auto_start=False)
    # task2.start()


def close_task(task):
    task.stop()
    # time.sleep(1)
    task.close()

def linear_phase_model(th):
    dv = 0.8/28.8 * th
    return dv


def check_local_ext(nidaq):
    # find a and b
    max_ch1_temp = max(nidaq[1,:])
    min_ch1_temp = min(nidaq[1,:])
    max_ch2_temp = max(nidaq[4,:])
    min_ch2_temp = min(nidaq[4,:])
    PEAK_DIST1 = SamplingRate/(aoFreq * 3)#350 # Need to change for each plot
    PEAK_DIST2 = SamplingRate/(aoFreq * 3)#350 # Need to change for each plot
    PEAK_HEIGHT1 = min([max_ch1_temp, -min_ch1_temp, 0])
    PEAK_HEIGHT2 = min([max_ch2_temp, -min_ch2_temp, 0])
    PEAK_HEIGHT3 = -max_ch2_temp
    PEAK_PROM1 = min([max_ch1_temp, -min_ch1_temp])
    PEAK_PROM2 = min([max_ch2_temp, -min_ch2_temp])
    maxima1, max1_properties = signal.find_peaks(nidaq[1,:], height=PEAK_HEIGHT1, distance=PEAK_DIST1, prominence=PEAK_PROM1)
    minima1, min1_properties = signal.find_peaks(-nidaq[1,:], height=PEAK_HEIGHT1, distance=PEAK_DIST1, prominence=PEAK_PROM1)

    # find c and d
    maxima2, max2_properties = signal.find_peaks(nidaq[4,:], height=PEAK_HEIGHT2, distance=PEAK_DIST2, prominence=PEAK_PROM2)
    minima2, min2_properties = signal.find_peaks(-nidaq[4,:], height=PEAK_HEIGHT3, distance=PEAK_DIST2, prominence=PEAK_PROM2)

    max1_values = max1_properties["peak_heights"]
    min1_values = -min1_properties["peak_heights"]
    max2_values = max2_properties["peak_heights"]
    min2_values = -min2_properties["peak_heights"]

    # Checking that maxima and minima are working
    # plt.figure()
    # plt.title("Maxima of BHD1")
    # plt.plot(nidaq[1,:], c='b', label="BHD1")
    # plt.plot(maxima1, max1_values, "gx", label="BHD1 max")
    # # plt.plot(max2_values, c='r', label="BHD2 max-min")
    # plt.legend()

    # plt.figure()
    # plt.title("Minima of BHD1")
    # plt.plot(nidaq[1,:], c='b', label="BHD1")
    # plt.plot(minima1, min1_values, "gx", label="BHD1 min")
    # # plt.plot(max2_values, c='r', label="BHD2 max-min")
    # plt.legend()

    # plt.figure()
    # plt.title("Maxima of BHD2")
    # plt.plot(nidaq[4,:], c='r', label="BHD2")
    # plt.plot(maxima2, max2_values, "gx", label="BHD2 max")
    # # plt.plot(max2_values, c='r', label="BHD2 max-min")
    # plt.legend()

    # plt.figure()
    # plt.title("Minima of BHD2")
    # plt.plot(nidaq[4,:], c='r', label="BHD2")
    # plt.plot(minima2, min2_values, "gx", label="BHD2 min")
    # # plt.plot(max2_values, c='r', label="BHD2 max-min")
    # plt.legend()

    return((maxima1, max1_values), (minima1, min1_values), (maxima2, max2_values), (minima2, min2_values))

def calculate_abcd(nidaq):
    extrema = check_local_ext(nidaq)

    max1 = extrema[0]
    min1 = extrema[1]
    max2 = extrema[2]
    min2 = extrema[3]

    # a and b values (BD1)

    max1x = max1[0]
    max1y = max1[1]
    min1x = min1[0]
    min1y = min1[1]

    a1211 = []
    b1211 = []

    for i in range(min(len(max1x), len(min1x))):
        a_i = (max1y[i] + min1y[i])/2
        b_i = (max1y[i] - min1y[i])/2
        a1211.append(a_i)
        b1211.append(b_i)

    # c and d values (BD2)

    max2x = max2[0]
    max2y = max2[1]
    min2x = min2[0]
    min2y = min2[1]

    c1211 = []
    d1211 = []

    for i in range(min(len(max2x), len(min2x))):
        c_i = (max2y[i] + min2y[i])/2
        d_i = (max2y[i] - min2y[i])/2
        c1211.append(c_i)
        d1211.append(d_i)
    
    # plt.figure()
    # plt.title("a, b, c, and d values using find_peaks")
    # plt.plot(a1211, c='blue', label="a")
    # plt.plot(b1211, c='red', label="b")
    # plt.plot(c1211, c='green', label="c")
    # plt.plot(d1211, c='yellow', label="d")
    # plt.legend(loc='upper right')

    # plt.figure()
    # plt.suptitle("Histograms of a, b, c, and d")
    # plt.subplot(2, 2, 1)
    # plt.title(f"Histogram of a values with mean = {np.mean(a1211)}\nand stddev = {np.std(a1211)}")
    # plt.hist(a1211, bins=40)
    # plt.subplot(2, 2, 2)
    # plt.title(f"Histogram of b values with mean = {np.mean(b1211)}\nand stddev = {np.std(b1211)}")
    # plt.hist(b1211, bins=40)
    # plt.subplot(2, 2, 3)
    # plt.title(f"Histogram of c values with mean = {np.mean(c1211)}\nand stddev = {np.std(c1211)}")
    # plt.hist(c1211, bins=40)
    # plt.subplot(2, 2, 4)
    # plt.title(f"Histogram of d values with mean = {np.mean(d1211)}\nand stddev = {np.std(d1211)}")
    # plt.hist(d1211, bins=40)

    return(a1211, b1211, c1211, d1211)

def find_ai_params(save=False):
    global aoData
    is_saved = False
    a0 = 0
    b0 = 0
    c0 = 0
    d0 = 0

    i = 0
    tic = time.perf_counter()
    attempts = 0 
    success = False

    charAISamples = int(150e3)
    charDuration = charAISamples / SamplingRate
    charAOSamples = int(aoSamplingRate*charDuration)

    t_linspace_char = np.linspace(0, charDuration, charAOSamples, endpoint=False)
    charAOSweep = voltage_range/2 * signal.sawtooth(2*np.pi*aoFreq * t_linspace_char, 1)  + voltage_range/2
    data_values_char = np.zeros([NoChannels+1,charAISamples])
    FixedVoltage = np.ones(charAOSamples)
    voltages_char = charAOSweep
    if np.any(voltages_char < 0) or np.any(voltages_char > 2) or np.any(voltages_char == np.nan):
        # task1.close()
        # task2.stop()
        # task2.close()
        raise Exception(f"Voltage range is too high!")
    
    setup_ao_task(charAOSamples)
    task2.write(voltages_char)
    start_ai_task(charAISamples)
    task2.start()
    task1.start()
    while attempts<max_attempts and not success:
        try:
            # AO
            time.sleep(charDuration+0.01)
            close_task(task2)

            # AI
            data0 = task1.read(number_of_samples_per_channel=charAISamples)
            data1 = np.array(data0) #reads from channel every loop
            # data = data1
            data_values_char[0,:] = np.linspace(0,charAISamples, charAISamples, endpoint=False)#time.time()# - tic
            data_values_char[1:,:] = data1

            i=i+1
        
            if i == 1:
                print("Success!")
                success =True
                break
            attempts = 0
        except KeyboardInterrupt:
            print("Interrupting data collection...")
            task1.stop()
            task1.close()
            return None
        except Exception as e:
            print(e)
            attempts += 1  
            save = False

    toc = time.perf_counter()

    # print(data_values_char)
    print(f"The time elapsed is {toc - tic}s, time taken per sample: {(toc-tic)/charAISamples} ")
    print(f"Expected time taken per sample: {1/SamplingRate}")

    close_task(task1)

    runner_idx = 0
    filename = ''

    a_mean_0802, b_mean_0802, c_mean_0802, d_mean_0802 = calculate_abcd(data_values_char)
    a0 = np.mean(a_mean_0802)
    b0 = np.mean(b_mean_0802)
    c0 = np.mean(c_mean_0802)
    d0 = np.mean(d_mean_0802)

    print(f"a0: {a0}\nb0: {b0}\nc0: {c0}\nd0: {d0}")

    # plt.figure()
    # plt.plot(data_values_char[1,:], c='b', label="ch1")
    # plt.plot(data_values_char[4,:], c='r', label="ch2")
    # plt.legend(loc="upper right")
    # plt.show()

    if save:
        print("Saving file...")
        while not is_saved:
            print("Checking file name...")
            runner_idx += 1
            print(runner_idx)
            filename = f'{current_date}_NIDAQ_channels_1_and_4_data_no_touching_PS{runner_idx}on_PSchar.txt'
            is_saved = not os.path.exists(filename)
        np.savetxt(f'{current_date}_NIDAQ_channels_1_and_4_data_no_touching_PS{runner_idx}on_PSchar.txt', data_values_char)
        # np.savetxt(f'{current_date}_NIDAQ_channels_1_and_4_theta_no_touching_PS{runner_idx}on_PSchar.txt', theta)
        np.savetxt(f'{current_date}_NIDAQ_channels_1_and_4_voltages_no_touching_PS{runner_idx}on_PSchar.txt', voltages_char)
        print("File saved!")

    return (a0, b0, c0, d0)

def ai_measurement(incr, max_attempts, save=False):
    global isSaved
    global aoData
    global task1
    global task2
    global AI_times
    i = 0
    a, b, c, d = find_ai_params(save)
    # print("Calculated a,b,c,d values from prescan")
    # print(f"a = {a}")
    # print(f"b = {b}")
    # print(f"c = {c}")
    # print(f"d = {d}")
    # start = time.time()
    start_ai_task() # Enable if not using with
    # finish = time.time()
    # print(f"Time to start task {finish - start}")
    tic = time.perf_counter()
    attempts = 0 
    success = False
    V_PM = np.ones(2)#2.5*np.ones(2) # maybe need to modify size???
    th_c = 0
    V_PM_ao = V_PM/GAIN
    ch2Tol = 0.025
    thTol = 5
    # th_PM_sum = 0
    th_PM_old = 0
    # read_time = incr * 1/SamplingRate
    # ratio_12 = np.zeros(numThetaValues)
    setup_ao_task() # Enable if not using with
    timing = np.zeros(numThetaValues)
    lm = 0.8/28.8

    time.sleep(0.001)
    while attempts<max_attempts and not success:
        try:
            start = time.perf_counter()
            # AO
            # print(f"i: {i}")
            # ao_start = time.perf_counter()
            task2.write(V_PM_ao)
            # print(f"Samples #{i*incr} to {(i+1)*incr-1}, voltage: {V_PM[0] * 5}")
            task2.start()
            time.sleep(2 * 1/aoSamplingRate)
            task2.stop()
            # ao_end = time.perf_counter()
            # print(f"Elapsed time to run the AO task is = {ao_end - ao_start} s")

            # AI
            ai_start = time.perf_counter()
            for i in range(1000):
                task1.start()
                data0 = task1.read(number_of_samples_per_channel=2)#nidaqmx.constants.READ_ALL_AVAILABLE)#NoSamples)
                # time.sleep(0.0005)
                task1.stop()
                data1 = np.array(data0) #reads from channel every loop
                # data = data1
            ai_end = time.perf_counter()

            print(f"Elapsed time to run the AI task w/o with is = {ai_end - ai_start} s")

            data3 = []
            ai_start = time.perf_counter()
            for i in range(1000):
                with nidaqmx.Task() as task3:
                    task3.ai_channels.add_ai_voltage_chan(f"Dev1/ai0:{NoChannels-1}", terminal_config=TerminalConfiguration.RSE) #initialize data acquisition task
                    task3.timing.cfg_samp_clk_timing(rate=SamplingRate,  source="", active_edge=Edge.RISING, sample_mode=AcquisitionType.FINITE, samps_per_chan=incr)#=incr)
                    data2 = task3.read(number_of_samples_per_channel=incr)#nidaqmx.constants.READ_ALL_AVAILABLE)#NoSamples)
                    data3 = np.array(data2) #reads from channel every loop
            ai_end = time.perf_counter()

            print(f"Elapsed time to run the AI task w/ with is = {ai_end - ai_start} s")

            data_values[0,(incr * (i)):(incr * (i+1))] = i#time.perf_counter() - tic
            data_values[1:,(incr * (i)):(incr * (i+1))] = data1
            

            # ch1_est = (data_values[1,(incr * (i)):(incr * (i+1))] - a)/b
            # ch2_est = (data_values[2,(incr * (i)):(incr * (i+1))] - c)/d
            # th_c = np.mean(np.arctan(ch1_est/ch2_est) * 180/np.pi)
            # theta[0, (incr * (i)):(incr * (i+1))] = i
            # theta[1, (incr * (i)):(incr * (i+1))] = th_c

            # V_PM Calculation
            # # calculation_start = time.perf_counter()
            # ch1_est = (data_values[1,(incr * (i)):(incr * (i+1))] - a)/b
            # ch2_est = (data_values[4,(incr * (i)):(incr * (i+1))] - c)/d
            ch1_est_ave = np.mean((data_values[1,(incr * (i)):(incr * (i+1))] - a)/b)
            ch2_est_ave = np.mean((data_values[4,(incr * (i)):(incr * (i+1))] - c)/d)
            # ch1_est = data_values[1,(incr * (i)):(incr * (i+1))]
            # ch2_est = data_values[2,(incr * (i)):(incr * (i+1))] 
            if (abs(ch2_est_ave) <= ch2Tol) or (abs(ch1_est_ave) <= ch2Tol):
                th_c = th_t # If CH2 is 0±ch2Tol, assume you are at th_t and don't change the PM voltage
            else:
                th_c = (np.arctan(ch1_est_ave/ch2_est_ave) * 180/np.pi)
            # theta[0, (incr * (i)):(incr * (i+1))] = i
            theta[1, (incr * (i)):(incr * (i+1))] = th_c
            if abs(th_c - th_t) <= thTol:
                th_PM = 0
            else:
                th_PM = th_t - th_c
                # V_PM[:] = (V_PM[:] + linear_phase_model(th_PM))%10
                V_PM[:] = (V_PM[:] + 1 * th_PM)%5 # Maybe need to replace 10 with V_pi?
            # # V_PM[:] = V_PI*(th_PM)/ np.pi 
            # # V_PM[:] = V_PM[:] + V_PM_old
            # if th_PM >= th_PM_old:
            #     dV = 0.01 * abs(th_PM)
            # elif th_PM < th_PM_old:
            #     dV = -0.01 * abs(th_PM)
            # # dV = 0.1 * -(th_t - (th_PM))/180
            # print(f"dV: {dV}")
            # V_PM[:] = (dV + V_PM_old)%10
            # # V_PM = V_PM%(2*V_PI) # This 7.4 value is because of the amplifier. When we have the new one, this could be equal to 2*V_PI
            
            # print(f"i: {i}, th_c: {th_c}, th_t: {th_t}, th_PM: {th_PM}, V_PM: {V_PM[0]}")
            V_PM_ao = V_PM/GAIN
            # print(f"V_PM_old:{V_PM_old} V, V_PM: {V_PM} V, V_PM_ao:{V_PM_ao} V")

            # th_PM_old = th_PM

            # V_PM ratio calculation
            # ch1_est = data_values[1,(incr * (i)):(incr * (i+1))]
            # ch2_est = data_values[2,(incr * (i)):(incr * (i+1))] 

            # ratio_target = 0.25
            # ratio_val = np.mean(ch1_est/ch2_est)
            # ratio_12[i] = ratio_val
            # ratio_diff = ratio_val - ratio_target            

            # print(f"th_c: {ratio_val}, th_t: {ratio_target}, th_PM: {ratio_diff}")
            # dV = 0.001*(ratio_diff)
            # V_PM_old = V_PM[0]
            # V_PM[:] = dV + V_PM_old
            # V_PM = V_PM%(2*V_PI) # This 7.4 value is because of the amplifier. When we have the new one, this could be equal to 2*V_PI
            
            # V_PM_ao = V_PM/GAIN # Comment to not update AO voltage
            # print(f"V_PM_old:{V_PM_old} V, V_PM: {V_PM} V, V_PM_ao:{V_PM_ao} V")

            '''
            # print(f"th_PM: {th_PM}")
            # th_PM_interp = (th_PM + th_PM_old + 90) % 180 - 90
            # # th_PM_interp = th_PM

            # # lr = 0.5
            # # Vpi = 5
            # # print(((th_PM + th_PM_old) % 180 - B)/A - phi)
            # # V_PM[:] = ( ( Vpi/np.pi * np.arcsin( ((th_PM + th_PM_old) % 180 - B)/A - phi ) ) % 5) / 5#v_th_interp((th_PM + th_PM_old) % -180)/5       #GD.input_voltage(th_c, th_t, lr, th_PM_sum, V_PI=Vpi)
            # V_PM[:] = v_th_interp(((th_PM_interp)))/5 % 1.2
            # if th_PM_interp >= 0:
            #     V_PM[:] += v_th_interp(((th_PM_interp)))
            # elif th_PM_interp < 0:
            #     V_PM[:] -= v_th_interp((np.abs(th_PM_interp)))
            # # V_PM = V_PM % (6)
            # # print(V_PM)
            # if V_PM[0] < 0:
            #     V_PM[:] = 0
            # if V_PM[0] > 6:
            #     V_PM[:] = 6

            # V_PM[:] = V_PM/5
            '''
            
            if V_PM_ao[0] < min_v or V_PM_ao[0] > max_v or V_PM_ao[0] == np.nan:
                task1.close()
                # task2.stop()
                task2.close()
                raise Exception(f"V: {V_PM_ao} V, Voltage range is too high!")
            
            end = time.perf_counter()
            timing[i] = end - start
            voltages[(incr * (i)):(incr * (i+1))] = V_PM_ao[0]
            # th_PM_old = th_PM_interp
            # print(f"th_PM inputted: {th_PM_old}")
            # calculation_end = time.perf_counter()
            # print(f"Elapsed time to calculate the next V_PM is = {calculation_end - calculation_start} s")

            # time.sleep(0.0001)
            # task2.stop()

            # print(f"The total time elapsed for the AO, AI, and V_PM calculation for i: {i} is {end - start} s")
            i=i+1

        
            if i >= 1:#numThetaValues:
                print("Success!")
                success =True
                break
            attempts = 0
        except KeyboardInterrupt:
            print("Interrupting data collection...")
            # task1.stop()
            task1.close()
            task2.close()
            return None
        except Exception as e:
            print(e)
            attempts += 1  
            save = False
            return None

    toc = time.perf_counter()

    print(data_values)
    print(f"The time elapsed is {toc - tic}s, time taken per sample: {(toc-tic)/NoSamples} ")
    print(f"Expected time taken per sample: {1/SamplingRate}")

    ratio_12 = data_values[1,:]/data_values[2,:]

    task1.stop()
    task1.close()
    # task2.stop()
    task2.close()
    # close_task(task1)
    # close_task(task2)

    # data_values[0,:] -= tic
    # theta[0,:] -= tic

    runner_idx = 0
    filename = ''
    if save:
        print("Saving file...")
        while not isSaved:
            print("Checking file name...")
            runner_idx += 1
            print(runner_idx)
            filename = f'{current_date}_NIDAQ_channels_1_and_4_data_no_touching_PS{runner_idx}on_PSonly.txt'
            isSaved = not os.path.exists(filename)
        np.savetxt(f'{current_date}_NIDAQ_channels_1_and_4_data_no_touching_PS{runner_idx}on_PSonly.txt', data_values)
        np.savetxt(f'{current_date}_NIDAQ_channels_1_and_4_theta_no_touching_PS{runner_idx}on_PSonly.txt', theta)
        np.savetxt(f'{current_date}_NIDAQ_channels_1_and_4_ratio12_no_touching_PS{runner_idx}on_PSonly.txt', ratio_12)
        np.savetxt(f'{current_date}_NIDAQ_channels_1_and_4_voltages_no_touching_PS{runner_idx}on_PSonly.txt', voltages)
        np.savetxt(f'{current_date}_NIDAQ_channels_1_and_4_timing_no_touching_PS{runner_idx}on_PSonly.txt', timing)
        print("File saved!")
        isSaved = False

    # plt.savefig(f'{current_date}_NIDAQ_channels_1_and_4_data_no_touching_PS{runner_idx}on_PSonly_plt.png') # <- remember to change!!!
    # plt.ioff()

if __name__ == "__main__":
    for _ in range(1, 2):
        ai_measurement(incr, max_attempts, save=False)
        time.sleep(1)
    # ai_measurement(incr, max_attempts, save=True)

# plt.figure()
# plt.plot(data_values[0,:], data_values[1,:])
# plt.plot(data_values[0,:], data_values[2,:])
# plt.show()

# print(data_values)