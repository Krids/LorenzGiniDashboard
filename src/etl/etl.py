import os
import pandas as pd
import numpy as np

from src.utils.project_paths import DATA_PROCESSED

class Etl:

    def get_data(self):
        """ Load the data from processed data folder.
        """   
        ilv_core = pd.read_csv(os.path.join(DATA_PROCESSED, 'ilv_core.csv'))
        ilv_eth_lp = pd.read_csv(os.path.join(DATA_PROCESSED, 'ilv_eth_lp.csv'))
        ilv = pd.read_csv(os.path.join(DATA_PROCESSED, 'ilv.csv'))

        return ilv_core, ilv_eth_lp, ilv     

    def process_data(self, ilv_core: pd.DataFrame, ilv_eth_lp: pd.DataFrame, ilv: pd.DataFrame):
        """Process the group by of the data and return the grouped dataframe (one line per address).

        Args:
            ilv_core (pd.DataFrame): Dataframe of ilv_core.
            ilv_eth_lp (pd.DataFrame): Dataframe of ilv-eth lp.
            ilv (pd.DataFrame): Dataframe of ilv transfers.

        Returns:
            The dataframes transformed.
        """
        ilv_core_x = ilv_core.groupby(['address', 'year', 'month']).amount.sum().reset_index()
        ilv_eth_lp_x = ilv_eth_lp.groupby(['address', 'year', 'month']).amount.sum().reset_index()
        ilv_x = ilv.groupby(['address', 'year', 'month']).value.sum().reset_index()

        return ilv_core_x, ilv_eth_lp_x, ilv_x
              