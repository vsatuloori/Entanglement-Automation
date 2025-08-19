
import numpy as np 
import ctypes
import threading
import enum 
from dataclasses import dataclass
import math 
import matplotlib.pyplot as plt
import sys
import os

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
#print(f'PYPOLARIMETER DIRECTORY {parent_dir}')
sys.path.append(parent_dir)

from PolarimeterSupport.PyAB3510Driver import PyAB3510Driver

class OnTimer(object):
    def __init__(self, interval, function, *args, **kwargs):
        self._timer     = None
        self.interval   = interval
        self.function   = function
        self.args       = args
        self.kwargs     = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self._timer = threading.Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False

# -----------------------------------------------------------------------------

######  AB1050 Board ######
class IOBit(enum.Enum):
    A0 = 0
    A1 = 1
    A2 = 2
    A3 = 3
    A4 = 4
    A5 = 5
    A6 = 6
    A7 = 7
    B0 = 8
    B1 = 9
    B2 = 10
    B3 = 11
    B4 = 12
    B5 = 13

# AB1050Board = PyAB1050Driver()
# AB1050Board.Open()
# AB1050Board.GetSerialNumber()
    
######  Struct and Enum ######
class PolarDisplay(enum.Enum):
    pdPoincare = 0
    pdJones = 1
    pdSpectrum = 2

class PolarPath(enum.Enum):
    ppFull = 0
    ppFiltered = 1 

@dataclass 
class SOP: 
    S0: float
    S1: float
    S2: float
    S3: float
    Power: float
    Time: float 
    Wavelength: float 

## Calibration of the State of Polarization
class CalibrationSOP:
    Matrix=[[float]*4]*4
    dWavelength= float
    CalYesNo= bool    


## Calibration of the Polar
class CalibrationPolar():
    def __init__(self):
        self.Matrix = [[float]*4]*4
        self.Wl = float
        self.CalYesNo = bool


