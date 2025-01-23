import hyperspy.api as hs
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

class EDS_Bruker:
    def __init__(self,elements, x_ray_lines):
        self.colors = ['r','g','b','m','c','y','w','r','g','b','m','c','y','w']
        self.elements = elements
        self.x_ray_lines = x_ray_lines
        self.extended_color_names = [
            'blue', 'green', 'red', 'cyan', 'magenta', 'yellow',  'white',
            'navy', 'teal', 'maroon', 'olive', 'purple', 'gold', 'brown', 'pink'
            ]
        self.colormaps4overlay = {}
        self.colormaps4individual = {}
        for color_name in self.extended_color_names:
            self.colormaps4overlay[color_name] = mcolors.LinearSegmentedColormap.from_list(
                color_name, [(0, 0, 0, 0), mcolors.to_rgba(color_name)]  # Transparent to color
            )
            self.colormaps4individual[color_name] = mcolors.LinearSegmentedColormap.from_list(
                color_name, ['black', color_name]
            )
    def plot_images_non_hs(self,eds_maps, plot_type,alpha=0.8,vmax_scaler=1.5):
        """
        Plots EDS maps either individually or as an overlay based on plot_type.
        Parameters:
        - eds_maps: List of 2D arrays (EDS maps to plot).
        - plot_type: 'i' for individual plots, 'o' for overlay.
        - alpha: transparency for each map in overlay mode
        - vmax_scaler: a scaler of vmax in overlay mode
        """
        if plot_type == 'i':
            # Plot each EDS map individually
            for i in range(len(eds_maps)):
                cmap_name = self.extended_color_names[i % len(self.extended_color_names)]  # Cycle through colormaps
                cmap = self.colormaps4individual[cmap_name]
                
                plt.figure(figsize=(6, 6))
                plt.imshow(eds_maps[i], cmap=cmap)
                plt.colorbar(label='Intensity')
                plt.title(f"EDS Map {i} - {cmap_name}", fontsize=14)
                plt.axis('off')
                plt.show()
        
        elif plot_type == 'o':
            # Overlay all EDS maps on the same plot
            plt.figure(figsize=(8, 8))
            for i in range(len(eds_maps)):
                color_min = np.min(eds_maps[i].data)
                color_max = np.max(eds_maps[i].data)
                cmap_name = self.extended_color_names[i % len(self.extended_color_names)]
                cmap = self.colormaps4overlay[cmap_name]
                
                # Overlay each map with some transparency (alpha)
                plt.imshow(eds_maps[i], cmap=cmap, alpha=alpha , interpolation='None',vmin=0, vmax=color_max/vmax_scaler)
            
            #plt.colorbar(label='Overlay Intensity')
            #plt.legend()
            plt.title("Overlay of EDS Maps", fontsize=16)
            plt.axis('off')
            plt.show()

    def plot_images_hs(self,eds_maps, plot_type,alpha=0.8,vmax_scaler=1.5):
        """
        Plots EDS maps either individually or as an overlay based on plot_type.
        Parameters:
        - eds_maps: List of 2D arrays (EDS maps to plot).
        - plot_type: 'i' for individual plots, 'o' for overlay.
        - alpha: transparency for each map in overlay mode
        - vmax_scaler: a scaler of vmax in overlay mode
        """
        if plot_type == 'i':
            # Plot each EDS map individually
            for i in range(len(eds_maps)):
                cmap_name = self.extended_color_names[i % len(self.extended_color_names)]  # Cycle through colormaps
                cmap = self.colormaps4individual[cmap_name]
                
                plt.figure(figsize=(6, 6))
                plt.imshow(eds_maps[i], cmap=cmap)
                plt.colorbar(label='Intensity')
                plt.title(f"EDS Map {i} - {cmap_name}", fontsize=14)
                plt.axis('off')
                plt.show()
        
        elif plot_type == 'o':
            # Overlay all EDS maps on the same plot
            plt.figure(figsize=(8, 8))
            for i in range(len(eds_maps)):
                color_min = np.min(eds_maps[i].data)
                color_max = np.max(eds_maps[i].data)
                cmap_name = self.extended_color_names[i % len(self.extended_color_names)]
                cmap = self.colormaps4overlay[cmap_name]
                
                # Overlay each map with some transparency (alpha)
                plt.imshow(eds_maps[i], cmap=cmap, alpha=alpha , interpolation='None',vmin=0, vmax=color_max/vmax_scaler)
            
            #plt.colorbar(label='Overlay Intensity')
            #plt.legend()
            plt.title("Overlay of EDS Maps", fontsize=16)
            plt.axis('off')
            plt.show()


"""
Example use:
plot_images_non_hs(eds_maps, 'o') for overlay 
plot_images_non_hs(eds_maps, 'i') for each individual map
"""