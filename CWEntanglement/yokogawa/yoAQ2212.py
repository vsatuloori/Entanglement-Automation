"""
see this document for help: https://cdn.tmi.yokogawa.com/1/6180/files/IM735101-17EN.pdf

Author: Alex Ramirez, Andrew Mueller
Date: Jul 20, 2023

With inspiration from the andoAQ8201A script by Alex Walter, Andrew Mueller

An ethernet based instrument subclass for the Yokogawa AQ2212 mainframe and its modules
"""


import os, time, traceback
from pkg_resources import resource_filename
import numpy as np
import matplotlib.pyplot as plt
# import snspd_measure.config
from visaInst import visaInst
from datetime import datetime
from scipy.constants import c
from tqdm import tqdm

class yoAQ2212_frame_controller(visaInst):
    def __init__(self, params=None, ipAddress=None, port=None, **kwargs):
        """
        :param ipAddress: ie. '10.7.0.13x'
        :param kwargs:
                     - offline: If True, then don't actually read/send data over visa
        """
        if (params):
            ipAddress = params["ip_addr"]
            port = params["port"]

        super().__init__(ipAddress, **kwargs)
        self.ipAddress = ipAddress
        self.port = port
        self.connect() # RAII
        # self.port = visaInst.port
    def set_date(self, year=None, month=None, day=None):
        if day is not None:
            msg = f'SYSTem:DATE {year}, {month}, {day}'
            return float(self.write(msg))
        else:
            now = datetime.now()
            year = int(now.strftime("%Y"))
            month = int(now.strftime("%m"))
            day = int(now.strftime("%d"))
            msg = f'SYSTem:DATE {year}, {month}, {day}'
            return self.write(msg)

    def set_time(self, hour=None, minute=None, seconds=None):
        # msg = f":SYSTem:DATE"
        if minute is not None:
            msg = f'SYSTem:TIME {hour},{minute},{seconds}'
            return self.write(msg)
        else:
            now = datetime.now()
            hour = now.strftime("%H")
            minute = now.strftime("%M")
            seconds = now.strftime("%S")
            msg = f'SYSTem:TIME {hour},{minute},{seconds}'
            return self.write(msg)

