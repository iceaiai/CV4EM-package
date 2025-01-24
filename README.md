# CV4EM

This is the repository for a library with integrated modules developed by the **CV4EM team**.

---

### Table of Contents
  1. **Installation and Setup**
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
## 1. Installation and Setup
### Dependencies
The `kfactor.py` module requires the following Python libraries:

   - `pandas`: For data manipulation.
   - `hyperspy`:
   - `expy`: 
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

  __self.column :__

  A list defining the names of the columns in the data table.

  - `'Z'`: Atomic number of the element (e.g., for oxygen, Z = 8).
  - `'Element'`: Atomic number of the element (e.g., for oxygen, Z = 8).
  - `'K'`, `'L'`, `'M'`: K-factors for K, L, and M X-ray lines.

**self.data :**

A list of lists containing the data for each element. Each inner list contains: 
  - Atomic number.
  - Element name.
  - K-factors for K, L, and M lines.

**self.kfactors_HD2700 :**

A Pandas DataFrame created using self.data and self.column. This DataFrame stores the data for easy access and manipulation.


> ### **Constructors:**
**pd.DataFrame(data=data, df=None, columns=column)**

> #### **Parameters:**
**data**: `list` of `lists`, `NumPy array`, `dict`, `DataFrame`, or similar, default `None`

This is the main data that will populate the `DataFrame`. If you pass a list of lists, each sublist is treated as a row in the DataFrame. It can also be a `NumPy array` or a dictionary, depending on the structure of the data. If a `DataFrame` is provided, it will be used directly. If `list of lists`, each inner list corresponds to a row of data.
If `NumPy array`, the shape of the array should match the intended number of rows and columns.
If `dict`, keys are used as column labels, and values are the data.
If a `DataFrame` is passed, it will be used as-is, meaning the columns parameter will be ignored.
If `None`, a `ValueError` will be raised as `data` is a required parameter.


**df**: DataFrame, optional, default `None`

An optional Pandas DataFrame to use for k-factor data lookup. If not provided, the method uses the default DataFrame (`self.kfactors_HD2700`) initialized in the class.

**columns** : `list` of `str`, optional, default `None`

A list of column names to use for indexing in the DataFrame. If not provided, the method will use the default columns defined in the class (i.e., `['Z', 'Element', 'K', 'L', 'M']`).

> ## **Method:**
find_kfactors(x_rayline_list, index='Element')

Finds the k-factor(s) for the specified x-ray line(s). It looks up the corresponding k-factors in the DataFrame (e.g., `self.kfactors_HD2700`). The `index` allows for flexible searching through different columns of the DataFrame (e.g., `'Element'`, `'Z'`, etc.).

> #### **Parameters:**

x_rayline_list : `list` of `str`, default `None`

A list of X-ray lines (e.g., ['Al_Ka', 'Zr_Ka']) that you want to find the corresponding k-factors for. The X-ray lines are typically a combination of element symbol and X-ray line (e.g., Al_Ka, Zr_Ka). This parameter is required and cannot be None.

index : str, default: `'Element'`

This parameter specifies which column in the DataFrame should be used as the search index. By default, it is set to `'Element'`. The method will search the `self.kfactors_HD2700 DataFrame` (or whichever DataFrame is being used) based on the values in the specified column (`index`). You can set index to another column name (e.g., 'Z', 'K', etc.) if you want to search using that column instead of 'Element'.


> #### **Returns:**
A list of k-factors corresponding to the provided X-ray lines. The list will have the same length as the input `x_rayline_list`.


Example Usage:

