Periodic Table
=============================

.. Class:: PeriodicTableApp
   Class to interactively look at elemental x-ray lines (Elements from H to Og)
   :Input Parameter: 
    - **Root** 
      Import and use tkinter.tk.TK() as root 
   
.. attribute:: add_xray_lines()
   Select on a particular elmenent to retrieve the K_a, L_a and M_a lines of that element in keV

.. attribute:: delete_xray_lines()
   Click on an already selected to remove the x-ray lines of that element
.. attribute:: xray_lines():
   View a list of selected x-ray lines
.. attribute:: xray_lines_display()
   View a list of selectec x-ray lines along with their energy
.. attribute:: update_xray_lines(symbol)
   
   :param symbol: Symbol of element 
   :type symbol: str

   