class yoAQ2212_laser(visaInst):
    def __init__(self, frame_cont: yoAQ2212_frame_controller, slot=None, params=None, **kwargs):
        """
        port, ipAddress,
        :param ipAddress: ie. '10.7.0.134'
        :param kwargs:
                     - offline: If True, then don't actually read/send data over visa
        """
        if (params):
            slot = params["slot"]

        super().__init__(frame_cont, **kwargs)
        self.slot = slot
        self.frame_cont = frame_cont

    def write(self, msg):
        return self.frame_cont.write(msg)

    def query(self, msg):
        return self.frame_cont.query(msg)

    def getModule(self):
        msg1 = f'SLOT{self.slot}:EMPT?'
        empty = int(self.query(msg1))  # first ask if there is a module (0 = yes, 1 = no)
        if empty == 0:
            msg = f'SLOT{self.slot}:IDN?'  # will return string of device info and module info
            info = self.query(msg).split(",")  # separate info
            return info[1]  # return just the module info
        else:
            return 'Empty Slot'

        ###############################
        # Laser Module

    def getLaserStatus(self):
        msg1 = f'SOUR{self.slot}:POW:STAT? '  # get status of laser
        state = int(self.query(msg1))  # first ask if there is a module (0 = OFF, 1 = ON)
        return state

    def toggleLaser(self):
        state = self.getLaserStatus()

        if state == 0:
            # print('Laser OFF')  # return just the module info
            # turn_on = input('Would you like to enable the laser? (Y/n)')
            turn_on = 'Y'
            if turn_on == 'Y' or turn_on == 'y':
                msg2 = f'SOUR{self.slot}:POW:STAT ON'
                # should be :OUTPut[m][:CHANnel[d]][:STATe] ?? maybe
                try:
                    self.write(msg2)
                except:
                    print('Error enabling laser')
                finally:
                    for a in tqdm(range(10),
                                  desc='Warming Up...',
                                  ncols=10,
                                  ascii=True,
                                  ):
                        time.sleep(1)  # needed so laser can warm up and turn on

                    state = self.getLaserStatus()
                    if state == 1:
                        print('Laser is enabled')  #
                    else:
                        print('Unable to enable laser')
            else:
                return print('Laser OFF')
        else:
            # print('Laser ON')  # return just the module info
            # turn_off = input('Would you like to disable the laser? (Y/n)')
            turn_off = 'Y'
            if turn_off == 'Y' or turn_off == 'y':
                msg3 = f'SOUR{self.slot}:POW:STAT OFF'
                try:
                    self.write(msg3)
                except:
                    print('Error disabling laser')
                finally:
                    time.sleep(3)  # needed so laser can turn off
                    state = self.getLaserStatus()
                    if state == 0:
                        print('Laser is disabled')  #
                    else:
                        print('Unable to disable laser')
            else:
                return print('Laser ON')

    def setLaserOUT(self, output):

        if output is True:
            msg2 = f'SOUR{self.slot}:POW:STAT ON'
            # should be :OUTPut[m][:CHANnel[d]][:STATe] ?? maybe
            try:
                self.write(msg2)
            except:
                print('Error enabling laser')
            finally:
                for a in tqdm(range(10),
                              desc='Warming Up...',
                              ncols=10,
                              ascii=True,
                              ):
                    time.sleep(1)  # needed so laser can warm up and turn on

                state = self.getLaserStatus()
                if state == 1:
                    print('Laser is enabled')  #
                else:
                    print('Unable to enable laser')
        else:
            msg3 = f'SOUR{self.slot}:POW:STAT OFF'
            try:
                self.write(msg3)
            except:
                print('Error disabling laser')
            finally:
                time.sleep(3)  # needed so laser can turn off
                state = self.getLaserStatus()
                if state == 0:
                    print('Laser is disabled')  #
                else:
                    print('Unable to disable laser')

    def getLaserFreqWav(self):
        msg = f'SOUR{self.slot}:FREQ?'  # get attenuation val of attenuator
        freq = float(self.query(msg))
        wav = np.round((c / freq) * 1e9, 3)
        # print(f'Laser wavelength on slot-{slot}: {wav} nm')
        return freq, wav  # freq given in Hz, wav given in nanometers

    def setLaserFreqWav(self, freq=193.1, wav=None):  # freq shown is default module freq 139.1 THz
        if wav is not None:
            freq = np.round((c / wav) * 1e-3, 1)  # wav in nm so convert from GHz to Thz
        else:
            pass
        freq = freq * 1e12  # convert input freq from THz to Hz
        msg = f'SOUR{self.slot}:FREQ {freq}'  # set using frequency (in Hz)
        return self.write(msg)

    def getLaserPow(self):
        msg = f'SOUR{self.slot}:POW:AMPL?'  # get power amp of laser
        pow = self.query(msg)
        # print(f'Laser power on slot-{self.slot}: {pow} mW')
        return pow

    def setLaserPow(self, dBm=10.0, mW=None):
        if mW is not None:
            dBm = np.round(10 * np.log10(1000 * mW / 1000), 2)  # PdBm = 10*Log_10(1000*W/1W)
            # print(dBm)
        else:
            pass
        msg = f'SOUR{self.slot}:POW:AMPL {dBm}'  # set power amp of laser in dBm
        return self.write(msg)

