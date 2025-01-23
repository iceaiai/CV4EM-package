# CV4EM

This is the repository for a library with integrated modules developed by the **CV4EM team**.

---

## Prerequisites

Make sure you have the following libraries installed:

- `pandas`
- `numpy`
- `hyperspy`
- `exspy`

You can install these dependencies using pip:

```
 pip install pandas numpy hyperspy exspy

```

## kfactor.py 
### Table of Contents
  1. **Introduction**
     - Purpose of the Module
     - Key Features
  2. **Installation and Setup**
     - Dependencies
     - Importing the Module
  3. **Class Overview**
     - `kfactors` Class
  4. **Methods**
     - `__init__`
     - `find_kfactors`
5. **Examples**
    - Basic Usage
    - Advanced Usage
6. **Troubleshooting**
    - Common Errors
    - Debugging Tips
7. **FAQs**
---
## 1. Introduction
### Purpose of the Module
The `kfactor.py` module is designed to manage and retrieve **k-factors** for elements and their X-ray lines. K-factors are essential for quantitative analysis in **Energy Dispersive X-ray Spectroscopy (EDS)**, as they allow the conversion of X-ray intensities into elemental concentrations. This module is specifically tailored for **Bruker EDS detectors** used in **Hitachi HD2700 STEM** systems.

### Key Features
 - **Predefined k-factors**: Includes k-factors for a wide range of elements and their X-ray lines (K, L, M).
 - **Flexible input formats**: Supports lists of X-ray lines and EDS spectrum objects.
 - **Easy retrieval**: Quickly retrieve k-factors for specific elements and X-ray lines.
## 2. Installation and Setup
### Dependencies
The `kfactor.py` module requires the following Python libraries:

   - `pandas`: For data manipulation.
   - `hyperspy`:
   - `expy`: 
   -  `numpy`: For numerical operations.
   - `copy`: For creating deep copies of objects.

Install the dependencies using `pip`:
```python 
  pip install pandas numpy
```
### Importing the Module
To use the `kfactors` class, import the module as follows:
```python
from kfactor import kfactors
```
## 3. Class Overview
### `kfactors` Class
The `kfactors` class is the core of the module. It provides methods to store, access, and retrieve k-factors for elements and their X-ray lines.

#### **Attributes**
  - `column`: A list of column names for the k-factor data (`['Z', 'Element', 'K', 'L', 'M']`).
  - `data`: A list of lists containing k-factor data for each element.
  - `kfactors_HD2700`: A `pandas.DataFrame` storing the k-factor data in a tabular format.
#### **Methods**
  - `__init__`: Initializes the class and sets up the k-factor data.
  - `find_kfactors`: Retrieves k-factors for a given list of X-ray lines.
## 4. Methods
### `__init__`  Method
#### Description
Initializes the `kfactors` class and sets up the k-factor data.

#### **Parameters**
None.

#### **Returns**
None.

#### **Example**
```python
kfactor = kfactors()  # Initializes the clas
```


### `find_kfactors` Method
#### Description
Retrieves k-factors for a given list of X-ray lines. Supports multiple input formats, including lists of X-ray lines and EDS spectrum objects.

#### **Parameters**
  - `x_rayline_list`: `list`, `numpy.ndarray`, `exspy.signals.eds_tem.EDSTEMSpectrum`, or `exspy.signals.eds_sem.EDSSEMSpectrum`.
    - A list of X-ray lines (e.g., `['Al_Ka', 'Zr_Ka']`) or an EDS spectrum object.
  - `index`: `str`, optional (default: `'Element'`).
    - The column to use as the index for searching in the DataFrame.

#### **Returns**
- `data_list`: `list`.
   - A list of k-factors corresponding to the provided X-ray lines.

#### **Example**
````python
results = kfactor.find_kfactors(x_rayline_list=['Al_Ka', 'Zr_Ka', 'O_Ka', 'Ti_Ka'], index='Element')
print(results)  # Output: [11.011, 6.18, 1.7, 1.21]
````
## 5. Examples
### Basic Usage
Retrieve k-factors for specific X-ray lines:

```python
from kfactor import kfactors

# Initialize the kfactors class
kfactor = kfactors()

# Retrieve k-factors for specific X-ray lines
results = kfactor.find_kfactors(x_rayline_list=['Al_Ka', 'Zr_Ka', 'O_Ka', 'Ti_Ka'], index='Element')

# Display the results
print(results)  # Output: [11.011, 6.18, 1.7, 1.21]
````
### Advanced Usage
Retrieve k-factors from an EDS spectrum object:

```python
from kfactor import kfactors
import exspy.signals.eds_tem as eds_tem

# Load an EDS spectrum object
eds_spectrum = eds_tem.EDSTEMSpectrum.load('spectrum_file.hdf5')

# Initialize the kfactors class
kfactor = kfactors()

# Retrieve k-factors from the EDS spectrum
results = kfactor.find_kfactors(x_rayline_list=eds_spectrum)

# Display the results
print(results)
````
## 6. Troubleshooting
### Common Errors
  1. **Invalid X-ray line format**:
     - Error: `Please assign x-rayline_list values with a list format: [element1_K(or L or M)a','element2_K(or L or M)a'... ]`
     - Solution: Ensure the X-ray lines are in the correct format (e.g., `'Al_Ka'`).

2. **Missing dependencies**:
    - Error: `ModuleNotFoundError: No module named 'pandas'`
    - Solution: Install the required dependencies using `pip install pandas numpy`.

### Debugging Tips
  - Use `print` statements to inspect intermediate values (e.g., `EDS_lines`, `idx`, `line`).
  - Verify the input format of `x_rayline_list`.

## 7. FAQs
### **Q1: What are k-factors?**
K-factors are conversion factors used in EDS to convert X-ray intensities into elemental concentrations. They are specific to the detector and instrument configuration.

### **Q2: Can I add new k-factors to the module?**
Yes, you can modify the `data` attribute in the `kfactors` class to include additional elements or update existing k-factors.

### **Q3: How do I handle missing k-factors?**
If a k-factor is not available for a given X-ray line, the module returns `0`. You can manually update the `data` attribute to include the missing k-factor.

$${\color{red}blank \space \color{lightblue}blank \space \color{orange}blank}$$
