
import datetime
import os
import time
import logging

from web3 import Web3

from src.contracts.event_scanner import EventScanner
from src.contracts.json_event_scanner import JSONifiedState

from src.utils.project_paths import DOC_PATH, DATA_PATH

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # The demo supports persistant state by using a JSON file.
    # You will need an Ethereum node for this.
    # With locally running Geth, the script takes 10 minutes.
    # The resulting JSON state file is 2.9 MB.
    import sys
    import json
    from web3.providers.rpc import HTTPProvider

    from tqdm import tqdm

    # RCC has around 11k Transfer events
    # https://etherscan.io/token/0x9b6443b0fb9c241a7fdac375595cea13e6b7807a

    # pools = {
    #     "ILV Core": "0x25121EDDf746c884ddE4619b573A7B10714E2a36",
    #     "ILV-ETH LP": "0x8B4d8443a0229349A9892D4F7CbE89eF5f843F72",
    #     "LINK Flash": "0xc759C6233e9C1095328D29CffF319780b28CecD8",
    #     "XYZ Flash": "0x4C6997D462b0146fA54b747065411C1Ba0248595",
    #     "AXIE Flash": "0x099A3B242dceC87e729cEfc6157632d7D5F1c4ef",
    #     "SNX Flash": "0x9898d72c2901D09E72A426d1c24b6ab90eB100e7"
    # }
    RCC_ADDRESS = "0x767FE9EDC9E0dF98E07454847909b5E959D7ca0E"

    # Reduced ERC-20 ABI, only Transfer event
    with open(os.path.join(DOC_PATH, 'abi.json'), 'r') as f:
        ABI = json.load(f)

    def run():

        if len(sys.argv) < 2:
            print("Usage: eventscanner.py https://eth-mainnet.alchemyapi.io/v2/uanCKV5LOP7NtaVUos3qtH-R-V1xy-A3")
            sys.exit(1)

        api_url = sys.argv[1]

        # Enable logs to the stdout.
        # DEBUG is very verbose level
        logging.basicConfig(level=logging.INFO)

        provider = HTTPProvider(api_url)

        # Remove the default JSON-RPC retry middleware
        # as it correctly cannot handle eth_getLogs block range
        # throttle down.
        provider.middlewares.clear()

        w3 = Web3(provider)

        # Prepare stub ERC-20 contract object
        abi = ABI
        ERC20 = w3.eth.contract(abi=abi)

        # Restore/create our persistent state
        state = JSONifiedState()
        state.restore()

        # chain_id: int, w3: Web3, abi: dict, state: EventScannerState, events: List, filters: {}, max_chunk_scan_size: int=10000
        scanner = EventScanner(
            w3=w3,
            contract=ERC20,
            state=state,
            # events=[ERC20.events.Staked, ERC20.events.Unstaked, ERC20.events.Transfer],
            events=[ERC20.events.Transfer],
            filters={"address": RCC_ADDRESS},
            # How many maximum blocks at the time we request from JSON-RPC
            # and we are unlikely to exceed the response size limit of the JSON-RPC server
            max_chunk_scan_size=100000
        )

        # Assume we might have scanned the blocks all the way to the last Ethereum block
        # that mined a few seconds before the previous scan run ended.
        # Because there might have been a minor Etherueum chain reorganisations
        # since the last scan ended, we need to discard
        # the last few blocks from the previous scan results.
        chain_reorg_safety_blocks = 10
        scanner.delete_potentially_forked_block_data(state.get_last_scanned_block() - chain_reorg_safety_blocks)

        # Scan from [last block scanned] - [latest ethereum block]
        # Note that our chain reorg safety blocks cannot go negative
        start_block = max(state.get_last_scanned_block() - chain_reorg_safety_blocks, 0)
        end_block = scanner.get_suggested_scan_end_block()
        blocks_to_scan = end_block - start_block

        print(f"Scanning events from blocks {start_block} - {end_block}")

        # Render a progress bar in the console
        start = time.time()
        with tqdm(total=blocks_to_scan) as progress_bar:
            def _update_progress(start, end, current, current_block_timestamp, chunk_size, events_count):
                if current_block_timestamp:
                    formatted_time = current_block_timestamp.strftime("%d-%m-%Y")
                else:
                    formatted_time = "no block time available"
                progress_bar.set_description(f"Current block: {current} ({formatted_time}), blocks in a scan batch: {chunk_size}, events processed in a batch {events_count}")
                progress_bar.update(chunk_size)

            # Run the scan
            result, total_chunks_scanned = scanner.scan(start_block, end_block, progress_callback=_update_progress)

        state.save()
        duration = time.time() - start
        print(f"Scanned total {len(result)} Transfer events, in {duration} seconds, total {total_chunks_scanned} chunk scans performed")

    run()