class yoAQ2212_Attenuator(visaInst):
    def __init__(self, frame_cont: yoAQ2212_frame_controller, slot=None, atten=None, params=None, **kwargs):
        """
        port, ipAddress,
        :param ipAddress: ie. '10.7.0.134'
        :param kwargs:
                     - offline: If True, then don't actually read/send data over visa
        """
        if (params):
            self.slot = params["slot"]
            atten = params["attenuation"]

        super().__init__(frame_cont, **kwargs)
        self.slot = slot
        self.frame_cont = frame_cont
        self.setAtten(atten)

    def write(self, msg):
        return self.frame_cont.write(msg)

    def query(self, msg):
        return self.frame_cont.query(msg)

    def getAtten(self):
        msg = f'INP{self.slot}:ATT?' # get attenuation val of attenuator
        atten = float(self.query(msg))
        # print(f'Attenuation on slot-{slot}: {atten} db')
        return atten

    def setAtten(self, atten):
        msg = f'INP{self.slot}:ATT {atten} '  # set attenuation val in dB
        result = self.write(msg)
        print(f'Attenuation on slot-{self.slot}: {atten} db')
        # time.sleep(5)
        return result

    def getAttenWav(self):
        msg = f'INP{self.slot}:WAV?'  # get attenuation wavelength
        return float(self.query(msg))*1e9

    def setAttenWav(self, wav):
        wav_str = f'+{wav}E-009' # input wav in nm
        msg = f'INP{self.slot}:WAV {wav_str} '  # set attenuation wavelength nm
        return self.write(msg)

    # the auto set does not work, but maybe we can make our own?
    # def setAttenWavAUTO(self, slot, laserSlot=1, dev=1): # test to see if we can auto-set wav to laser wav
    #     # wav_str = f'+{wav}E-009' # input wav in nm
    #     msg = f'INP{slot}:WAV:MDS S{laserSlot}D{dev}'  # set attenuation wavelength nm
    #     return self.write(msg)

    def getAttenOutStat(self):
        msg = f'OUTP{self.slot}:STAT?'  # get status of laser
        return int(self.query(msg)) #(0 = OFF, 1 = ON)

    def toggleAttenOut(self):
        start_state = self.getAttenOutStat()  # first ask if there is a module (0 = yes, 1 = no)
        if start_state == 0:
            msg2 = f'OUTP{self.slot}:STAT 1'
            self.write(msg2)
            print('Attenuation output is now ON')
        else:
            msg3 = f'OUTP{self.slot}:STAT 0'
            self.write(msg3)
            print('Attenuation output is now OFF')
        # time.sleep(4) you should wait at least 4 seconds between each toggle

    def setAttenOUT(self, output):

        if output is True:
            msg2 = f'OUTP{self.slot}:STAT 1'
            self.write(msg2)
            print('Attenuation output is now ON')
        else:
            msg3 = f'OUTP{self.slot}:STAT 0'
            self.write(msg3)
            print('Attenuation output is now OFF')
        # time.sleep(4) you should wait at least 4 seconds between each toggle

class yoAQ2212_Switch(visaInst):
    def __init__(self, frame_cont: yoAQ2212_frame_controller, slot=None, params=None, **kwargs):
        """
        port, ipAddress,
        :param ipAddress: ie. '10.7.0.134'
        :param kwargs:
                     - offline: If True, then don't actually read/send data over visa
        """
        if (params):
            slot = params["slot"]

        super().__init__(frame_cont, **kwargs)
        self.slot = slot
        self.frame_cont = frame_cont

    def write(self, msg):
        return self.frame_cont.write(msg)

    def query(self, msg):
        return self.frame_cont.query(msg)

    def getSwitchStat(self, dev=1):  # select the device to check
        # msg = f'ROUT{slot}:CHAN{dev}:CONF?'  # get status of switch
        msg = f'ROUT{self.slot}:CHAN{dev}?'  # get status of switch
        return self.query(msg)

    def toggleSwitch(self, dev=1):
        state = int(self.getSwitchStat(dev=dev).split(',')[1])
        print(state)
        if state == 1:
            switch = 2
        else:
            switch = 1
        msg = f'ROUT{self.slot}:CHAN{dev} A,{switch}'  # toggle switch (1 or 2)
        return self.write(msg)

    def setSwitch(self, position, dev):
        msg = f'ROUT{self.slot}:CHAN{dev} A,{position}'  # toggle switch (1 or 2)
        switch = self.write(msg)
        # time.sleep(5)
        return switch