```python
# Example Usage of the `kfactors` class and `find_kfactors` method
kfactor = kfactors()  # Instantiate the kfactors object

# List of X-ray lines (e.g., ['Al_Ka', 'Zr_Ka', 'O_Ka', 'Ti_Ka'])
x_rayline_list = ['Al_Ka', 'Zr_Ka', 'O_Ka', 'Ti_Ka']

# Finding the k-factors for the provided X-ray lines based on the 'Element' column
results = kfactor.find_kfactors(x_rayline_list=x_rayline_list, index='Element')

# Output: results will contain the k-factors corresponding to each element's X-ray line in the list
print(results)
````

Expected Output:
```python
>>> [11.011, 1.7, 1.21, 6.18]
```





## 4. Methods
## `__init__(self)`

The constructor method that initializes the attributes of the kfactors class. It defines the column names and k-factor data, then converts the data into a Pandas DataFrame for easy access.

### **Parameters**
No parameters are needed for initialization.
### **Returns**
None (initializes the object).
### **Example**
```python
kfactor = kfactors()  # Initializes the class
```

## `find_kfactors`
```python
def find_kfactors(self, x_rayline_list, index='Element'):
```
 Retrieves the k-factors for the specified X-ray lines. This method allows users to look up k-factors by providing a list of X-ray lines (such as Al_Ka, Zr_Ka).



### **Parameters**

`x_rayline_list`: `list`, `numpy.ndarray`, `exspy.signals.eds_tem.EDSTEMSpectrum`, or `exspy.signals.eds_sem.EDSSEMSpectrum`.

Specifies the X-ray lines for which k-factors are to be retrieved.

  - If a **list** or **NumPy array** is provided, it should contain X-ray lines in the format `'Element_Line'` (e.g., `['Al_Ka', 'Zr_Ka']`).

  - If an **EDS spectrum object** is provided (from the `exspy` library), the X-ray lines will be extracted automatically from the object's metadata.

`index` : `str`, optional (default: `'Element'`)

Specifies the column to use as the index for searching in the DataFrame. By default, the `'Element'` column is used as the index. This parameter allows you to change the index to another column (e.g., `'Z'` for atomic number).


### **Returns**
`data_list` (list of float):

A list of k-factor values corresponding to the X-ray lines provided in `x_rayline_list`. The list is ordered in the same way as the input list of X-ray lines.

### **Example**
```python
# Create an instance of the kfactors class
kfactor = kfactors()

# Define a list of X-ray lines you want to retrieve k-factors for
x_rayline_list = ['Al_Ka', 'Zr_Ka', 'O_Ka', 'Ti_Ka']

# Use the find_kfactors method to get the k-factors for the specified X-ray lines
results = kfactor.find_kfactors(x_rayline_list=x_rayline_list)

# Print the results
print(results)  # Output: [11.011, 1.7, 1.21, 6.18]

```




### **Example**:

````python
index = 'Z'  # Use atomic number as the index
````

### **Returns**
## `data_list` : `list`
A list of k-factors corresponding to the provided X-ray lines.

Each element in the list corresponds to the k-factor for the respective X-ray line in x_rayline_list.

If a k-factor is not available for a given X-ray line, 0 is returned.

Example:

```python
[11.011, 6.18, 1.7, 1.21]  # K-factors for ['Al_Ka', 'Zr_Ka', 'O_Ka', 'Ti_Ka']
```

#### **Example**
````python
results = kfactor.find_kfactors(x_rayline_list=['Al_Ka', 'Zr_Ka', 'O_Ka', 'Ti_Ka'], index='Element')
print(results)  # Output: [11.011, 6.18, 1.7, 1.21]
````

1. The method first checks if a custom DataFrame (`df`) is provided. If not, it uses the internal `kfactors_HD2700` DataFrame.
2. It sets the index of the DataFrame to the `index` parameter (default: `'Element'`).
3. It iterates over the provided `x_rayline_list`, extracts the element and X-ray line (e.g., `Al_Ka` -> `Al` and `Ka`), and retrieves the corresponding k-factor from the DataFrame.
4. It returns a list of k-factors.

> [!WARNING]
> If the input x_rayline_list is not in the correct format, the method will print a helpful error message:

> Error Message Example:
```python
print(f"Please assign x-rayline_list values with a list format: [element1_Ka', 'element2_La'... ]")
````
> This ensures that users are aware of the required format and can correct the input accordingly.

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
Suppose you're working with a HyperSpy EDS spectrum and want to retrieve the k-factors for the X-ray lines present in the spectrum. Here's how you can do it:

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
