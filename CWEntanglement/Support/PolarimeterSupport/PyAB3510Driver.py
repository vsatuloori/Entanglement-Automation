
import ctypes 
# import threading
import numpy as np 
import os
import sys

directory = os.getcwd()
#print(f'DIRECTORYYYY: {directory}')
path_dll = directory + "\Components\Support\PolarimeterSupport\PyAB3510.dll"

lib = ctypes.cdll.LoadLibrary(path_dll)



class PyAB3510Driver():
         
    # Constructor 
    def __init__(self):
        
        ####### AB3510 STATUS ######### 
        self.AB3510_EEPROM_ERROR = 71
        self.AB3510_OK = 0
        
        ####### CALIBRATION CONSTANTS ######### 
        self.AB3510_MAXIMUM_POINTS_CALIB	= 200
        self.AB3510_POLAR_PATH = 3
        self.AB3510_POLAR_MATRIX_WAVELENGTH = 10
        
        ####### Struct definition ######### 
        # A binary power sample for each channel 
        class Sample(ctypes.Structure): 
            _fields_ = [
                        ("Channel0", ctypes.c_ushort),
                        ("Channel1", ctypes.c_ushort),
                        ("Channel2", ctypes.c_ushort),
                        ("Channel3", ctypes.c_ushort)
                       ]
        
        # The power (in dBm) is converted from the calibration 
        class PowerSample(ctypes.Structure): 
            _fields_ = [
                        ("Channel0", ctypes.c_float),
                        ("Channel1", ctypes.c_float),
                        ("Channel2", ctypes.c_float),
                        ("Channel3", ctypes.c_float)
                       ]
        # A state of polarization 
        class SOP(ctypes.Structure): 
            _fields_ = [
                        ("S0", ctypes.c_float),
                        ("S1", ctypes.c_float),
                        ("S2", ctypes.c_float),
                        ("S3", ctypes.c_float),
                        ("Power", ctypes.c_float)
                       ]
        
        class CalibrationSOP(ctypes.Structure):
            _fields_ = [
                        ("Matrix", (ctypes.c_float*4)*4),
                        ("dWavelength",ctypes.c_float),
                        ("CalYesNo",ctypes.c_bool)
                        ]
    
        # class CalibrationPolar(ctypes.Structure):
        #     _fields_ = [
        #                 ("Matrix", (ctypes.c_float*4)*4),
        #                 ("Wl",ctypes.c_float),
        #                 ("CalYesNo",ctypes.c_bool)
        #                 ]

        # Header data of the board 
        class EmbeddedHeader(ctypes.Structure):
             _fields_ = [
                         ("SerialNumber", ctypes.c_char * 20),
                         ("FirmwareVersion", ctypes.c_char * 6),
                         ("EEPromVersion", ctypes.c_char * 6)           
                        ]
             
        
        # Power Calibration data of the board for 1 channel - Version 1
        class CalibrationV1(ctypes.Structure):
             _fields_ = [("NbPoints", ctypes.c_ushort),
                        ("Power", ctypes.c_float * self.AB3510_MAXIMUM_POINTS_CALIB),      # float Power[AB3510_MAXIMUM_POINTS_CALIB];
                        ("RawData", ctypes.c_ushort * self.AB3510_MAXIMUM_POINTS_CALIB),   # unsigned short RawData[AB3510_MAXIMUM_POINTS_CALIB];
                        ("TempCoeff1", ctypes.c_float),
                        ("TempCoeff0", ctypes.c_float),
                        ("WavelengthCoeff1", ctypes.c_float),
                        ("WavelengthCoeff0", ctypes.c_float)
                        ]
        # Power Calibration data of the board for 1 channel - Version 2 
        class CalibrationV2(ctypes.Structure):
             _fields_ = [
                        ("NbPoints", ctypes.c_ushort),
                        ("Power", ctypes.c_float * self.AB3510_MAXIMUM_POINTS_CALIB),      # float Power[AB3510_MAXIMUM_POINTS_CALIB];
                        ("RawData", ctypes.c_ushort * self.AB3510_MAXIMUM_POINTS_CALIB),   # unsigned short RawData[AB3510_MAXIMUM_POINTS_CALIB];
                        ("NormPoints", ctypes.c_ushort),
                        ("NormWavelength", ctypes.c_float * self.AB3510_MAXIMUM_POINTS_CALIB),
                        ("NormCoeff", ctypes.c_float * self.AB3510_MAXIMUM_POINTS_CALIB),
                        ("TempCoeff1", ctypes.c_float),
                        ("TempCoeff0", ctypes.c_float)
                        ]
        # Polarization Calibration data of the board - Version 1 
        # https://stackoverflow.com/questions/11384015/python-ctypes-multi-dimensional-array
        class PolarV1(ctypes.Structure):
            _fields_ = [ # Mueller matrix of the polarimeter 
                        ("Matrix", (ctypes.c_float*4)*4),
                        # Power offset between power measurement and power calibration 
                        ("Offset", ctypes.c_float)]
        
        # Polarization Calibration data of the board - Version 2 
        class PolarV2(ctypes.Structure): 
            _fields_ = [
                        # Muller matrix of the polarimeter 
                        ("Matrix", (ctypes.c_float*4)*4),
                        # Power offset between power measurement and power calibration 
                        ("Offset", ctypes.c_float),
                        ("Wavelength", ctypes.c_float)
                        ]
        
        # Embedded Calibration data of the board for all channels - Version 1.0
        class EmbeddedDataV0100(ctypes.Structure):
            _fields_ = [
                        # Power calibration data Version 1 for all channels 
                        ("Channels", CalibrationV1*4),
                        # Polarization Calibration data Version 1 for all paths (3 paths)
                        ("PolarPath", PolarV1*self.AB3510_POLAR_PATH)
                       ]
        
        # Embedded Calibration data of the board for all channelqs - Version 1.1
        class EmbeddedDataV0101(ctypes.Structure):
            _fields_ = [
                        # Power Calibration data Version 2 for all channels
                        ("Channels", CalibrationV2*4),
                        # \brief Polarization Calibration data Version 2 for all paths (3 paths) and different wavelengths
                        ("PolarPath", (PolarV2*self.AB3510_POLAR_PATH)*self.AB3510_POLAR_MATRIX_WAVELENGTH)
                       ]
            
        # //! \brief Structure of the embedded data
        # //! This data take in account all calibration data version. These versions
        # //! are saved in the 'union' structure. This data can be saved in an INI file
        # //! or in the EEPROM.
        # https://stackoverflow.com/questions/46534736/ctypes-structure-with-variable-types
        class EmbeddedData(ctypes.Structure):
             _fields_ = [
                        # //! \brief Board general data
                        # //! This header has to be common to all Embedded data versions
                         ("Header",  EmbeddedHeader),
                        # //! \brief Union with all Calibration data
                        # //!
                        # //! \b Be \b careful, each embedded data version is starting at the
                        # //! same address. So, only one version has to be used at a time.
                        # //! \brief Embedded Data for EEPROM version 1.0 only
                        # //! \brief Embedded Data for EEPROM version 1.0 only
                         ("edv0100", EmbeddedDataV0100),
                        # //! \brief Embedded Data for EEPROM version 1.1 only
                         ("edv0101",EmbeddedDataV0100) 
                         ]
        
        ######## Struct Initialization  ########
        self.EmbeddedData = EmbeddedData()
        self.Sample = Sample()
        self.PowerSample = PowerSample()
        self.SOP = SOP()
        self.CalibrationSOP = CalibrationSOP()
        self.PolarV1 = PolarV1()
        self.PolarV2 = PolarV2()
        # self.CalibrationPolar = CalibrationPolar()
        
        ####### TYPE of PYTHON FUNCTIONS #########
        
        #=====================================================================
        #      Hardware control 
        #=====================================================================
        # ---------------------------------------------------------------------
        # __declspec(dllexport) AB3510 * AB3510_new() {return new AB3510();}
        lib.AB3510_new.restype = ctypes.c_void_p
        lib.AB3510_new.argtypes = []
        
        # ---------------------------------------------------------------------
        # __declspec(dllexport) unsigned short PyOpen(AB3510* pAB3510, int Handle, bool Simulation)
        lib.PyOpen.restype = ctypes.c_ushort
        lib.PyOpen.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_bool]
        
        # ---------------------------------------------------------------------
        # __declspec(dllexport) unsigned short PyClose(AB3510* pAB3510) {return pAB3510->Close();}
        lib.PyClose.restype = ctypes.c_ushort
        lib.PyClose.argtypes = [ctypes.c_void_p]
        
        # ---------------------------------------------------------------------
        # __declspec(dllexport) bool PyIsConnected(AB3510 *pAB3510)
        lib.PyIsConnected.restype = ctypes.c_bool
        lib.PyIsConnected.argtypes = [ctypes.c_void_p]
        
        
        # ---------------------------------------------------------------------
        # __declspec(dllexport) unsigned short PyFindBoards(AB3510* pAB3510, std::vector<int> *Handles)
        # Reference Link: https://stackoverflow.com/questions/16885344/how-to-handle-c-return-type-stdvectorint-in-python-ctypes
        # https://numpy.org/doc/stable/reference/routines.ctypeslib.html
        lib.PyFindBoards.restype = ctypes.c_ushort
        lib.PyFindBoards.argtypes = [ctypes.c_void_p, np.ctypeslib.ndpointer(dtype=np.int32,
                                                  ndim=1,
                                                  flags='CONTIGUOUS')]
        
        # ---------------------------------------------------------------------
        # __declspec(dllexport) unsigned short PyFindBoards1(AB3510* pAB3510, int *Handles)
        lib.PyFindBoards1.restype = ctypes.c_ushort
        lib.PyFindBoards1.argtypes = [ctypes.c_void_p, np.ctypeslib.ndpointer(dtype=np.int32,
                                                  ndim=1,
                                                  flags='C_CONTIGUOUS')]
        
        # ---------------------------------------------------------------------
        # __declspec(dllexport) unsigned short PyGetAcquisitionPeriod(AB3510 *pAB3510, unsigned short *TimeUnit)
        lib.PyGetAcquisitionPeriod.restype = ctypes.c_ushort
        lib.PyGetAcquisitionPeriod.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ushort)]
        
        #=====================================================================
        #      EEPROM 
        #=====================================================================
        # ---------------------------------------------------------------------
        # __declspec(dllexport) unsigned short PySetDefaultParameters(AB3510 *pAB3510, AB3510::EmbeddedData *Data)
        lib.PySetDefaultParameters.restype = ctypes.c_ushort
        lib.PySetDefaultParameters.argtypes = [ctypes.c_void_p, ctypes.POINTER(EmbeddedData)]
        
        # ---------------------------------------------------------------------
        # __declspec(dllexport) bool PyCreateCalibTable(AB3510 *pAB3510, AB3510::EmbeddedData *Data)
        lib.PyCreateCalibTable.restype = ctypes.c_bool
        lib.PyCreateCalibTable.argtypes = [ctypes.c_void_p, ctypes.POINTER(EmbeddedData)]
        
        # ---------------------------------------------------------------------
        # __declspec(dllexport) unsigned short PyGetParametersFromEEPROM(AB3510 *pAB3510, AB3510::EmbeddedData *Data)
        lib.PyGetParametersFromEEPROM.restype = ctypes.c_ushort
        # lib.PyGetParametersFromEEPROM.argtypes = [ctypes.c_void_p, EmbeddedData]
        lib.PyGetParametersFromEEPROM.argtypes = [ctypes.c_void_p, ctypes.POINTER(EmbeddedData)]
        
        # ---------------------------------------------------------------------
        # __declspec(dllexport) unsigned short PySetParametersToEEPROM(AB3510 *pAB3510, AB3510::EmbeddedData *Data)
        lib.PySetParametersToEEPROM.restype = ctypes.c_ushort
        lib.PySetParametersToEEPROM.argtypes = [ctypes.c_void_p, ctypes.POINTER(EmbeddedData)]
        
        # ---------------------------------------------------------------------
        # __declspec(dllexport) unsigned short PyGetEEPromVersion(AB3510 *pAB3510, char *EEPromVersion)
        lib.PyGetEEPromVersion.restype = ctypes.c_ushort
        # lib.PyGetEEPromVersion.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_char)]
        lib.PyGetEEPromVersion.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        
        # ---------------------------------------------------------------------