class PyPolarimeter(): 
    def __init__(self):
        
        # Angele of Sphere 
        self.XSphereAngle = 45
        self.YSphereAngle = 10
        
        # Sphere Radius   
        self.SphereRadius = 100
        self.PointRadius = 1
        
        # time of acqusition 
        self.AcqTime= 0.0
        
        # Initialize the SOP struct: initalize all paramters of state of polarization (SOP)
        self.s = SOP(S0=0.0, S1=0.0, S2=0.0, S3=0.0, Power = 0.0, Time = 0.0, Wavelength=0.0)
        self.s.S0 = 1.0 
        self.s.S1 = 1/np.sqrt(3)
        self.s.S2 = 1/np.sqrt(3)
        self.s.S2 = 1/np.sqrt(3)
        
        # Default Poincare display 
        self.dMode = PolarDisplay.pdPoincare.value
        
        # Time interval of Timer 
        self.Time_interval = 200e-3
        
        #  Timer
        self._timer =  threading.Timer(0.2,2**2)
        
        # Set polarimeter path (Input Pol./Pw)
        self.pPath = PolarPath.ppFull.value
        
        # Polarimeter Wavelength 
        self.PolarWavelength = 1550.00
        
        # Initialize the AB3510 board
        self.pAB3510 = PyAB3510Driver()
        
        # Initialize the AB1050 acq. board
        # self.AB1050Board = PyAB1050Driver()
   
    def Open(self): 
        Handles = np.zeros(10, dtype = np.int32)
        # AB3510Board.FindBoards(Handles)
        self.pAB3510.FindBoards1(Handles)
        status = self.pAB3510.Open(Handles[0], False) 
        
        if status == self.pAB3510.AB3510_EEPROM_ERROR: 
            # struct of EmbeddedData
            eData =  self.pAB3510.EmbeddedData
            status = self.pAB3510.SetDefaultParameters(eData)
            if not self.pAB3510.CreateCalibTable(eData):
                status = self.pAB3510.AB3510_CALIBRATION_ERROR
            else: 
                self.pAB3510.SetParametersToEEPROM(eData)
    
    def Close(self): 
        Handles = np.zeros(10, dtype = np.int32)
        # AB3510Board.FindBoards(Handles)
        self.pAB3510.FindBoards1(Handles)
        status = self.pAB3510.Close() 
        if status == self.pAB3510.AB3510_EEPROM_ERROR: 
            # struct of EmbeddedData
            eData =  self.pAB3510.EmbeddedData
            status = self.pAB3510.SetDefaultParameters(eData)
            if not self.pAB3510.CreateCalibTable(eData):
                status = self.pAB3510.AB3510_CALIBRATION_ERROR
            else: 
                self.pAB3510.SetParametersToEEPROM(eData)
        
    def PolarAcq_TimerTimer(self):
        # Get the center wavelength: 
        # FULL BANDWIDTH: Measure with the input (Pol./PW) and no filter 
        # 170 pm  BANDWIDTH: mesure with the input going to the filter 
        if self.pPath == PolarPath.ppFiltered.value:
            # self.pPath = ctypes.c_int(PolarPath.ppFull.value)                       
            # Wavelength = ctypes.c_float(PolarWavelength) # Get wavelength for Filter AB338x
            Wavelength = self.PolarWavelength
        else: 
            # pPath = ctypes.c_int(PolarPath.ppFull.value)                       
            # Wavelength = ctypes.c_float(PolarWavelength)
            Wavelength = self.PolarWavelength
        
        sop = self.pAB3510.SOP
        self.pAB3510.GetOneSample2(sop, ctypes.c_int(self.pPath), ctypes.c_float(Wavelength))
        
        # Measurement Results
        self.s.S0 = sop.S0
        self.s.S1 = sop.S1
        self.s.S2 = sop.S2
        self.s.S3 = sop.S3
        self.s.Power = sop.Power
        self.s.Wavelength = Wavelength
        
        self.s.Time = self.AcqTime
        
        # vs.append(s)
        if (self.dMode == PolarDisplay.pdPoincare.value):
            self.DisplaySOPPoincare(self.s)
        else: 
            # Display the results
            self.DisplaySOPJones(self.s)
            
    def SetDisplayMode(self, mode, Run=True):
        
        if (mode == PolarDisplay.pdPoincare.value): # Poincare sphere (Poincare mode)
            self.dMode = PolarDisplay.pdPoincare.value
            self.SphereRadius = 200    
            if(Run): 
                print("poincare mode display")
                self._timer = OnTimer(self.Time_interval, self.PolarAcq_TimerTimer)
                # self._timer = threading.Timer(self.Time_interval, self.PolarAcq_TimerTimer)
                # self._timer.start()
            # return obj_timer
        
        elif(mode == PolarDisplay.pdJones.value):  # Jones vecor (Jones mode)
            self.dMode = PolarDisplay.pdJones.value
            self.SphereRadius = 200
            if (Run): 
                # this->PolarAcq_Timer->Enabled = true; # Enable the Timer
                # print("execute the Jones mode")
                # PolarAcq_TimerTimer(pPath)
                print("Jones mode display")
                self._timer = OnTimer(self.Time_interval, self.PolarAcq_TimerTimer)
                # self._timer = threading.Timer(self.Time_interval, self.PolarAcq_TimerTimer)
                # self._timer.start()
            # return obj_timer
        elif(mode == PolarDisplay.pdSpectrum.value): 
            self.dMode = PolarDisplay.pdSpectrum.value
            self.SphereRadius = 200
            print("Spectrum mode: ", self.dMode)
            # Draw sphere: DrawSphere
        
    def DisplaySOPPoincare(self, vs):
        #  Results Display 
        print("\n------- POINCARE Mode : --------")
        print("Power: ", "{:.2f}".format(vs.Power), " dBm")
        print("Wavelength: ", vs.Wavelength, " nm")
        
        # calculate DOP 
        DOP = math.sqrt((vs.S1)**2 + (vs.S2)**2 + (vs.S3)**2)/vs.S0
        DOP *= 100.0
        print("DOP: ", "{:.2f}".format(DOP), "%")
        print("Stokes Parameters:")
        # Stokes parameters 
        print("S1 : ", "{:.2f}".format(vs.S1))
        print("S2 : ", "{:.2f}".format(vs.S2))
        print("S3 : ", "{:.2f}".format(vs.S3))
        
    def DisplaySOPJones(self, state, b_plot = False): 
        # calculate DOP 
        DOP = math.sqrt((state.S1)**2 + (state.S2)**2 + (state.S3)**2)/state.S0

        DOP *= 100.0
        # Normalized Stockes parameters 
        state.S1 /= state.S0
        state.S2 /= state.S0
        state.S3 /= state.S0

        # Ellipticity of polarization state 
        Epsilon = 0.5 * math.asin(state.S3)

        # Azimuth (tilt angle) orientation of polarization state 
        Theta = 0.5 * math.atan(state.S2 /state.S1)

        # length of semi-major axis (a) 
        # length of semi-minor axis (b) 
        b = 0.75 *self.SphereRadius
        a = b * math.tan(Epsilon) 

        #  Results Display 
        print("\n------- JONES Mode : --------")
        print("Power: ", "{:.2f}".format(state.Power), " dBm")
        print("Wavelength: ", state.Wavelength, " nm")
        print("DOP: ", "{:.2f}".format(DOP), "%")
        print("Azimuth and Ellipticity: ")
        print("Azimuth : ", "{:.2f}".format(Theta*180/math.pi),"°")
        print("Ellipticity: ", "{:.2f}".format(Epsilon*180/math.pi),"°")
        
        # Figures 
        if b_plot: 
            #  Draw ellipse 
            N = 360
            Th = np.zeros(N,dtype = float) 
            for i in range (N): 
                Th[i] =  i*math.pi/180 
                
            X_axis = np.zeros(N, dtype=float)
            Y_axis = np.copy(X_axis)
        
            for i in range(N): 
                y = a*b*math.cos(Th[i])/math.sqrt((b * math.cos(Th[i]))**2 + (a * math.sin(Th[i]))**2)     
                x = a * b * math.sin(Th[i])/math.sqrt((b * math.cos(Th[i]))**2 + (a * math.sin(Th[i]))**2)                                
                X_axis[i] = x * math.cos(-Theta) + y * math.sin(-Theta)
                Y_axis[i] = y * math.cos(-Theta) - x * math.sin(-Theta)
                    
        
            plt.figure()
            # Remove ticks and labels on x-axis and y-axis both
            ax = plt.gca()
            ax.axes.xaxis.set_visible(False)
            ax.axes.yaxis.set_visible(False)
        
            plt.plot([0.0, 0.0], [-self.SphereRadius, +self.SphereRadius], 'k')
            plt.plot([-self.SphereRadius, +self.SphereRadius], [-0.0, 0.0], 'k')
            plt.plot(X_axis, Y_axis)
            plt.grid(color='lightgray',linestyle='--')
            plt.grid(True)
            plt.show()
    
    def SetPolarPath(self,path):
        self.pPath = path
        # bit = IOBit.B5.value
        
        # if self.pPath == PolarPath.ppFull.value: 
        #     UlStat = AB1050Board.SetOutBit(bool(1), bit)
        #     # Acquis.SetOutBit(bBit, iChannel)
        # else:
        #     UlStat = AB1050Board.SetOutBit(bool(0), bit)
        
        # print("UlStat = ", UlStat)
        
    def LoadFileTxT(self,obj,path_CalSOP):
        data = np.loadtxt(path_CalSOP,skiprows=2)
        
        obj.Wl = data[:, 0].tolist()
        obj.CalYesNo = data[:, 1].tolist()
        for i in range(data.shape[0]):
            Mat = data[i,2:].reshape((4, 4))
            obj.Matrix.append(Mat.tolist())
        return  data.shape[0]
    
    def GetCalOffset(self,Npoint,WavelengthCur,Mat,sop_offset):              
        if(WavelengthCur == Mat.Wl[0]):
            sop_offset.dWavelength = Mat.Wl[0]
            sop_offset.CalYesNo = int(Mat.CalYesNo[0])
            for k1 in range(4): 
                for k2 in range(4):
                    sop_offset.Matrix[k1][k2] = Mat.Matrix[0][k1][k2]
        else:
            for i in range(Npoint-1):
                dWlength = (Mat.Wl[i+1] - Mat.Wl[i])/2
                if ((WavelengthCur > Mat.Wl[i]) & (WavelengthCur <= Mat.Wl[i+1] - dWlength)):
                    sop_offset.dWavelength = Mat.Wl[i]
                    sop_offset.CalYesNo = int(Mat.CalYesNo[i])
                    for k1 in range(4): 
                        for k2 in range(4):
                            sop_offset.Matrix[k1][k2] = Mat.Matrix[i][k1][k2]
                elif((WavelengthCur > Mat.Wl[i] + dWlength) & (WavelengthCur <= Mat.Wl[i+1])):
                    sop_offset.dWavelength = Mat.Wl[i+1]
                    sop_offset.CalYesNo = int(Mat.CalYesNo[i+1])
                    for k1 in range(4): 
                        for k2 in range(4):
                            sop_offset.Matrix[k1][k2] = Mat.Matrix[i+1][k1][k2]
        return sop_offset
        
    def GetSOPAndPOWER(self,WavelengthCur,CalSOP,Normalise):
        Wavelength = WavelengthCur
        sop = self.pAB3510.SOP
        self.pAB3510.GetOneSamplewithCal(sop, ctypes.c_int(self.pPath), ctypes.c_float(Wavelength),CalSOP,ctypes.c_bool(Normalise))            
        # Measurement Results
        self.s.S0 = sop.S0
        self.s.S1 = sop.S1
        self.s.S2 = sop.S2
        self.s.S3 = sop.S3
        self.s.Power = sop.Power
        self.s.Wavelength = Wavelength
        self.s.Time = self.AcqTime
        # print("S1 : ", "{:.3f}".format(self.s.S1))
        # print("S2 : ", "{:.3f}".format(self.s.S2))
        # print("S3 : ", "{:.3f}".format(self.s.S3))
        # print("Power: ", "{:.3f}".format(self.s.Power), " dBm")
        del sop
        return self.s
        
    def HorizontalCalibration(self,WavelengthCur,MatrixCal):
        Wavelength = WavelengthCur 
        self.pAB3510.HorizontalCalib(ctypes.c_float(Wavelength),MatrixCal)
        return MatrixCal
    
    def VerticalCalibration(self,WavelengthCur,MatrixCal):
        Wavelength = WavelengthCur 
        self.pAB3510.VerticalCalib(ctypes.c_float(Wavelength),MatrixCal)
        return MatrixCal
    
    def LinearCalibration(self,WavelengthCur,MatrixCal,Tab_MatrixCal):
        Wavelength = WavelengthCur 
        self.pAB3510.LinearCalib(ctypes.c_float(Wavelength),MatrixCal,Tab_MatrixCal)
        return MatrixCal
        
    def Horizontal_Cal_Function(self,Npoint,WavelengthCur,MatrixAfterCal,Tab_MatrixCal):
        self.HorizontalCalibration(WavelengthCur,MatrixAfterCal)
        for i in range(Npoint-1): 
            if WavelengthCur == Tab_MatrixCal.Wl[i]:
                Tab_MatrixCal.CalYesNo[i] = 1
                for j in range(4):
                    Tab_MatrixCal.Matrix[i][j] = MatrixAfterCal.Matrix[j][:]
        
    def LinearCal_Function(self,Npoint,WavelengthCur,MatrixAfterCal,Tab_MatrixCal,MatrixCal_WlCur):
            self.LinearCalibration(WavelengthCur,MatrixAfterCal,MatrixCal_WlCur)
            for i in range(Npoint-1): 
                if WavelengthCur == Tab_MatrixCal.Wl[i]:
                    Tab_MatrixCal.CalYesNo[i] = 1
                    for j in range(4):
                        Tab_MatrixCal.Matrix[i][j] = MatrixAfterCal.Matrix[j][:]
    
    def Vertical_Cal_Function(self,Npoint,WavelengthCur,MatrixAfterCal,Tab_MatrixCal):
        self.VerticalCalibration(WavelengthCur,MatrixAfterCal)
        for i in range(Npoint-1): 
            if WavelengthCur == Tab_MatrixCal.Wl[i]:
                Tab_MatrixCal.CalYesNo[i] = 1
                for j in range(4):
                    Tab_MatrixCal.Matrix[i][j] = MatrixAfterCal.Matrix[j][:]
    
    def SaveTextFile(self,path,Npoint,Tab_MatrixCal):
        file = open(path, "w+")
        file.write("")
        file.write("VERSION" + '\t' + str(1.0)+ '\t\n')
        file.write("POINTS" + '\t'+ str(Npoint) + '\t\n')
        for j in range(Npoint):
            Ar = np.array(np.round(Tab_MatrixCal.Matrix[j],5)).reshape(1,-1)
            StrAr =""
            StrAr +=str(int(Tab_MatrixCal.Wl[j])) +'\t'
            StrAr +=str(int(Tab_MatrixCal.CalYesNo[j])) +'\t'
            for i in range(len(Ar[0])):
                StrAr +=(str(Ar[0][i])) + '\t'
            
            file.write(str(StrAr) + '\t\n')
        file.close() 
    
    def RestoreFactoryOrUserCalibration(self,path1,path2,path3,Npoint,Tab_MatrixCal,factoryCal,UserSystemCal):
        #There are three text files in the "Polarimeter Files" folder. If the user want to back to the factory calibration file.
        #They need to use this function. 
        #path1: is the UserSystemMatrixFile.txt path
        #path2: is the UserPolarFile.txt path
        #path3: is the UserCurrentWLFile.txt path
        #Tab_MatrixCal: contain the data in the UserSystemMatrixFile.txt
        #factoryCal: True : restore the factory calibration file , False: restore the data calibration in the UserSystemMatrixFile.txt file
        #UserSystemCal: True:restore the UserSystemCal
        if factoryCal:
            PolarStruct = self.pAB3510.PolarV1
            for i in range(Npoint):
                WavelengthCur = Tab_MatrixCal.Wl[i]
                Tab_MatrixCal.CalYesNo[i] = 0
                self.pAB3510.GetPolarParameters(ctypes.c_int(self.pPath),ctypes.c_float(WavelengthCur),PolarStruct)
                for j in range(4):
                    for k in range(4):
                        Tab_MatrixCal.Matrix[i][j][k] = PolarStruct.Matrix[j][k]
            self.SaveTextFile(path1,Npoint,Tab_MatrixCal)
            self.SaveTextFile(path2,Npoint,Tab_MatrixCal)
            self.SaveTextFile(path3,Npoint,Tab_MatrixCal)
        elif ((factoryCal == False) & (UserSystemCal)):                  
            Npoint = self.LoadFileTxT(Tab_MatrixCal,path1)
            self.SaveTextFile(path2,Npoint,Tab_MatrixCal)
            self.SaveTextFile(path3,Npoint,Tab_MatrixCal)
        elif ((factoryCal == False) & (UserSystemCal== False)):
            Npoint = self.LoadFileTxT(Tab_MatrixCal,path2)
            self.SaveTextFile(path3,Npoint,Tab_MatrixCal)
        
        
    
    