# CV4EM

This is the repository for a library with integrated modules developed by the **CV4EM team**.

<p align="center">Centered text</p>

---
## 1. Installation and Setup
### Dependencies
The `kfactor.py` module requires the following Python libraries:

   - `pandas`: For data manipulation.
   - `hyperspy`: For analyzing spectroscopy or electron microscopy data.
   - `expy`: For advanced signal processing and data analysis.
   -  `numpy`: For numerical operations.
   - `copy`: For creating deep copies of objects.

Install the dependencies using `pip`:
```python 
  pip install pandas hyperspy expy numpy 
```
### Importing the Module
To use the `kfactors` class, import the module as follows:
```python
from kfactor import kfactors
```
## 3. Class Overview
|Class/Method Name |	Description |
| -----------------| -------------|
| `kfactors` | Class to store and retrieve k-factors for elements based on their X-ray lines (K, L, M) specific to the Bruker EDS detector in the Hitachi HD2700 STEM. | 
| `__init__`	| Initializes the `kfactors` class, setting up the column names and data (including the k-factors for various elements). | 
| `column`	| Attribute that defines the column names in the k-factor data (e.g., `Z`, `Element`, `K`, `L`, `M`). | 
| `data` | 	Attribute that stores the raw k-factor data as a list, representing various elements and their corresponding k-factors. | 
| `kfactors_HD2700`	| A pandas DataFrame created from the `data` attribute, allowing easy querying and manipulation of the k-factor data. | 
| `find_kfactors`	| Method to find and retrieve k-factors based on a list of X-ray lines (e.g., `Al_Ka`, `Zr_Ka`). It can work with lists or special spectrum objects.| 

### _class_ **kfactors**
Bases: `object`

Class to store and retrieve k-factors for elements based on their X-ray lines (K, L, M) for the Bruker EDS detector equipped in Hitachi HD2700 STEM. It allows querying k-factors for specific elements and X-ray lines, including handling complex spectrum data. The k-factors are stored in a pandas DataFrame (`kfactors_HD2700`), which is created from a list of raw data.

> ## **Attributes:**

 **column (list) :**
 
 Column names for the k-factor DataFrame ('Z', 'Element', 'K', 'L', 'M').

**self.data :**

A list of lists containing the data for each element. Each inner list contains: 
  - Atomic number.
  - Element name.
  - K-factors for K, L, and M lines.

**kfactors_HD2700 (pd.DataFrame) :** 

 DataFrame holding the k-factor data for each element.


> ## **Method:**
_**find_kfactors(x_rayline_list, index='Element')**_

Finds the k-factor(s) for the specified x-ray line(s). It looks up the corresponding k-factors in the DataFrame (e.g., `self.kfactors_HD2700`). The `index` allows for flexible searching through different columns of the DataFrame (e.g., `'Element'`, `'Z'`, etc.).

> #### **Parameters:**

**x_rayline_list :** `list` of `str`, default `None`

List of X-ray lines (e.g., ['Al_Ka', 'Zr_Ka']).

**index : str, default:** `'Element'`

Column to use as the search index (default is 'Element').


> #### **Returns:**
A list of k-factors corresponding to the provided X-ray lines. The list will have the same length as the input `x_rayline_list`.

> #### **Raises:**
### `ValueError`

  If the input is not a list or array of X-ray lines.
  
 ### `KeyError` 
 
 If an X-ray line cannot be found in the DataFrame.


### Examples

```python
# Example Usage of the `kfactors` class and `find_kfactors` method
kfactor = kfactors()  # Instantiate the kfactors object

# List of X-ray lines (e.g., ['Al_Ka', 'Zr_Ka', 'O_Ka', 'Ti_Ka'])
x_rayline_list = ['Al_Ka', 'Zr_Ka', 'O_Ka', 'Ti_Ka']

# Finding the k-factors for the provided X-ray lines based on the 'Element' column
results = kfactor.find_kfactors(x_rayline_list=x_rayline_list, index='Element')

# Output: results will contain the k-factors corresponding to each element's X-ray line in the list
print(results)  # Output: [11.011, 1.7, 1.21, 6.18]
````



## 4. Troubleshooting
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

## 5. FAQs
### **Q1: What are k-factors?**
K-factors are conversion factors used in EDS to convert X-ray intensities into elemental concentrations. They are specific to the detector and instrument configuration.

### **Q2: Can I add new k-factors to the module?**
Yes, you can modify the `data` attribute in the `kfactors` class to include additional elements or update existing k-factors.

### **Q3: How do I handle missing k-factors?**
If a k-factor is not available for a given X-ray line, the module returns `0`. You can manually update the `data` attribute to include the missing k-factor.

$${\color{red}blank \space \color{lightblue}blank \space \color{orange}blank}$$
