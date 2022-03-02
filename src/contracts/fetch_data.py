

from itertools import count
import os
import json    
import pandas as pd
from web3 import Web3

from src.utils.project_paths import DOC_PATH

class FetchData:

    def __init__(self) -> None:
        with open(os.path.join(DOC_PATH, 'abi.json'), 'r') as f:
            self.abi = json.load(f)    
        self.hard_block_start = 12736883
        self.hard_block_end = 14307725
        self.block_window_size = 2000
        provider_url = "https://eth-mainnet.alchemyapi.io/v2/uanCKV5LOP7NtaVUos3qtH-R-V1xy-A3"
        self.w3 = Web3(Web3.HTTPProvider(provider_url))
        self.pools = {
        "ILV Core": "0x25121EDDf746c884ddE4619b573A7B10714E2a36",
        "ILV-ETH LP": "0x8B4d8443a0229349A9892D4F7CbE89eF5f843F72",
        # "LINK Flash": "0xc759C6233e9C1095328D29CffF319780b28CecD8",
        # "XYZ Flash": "0x4C6997D462b0146fA54b747065411C1Ba0248595",
        # "AXIE Flash": "0x099A3B242dceC87e729cEfc6157632d7D5F1c4ef",
        # "SNX Flash": "0x9898d72c2901D09E72A426d1c24b6ab90eB100e7"
    }
    
    def get_relevant_event_logs(self):
        self.stake_events = self.make_events_df_all_pools(event_name="Staked")
        self.unstake_events = self.make_events_df_all_pools(event_name="Unstaked")
        # self.yield_claim_events = self.make_events_df_all_pools(event_name="YieldClaimed")

    def make_events_df_all_pools(self, event_name):
        dfs = []
        for pool_name, pool_address in self.pools.items():
            pool_dfs = self.make_events_df_per_pool(pool_address, pool_name, event_name)
            dfs.extend(pool_dfs)
        return pd.concat(dfs).reset_index(drop=True)

    def make_events_df_per_pool(self, pool_address, pool_label, event_name, abi=None):
        if abi is None:
            abi = self.abi
        contract = self.w3.eth.contract(address=pool_address, abi=abi)
        start = self.hard_block_start
        end = self.hard_block_start + self.block_window_size
        dfs = []
        for batch in count():
            data = self.get_events_data(contract, event_name, block_start=start, block_end=end)
            print("Batch nr: {}, elements: {}".format(batch, len(data)))
            start, end = self.get_new_block_window(len(data), start, end)
            print("START: {}, END: {}".format(start, end))
            df = self.parse_event_batch_to_df(pool_label, data, event_name)
            print("LENGTH DF: {}".format(len(df)))
            if df.empty:
                pass
            else:
                dfs.append(df)
            if start > self.hard_block_end:
                break
        return dfs

    def get_events_data(self, contract, event_name, block_start, block_end):
        staked_filter = contract.events[event_name].createFilter(fromBlock=block_start, toBlock=block_end)
        try:
            data = staked_filter.get_all_entries()
        except ValueError as e:
            print(e)
            """
            if e['code'] == -32000:
                pass
            else:
                raise
            """
            raise
        return data

    def parse_event_batch_to_df(self, pool_label, data, event_name):
        parsed = {}
        for i in range(len(data)):
            if event_name == "Staked":
                el = {
                    "address": data[i]["args"]["_from"],
                    "blockNumber": data[i]["blockNumber"],
                    "amount": data[i]["args"]["amount"],
                    "Pool": pool_label
                }
            elif event_name == "Unstaked":
                el = {
                    "address": data[i]["args"]["_to"],
                    "blockNumber": data[i]["blockNumber"],
                    "amount": data[i]["args"]["amount"],
                    "Pool": pool_label
                }
            elif event_name == "YieldClaimed":
                el = {
                    "blockNumber": data[i]["blockNumber"],
                    "address": data[i]['args']['_to'],
                    "sILV": data[i]['args']['sIlv'],
                    "amount": data[i]['args']['amount'],
                    "txhash": data[i]["transactionHash"].hex(),
                    "Pool": pool_label
                }
            elif event_name == "Transfer":
                el = {
                    "to": data[i]["args"]["to"],
                    "blockNumber": data[i]["blockNumber"],
                    "txhash": data[i]["transactionHash"].hex(),
                    "Pool": pool_label
                }
            else:
                el = {
                    "txhash": data[i]["transactionHash"].hex(),
                    "blockNumber": data[i]["blockNumber"],
                    "by": data[i]["args"]["_by"]
                }
            parsed[i] = el
        df = pd.DataFrame.from_dict(parsed, orient='index')
        return df


    def get_new_block_window(self, n_elements, start, end):
        window_size = end - start
        # if n_elements > 5000:
        #     window_size /= 2
        # elif n_elements < 50:   
        #     window_size *= 2
        start = end + 1
        end = start + window_size - 1
        return int(start), int(end)