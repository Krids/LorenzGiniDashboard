"""
This class is responsible for plotting the Lorenz-Curve

Name: Felipe Lana Machado
Date: 02/03/2022
"""

import numpy as np
import plotly.express as px
from plotly.graph_objs import Data, Figure

import warnings
warnings.filterwarnings("ignore")

class LorenzCurve:

    def __init__(self, lst: list) -> None:
        self.lst = np.sort(np.array(lst))

    def plot_lorenz(self) -> None:
        """Plots the Lorenz curve given some list of values.
        """                
        # normalisation and summation
        vals = self.lst.cumsum() / self.lst.sum()
        # add (0,0) to values
        plt_vals = np.insert(vals, 0, 0)

        trace1 = {
        "name": "Lorenz Curve", 
        "x": np.linspace(0.0, 1.0, plt_vals.size),
        "y": plt_vals}
        trace2 = {
        "name": "Line of equality", 
        "x": [0, 1], 
        "y": [0, 1]
        }
        data = Data([trace1, trace2])
        txt = str(np.round(self.gini(plt_vals),2))
        layout = {
        "title": f"Lorenz Curve - GINI: {txt}", 
        "xaxis": {"title": "Fraction of hodlers"}, 
        "yaxis": {"title": "Fraction of ILV owned"}, 
        "autosize": True
        }
        fig = Figure(data=data, layout=layout)
        fig.show()

    def gini(self, vals, norm=False):
        """_summary_

        Args:
            vals (_type_): Values to calculate the gini coeficient.
            norm (bool, optional): Normalize the data?. Defaults to False.

        Returns:
            _type_: Gini coeficient for the data inputed.
        """        
        n = self.lst.size
        if n == 1:
            return 0.5*2
        a_sum = vals.sum()
        gini = (n+1-2*a_sum)/n
        if norm:
            return (n/(n-1))*gini
        else:
            return gini