import numpy as np
import pyxem as pxm
import hyperspy.api as hs
from pyxem.libraries.calibration_library import CalibrationDataLibrary
from pyxem.generators.calibration_generator import CalibrationGenerator

class NBED_calibration:
    def __init__(self,NBED_data, EM_type =None):
        self.s = NBED_data
        self.EM_type = EM_type
        self.NBED_F30={
            200:0.2345746633560363,
            250:0.1862625415225771,
            300:0.1562169503514413,
            380:0.1225684262753367,
            580:0.0829012794983478,
            750:0.0621134215923645,
            1000:0.0463765534986008,
            1200:0.0385675398614808,
            1500:0.0304885392056699,
            2000:0.022962175785559,
            3000:0.0153784852837892,
            4500:0.0101846964140601
            }
        self.NBED_HD2700={
            1:0.268622,
            1.049:0.214803,
            1.1:0.175866,
            1.149:0.150919,
            1.2:0.129091,
            1.251:0.11219,
            1.3:0.09901,
            1.351:0.089018,
            1.4:0.079783,
            1.451:0.072484,
            1.5:0.066695,
            1.551:0.061213,
            1.6:0.056804,
            1.651:0.052335,
            1.699:0.048822,
            1.751:0.045686,
            1.8:0.04286,
            1.851:0.040391,
            1.881:0.039397,
            1.951:0.03637,
            2:0.03413
            }
    def calibration(self):
        try:
            # Determine microscope type
            if self.EM_type is None:
                if hasattr(self.s.metadata.Acquisition_instrument.TEM, 'microscope'):
                    self.EM_type = self.s.metadata.Acquisition_instrument.TEM.microscope
                else:
                    self.EM_type = 'F30'
            
            # Print microscope info
            print(f'Microscope is {self.EM_type}')
            
            # Get camera length
            camera_length = self.s.metadata.Acquisition_instrument.TEM.camera_length
            print(f'Camera length = {camera_length} mm')
            
            # Calibration for F30 microscope
            if self.EM_type == 'F30':
                for key, value in self.NBED_F30.items():
                    if camera_length == int(key):
                        nbed_units = value
                        print(f'Calibration units: {nbed_units}')
                        break
                else:
                    raise ValueError(f"No calibration found for camera length {camera_length}")
            
            # Calibration for HD2700 microscope
            elif self.EM_type == 'HD2700':
                for key, value in self.NBED_HD2700.items():
                    if abs(camera_length - key) < 0.01:
                        nbed_units = value
                        print(f'Using calibration {nbed_units} for camera length {key}')
                        break
                else:
                    raise ValueError(f"No calibration found for camera length {camera_length}")
            
            # Set axis scales
            self.s.axes_manager[0].units = '/nm'
            self.s.axes_manager[0].scale = nbed_units
            self.s.axes_manager[1].units = '/nm'
            self.s.axes_manager[1].scale = nbed_units
            
            #return nbed_units
        
        except AttributeError:
            # Fallback for missing metadata
            camera_length = float(input("Please enter camera length (CL) for HD2700: "))
            print(f'CL of HD2700 = {camera_length} Å')
            
            for key, value in self.NBED_HD2700.items():
                if abs(camera_length - key) < 0.01:
                    nbed_units = value
                    print(f'Using calibration {nbed_units} for camera length {key}')
                    
                    # Set axis scales
                    self.s.axes_manager[0].units = '/nm'
                    self.s.axes_manager[0].scale = nbed_units
                    self.s.axes_manager[1].units = '/nm'
                    self.s.axes_manager[1].scale = nbed_units
                    
                    #return nbed_units
            
            print('Sorry, this camera length is out of the calibrated range')
        return self.s
"""
Example use:
file_name = your NBED data
NBED_data = hs.load(file_name, 'F30')
SI = NBED_data[2] (be careful to select NBED SI only. NBED_data file might be a list which contains survery image, ROI image and SI data)
SI=SI.calibration()
SI.plot()
"""