class yoAQ2212_PowerMeter(visaInst):
    def __init__(self, frame_cont: yoAQ2212_frame_controller, slot=None, params=None, **kwargs):
        """
        port, ipAddress,
        :param ipAddress: ie. '10.7.0.134'
        :param kwargs:
                     - offline: If True, then don't actually read/send data over visa
        """
        if (params):
            slot = params["slot"]
        super().__init__(frame_cont, **kwargs)
        self.slot = slot
        self.frame_cont = frame_cont

    def write(self, msg):
        return self.frame_cont.write(msg)

    def query(self, msg):
        return self.frame_cont.query(msg)

    def getPowerMeas(self):  # display value read (dBm); includes power offset
        msg = f'FETC{self.slot}:POW?'  # get amplitude of power measurement
        return float(self.query(msg))  # allows for reading instrument while lcd continually updates

    def getPowerMeasSing(self):  # single power read measurement (W)
        msg = f'READ{self.slot}:POW?'  # get amplitude of power measurement
        return float(self.query(msg))

    # def getMeasMode(self, slot):
    #     msg = f'SENS{slot}:POW:REF:STAT?'  # get measurement mode of power meter
    #     return self.query(msg)
    #
    # def setMeasMode(self, slot, measmode): # not working yet ...
    #     # options: 0: Normal | 1: Single | 2: Input Trig
    #     msg = f'SENS{slot}:POW:REF:STAT {measmode}'  # set measurement mode of power meter
    #     # msg = f'SENS{slot}:AOUT:TRIG:OUTP {measmode}' # for trigger mode??
    #     return self.write(msg)

    def getMeasAvg(self):
        msg = f'SENS{self.slot}:POW:ATIM? '  # get status of laser
        return float(self.query(msg))  # shown in seconds

    def setMeasAvg(self, avgtime):  # will auto set to nearest value
        # set options: 0.0001, 0.0002, 0.0005 (us)
        #             0.001, 0.002, 0.005 (ms)
        #             0.01, 0.02, 0.05, 0.1, 0.2, 0.5 (ms)
        #             1, 2, 5, 10 (s)
        msg = f'SENS{self.slot}:POW:ATIM {avgtime} '  # set averaging time of power measurements
        return self.write(msg)

    def getMeasWav(self):
        msg = f'SENS{self.slot}:POW:WAV?'  # get power meter measurement wavelength
        return self.query(msg)

    def setMeasWav(self, wav):
        wav_str = f'+{wav}E-009'  # input wav in nm
        msg = f'SENS{self.slot}:POW:WAV {wav_str}'  # set wavelength of measurement
        return self.write(msg)

    def setMeasWavAUTO(self, laserSlot=1, dev=1):  # set laser slot number and device number if not default
        msg = f'SENS{self.slot}:POW:WAV:MDS S{laserSlot}D{dev}'  # sets to wavelength of laser automatically
        return self.write(msg)

    def setMeasTime(self, time=1, unit="S"):
        # options for time:
        # US: 100, 200, 500
        # MS: 1, 2, 5, 10, 20, 50, 100, 200, 500
        #  S: 1, 2, 5, 10

        msg = f'SENS{self.slot}:POW:ATIM{time}{unit}'  # sets to wavelength of laser automatically
        return self.write(msg)

    def getMeasTime(self):
        msg = f'SENS{self.slot}:POW:ATIM?'  # sets to wavelength of laser automatically
        return self.query(msg)

    # def getMeasCal(self, slot):
    #     msg = f'xxx{slot}:xxx:xxxx? '  # get current calibration val of power meter
    #     return state
    #
    # def setMeasCal(self, slot):
    #     msg = f'xxx{slot}:xxx:xxxx? '  # set calibration of power meter
    #     return state

class yokogawa:
    def __init__(self, params):
        self.inst = yoAQ2212_frame_controller(params=params["Frame Controller"])  # attempts to autoconnect
        self.laser = yoAQ2212_laser(frame_cont=self.inst, params=params["Laser"])
        
        self.attenuators = {}

        for atten_name, settings in params['Attenuators'].items():
            atten_obj = yoAQ2212_Attenuator(frame_cont=self.inst, params=settings)
            self.attenuators[atten_name] = atten_obj

        self.switch = yoAQ2212_Switch(frame_cont=self.inst, params=params["Switch"])
        self.pwrmeter = yoAQ2212_PowerMeter(frame_cont=self.inst, params=params["Power Meter"])