#         __declspec(dllexport) unsigned short PyGetPolarParameters(AB3510 *pAB3510, int PolarPath,
# 												float Wavelength,
# 												AB3510::PolarV1 *PolarStruct)
        lib.PyGetPolarParameters.restype = ctypes.c_ushort
        lib.PyGetPolarParameters.argtypes = [ctypes.c_void_p, ctypes.c_int, 
                                             ctypes.c_float, ctypes.POINTER(PolarV1)]
        
        # ---------------------------------------------------------------------
#         __declspec(dllexport) unsigned short PyGetBoardParameters(AB3510 *pAB3510,
# 							AB3510::EmbeddedData *Data)//AB3510::EmbeddedData *Data, const char* INIFile)
        lib.PyGetBoardParameters.restype = ctypes.c_ushort
        lib.PyGetBoardParameters.argtypes = [ctypes.c_void_p, ctypes.POINTER(EmbeddedData)]
        
        #=====================================================================
        #      Get Smaples  
        #=====================================================================
        # ---------------------------------------------------------------------
        # __declspec(dllexport) unsigned short PyGetOneSample1(AB3510 *pAB3510, AB3510::PowerSample *ps)
        lib.PyGetOneSample.restype = ctypes.c_ushort
        lib.PyGetOneSample.argtypes = [ctypes.c_void_p, ctypes.POINTER(Sample)]
        
        # ---------------------------------------------------------------------
