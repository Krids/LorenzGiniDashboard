import numpy as np
import matplotlib.pyplot as plt


class Lorenz:
    """class for creating a lorenz curve"""
    
    def __init__(self, lst):
        """constructor"""
        self.lst = np.sort(np.array(lst))

        
    def lorenz(self, plot=True, verbose=False):
        """calculate the lorenz curbve values with option to plot the curve"""
        
        # check size of input list
        if(self.lst.size == 1):
            raise ValueError('n has to be greater than 1')
            
        # normalisation and summation
        vals = self.lst.cumsum() / self.lst.sum()
        # add (0,0) to values
        plt_vals = np.insert(vals, 0, 0)
        if verbose:
            print(vals)

        if plot == True:
            # plot lorenz curve
            plt.plot(np.linspace(0.0, 1.0, plt_vals.size), plt_vals, "-bo")
            # plot equality curve
            plt.plot([0,1], [0,1], "-go")
            if verbose:
                plt.fill_between(np.linspace(0.0, 1.0, plt_vals.size),np.linspace(0.0, 1.0, plt_vals.size),
                                 plt_vals, color="lightsteelblue")
                txt = str(np.round(self.gini(plt_vals),2))
                plt.text(0.48, 0.4, f"Gini = {txt}", size="large")
                plt.show()
                
        return vals
    
    
    def gini(self, vals, norm=False):
        """calculation of the gini coefficient"""
        
        n = self.lst.size
        if n == 1:
            return 0.5*2
        a_sum = vals.sum()
        gini = (n+1-2*a_sum)/n
        if norm:
            return (n/(n-1))*gini
        else:
            return gini