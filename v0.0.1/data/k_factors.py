"""
Author: Mengkun Tian
Latest updated Jan 12th, 2025
This file contains the k-factors for bruker EDS detector, which is equipped in Hitachi HD2700 STEM
"""

import pandas as pd
import numpy as np
import copy
class kfactors:
     """
    A class to store and retrieve k-factors for elements based on their X-ray lines (K, L, M).
    The k-factors are specific to the Bruker EDS detector equipped in the Hitachi HD2700 STEM.

    Attributes:
        column (list): Column names for the k-factor data (Z, Element, K, L, M).
        data (list): A list of lists containing k-factor data for elements.
        kfactors_HD2700 (pd.DataFrame): A DataFrame storing the k-factor data.

    Methods:
        find_kfactors(x_rayline_list, index='Element'):
            Retrieves k-factors for the given X-ray lines. Can accept a list of X-ray lines
            or a HyperSpy EDS spectrum as input.
    """
    # Initializes the class and sets up the data
    def __init__(self): 
        # defines the structure of the data table. It has column for: Z: Atomic number of the element. Element: Name of the element. K, L, M: K-factors for the K, L, M X-ray lines of each element.
        self.column = ['Z', 'Element', 'K','L','M'] 
        # List  containing the k-factors data for each element.
        self.data = [
                        [1, 'H', 0, 0, 0],[2, 'He', 0, 0, 0],[3, 'Li', 0, 0, 0],[4, 'Be', 181.983, 0, 0],[5, 'B', 8.985, 0, 0],
                        [6, 'C', 11.907, 0, 0], [7, 'N', 3.218, 0, 0],[8, 'O', 1.700, 0, 0],[9, 'F', 1.503, 0, 0],[10, 'Ne', 0.966, 0, 0],
                        [11, 'Na', 0.932, 0, 0], [12, 'Mg', 9.868, 0, 0], [13, 'Al', 11.011, 0, 0], [14, 'Si', 3.596, 0.000, 0.000],
                        [15, 'P', 1.050, 0.000, 0.000],    [16, 'S', 4.296, 0, 0], [17, 'Cl', 1.049, 0, 0], [18, 'Ar', 1.141, 0, 0], [19, 'K', 1.077, 0, 0], [20, 'Ca', 1.157, 92.905, 0], [21, 'Sc', 1.191, 40.965, 0],
                        [22, 'Ti', 1.210, 29.213, 0],  [23, 'V', 1.259, 15.657, 0], [24, 'Cr', 1.278, 7.943, 0],
                        [25, 'Mn', 3.469, 4.798, 0], [26, 'Fe', 2.806, 2.863, 0],
                        [27, 'Co', 1.518, 2.311, 0], [28, 'Ni', 1.556, 1.853, 0],
                        [29, 'Cu', 2.073, 1.677, 0], [30, 'Zn', 1.860, 1.723, 0],
                        [31, 'Ga', 2.070, 2.123, 0], [32, 'Ge', 2.265, 2.054, 0],
                        [33, 'As', 2.481, 2.136, 0], [34, 'Se', 2.807, 2.154, 0],
                        [35, 'Br', 3.078, 2.113, 0], [36, 'Kr', 3.546, 2.263, 0],
                        [37, 'Rb', 4.009, 2.233, 0],[38, 'Sr', 4.616, 2.274, 0.000],
                        [39, 'Y', 5.295, 2.343, 0.000], [40, 'Zr', 6.180, 2.360, 0.000],
                        [41, 'Nb', 7.262, 2.320, 0.000],
                        [42, 'Mo', 8.642, 2.361, 0.000],
                        [43, 'Tc', 10.257, 2.520, 0.000],
                        [44, 'Ru', 12.381, 2.493, 0.000],
                        [45, 'Rh', 14.768, 2.622, 0.000],
                        [46, 'Pd', 17.985, 2.738, 0.000],
                        [47, 'Ag', 21.470, 2.804, 0.000],
                        [48, 'Cd', 26.328, 2.939, 0.000],
                        [49, 'In', 31.736, 2.938, 0.000],
                        [50, 'Sn', 38.849, 3.303, 0.000],
                        [51, 'Sb', 47.074, 3.421, 0.000],
                        [52, 'Te', 58.429, 3.575, 0.000],
                        [53, 'I', 68.682, 3.557, 0.000],
                        [54, 'Xe', 83.757, 3.652, 0.000],
                        [55, 'Cs', 100.587, 3.678, 0.000],
                        [56, 'Ba', 122.888, 3.789, 251.024],
                        [57, 'La', 146.460, 3.779, 36.353],
                        [58, 'Ce', 174.287, 3.779, 21.616],
                        [59, 'Pr', 206.116, 3.772, 16.083],
                        [60, 'Nd', 248.193, 3.835, 12.610],[61, 'Pm', 293.576, 3.847, 9.775],
                        [62, 'Sm', 357.046, 4.036, 9.526],
                        [63, 'Eu', 423.472, 4.054, 7.025],
                        [64, 'Gd', 513.709, 4.178, 3.642],
                        [65, 'Tb', 608.318, 4.188, 5.337],
                        [66, 'Dy', 726.462, 4.229, 4.202],[67, 'Ho', 863.910, 4.297, 3.838],
                        [68, 'Er', 1020.079, 4.322, 3.737],
                        [69, 'Tm', 1203.458, 4.369, 2.699],
                        [70, 'Yb', 1435.566, 4.310, 2.588],
                        [71, 'Lu', 1690.141, 4.565, 1.928],
                        [72, 'Hf', 2008.353, 4.674, 1.839],
                        [73, 'Ta', 2366.031, 4.739, 1.768],
                        [74, 'W', 2793.954, 4.824, 1.740],
                        [75, 'Re', 3280.444, 4.813, 2.310],
                        [76, 'Os', 3894.591, 4.834, 0.734],
                        [77, 'Ir', 4566.981, 4.817, 1.275],
                        [78, 'Pt', 5378.208, 4.893, 1.438],
                        [79, 'Au', 6288.581, 4.892, 1.536],
                        [80, 'Hg', 7434.261, 4.991, 1.950],
                        [81, 'Tl', 8777.332, 5.122, 2.841],
                        [82, 'Pb', 10312.191, 5.257, 3.562],
                        [83, 'Bi', 12054.599, 5.395, 3.445],[84, 'Po', 13950.156, 5.504, 3.495],
                        [85, 'At', 16250.293, 5.628, 3.475],
                        [86, 'Rn', 19882.856, 6.125, 3.419],
                        [87, 'Fr', 23123.224, 6.316, 3.577],
                        [88, 'Ra', 27146.164, 6.580, 3.493],
                        [89, 'Ac', 31583.326, 6.829, 3.390],
                        [90, 'Th', 37429.922, 7.223, 3.269],
                        [91, 'Pa', 43238.079, 7.315, 3.232],
                        [92, 'U', 51724.858, 7.220, 3.198],
                        [93, 'Np', 59588.090, 7.361, 3.125],
                        [94, 'Pu', 71681.625, 7.885, 3.223],
                        [95, 'Am', 83205.325, 8.187, 3.108],
                        [96, 'Cm', 98894.698, 9.382, 3.032],
                        [97, 'Bk', 15703.642, 9.892, 3.018],
                        [98, 'Cf', 37892.321, 10.560, 3.050]
                    ] 
         # Converts the self.data list into a Pandas DataFrame for easier manipulatioon and searching.
        self.kfactors_HD2700 = pd.DataFrame(data = data,df=None, columns = column) 
         # This method retrieves the k-factors for a given list of X-ray lines.
    def find_kfactors(self,x_rayline_list, index='Element'): 
        """
        Find the k-factor for the given x-ray line list. Looks up the corresponding k-factor in the DataFrame.
        :param x_rayline_list: List of x-ray lines (e.g., ['Al_Ka', 'Zr_Ka'])
        :param df: DataFrame to search (defaults to self.kfactors_2700, might use our other facilities if vendor can provide their kfactors)
        :param index: Index column for searching (default is 'Element')
        :return: List of k-factors. It returns a list of k-factors for the given X-ray lines.
        """
        # To store the k-factors (values) retrieved for the given X-ray lines.
        data_list = [] 
        # If no DataFrame is provided as input, the code ses a deep copy of the self.kfactors_HD2700 
        if df is None: 
             # copy.deepcopy ensures that the original DataFrame is not moodified accidentally.
            df = copy.deepcopy(self.kfactors_HD2700) 
        df.set_index(index, inplace=True)  # Replaces the default numeric indices with the values from the 'Elemen' column
        # If it's a list or NumPy array => assigns it directly to EDS_lines
        if isinstance(x_rayline_list, (list, np.ndarray)): 
            EDS_lines = x_rayline_list
        # If it's a special spectum object =>
        elif isinstance(x_rayline_list, (exspy.signals.eds_tem.EDSTEMSpectrum, 
                                exspy.signals.eds_sem.EDSSEMSpectrum)):
            EDS_lines = x_rayline_list.metadata.Sample.xray_lines
        else:
            print (f"Please assign x-rayline_list values with a list format: [element1_K(or L or M)a','element2_K(or L or M)a'... ]")
        # This loop processes each X-ray line in the EDS_lines list.
         for item in EDS_lines: 
            # Extracts the element name by splitting the string at the underscore. (Row)
            idx = item.split('_')[0] 
            # Extracts last two characters of the X-ray line string. (Column)
            line = item[-2]  
            # Retrieves a specific value (k-factor) using row (idx = Element name ) and column (line = X-ray line) labels.
            value = df.at[idx, line] 
            # This retrieves k-factor(value) is added to the data_list.
            data_list.append(value) 
        # Returns a list of k-factors
        return data_list 
"""
Example usage:
kfactor = kfactors()
results = kfactors.find_kfactors(x_rayline_list =['Al_Ka', 'Zr_Ka', 'O_Ka', 'Ti_Ka'],  index = 'Element')
the result will display like this:
>>>>[11.011, 1.7, 1.21, 6.18] where 11.011 is k_factor of Ka peak for Al, 1.7 is for 'Zr_Ka'....
"""