#         __declspec(dllexport) unsigned short PyGetOneSample2(AB3510 *pAB3510, AB3510::SOP *sop,
# 												int path, float wavelength)
        lib.PyGetOneSample2.restype = ctypes.c_ushort
        lib.PyGetOneSample2.argtypes = [ctypes.c_void_p, ctypes.POINTER(SOP), 
                                        ctypes.c_int, ctypes.c_float]
        
         # ---------------------------------------------------------------------
#         __declspec(dllexport) unsigned short PyGetOneSampleWithCal(AB3510 *pAB3510, AB3510::SOP *sop,
# 												int path, float wavelength,AB3510::CalibrationSOP *CalSOP,bool Normalise)
        lib.PyGetOneSamplewithCal.restype = ctypes.c_ushort
        lib.PyGetOneSamplewithCal.argtypes = [ctypes.c_void_p, ctypes.POINTER(SOP), 
                                        ctypes.c_int, ctypes.c_float,ctypes.POINTER(CalibrationSOP),ctypes.c_bool]
        
        # ---------------------------------------------------------------------
#         __declspec(dllexport) unsigned short PyGetSNList(AB3510* pAB3510, std::vector<std::string> *SNList,
# 													char const *ModelType)
        #  in C++, const char * and char const *, are equivalent: 
        # the value being pointed at can change but the pointer can't (similar to a reference).
        #  char * const: the value being pointed to can't be changed, but the pointer can be
        lib.PyGetSNList.restype = ctypes.c_ushort
        lib.PyGetSNList.argtypes = [ctypes.c_void_p,  np.ctypeslib.ndpointer(dtype=str,
                                                  ndim=1,
                                                  flags='C_CONTIGUOUS'), ctypes.c_char_p]
        
        # ---------------------------------------------------------------------
