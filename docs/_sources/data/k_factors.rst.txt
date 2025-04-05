kfactors
========

.. class:: kfactors

   Class to find k-factors (Cliff-Lorimer factors) for STEM/SEM EDS spectra.

   :Input Parameter:
      None

   :Attributes:
      - **Data**
        The k-factors data for elements ranging from H to Cf.

      - **Column** 
        The format of attribute 'Data'.  
        The format is [atomic number, elemental symbol, K factors for K shell, K factors for L shell, K factors for M shell].

.. attribute:: Kfactors_HD2700

   Pandas DataFrame format of the k-factors data.

   .. method:: find_kfactors(x_rayline_list, index='Element')

      Find the k-factor for the given x-ray line list.

      :param x_rayline_list: List of x-ray lines (e.g., ['Al_Ka', 'Zr_Ka']).
      :type x_rayline_list: list
      :param index: Index column for searching (default is 'Element').
      :type index: str, optional
      :return: List of k-factors corresponding to the x-ray lines.
