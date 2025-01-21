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

### **Modules**

#### **`K_factor.py`**
The `K_factor.py` module provides functionality to manage and retrieve k-factors for an EDS detector. K-factors are used to quantify the relationship between X-ray signal intensity and elemental concentration in materials science.



### Notes

- The `data/` directory includes core modules like `K_factor.py` and `Periodical_table.py`.
- The `module/` directory is for application-specific modules (add your custom modules here
- The `utils/` directory contains helper functions and utilities.
- The top-level `__init__.py` initializes the `CV4EM` package, enabling imports like `from CV4EM import ...`.




