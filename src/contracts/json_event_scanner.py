import datetime
import json
import os
import time
from src.contracts.event_scanner_state import EventScannerState

from web3.datastructures import AttributeDict

from src.utils.project_paths import DATA_PATH


class JSONifiedState(EventScannerState):
        """Store the state of scanned blocks and all events.

        All state is an in-memory dict.
        Simple load/store massive JSON on start up.
        """

        def __init__(self):
            self.state = None
            self.fname = os.path.join(DATA_PATH, "ILV-Transfer.json")
            # How many second ago we saved the JSON file
            self.last_save = 0

        def reset(self):
            """Create initial state of nothing scanned."""
            self.state = {
                "last_scanned_block": 0,
                "blocks": {},
            }

        def restore(self):
            """Restore the last scan state from a file."""
            try:
                self.state = json.load(open(self.fname, "rt"))
                print(f"Restored the state, previously {self.state['last_scanned_block']} blocks have been scanned")
            except (IOError, json.decoder.JSONDecodeError):
                print("State starting from scratch")
                self.reset()

        def save(self):
            """Save everything we have scanned so far in a file."""
            with open(self.fname, "wt") as f:
                json.dump(self.state, f)
            self.last_save = time.time()

        #
        # EventScannerState methods implemented below
        #

        def get_last_scanned_block(self):
            """The number of the last block we have stored."""
            return self.state["last_scanned_block"]

        def delete_data(self, since_block):
            """Remove potentially reorganised blocks from the scan data."""
            for block_num in range(since_block, self.get_last_scanned_block()):
                if block_num in self.state["blocks"]:
                    del self.state["blocks"][block_num]

        def start_chunk(self, block_number, chunk_size):
            pass

        def end_chunk(self, block_number):
            """Save at the end of each block, so we can resume in the case of a crash or CTRL+C"""
            # Next time the scanner is started we will resume from this block
            self.state["last_scanned_block"] = block_number

            # Save the database file for every minute
            if time.time() - self.last_save > 60:
                self.save()

        def process_event(self, block_when: datetime.datetime, event: AttributeDict) -> str:
            """Record a ERC-20 staked in our database."""
            # Events are keyed by their transaction hash and log index
            # One transaction may contain multiple events
            # and each one of those gets their own log index

            # event_name = event.event # "Transfer"
            log_index = event.logIndex  # Log index within the block
            # transaction_index = event.transactionIndex  # Transaction index within the block
            txhash = event.transactionHash.hex()  # Transaction hash
            block_number = event.blockNumber

            # Convert ERC-20 Staked event to our internal format
            args = event["args"]
            event_name = event['event']

          

            if event_name == "Staked":
                el = {
                    "address": args["_from"],
                    "amount": args['amount'],
                    "event": event_name,
                    "timestamp": block_when.isoformat()
                }
            elif event_name == "Unstaked":
                el = {
                    "address": args["_to"],
                    "amount": args['amount'],
                    "event": event_name,
                    "timestamp": block_when.isoformat()
                }
            elif event_name == "Transfer":
                el = {
                    "to": args["to"],
                    "from": args['from'],
                    "value": args['value'],
                    "event": event_name,
                    "timestamp": block_when.isoformat()
                }
            

            # Create empty dict as the block that contains all transactions by txhash
            if block_number not in self.state["blocks"]:
                self.state["blocks"][block_number] = {}

            block = self.state["blocks"][block_number]
            if txhash not in block:
                # We have not yet recorded any transfers in this transaction
                # (One transaction may contain multiple events if executed by a smart contract).
                # Create a tx entry that contains all events by a log index
                self.state["blocks"][block_number][txhash] = {}

            # Record ERC-20 Staked in our database
            self.state["blocks"][block_number][txhash][log_index] = el

            # Return a pointer that allows us to look up this event later if needed
            return f"{block_number}-{txhash}-{log_index}"