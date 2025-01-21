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

##  Data Directory Documentation

The `data/` directory contains core modules for managing k-factors and periodic table data.

### K-Factor Script Documentation 
The `k_factor.py` script provides functionality to manage and retrieve k-factors for an EDS (Energy-Dispersive X-ray Spectroscopy) detector. K-factors are used to quantify the relationship between X-ray signal intensity and elemental concentration in materials science. This script is specifically designed for a Bruker EDS detector installed in a Hitachi HD2700 STEM.

#### Installation / Dependencies 

The script requires the following Python libraries:

- `Pandas`: For organizing and querying k-factor data.

- `NumPy`: For handling array-like inputs.

- `HyperSpy`: For compatibility with HyperSpy spectrum objects.

To install the dependencies, run:

```
 pip install pandas numpy hyperspy exspy

```

#### Usage
##### The `kfactors` Class
The `kfactors` class is the core of the script. It organizes k-factor data and provides methods to retrieve k-factors for specific X-ray lines.

Attributes
- `self.column`: A list of column names in the k-factor data table.

    - Format: `['Z', 'Element', 'K', 'L', 'M']`

- `self.data`: A list of lists containing k-factor data for each element.

- `self.kfactors_HD2700`: A Pandas DataFrame storing the k-factor data.

Methods

`__init__()`
Initializes the `kfactors` class and sets up the k-factor data.

`find_kfactors(x_rayline_list, index='Element')`
Retrieves the k-factors for the given X-ray lines.

Parameters:

- `x_rayline_list`: A list of X-ray lines (e.g., `['Al_Ka', 'Zr_Ka']`) or a HyperSpy `EDSTEMSpectrum`/`EDSSEMSpectrum` object.

-`index`: The column to use for searching (default is `'Element'`).

Returns:

A list of k-factors corresponding to the requested X-ray lines.

#### Examples 


#### **`K_factor.py`**



### Notes

- The `data/` directory includes core modules like `K_factor.py` and `Periodical_table.py`.
- The `module/` directory is for application-specific modules (add your custom modules here
- The `utils/` directory contains helper functions and utilities.
- The top-level `__init__.py` initializes the `CV4EM` package, enabling imports like `from CV4EM import ...`.




