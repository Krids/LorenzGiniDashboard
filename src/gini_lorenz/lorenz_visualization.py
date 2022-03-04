"""
This class is responsible for plotting the Lorenz-Curve

Name: Felipe Lana Machado
Date: 02/03/2022
"""

from cProfile import label
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
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
        txt = str(np.round(self.gini(plt_vals, norm=True),2))
        layout = {
        "title": f"Lorenz Curve - GINI: {txt}", 
        "xaxis": {"title": "Fraction of hodlers"}, 
        "yaxis": {"title": "Fraction of ILV owned"}, 
        "autosize": True
        }
        
        fig = Figure(data=data, layout=layout)
        fig.show()

    def plot_lorenz_by_month(self, df: pd.DataFrame) -> None:
        """This function plot the lorenz curve for all months in dataframe.

        Args:
            df (pd.DataFrame): Dataframe containing the month variable and the amount variable wich is going to
            be used to plot the chart.
        """
        layout = {
            "title": f"Lorenz Curve", 
            "xaxis": {"title": "Fraction of hodlers"}, 
            "yaxis": {"title": "Fraction of ILV owned"}, 
            "autosize": True
        }

        # Create figure
        fig = go.Figure(layout=layout)

        gini_list = []
        # Add traces, one for each slider step
        for step in np.arange(7, 13, 1):
            if step < 6:
                lst = list(df.loc[(df['amount'] > 0) & (df['month'] <= step)].amount)
            else:
                lst = list(df.loc[(df['amount'] > 0) & (df['month'] <= step) & (df['month'] >= 6)].amount)

            lst = np.sort(np.array(lst))       
            vals = lst.cumsum() / lst.sum()
            plt_vals = np.insert(vals, 0, 0)
            gini_list.append(str(np.round(self.gini(plt_vals, norm=True),2)))
            trace = {
                "name": f"Month: {df.loc[df['month'] == step].iloc[0]['month_name']} ({step})", 
                "x": np.linspace(0.0, 1.0, plt_vals.size),
                "y": plt_vals
                }

            fig.add_trace(trace)

        for step in np.arange(1, 4, 1):
            if step < 6:
                lst = list(df.loc[(df['amount'] > 0) & (df['month'] <= step)].amount)
            else:
                lst = list(df.loc[(df['amount'] > 0) & (df['month'] <= step) & (df['month'] >= 6)].amount)

            lst = np.sort(np.array(lst))       
            vals = lst.cumsum() / lst.sum()
            plt_vals = np.insert(vals, 0, 0)
            gini_list.append(str(np.round(self.gini(plt_vals, norm=True),2)))
            trace = {
                "name": f"Month: {df.loc[df['month'] == step].iloc[0]['month_name']} ({step})", 
                "x": np.linspace(0.0, 1.0, plt_vals.size),
                "y": plt_vals
                }

            fig.add_trace(trace)

        trace2 = {
            "name": "Line of equality", 
            "x": [0, 1], 
            "y": [0, 1]
        }
        fig.add_trace(trace2)

        fake_dict = {
            0: "July",
            1: "August",
            2: "September",
            3: "October",
            4: "November",
            5: "December",
            6: "January",
            7: "February",
            8: "March"
        }

        steps = []
        for i in range(len(fig.data)-1):
            step = dict(
                label=f"{fake_dict.get(i)}",
                method="update",
                args=[{"visible": [False] * (len(fig.data))},
                    {"title": str(i) + " Months since the release"}], 
            )
            step["args"][0]["visible"][i] = True  
            step["args"][0]["visible"][len(fig.data)-1] = True  
            steps.append(step)

        sliders = [dict(
            active=0,
            currentvalue={"prefix": "Months since release: "},
            steps=steps
        )]

        fig.update_layout(
            sliders=sliders
        )

        fig.show()

    def lorenz_matplotlib(self, plot=True, verbose=False) -> None:
        """Calculate the lorenz curve values with option to plot the the gini on the curve,
         also uses matplotlib here.

        Args:
            plot (bool, optional): if true plots the chart, else return only the lorenz values. Defaults to True.
            verbose (bool, optional): Print the gini inside the chart. Defaults to False.

        Raises:
            ValueError: ValueError when don`t have more then one element on the list.

        """
        
        # check size of input list
        if(self.lst.size == 1):
            raise ValueError('n has to be greater than 1')
            
        # normalisation and summation
        vals = self.lst.cumsum() / self.lst.sum()
        # add (0,0) to values
        plt_vals = np.insert(vals, 0, 0)

        if plot == True:
            # plot lorenz curve
            plt.plot(np.linspace(0.0, 1.0, plt_vals.size), plt_vals, "-bo")
            # plot equality curve
            plt.plot([0,1], [0,1], "-go")
            if verbose:
                plt.fill_between(np.linspace(0.0, 1.0, plt_vals.size),np.linspace(0.0, 1.0, plt_vals.size),
                                 plt_vals, color="lightsteelblue")
                txt = str(np.round(self.gini(plt_vals, norm=True),2))
                plt.text(0.48, 0.4, f"Gini = {txt}", size="large")
            plt.show()
                

    def gini(self, vals, norm=False):
        """This function calculates the gini corficient given some list of values.

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