#         __declspec(dllexport) unsigned short PyGetHandleFromSN(AB3510* pAB3510,
# 											const char *SerialNumber, int *Handle)
        lib.PyGetHandleFromSN.restype = ctypes.c_ushort
        lib.PyGetHandleFromSN.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.POINTER(ctypes.c_int)]
        
        # ---------------------------------------------------------------------
        # __declspec(dllexport) unsigned short PyGetModelType(AB3510* pAB3510, char *ModelType)
        lib.PyGetModelType.restype = ctypes.c_ushort
        lib.PyGetModelType.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        
        
        # ---------------------------------------------------------------------
#         __declspec(dllexport) unsigned short PyGetFirmwareRevision(AB3510 *pAB3510,
# 														unsigned char *Major,
# 														unsigned char *Minor)
        lib.PyGetFirmwareRevision.restype = ctypes.c_ushort
        lib.PyGetFirmwareRevision.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ubyte), 
                                              ctypes.POINTER(ctypes.c_ubyte)]
        
         # ---------------------------------------------------------------------
          # ---------------------------------------------------------------------
#        __declspec(dllexport) unsigned short PyHorizontalCalib(AB3510 *pAB3510,float WavelengthCur,
#							AB3510::CalibrationSOP *MatrixCal)
        lib.PyHorizontalCalib.restype = ctypes.c_ushort
        lib.PyHorizontalCalib.argtypes = [ctypes.c_void_p, ctypes.c_float,ctypes.POINTER(CalibrationSOP)]
        
         # ---------------------------------------------------------------------
