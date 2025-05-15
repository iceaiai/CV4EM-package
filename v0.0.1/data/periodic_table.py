import tkinter as tk
import pandas as pd
import numpy as np
"""
cv4em.periodic_table
~~~~~~~~~~~~~~~~~~~~

Provides a Tkinter‑based interactive periodic table that lets users
select chemical elements and build custom X‑ray emission line lists
(e.g. Kα, Lα, Mα).  Useful for quickly visualizing and exporting
an element‑line specification for EDS or XRF workflows.
"""
class PeriodicTableApp:
    """
    A fully‑featured Periodic Table GUI with X‑ray line selection (EDS use). Note this is an optional tool for you

    Usage:
    import tkinter as tk
    import CV4EM as cv4em

    # Instantiate the root Tkinter window and the PeriodicTableApp
    root = tk.Tk()
    app = PeriodicTableApp(root)
    root.mainloop()

    ## After select the element and line, run the following:
    Xray_lines = app.xray_lines
    Xray_lines should have format like ['Al_Ka','O_Ka']

    Attributes:
      selected_elements (List[str]): currently‑chosen element symbols.
      xray_lines        (List[str]): raw element‑line codes for export.
      xray_lines_display(List[str]): human‑readable lines with keV labels.
    """
    def __init__(self, root):
        self.root = root
        self.root.title("Interactive Periodic Table with X-ray Lines")
        """
        Data structure for elements: 
        Symbol, Name, AtomicNumber for pplotting in each block of element
        Row and column for location in periodic table 
        Category for coloring
        """
        self.colors = {
            "Nonmetal": "#FF9999",
            "Noble Gas": "#99CCCC",
            "Alkali Metal": "#FFFF99",
            "Alkaline Earth": "#CCCCFF",
            "Metalloid": "#FFCC99",
            "Halogen": "#CCCCFF",
            "Transition Metal": "#FF6666",
            "Post-transition Metal": "#66CCCC",
        }
        self.elements = [
            # Row 1
            {"Symbol": "H", "Name": "Hydrogen", "AtomicNumber": 1, "Row": 0, "Column": 0, "Category": "Nonmetal"},
            {"Symbol": "He", "Name": "Helium", "AtomicNumber": 2, "Row": 0, "Column": 17, "Category": "Noble Gas"},

            # Row 2
            {"Symbol": "Li", "Name": "Lithium", "AtomicNumber": 3, "Row": 1, "Column": 0, "Category": "Alkali Metal"},
            {"Symbol": "Be", "Name": "Beryllium", "AtomicNumber": 4, "Row": 1, "Column": 1, "Category": "Alkaline Earth"},
            {"Symbol": "B", "Name": "Boron", "AtomicNumber": 5, "Row": 1, "Column": 12, "Category": "Metalloid"},
            {"Symbol": "C", "Name": "Carbon", "AtomicNumber": 6, "Row": 1, "Column": 13, "Category": "Nonmetal"},
            {"Symbol": "N", "Name": "Nitrogen", "AtomicNumber": 7, "Row": 1, "Column": 14, "Category": "Nonmetal"},
            {"Symbol": "O", "Name": "Oxygen", "AtomicNumber": 8, "Row": 1, "Column": 15, "Category": "Nonmetal"},
            {"Symbol": "F", "Name": "Fluorine", "AtomicNumber": 9, "Row": 1, "Column": 16, "Category": "Halogen"},
            {"Symbol": "Ne", "Name": "Neon", "AtomicNumber": 10, "Row": 1, "Column": 17, "Category": "Noble Gas"},

            # Row 3
            {"Symbol": "Na", "Name": "Sodium", "AtomicNumber": 11, "Row": 2, "Column": 0, "Category": "Alkali Metal"},
            {"Symbol": "Mg", "Name": "Magnesium", "AtomicNumber": 12, "Row": 2, "Column": 1, "Category": "Alkaline Earth"},
            {"Symbol": "Al", "Name": "Aluminum", "AtomicNumber": 13, "Row": 2, "Column": 12, "Category": "Post-transition Metal"},
            {"Symbol": "Si", "Name": "Silicon", "AtomicNumber": 14, "Row": 2, "Column": 13, "Category": "Metalloid"},
            {"Symbol": "P", "Name": "Phosphorus", "AtomicNumber": 15, "Row": 2, "Column": 14, "Category": "Nonmetal"},
            {"Symbol": "S", "Name": "Sulfur", "AtomicNumber": 16, "Row": 2, "Column": 15, "Category": "Nonmetal"},
            {"Symbol": "Cl", "Name": "Chlorine", "AtomicNumber": 17, "Row": 2, "Column": 16, "Category": "Halogen"},
            {"Symbol": "Ar", "Name": "Argon", "AtomicNumber": 18, "Row": 2, "Column": 17, "Category": "Noble Gas"},

            # Row 4
            {"Symbol": "K", "Name": "Potassium", "AtomicNumber": 19, "Row": 3, "Column": 0, "Category": "Alkali Metal"},
            {"Symbol": "Ca", "Name": "Calcium", "AtomicNumber": 20, "Row": 3, "Column": 1, "Category": "Alkaline Earth"},
            {"Symbol": "Sc", "Name": "Scandium", "AtomicNumber": 21, "Row": 3, "Column": 2, "Category": "Transition Metal"},
            {"Symbol": "Ti", "Name": "Titanium", "AtomicNumber": 22, "Row": 3, "Column": 3, "Category": "Transition Metal"},
            {"Symbol": "V", "Name": "Vanadium", "AtomicNumber": 23, "Row": 3, "Column": 4, "Category": "Transition Metal"},
            {"Symbol": "Cr", "Name": "Chromium", "AtomicNumber": 24, "Row": 3, "Column": 5, "Category": "Transition Metal"},
            {"Symbol": "Mn", "Name": "Manganese", "AtomicNumber": 25, "Row": 3, "Column": 6, "Category": "Transition Metal"},
            {"Symbol": "Fe", "Name": "Iron", "AtomicNumber": 26, "Row": 3, "Column": 7, "Category": "Transition Metal"},
            {"Symbol": "Co", "Name": "Cobalt", "AtomicNumber": 27, "Row": 3, "Column": 8, "Category": "Transition Metal"},
            {"Symbol": "Ni", "Name": "Nickel", "AtomicNumber": 28, "Row": 3, "Column": 9, "Category": "Transition Metal"},
            {"Symbol": "Cu", "Name": "Copper", "AtomicNumber": 29, "Row": 3, "Column": 10, "Category": "Transition Metal"},
            {"Symbol": "Zn", "Name": "Zinc", "AtomicNumber": 30, "Row": 3, "Column": 11, "Category": "Transition Metal"},
            {"Symbol": "Ga", "Name": "Gallium", "AtomicNumber": 31, "Row": 3, "Column": 12, "Category": "Post-transition Metal"},
            {"Symbol": "Ge", "Name": "Germanium", "AtomicNumber": 32, "Row": 3, "Column": 13, "Category": "Metalloid"},
            {"Symbol": "As", "Name": "Arsenic", "AtomicNumber": 33, "Row": 3, "Column": 14, "Category": "Metalloid"},
            {"Symbol": "Se", "Name": "Selenium", "AtomicNumber": 34, "Row": 3, "Column": 15, "Category": "Nonmetal"},
            {"Symbol": "Br", "Name": "Bromine", "AtomicNumber": 35, "Row": 3, "Column": 16, "Category": "Halogen"},
            {"Symbol": "Kr", "Name": "Krypton", "AtomicNumber": 36, "Row": 3, "Column": 17, "Category": "Noble Gas"},

            # Row 5
            {"Symbol": "Rb", "Name": "Rubidium", "AtomicNumber": 37, "Row": 4, "Column": 0, "Category": "Alkali Metal"},
            {"Symbol": "Sr", "Name": "Strontium", "AtomicNumber": 38, "Row": 4, "Column": 1, "Category": "Alkaline Earth"},
            {"Symbol": "Y", "Name": "Yttrium", "AtomicNumber": 39, "Row": 4, "Column": 2, "Category": "Transition Metal"},
            {"Symbol": "Zr", "Name": "Zirconium", "AtomicNumber": 40, "Row": 4, "Column": 3, "Category": "Transition Metal"},
            {"Symbol": "Nb", "Name": "Niobium", "AtomicNumber": 41, "Row": 4, "Column": 4, "Category": "Transition Metal"},
            {"Symbol": "Mo", "Name": "Molybdenum", "AtomicNumber": 42, "Row": 4, "Column": 5, "Category": "Transition Metal"},
            {"Symbol": "Tc", "Name": "Technetium", "AtomicNumber": 43, "Row": 4, "Column": 6, "Category": "Transition Metal"},
            {"Symbol": "Ru", "Name": "Ruthenium", "AtomicNumber": 44, "Row": 4, "Column": 7, "Category": "Transition Metal"},
            {"Symbol": "Rh", "Name": "Rhodium", "AtomicNumber": 45, "Row": 4, "Column": 8, "Category": "Transition Metal"},
            {"Symbol": "Pd", "Name": "Palladium", "AtomicNumber": 46, "Row": 4, "Column": 9, "Category": "Transition Metal"},
            {"Symbol": "Ag", "Name": "Silver", "AtomicNumber": 47, "Row": 4, "Column": 10, "Category": "Transition Metal"},
            {"Symbol": "Cd", "Name": "Cadmium", "AtomicNumber": 48, "Row": 4, "Column": 11, "Category": "Transition Metal"},
            {"Symbol": "In", "Name": "Indium", "AtomicNumber": 49, "Row": 4, "Column": 12, "Category": "Post-transition Metal"},
            {"Symbol": "Sn", "Name": "Tin", "AtomicNumber": 50, "Row": 4, "Column": 13, "Category": "Post-transition Metal"},
            {"Symbol": "Sb", "Name": "Antimony", "AtomicNumber": 51, "Row": 4, "Column": 14, "Category": "Metalloid"},
            {"Symbol": "Te", "Name": "Tellurium", "AtomicNumber": 52, "Row": 4, "Column": 15, "Category": "Metalloid"},
            {"Symbol": "I", "Name": "Iodine", "AtomicNumber": 53, "Row": 4, "Column": 16, "Category": "Halogen"},
            {"Symbol": "Xe", "Name": "Xenon", "AtomicNumber": 54, "Row": 4, "Column": 17, "Category": "Noble Gas"},

            # Row 6
            {"Symbol": "Cs", "Name": "Cesium", "AtomicNumber": 55, "Row": 5, "Column": 0, "Category": "Alkali Metal"},
            {"Symbol": "Ba", "Name": "Barium", "AtomicNumber": 56, "Row": 5, "Column": 1, "Category": "Alkaline Earth"},
            {"Symbol": "La", "Name": "Lanthanum", "AtomicNumber": 57, "Row": 8, "Column": 2, "Category": "Lanthanide"},
            {"Symbol": "Ce", "Name": "Cerium", "AtomicNumber": 58, "Row": 8, "Column": 3, "Category": "Lanthanide"},
            {"Symbol": "Pr", "Name": "Praseodymium", "AtomicNumber": 59, "Row": 8, "Column": 4, "Category": "Lanthanide"},
            {"Symbol": "Nd", "Name": "Neodymium", "AtomicNumber": 60, "Row": 8, "Column": 5, "Category": "Lanthanide"},
            {"Symbol": "Pm", "Name": "Promethium", "AtomicNumber": 61, "Row": 8, "Column": 6, "Category": "Lanthanide"},
            {"Symbol": "Sm", "Name": "Samarium", "AtomicNumber": 62, "Row": 8, "Column": 7, "Category": "Lanthanide"},
            {"Symbol": "Eu", "Name": "Europium", "AtomicNumber": 63, "Row": 8, "Column": 8, "Category": "Lanthanide"},
            {"Symbol": "Gd", "Name": "Gadolinium", "AtomicNumber": 64, "Row": 8, "Column": 9, "Category": "Lanthanide"},
            {"Symbol": "Tb", "Name": "Terbium", "AtomicNumber": 65, "Row": 8, "Column": 10, "Category": "Lanthanide"},
            {"Symbol": "Dy", "Name": "Dysprosium", "AtomicNumber": 66, "Row": 8, "Column": 11, "Category": "Lanthanide"},
            {"Symbol": "Ho", "Name": "Holmium", "AtomicNumber": 67, "Row": 8, "Column": 12, "Category": "Lanthanide"},
            {"Symbol": "Er", "Name": "Erbium", "AtomicNumber": 68, "Row": 8, "Column": 13, "Category": "Lanthanide"},
            {"Symbol": "Tm", "Name": "Thulium", "AtomicNumber": 69, "Row": 8, "Column": 14, "Category": "Lanthanide"},
            {"Symbol": "Yb", "Name": "Ytterbium", "AtomicNumber": 70, "Row": 8, "Column": 15, "Category": "Lanthanide"},
            {"Symbol": "Lu", "Name": "Lutetium", "AtomicNumber": 71, "Row": 8, "Column": 16, "Category": "Lanthanide"},
            {"Symbol": "Hf", "Name": "Hafnium", "AtomicNumber": 72, "Row": 5, "Column": 3, "Category": "Transition Metal"},
            {"Symbol": "Ta", "Name": "Tantalum", "AtomicNumber": 73, "Row": 5, "Column": 4, "Category": "Transition Metal"},
            {"Symbol": "W", "Name": "Tungsten", "AtomicNumber": 74, "Row": 5, "Column": 5, "Category": "Transition Metal"},
            {"Symbol": "Re", "Name": "Rhenium", "AtomicNumber": 75, "Row": 5, "Column": 6, "Category": "Transition Metal"},
            {"Symbol": "Os", "Name": "Osmium", "AtomicNumber": 76, "Row": 5, "Column": 7, "Category": "Transition Metal"},
            {"Symbol": "Ir", "Name": "Iridium", "AtomicNumber": 77, "Row": 5, "Column": 8, "Category": "Transition Metal"},
            {"Symbol": "Pt", "Name": "Platinum", "AtomicNumber": 78, "Row": 5, "Column": 9, "Category": "Transition Metal"},
            {"Symbol": "Au", "Name": "Gold", "AtomicNumber": 79, "Row": 5, "Column": 10, "Category": "Transition Metal"},
            {"Symbol": "Hg", "Name": "Mercury", "AtomicNumber": 80, "Row": 5, "Column": 11, "Category": "Transition Metal"},
            {"Symbol": "Tl", "Name": "Thallium", "AtomicNumber": 81, "Row": 5, "Column": 12, "Category": "Post-transition Metal"},
            {"Symbol": "Pb", "Name": "Lead", "AtomicNumber": 82, "Row": 5, "Column": 13, "Category": "Post-transition Metal"},
            {"Symbol": "Bi", "Name": "Bismuth", "AtomicNumber": 83, "Row": 5, "Column": 14, "Category": "Post-transition Metal"},
            {"Symbol": "Po", "Name": "Polonium", "AtomicNumber": 84, "Row": 5, "Column": 15, "Category": "Metalloid"},
            {"Symbol": "At", "Name": "Astatine", "AtomicNumber": 85, "Row": 5, "Column": 16, "Category": "Halogen"},
            {"Symbol": "Rn", "Name": "Radon", "AtomicNumber": 86, "Row": 5, "Column": 17, "Category": "Noble Gas"},

            # Row 7
            {"Symbol": "Fr", "Name": "Francium", "AtomicNumber": 87, "Row": 6, "Column": 0, "Category": "Alkali Metal"},
            {"Symbol": "Ra", "Name": "Radium", "AtomicNumber": 88, "Row": 6, "Column": 1, "Category": "Alkaline Earth"},
            {"Symbol": "Ac", "Name": "Actinium", "AtomicNumber": 89, "Row": 9, "Column": 2, "Category": "Actinide"},
            {"Symbol": "Th", "Name": "Thorium", "AtomicNumber": 90, "Row": 9, "Column": 3, "Category": "Actinide"},
            {"Symbol": "Pa", "Name": "Protactinium", "AtomicNumber": 91, "Row": 9, "Column": 4, "Category": "Actinide"},
            {"Symbol": "U", "Name": "Uranium", "AtomicNumber": 92, "Row": 9, "Column": 5, "Category": "Actinide"},
            {"Symbol": "Np", "Name": "Neptunium", "AtomicNumber": 93, "Row": 9, "Column": 6, "Category": "Actinide"},
            {"Symbol": "Pu", "Name": "Plutonium", "AtomicNumber": 94, "Row": 9, "Column": 7, "Category": "Actinide"},
            {"Symbol": "Am", "Name": "Americium", "AtomicNumber": 95, "Row": 9, "Column": 8, "Category": "Actinide"},
            {"Symbol": "Cm", "Name": "Curium", "AtomicNumber": 96, "Row": 9, "Column": 9, "Category": "Actinide"},
            {"Symbol": "Bk", "Name": "Berkelium", "AtomicNumber": 97, "Row": 9, "Column": 10, "Category": "Actinide"},
            {"Symbol": "Cf", "Name": "Californium", "AtomicNumber": 98, "Row": 9, "Column": 11, "Category": "Actinide"},
            {"Symbol": "Es", "Name": "Einsteinium", "AtomicNumber": 99, "Row": 9, "Column": 12, "Category": "Actinide"},
            {"Symbol": "Fm", "Name": "Fermium", "AtomicNumber": 100, "Row": 9, "Column": 13, "Category": "Actinide"},
            {"Symbol": "Md", "Name": "Mendelevium", "AtomicNumber": 101, "Row": 9, "Column": 14, "Category": "Actinide"},
            {"Symbol": "No", "Name": "Nobelium", "AtomicNumber": 102, "Row": 9, "Column": 15, "Category": "Actinide"},
            {"Symbol": "Lr", "Name": "Lawrencium", "AtomicNumber": 103, "Row": 9, "Column": 16, "Category": "Actinide"},
            {"Symbol": "Rf", "Name": "Rutherfordium", "AtomicNumber": 104, "Row": 6, "Column": 3, "Category": "Transition Metal"},
            {"Symbol": "Db", "Name": "Dubnium", "AtomicNumber": 105, "Row": 6, "Column": 4, "Category": "Transition Metal"},
            {"Symbol": "Sg", "Name": "Seaborgium", "AtomicNumber": 106, "Row": 6, "Column": 5, "Category": "Transition Metal"},
            {"Symbol": "Bh", "Name": "Bohrium", "AtomicNumber": 107, "Row": 6, "Column": 6, "Category": "Transition Metal"},
            {"Symbol": "Hs", "Name": "Hassium", "AtomicNumber": 108, "Row": 6, "Column": 7, "Category": "Transition Metal"},
            {"Symbol": "Mt", "Name": "Meitnerium", "AtomicNumber": 109, "Row": 6, "Column": 8, "Category": "Transition Metal"},
            {"Symbol": "Ds", "Name": "Darmstadtium", "AtomicNumber": 110, "Row": 6, "Column": 9, "Category": "Transition Metal"},
            {"Symbol": "Rg", "Name": "Roentgenium", "AtomicNumber": 111, "Row": 6, "Column": 10, "Category": "Transition Metal"},
            {"Symbol": "Cn", "Name": "Copernicium", "AtomicNumber": 112, "Row": 6, "Column": 11, "Category": "Transition Metal"},
            {"Symbol": "Nh", "Name": "Nihonium", "AtomicNumber": 113, "Row": 6, "Column": 12, "Category": "Post-transition Metal"},
            {"Symbol": "Fl", "Name": "Flerovium", "AtomicNumber": 114, "Row": 6, "Column": 13, "Category": "Post-transition Metal"},
            {"Symbol": "Mc", "Name": "Moscovium", "AtomicNumber": 115, "Row": 6, "Column": 14, "Category": "Post-transition Metal"},
            {"Symbol": "Lv", "Name": "Livermorium", "AtomicNumber": 116, "Row": 6, "Column": 15, "Category": "Post-transition Metal"},
            {"Symbol": "Ts", "Name": "Tennessine", "AtomicNumber": 117, "Row": 6, "Column": 16, "Category": "Halogen"},
            {"Symbol": "Og", "Name": "Oganesson", "AtomicNumber": 118, "Row": 6, "Column": 17, "Category": "Noble Gas"},
        ]
        self.df_elements = pd.DataFrame(data = self.elements)
        self.x_ray_energies = {
            "Li": [54.3, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],
            "Be": [108.5, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],
            "B": [183.3, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],
            "C": [277, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],
            "N": [392.4, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],
            "O": [524.9, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],
            "F": [676.8, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],
            "Ne": [848.6, 848.6, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],
            "Na": [1040.98, 1040.98, 1071.1, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],
            "Mg": [1253.60, 1253.60, 1302.2, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],
            "Al": [1486.70, 1486.27, 1557.45, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],
            "Si": [1739.98, 1739.38, 1835.94, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],
            "P": [2013.7, 2012.7, 2139.1, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],
            "S": [2307.84, 2306.64, 2464.04, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],
            "Cl": [2622.39, 2620.78, 2815.6, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],
            "Ar": [2957.70, 2955.63, 3190.5, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],
            "K": [3313.8, 3311.1, 3589.6, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],
            "Ca": [3691.68, 3688.09, 4012.7, 341.3, 341.3, 344.9, np.nan, np.nan, np.nan],
            "Sc": [4090.6, 4086.1, 4460.5, 395.4, 395.4, 399.6, np.nan, np.nan, np.nan],

            "Ti": [4510.84, 4504.86, 4931.81, 452.2, 452.2, 458.4, np.nan, np.nan, np.nan],
            "V": [4952.20, 4944.64, 5427.29, 511.3, 511.3, 519.2, np.nan, np.nan, np.nan],
            "Cr": [5414.72, 5405.509, 5946.71, 572.8, 572.8, 582.8, np.nan, np.nan, np.nan],
            "Mn": [5898.75, 5887.65, 6490.45, 637.4, 637.4, 648.8, np.nan, np.nan, np.nan],
            "Fe": [6403.84, 6390.84, 7057.98, 705.0, 705.0, 718.5, np.nan, np.nan, np.nan],
            "Co": [6930.32, 6915.30, 7649.43, 776.2, 776.2, 791.4, np.nan, np.nan, np.nan],
            "Ni": [7478.15, 7460.89, 8264.66, 851.5, 851.5, 868.8, np.nan, np.nan, np.nan],
            "Cu": [8047.78, 8027.83, 8905.29, 929.7, 929.7, 949.8, np.nan, np.nan, np.nan],
            "Zn": [8638.66, 8615.78, 9572.0, 1011.7, 1011.7, 1034.7, np.nan, np.nan, np.nan],
            "Ga": [9251.74, 9224.82, 10264.2, 1097.92, 1097.92, 1124.8, np.nan, np.nan, np.nan],
            "Ge": [9886.42, 9855.32, 10982.1, 1188.00, 1188.00, 1218.5, np.nan, np.nan, np.nan],
            "As": [10543.72, 10507.99, 11726.2, 1282.00, 1282.00, 1317.0, np.nan, np.nan, np.nan],
            "Se": [11222.4, 11181.4, 12495.9, 1379.10, 1379.10, 1419.23, np.nan, np.nan, np.nan],
            "Br": [11924.2, 11877.6, 13291.4, 1480.43, 1480.43, 1525.90, np.nan, np.nan, np.nan],
            "Kr": [12649, 12598, 14112, 1586.0, 1586.0, 1636.6, np.nan, np.nan, np.nan],
            "Rb": [13395.3, 13335.8, 14961.3, 1694.13, 1692.56, 1752.17, np.nan, np.nan, np.nan],
            "Sr": [14165, 14097.9, 15835.7, 1806.56, 1804.74, 1871.72, np.nan, np.nan, np.nan],
            "Y": [14958.4, 14882.9, 16737.8, 1922.56, 1920.47, 1995.84, np.nan, np.nan, np.nan],
            "Zr": [15775.1, 15690.9, 17667.8, 2042.36, 2039.9, 2124.4, 2219.4, 2302.7, np.nan],
            
            "Nb": [16615.1, 16521.0, 18622.5, 2165.89, 2163.0, 2257.4, 2367.0, 2461.8, np.nan],
            "Mo": [17479.34, 17374.3, 19608.3, 2293.16, 2289.85, 2394.81, 2518.3, 2623.5, np.nan],
            "Tc": [18367.1, 18250.8, 20619.0, 2424.0, 2420.0, 2538.0, 2674.0, 2792.0, np.nan],
            "Ru": [19279.2, 19150.4, 21656.8, 2558.55, 2554.31, 2683.23, 2836.0, 2964.5, np.nan],
            "Rh": [20216.1, 20073.7, 22723.6, 2696.74, 2692.05, 2834.41, 3001.3, 3143.8, np.nan],
            "Pd": [21177.1, 21020.1, 23818.7, 2838.61, 2833.29, 2990.22, 3171.79, 3328.7, np.nan],
            "Ag": [22162.92, 21990.3, 24942.4, 2984.31, 2978.21, 3150.94, 3347.81, 3519.59, np.nan],
            "Cd": [23173.6, 22984.1, 26095.5, 3133.73, 3126.91, 3316.57, 3528.12, 3716.86, np.nan],
            "In": [24209.7, 24002.0, 27275.9, 3286.94, 3279.29, 3487.21, 3713.81, 3920.81, np.nan],
            "Sn": [25271.3, 25044.0, 28486.0, 3443.93, 3435.42, 3662.80, 3904.86, 4131.12, np.nan],
            "Sb": [26359.1, 26110.8, 29725.6, 3604.72, 3595.32, 3843.57, 4100.78, 4347.79, np.nan],
            "Te": [27472.4, 27201.7, 30995.7, 3769.33, 3758.8, 4029.58, 4301.7, 4570.9, np.nan],
            "I": [28612.0, 28317.2, 32294.7, 3937.65, 3926.04, 4209.58, 4507.5, 4800.9, np.nan],
            "Xe": [29779.0, 29458.0, 33624.0, 4109.9, np.nan, np.nan, np.nan, np.nan, np.nan],
            "Cs": [30972.8, 30625.1, 34986.9, 4286.5, 4272.2, 4619.8, 4935.9, 5280.4, np.nan],
            "Ba": [32193.6, 31817.1, 36378.2, 4466.26, 4450.9, 4827.53, 5156.5, 5531.1, np.nan],
            "La": [33441.8, 33034.1, 37801.0, 4650.97, 4634.23, 5042.1, 5383.5, 5788.5, 833.0],
            "Ce": [34719.7, 34278.9, 39257.3, 4840.2, 4823.0, 5262.2, 5613.4, 6052.0, 883.0],
            "Pr": [36026.3, 35550.2, 40748.3, 5037.7, 5013.5, 5488.9, 5850.0, 6322.1, 929.0],
            "Nd": [37361.0, 36847.4, 42271.3, 5236.6, 5207.7, 5721.6, 6089.4, 6602.1, 978.0],
            "Pm": [38724.7, 38171.2, 43826.0, 5432.5, 5407.8, 5961.0, 6339.0, 6892.0, np.nan],
            "Sm": [40118.1, 39522.4, 45413.0, 5636.1, 5609.0, 6205.1, 6586.0, 7178.0, 1081.0],

            "Eu": [41542.2, 40901.9, 47037.9, 5845.7, 5816.6, 6456.4, 6843.2, 7480.3, 1131.0],
            "Gd": [42996.2, 42308.9, 48697.0, 6057.2, 6025.0, 6713.2, 7102.8, 7785.8, 1185.0],
            "Tb": [44481.6, 43744.1, 50382.0, 6272.8, 6238.0, 6978.0, 7366.7, 8102.0, 1240.0],
            "Dy": [45998.4, 45207.8, 52119.0, 6495.2, 6457.7, 7247.7, 7635.7, 8418.8, 1293.0],
            "Ho": [47546.7, 46699.7, 53877.0, 6719.8, 6679.5, 7525.3, 7911.0, 8747.0, 1348.0],
            "Er": [49127.7, 48221.1, 55681.0, 6948.7, 6905.0, 7810.9, 8189.0, 9089.0, 1406.0],
            "Tm": [50741.6, 49772.6, 57517.0, 7179.9, 7133.1, 8101.0, 8468.0, 9426.0, 1462.0],
            "Yb": [52388.9, 51354.0, 59370.0, 7415.6, 7367.3, 8401.8, 8758.8, 9780.1, 1521.4],
            "Lu": [54069.8, 52965.0, 61283.0, 7655.5, 7604.9, 8709.0, 9048.9, 10143.4, 1581.3],
            "Hf": [55790.2, 54611.4, 63234.0, 7899.0, 7844.6, 9022.7, 9347.3, 10515.8, 1644.6],
            "Ta": [57532.0, 56277.0, 65223.0, 8146.1, 8087.9, 9343.1, 9651.8, 10895.2, 1710.0],
            "W": [59318.24, 57981.7, 67244.3, 8397.6, 8335.3, 9672.35, 9961.5, 11285.9, 1775.4],
            "Re": [61140.3, 59717.9, 69310.0, 8652.5, 8586.2, 10010.0, 10275.2, 11685.4, 1842.5],
            "Os": [63000.5, 61486.7, 71413.0, 8911.7, 8841.0, 10355.3, 10598.5, 12095.3, 1910.2],
            "Ir": [64995.6, 63286.7, 73560.8, 9175.1, 9099.5, 10708.3, 10920.3, 12512.6, 1979.9],
            "Pt": [66832.0, 65112.0, 75748.0, 9442.3, 9361.8, 11070.7, 11250.5, 12942.0, 2050.5],
            "Au": [68803.7, 66995.9, 77948.0, 9718.4, 9628.0, 11407.0, 11584.7, 13381.4, 2122.9],
            "Hg": [70819.0, 68895.0, 80253.0, 9988.8, 9897.6, 11822.6, 11924.1, 13830.1, 2195.3],
            "Tl": [72871.5, 70831.9, 82576.0, 10268.5, 10172.8, 12213.3, 12271.5, 14291.5, 2270.6],

                "Pb": [74969.4, 72804.2, 84936.0, 10551.5, 10449.5, 12613.7, 12622.6, 14764.4, 2345.5],
            "Bi": [77107.9, 74814.8, 87343.0, 10838.8, 10730.91, 13023.5, 12979.9, 15247.7, 2422.6],
            "Po": [79290.0, 76862.0, 89800.0, 11130.8, 11015.8, 13447.0, 13340.4, 15744.0, np.nan],
            "At": [81520.0, 78950.0, 92300.0, 11426.8, 11304.8, 13876.0, np.nan, 16251.0, np.nan],
            "Rn": [83780.0, 81070.0, 94870.0, 11727.0, 11597.9, 14316.0, np.nan, 16770.0, np.nan],
            "Fr": [86100.0, 83230.0, 97470.0, 12031.3, 11895.0, 14770.0, 14450.0, 17303.0, np.nan],
            "Ra": [88470.0, 85430.0, 100130.0, 12339.7, 12196.2, 15325.8, 14841.4, 17849.0, np.nan],
            "Ac": [90884.0, 87670.0, 102850.0, 12652.0, 12500.8, 15713.0, np.nan, 18408.0, np.nan],
            "Th": [93350.0, 89953.0, 105609.0, 12968.7, 12809.6, 16202.2, 15623.7, 18982.5, 2996.1],
            "Pa": [95868.0, 92287.0, 108427.0, 13290.7, 13122.2, 16702.0, 16024.0, 19568.0, 3082.3],
            "U": [98439.0, 94665.0, 111300.0, 13614.7, 13438.8, 17220.0, 16428.3, 20167.1, 3170.8],
            "Np": [np.nan, np.nan, np.nan, 13944.1, 13759.7, 17750.2, 16840.0, 20784.8, np.nan],
            "Pu": [np.nan, np.nan, np.nan, 14278.6, 14084.2, 18293.7, 17255.3, 21417.3, np.nan],
            "Am": [np.nan, np.nan, np.nan, 14617.2, 14411.9, 18852.0, 17676.5, 22065.2, np.nan]
        }
        self.df_xray_energies = pd.DataFrame(self.x_ray_energies).T
        self.df_xray_energies.columns = ["Ka", "Ka2", "Kb1", "La", "La2", "Lb1", "Lb2", "Ly1", "Ma"]
        self.selected_elements = []
        self.xray_lines = []
        self.xray_lines_display = []
        self.create_widgets()

    def create_widgets(self):
        """
        Build and layout all GUI widgets: element buttons, listboxes, and controls.

        - Places each element button in its grid position.
        - Sets up the selected-elements listbox and delete button.
        - Creates checkboxes for Kα, Lα, Mα line selection.
        - Adds listbox and buttons for managing chosen X-ray lines.
        """
        # Create buttons for each element
        #for symbol in elements_xray_energies:
        for _, element_data in self.df_elements.iterrows(): #iterate all elements in periodic table
            symbol = element_data['Symbol']
            row = element_data['Row']
            col = element_data['Column']
            category = element_data['Category']
            #grey out the elements which does not have x-ray energy in list
            energies = self.x_ray_energies.get(symbol, [np.nan]*9) #if no data, return all nans
            k_alpha = f"Kα: {energies[0]/1000:.2f} keV" if not np.isnan(energies[0]) else ""
            #k_alpha2 = f"Kα: {energies[1]/1000:.2f} keV" if not np.isnan(energies[1]) else ""
            #k_beta2 = f"Kb: {energies[2]/1000:.2f} keV" if not np.isnan(energies[2]) else ""
            l_alpha = f"Lα: {energies[3]/1000:.2f} keV" if not np.isnan(energies[3]) else ""
            m_alpha = f"Mα: {energies[8]/1000:.2f} keV" if not np.isnan(energies[8]) else ""

            btn_text = f"{symbol}\n{k_alpha}\n{l_alpha}\n{m_alpha}" #what show in the button
            btn_color = self.colors.get(category, "#CCCCCC")  # Default to grey if not found

            btn = tk.Button(self.root,
                            text=btn_text,
                            bg=btn_color,
                            command=lambda e=symbol: self.handle_click(e),
                            width=10, height=4)  
            btn.grid(row=row, column=col, padx=2, pady=2) # use the coordiantion row and col to make periodic table

        # Add a listbox to display selected elements
        self.selected_list = tk.Listbox(self.root, height=10)
        self.selected_list.grid(row=0, column=19, rowspan=7, padx=20)

        # Add a "Delete Element" button
        tk.Button(self.root, text="Delete Element", command=lambda: self.handle_delete(self.selected_list.get(tk.ANCHOR))).grid(row=5, column=19, padx=20)

        # Add checkbuttons for X-ray lines
        self.xray_lines_ka1 = tk.BooleanVar()
        self.ka1_check = tk.Checkbutton(self.root, text="Kα", variable=self.xray_lines_ka1)
        self.ka1_check.grid(row=0, column=20)

        self.xray_lines_la1 = tk.BooleanVar()
        self.la1_check = tk.Checkbutton(self.root, text="Lα", variable=self.xray_lines_la1)
        self.la1_check.grid(row=1, column=20)

        self.xray_lines_ma1 = tk.BooleanVar()
        self.ma1_check = tk.Checkbutton(self.root, text="Mα", variable=self.xray_lines_ma1)
        self.ma1_check.grid(row=2, column=20)

        # Add a listbox to display selected X-ray lines
        self.xray_line_list = tk.Listbox(self.root, height=10)
        self.xray_line_list.grid(row=0, column=21, rowspan=7, padx=20)

        # Add buttons to add or delete X-ray lines
        tk.Button(self.root, text="Add X-ray Line", command=self.add_xray_lines).grid(row=3, column=20)
        tk.Button(self.root, text="Delete X-ray Line", command=self.delete_xray_lines).grid(row=4, column=20)

    def handle_click(self, symbol):
        if symbol not in self.selected_elements:
            self.selected_elements.append(symbol)
        self.update_display()
        self.update_xray_options(symbol)

    def handle_delete(self, symbol):
        if symbol in self.selected_elements:
            self.selected_elements.remove(symbol)
        self.update_display()

    def update_display(self):
        self.selected_list.delete(0, tk.END)
        for elem in self.selected_elements:
            self.selected_list.insert(tk.END, elem)

        self.xray_line_list.delete(0, tk.END)
        for line in self.xray_lines:
            self.xray_line_list.insert(tk.END, line)

    def add_xray_lines(self):
        """
        Add checked X-ray lines (Kα, Lα, Mα) for the currently highlighted element.

        Reads which checkboxes are selected and appends both the
        raw code (e.g. 'Al_Ka') and display string (e.g. 'Al_Kα: 1.49 keV').
        """
        selected_element = self.selected_list.get(tk.ANCHOR)
        ka1_var = self.xray_lines_ka1.get()
        la1_var = self.xray_lines_la1.get()
        ma1_var = self.xray_lines_ma1.get()

        energies = self.x_ray_energies.get(selected_element, [np.nan]*9)

        if ka1_var and not np.isnan(energies[0]):
            energy = energies[0] / 1000  # Convert to keV
            self.xray_lines_display.append(f"{selected_element}_Kα: {energy:.2f} keV")
            self.xray_lines.append(f"{selected_element}_Ka")
        if la1_var and not np.isnan(energies[3]):
            energy = energies[3] / 1000  # Convert to keV
            self.xray_lines_display.append(f"{selected_element}_Lα: {energy:.2f} keV")
            self.xray_lines.append(f"{selected_element}_La")
        if ma1_var and not np.isnan(energies[8]):
            energy = energies[8] / 1000  # Convert to keV
            self.xray_lines_display.append(f"{selected_element}_Mα: {energy:.2f} keV")
            self.xray_lines.append(f"{selected_element}_Ma")

        self.update_display()

    def delete_xray_lines(self):
        selected_line = self.xray_line_list.get(tk.ANCHOR)
        if selected_line in self.xray_lines:
            self.xray_lines.remove(selected_line)
        self.update_display()

    def update_xray_options(self, symbol):
        """
        Enable or disable each line-selection checkbox based on
        whether the chosen element has a non-NaN energy for that line.

        Args:
            symbol: The atomic symbol whose data to inspect.
        """
        energies = self.x_ray_energies.get(symbol, [np.nan]*9)
        
        # Kα checkbox
        if not np.isnan(energies[0]):
            self.ka1_check.config(state="normal")
        else:
            self.ka1_check.config(state="disabled")

        # Lα checkbox
        if not np.isnan(energies[3]):
            self.la1_check.config(state="normal")
        else:
            self.la1_check.config(state="disabled")
            self.xray_lines_la1.set(False)

        # Mα checkbox
        if not np.isnan(energies[8]):
            self.ma1_check.config(state="normal")
        else:
            self.ma1_check.config(state="disabled")
            self.xray_lines_ma1.set(False)