def test_routine_1(test_routine=True):
    # all controls must be in off position before starting
    data_test1 = np.zeros(10)

    try:
        inst = yoAQ2212_frame_controller(ipAddress="192.168.0.145", port=50000)  # attempts to autoconnect
        laser = yoAQ2212_laser(frame_cont=inst, slot=1)
        atten1 = yoAQ2212_Attenuator(frame_cont=inst, slot=2)
        atten2 = yoAQ2212_Attenuator(frame_cont=inst, slot=3)
        atten3 = yoAQ2212_Attenuator(frame_cont=inst, slot=4)
        switch = yoAQ2212_Switch(frame_cont=inst, slot=5)
        pwrmeter = yoAQ2212_PowerMeter(frame_cont=inst, slot=6)
        print('Connected to Yokogawa AQ2212.')
        try:

            if test_routine is True:
                # Now we will run a routine script to get a power measurement from the laser
                # The laser will be set at 1550nm, 2 attenuators at 30 dB, and we will
                # use the switch to first take measurement then swap to the Thorlabs PM

                # setup laser
                laser.setLaserFreqWav(wav=1550.0)
                print('Laser wavelength: ', laser.getLaserFreqWav())
                time.sleep(0.5)
                laser.setLaserPow(mW=10.0)  # input in dBm or mW
                print('Laser power: ', laser.getLaserPow())
                time.sleep(0.5)

                # setup attenuators
                # inst.setAtten(2, 30.0)
                print(f'Atten1 attenuation set to {atten1.getAtten()} dB')
                time.sleep(0.5)
                # inst.setAtten(3, 30.0)
                print(f'Atten2 attenuation set to {atten2.getAtten()} dB')
                time.sleep(0.5)
                # inst.setAttenWav(2, 1550)  # enter in nm
                print(f'Atten1 wavelength set to {atten1.getAttenWav()} nm')
                time.sleep(0.5)
                # inst.setAttenWav(3, 1550)  # enter in nm
                print(f'Atten2 wavelength set to {atten2.getAttenWav()} nm')
                time.sleep(0.5)
                # toggle attenuator outputs to ON
                atten1.toggleAttenOut()
                time.sleep(0.5)
                atten2.toggleAttenOut()
                time.sleep(0.5)

                # toggle laser on
                print('Attempting to turn on laser now ...')
                laser.toggleLaser()  # maybe make this laser.toggleLaser(set='ON') and adjust to make sure its on or off
                time.sleep(1)
                # take 10 data points
                for i in range(len(data_test1)):
                    data_test1[i] = pwrmeter.getPowerMeasSing()
                    time.sleep(0.5)
                time.sleep(1)

                # print(f'Average power read from {inst.getModule(6)}: {np.mean(data_test1)} W')
                print(f'Average power read: {np.mean(data_test1)} W')

                # toggle switch to see on power meter
                switch.toggleSwitch(
                    dev=1)  # maybe updat this to do the same as laser above switch.toggle(1, dev=1) or 2
                for i in range(5):
                    time.sleep(1)
                    print('Waiting...')
                # toggle back to in box power meter
                switch.toggleSwitch()
                time.sleep(0.5)

                # turn off atten outputs and laser
                # see finally statement

                print('Test Successful')

            else:
                # subclass testing:
                print(laser.getModule())

                # Bellow are the tests used to check each function for running the system
                # print(inst.getModule(1))
                # print(inst.getModule(6))

                # inst.getLaserFreqWav(1)
                # # inst.setLaserFreqWav(1, freq=193.4)
                # inst.setLaserFreqWav(1, wav=1550.0)
                # inst.getLaserFreqWav(1)
                # print(inst.getModule(7))
                # print(inst.getLaserPow(1))
                # inst.setLaserPow(1, mW=10.0)# input in dBm or mW
                # inst.setLaserPow(1, mW=11.0)  # input in dBm or mW
                print(laser.getLaserPow())
                # inst.toggleLaser(1)
                # print('laser toggle success')

                # inst.getAtten(2)
                # inst.setAtten(2,30.0)
                # inst.getAtten(2)
                # print(inst.getAttenOutStat(2))
                # inst.toggleAttenOut(2)
                # print(inst.getAttenOutStat(2))
                # print(inst.getAttenWav(2))
                # inst.setAttenWav(2, 1549) # enter in nm
                # print(inst.getAttenWav(2))
                # print(f'Atten2 wavelength set to {inst.getAttenWav(2)} nm')

                # print(inst.getSwitchStat(5))
                # inst.toggleSwitch(5, dev=1)
                # print(inst.getSwitchStat(5))

                # print(inst.getPowerMeas(6))
                # print(inst.getPowerMeasSing(6))
                # time.sleep(2)
                # print(inst.getMeasMode(6))
                # inst.setMeasMode(6, 0)
                # print(inst.getMeasMode(6))
                # print(inst.setMeasMode(6, ))
                # print(inst.getMeasAvg(6))
                # inst.setMeasAvg(6, 0.05)
                # print(inst.getMeasAvg(6))
                # print(inst.getMeasWav(6))
                # inst.setMeasWav(6, 1515.0) # in nm
                # print(inst.getMeasWav(6))
                # time.sleep(3)
                # inst.setMeasWavAUTO(6)
                # print(inst.getMeasWav(6))

                # inst.toggleLaser(1)
                # time.sleep(1)
                # inst.set_date()
                # print('Date Set.')
                # inst.set_time()
                # print('Time Set')
                # inst.set_date(year=2023, month=11, day=18)

                pass
        except:
            print('Failed to execute.')
        finally:
            if test_routine == 1:
                # turn off and toggle outputs
                atten1.toggleAttenOut()
                time.sleep(1)
                atten2.toggleAttenOut()
                time.sleep(1)
                laser.toggleLaser()
                time.sleep(1)

            # disconnect from the devices
            inst.disconnect()
            print('Disconnected from Yokogawa AQ2212.')
    except Exception as e:
        print(e)
        print('Failed to connect.')

if __name__ == '__main__':
    test_routine_1()