#        __declspec(dllexport) unsigned short PyVerticalCalib(AB3510 *pAB3510,float WavelengthCur,
#							AB3510::CalibrationSOP *MatrixCal)
        lib.PyVerticalCalib.restype = ctypes.c_ushort
        lib.PyVerticalCalib.argtypes = [ctypes.c_void_p, ctypes.c_float,ctypes.POINTER(CalibrationSOP)]
        
         # ---------------------------------------------------------------------
#        __declspec(dllexport) unsigned short PyLinearCalib(AB3510 *pAB3510,float WavelengthCur,
#							AB3510::CalibrationSOP *MatrixCal,AB3510::CalibrationSOP *Tab_MatrixCal)
        lib.PyLinearCalib.restype = ctypes.c_ushort
        lib.PyLinearCalib.argtypes = [ctypes.c_void_p, ctypes.c_float,ctypes.POINTER(CalibrationSOP),ctypes.POINTER(CalibrationSOP)]
        
        
         # ---------------------------------------------------------------------
        
        self.obj = lib.AB3510_new()
        
        
    ####### FUNCTIONS #########
    def Open(self, Handle, Simulation):
        """
        Open connection with AB3510 Board 

        Returns
        -------
        None.

        """
        status = lib.PyOpen(self.obj, ctypes.c_int(Handle), ctypes.c_bool(Simulation))
        if status == 0:
            print("Connection to AB3510 board")
        else: 
            print("ERROR1 ", status, " Can not connect ot AB3510 Board")
        return status
    
    def Close(self): 
        
        # Close connection 
        status = lib.PyClose(self.obj)
        
        if status ==0:
            print("Disconnection to AB3510Board")
        else: 
            print("ERROR ", status, " Can not disconnect AB3510 Board")
        
        return status
    
    def IsConnected(self):
        
        status = lib.PyIsConnected(self.obj)
        
        return status 
    
    def FindBoards(self, Handles):
        try: 
            
            status = lib.PyFindBoards(self.obj, Handles)
            print("status using vector: ", status)
            print("device index using vector: ", Handles)
            
            if status != 0:
                print("find the AB3510 board index: ", Handles)
        except: 
            print("ERROR ", status, " Can not find the AB3510 board")
        
        return Handles 
    
    def FindBoards1(self, Handles):
         
        # Handles = np.ctypeslib.ndpointer(dtype=np.int,
        #                                           ndim=1,
        #                                           flags='C_CONTIGUOUS')        
        
        # Handles = np.array([0, 0, 0], dtype=np.int)
        # Handles = np.zeros(4, dtype=np.int)
        
        # status = lib.PyFindBoards(self.obj, np.ctypeslib.ndpointer(Handles))
        # status = lib.PyFindBoards1(self.obj, Handles)
        # print(status)
        # print(Handles)
        
        try: 
            
            status = lib.PyFindBoards1(self.obj, Handles)
            
            # print("status using pointer array: ", status)
            # print("device index using pointer array: ", Handles)
            
            if status != 0:
                print("find the AB3510 board index: ", Handles)
        except: 
            print("ERROR ", status, " Can not find the AB3510 board")
        
        return Handles 
    
    def GetParametersFromEEPROM(self, eData):
        # eData = EmbeddedData()
        if not isinstance(eData, type(self.EmbeddedData)):
            raise TypeError('Argument "eData" should be type of struct EmbeddedData')
        
        status = lib.PyGetParametersFromEEPROM(self.obj, eData)
        print("Serial Number: ", eData.Header.SerialNumber.decode("utf-8"))
        print("EEPROM Version: ", eData.Header.EEPromVersion.decode())
        print("EEPROM Version: ", eData.Header.FirmwareVersion.decode())
        
        return status
    
    def SetParametersToEEPROM(self, eData):
        # eData = EmbeddedData()
        if not isinstance(eData, type(self.EmbeddedData)):
            raise TypeError('Argument "eData" should be type of struct EmbeddedData')
        
        status = lib.PySetParametersToEEPROM(self.obj, eData)
        return status 
    
    def GetEEPromVersion(self, EEPromVersion):
        
        if not isinstance(EEPromVersion, ctypes.c_char_p):
            raise TypeError("Argument EEPromVersion should be ctypes.c_char_p()") 
            
        # EEPromVersion = ctypes.POINTER(ctypes.c_char)()
        # eev = lib.PyGetEEPromVersion(self.obj, EEPromVersion)
        
        EEPromVersion = ctypes.c_char_p()
        # EEPromVersion = ctypes.pointer(ctypes.c_char())
        # eev = lib.PyGetEEPromVersion(self.obj, ctypes.byref(EEPromVersion))
        eev = lib.PyGetEEPromVersion(self.obj, EEPromVersion)
        
        return eev
    
    def SetDefaultParameters(self, eData): 
        # eData = EmbeddedData()     
        if not isinstance(eData, type(self.EmbeddedData)):
            raise TypeError('Argument "eData" should be type of struct EmbeddedData')
        
        status = lib.PySetDefaultParameters(self.obj, eData)
        print("Serial Number: ", eData.Header.SerialNumber.decode("utf-8"))
        print("EEPROM Version: ", eData.Header.EEPromVersion.decode())
        print("EEPROM Version: ", eData.Header.FirmwareVersion.decode())
        
        return status
    
    def CreateCalibTable(self,eData):
        # eData = EmbeddedData()
        if not isinstance(eData, type(self.EmbeddedData)):
            raise TypeError('Argument "eData" should be type of struct EmbeddedData')
        status = lib.PyCreateCalibTable(self.obj, eData)
        return status 
    
    
    def GetAcquisitionPeriod(self, time_unit):
        # lib.PyGetAcquisitionPeriod.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ushort)]
        if not isinstance(time_unit, ctypes.c_ushort):
            raise TypeError("Argument time_unit should be ctypes.c_ushort")   
        
        # time_unit = ctypes.c_ushort(0)  # ISR: Interrupt service routine 
        status = lib.PyGetAcquisitionPeriod(self.obj, ctypes.byref(time_unit))
        print("time_unit =", time_unit.value)
        
        return status
    
    def GetOneSample(self, sp):
        # lib.PyGetOneSample.argtypes = [ctypes.c_void_p, ctypes.POINTER(PowerSample)]
        if not isinstance(sp, type(self.Sample)):
            raise TypeError("Argument sp should be type of struct Sample")  
        
        status = lib.PyGetOneSample(self.obj, sp)
        
        return status 
    
    def GetOneSample2(self, sop, pPath, Wavelength):
        
        if not isinstance(sop, type(self.SOP)):
            raise TypeError("Argument sop should be type of struct SOP") 
        
        if not isinstance(pPath, ctypes.c_int):
            raise TypeError("Argument pPath should be type ctypes.c_int") 
        
        if not isinstance(Wavelength, ctypes.c_float):
            raise TypeError("Argument pPath should be type ctypes.c_float") 
            
        # lib.PyGetOneSample2.argtypes = [ctypes.c_void_p, ctypes.POINTER(SOP), 
        #                                 ctypes.c_int, ctypes.c_float]
        status = lib.PyGetOneSample2(self.obj, sop, pPath, Wavelength)
        return status 
    
    def GetOneSamplewithCal(self, sop, pPath, Wavelength,CalSOP,Normalise):
        
        if not isinstance(sop, type(self.SOP)):
            raise TypeError("Argument sop should be type of struct SOP") 
        
        if not isinstance(pPath, ctypes.c_int):
            raise TypeError("Argument pPath should be type ctypes.c_int") 
        
        if not isinstance(Wavelength, ctypes.c_float):
            raise TypeError("Argument Wavelength should be type ctypes.c_float")
        
        if not isinstance(CalSOP, type(self.CalibrationSOP)):
            raise TypeError("Argument CalSOP should be type of struct CalibrationSOP")    
        
        if not isinstance(Normalise, ctypes.c_bool):
            raise TypeError("Argument Normalise should be type ctypes.c_bool")
        status = lib.PyGetOneSamplewithCal(self.obj, sop, pPath, Wavelength,CalSOP,Normalise)
        return status 
    
    def GetPolarParameters(self, pPath, Wavelength, PolarStruct):
        if not isinstance(pPath, ctypes.c_int):
            raise TypeError("Argument pPath should be type of ctypes.c_int")
        
        if not isinstance(Wavelength, ctypes.c_float):
            raise TypeError("Argument pPath should be type of ctypes.c_float")
        
        if not isinstance(PolarStruct, type(self.PolarV1)):
            raise TypeError("Argument sop should be type of struct SOP") 
        
        status = lib.PyGetPolarParameters(self.obj, pPath, Wavelength, PolarStruct)
        return status 
    
    def GetBoardParameters(self, eData):
        # lib.PyGetBoardParameters.argtypes = [ctypes.c_void_p, ctypes.POINTER(EmbeddedData)]
        if not isinstance(eData, type(self.EmbeddedData)):
            raise TypeError('Argument "eData" should be type of struct EmbeddedData')
        
        status = lib.PyGetBoardParameters(self.obj, eData)
        return status 
    
    def HorizontalCalib(self, Wavelength,MatrixCal):
        #PyHorizontalCalib(AB3510 *pAB3510,float WavelengthCur,AB3510::CalibrationSOP *MatrixCal)
        
        if not isinstance(Wavelength, ctypes.c_float):
            raise TypeError('Argument "Wavelength" should be type ctypes.c_float')
        
        if not isinstance(MatrixCal, type(self.CalibrationSOP)):
            raise TypeError('Argument "MatrixCal" should be type of struct CalibrationSOP')    
        
        status = lib.PyHorizontalCalib(self.obj, Wavelength,MatrixCal)
        return status 
            
    def VerticalCalib(self, Wavelength,MatrixCal):
        #PyVerticalCalib(AB3510 *pAB3510,float WavelengthCur,AB3510::CalibrationSOP *MatrixCal)
        
        if not isinstance(Wavelength, ctypes.c_float):
            raise TypeError('Argument "Wavelength" should be type ctypes.c_float')
        
        if not isinstance(MatrixCal, type(self.CalibrationSOP)):
            raise TypeError('Argument "MatrixCal" should be type of struct CalibrationSOP')    
        
        status = lib.PyVerticalCalib(self.obj, Wavelength,MatrixCal)
        return status 
    
    def LinearCalib(self, Wavelength,MatrixCal,Tab_MatrixCal):
        #PyLinearCalib(AB3510 *pAB3510,float WavelengthCur,AB3510::CalibrationSOP *MatrixCal,AB3510::CalibrationSOP *Tab_MatrixCal)
        
        if not isinstance(Wavelength, ctypes.c_float):
            raise TypeError('Argument "Wavelength" should be type ctypes.c_float')
        
        if not isinstance(MatrixCal, type(self.CalibrationSOP)):
            raise TypeError('Argument "MatrixCal" should be type of struct CalibrationSOP')    
        
        if not isinstance(Tab_MatrixCal, type(self.CalibrationSOP)):
            raise TypeError('Argument "Tab_MatrixCal" should be type of struct CalibrationSOP')  
        status = lib.PyLinearCalib(self.obj, Wavelength,MatrixCal,Tab_MatrixCal)
        return status 


        
        
        
        
        

        
    
            
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        



