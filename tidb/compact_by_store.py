#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# This script is used to compact TiKV regions based on their properties.
# It checks the number of deletes in the MVCC and WriteCF, and if they exceed a threshold,
# it triggers a compaction for those regions. 
# It can process a specific store or all stores in parallel.
# Warning: It can process all stores in parallel.
# Warning: It will get all regions for each store from PD which may have a performance impact on PD
# Usage:
# python compact_by_store.py --pd "127.0.0.1:2379" --version "v7.5.2" --store-id 0 --concurrency 4

import time
import os
import subprocess
import json
import sys
import argparse
from threading import Thread
import questionary

# global variables
cnt = {'total': 0, 'need compaction': 0, 'skipped': 0}
tls = ''
# tls = "--ca-path /path/to/ca.crt --cert-path /path/to/client.crt --key-path /path/to/client.pem"

parser = argparse.ArgumentParser(description='Compact TiKV regions by store ID or all stores in parallel.')
parser.add_argument('--pd', type=str, default='127.0.0.1:2379', help='PD address (default:127.0.0.1:2379)')
parser.add_argument('--version', type=str, default='v7.5.2', help='TiKV version (default:v7.5.2)') 
parser.add_argument('--store-id', type=int, default=0, help='Store ID to process (default:0, process all stores in parallel)') 
parser.add_argument('--concurrency', "-c",type=int, default=2, help='Number of concurrent threads per store (default:2)')

args = parser.parse_args()
pd = args.pd 
version = args.version 
thread_per_store = args.concurrency 



import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
    #filename='app.log',
    #filemode='a'
)
logger = logging.getLogger(__name__)

def log(msg):
    logger.info(msg)

# Function to check and compact one region based on its properties
def check_and_compact_one_region(region_id, store_address):
    cnt['total'] += 1
    cmd = f'tiup ctl:{version} tikv {tls} --host {store_address} region-properties -r {region_id}'
    log(cmd)
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
    result_dict = {}
    if result.returncode == 0:
        for line in result.stdout.split('\n'):
            if len(line) > 0:
                key, value = line.split(': ')
                result_dict[key] = value

        # log(f"mvcc.num_deletes: {result_dict['mvcc.num_deletes']}")
        # log(f"mvcc.num_rows: {result_dict['mvcc.num_rows']}")
        # log(f"writecf.num_deletes: {result_dict['writecf.num_deletes']}")
        # log(f"writecf.num_entries: {result_dict['writecf.num_entries']}")
        
        if (float(result_dict['mvcc.num_deletes']) / float(result_dict['mvcc.num_rows']) > .2 or
            float(result_dict['writecf.num_deletes']) / float(result_dict['writecf.num_entries']) > .2):
            cnt['need compaction'] += 1
            start_time = time.time()
            subprocess.run(f'tiup ctl:{version} tikv {tls} --host {store_address} compact --bottommost force -c write -r {region_id}', 
                        shell=True,                 
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE)
            subprocess.run(f'tiup ctl:{version} tikv {tls} --host {store_address} compact --bottommost force -c default -r {region_id}', 
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE)
            end_time = time.time()
            elapsed = end_time - start_time
            log(f"Compacted region {region_id} on {store_address} in {elapsed:.2f} seconds.")
        else:
            cnt['skipped'] += 1
            log(f"No need to compact {store_address} region {region_id}")

# Function to process one batch regions on a specific store          
def process_regions_on_store(store_address, regions): 
    log(f"Processing store {store_address} with {len(regions)} regions")
    for region_id in regions:
        log(f"Processing region {region_id} on store {store_address}")
        check_and_compact_one_region(region_id, store_address)


# Function to process one store and its regions with concurrency
def process_one_store(store_id,concurrency):
    cmd = f'tiup ctl:{version} pd -u {pd} {tls} store {store_id}'
    log(f"Running command: {cmd}") 
    try:
        result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
        store_data = json.loads(result.stdout)
        if not store_data.get("store"):
            log(f"Store {store_id} not found or no data returned.")
            return  
        store = store_data["store"]
        store_address = store.get("address") 
        region_count = store_data["status"].get("region_count") 

        logger.warning(f"Processing store {store_id} with concurrency {concurrency}, address {store_address}, region count {region_count}") 
        logger.warning(f" we will get {region_count} regions for this store from PD in 1 RPC, which may have a performance impact on PD")
    
        #answer = questionary.confirm("Do you want to continue?").ask()
        #if not answer:
        #    print("Exiting without processing.")
        #    return
        cmd = f'tiup ctl:{version} pd -u {pd} {tls} region store {store_id}' 
        logger.info(f"Running command to get regions for store {store_id}: {cmd}")
        result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True) 
        region_data = json.loads(result.stdout) 
        region_ids = [region["id"] for region in region_data.get("regions", [])]
        if not region_ids:
            log(f"No regions found for store {store_id}")
            return
        log(f"Found {len(region_ids)} regions for store {store_id}") 

        batch_size = len(region_ids) // concurrency + 1
        threads = []
        for i in range(0, len(region_ids), batch_size):
            batch = region_ids[i:i + batch_size]
            log(f"Processing batch {i // batch_size + 1} for store {store_id} with {len(batch)} regions")
            thread = Thread(target=process_regions_on_store, args=(store_address, batch))
            threads.append(thread) 
            thread.start()
        
        for thread in threads:
            thread.join() 
        
        logger.info(f"Finished processing store {store_id}. Total regions processed: {len(region_ids)}")
    except subprocess.CalledProcessError as e:
        print(f"Maybe no such store-id:Command failed with error:\n{e.stderr}", file=sys.stderr)
    except json.JSONDecodeError:
        print("Maybe no such store-id:Failed to parse JSON output.", file=sys.stderr)
    except Exception as e:
        print(f"Maybe no such store-id:Unexpected error: {e}", file=sys.stderr)

# Function to compact all stores in parallel
def compact_all_stores():
    print("Compacting all stores...") 
    store_regions = {}
    try:
        cmd = f'tiup ctl:{version} pd -u {pd} {tls} store'
        logger.info("Starting to get stores from PD")
        logger.info(f"Running command: {cmd}")
        
        # Run the shell command and capture the output
        result = subprocess.run(
            f'tiup ctl:{version} pd -u {pd} {tls} store',
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=True
        )

        # Parse the JSON output
        data = json.loads(result.stdout)
        if not data.get("stores"):
            print("No stores found or no data returned.", file=sys.stderr)
            return 

        for store_info in data.get("stores", []):
            store = store_info.get("store", {})
            store_id = store.get("id")
            logger.info(f" store_id: {store_id}, address: {store.get('address')}") 

        print(f"Found {len(data['stores'])} stores.We will process them in parallel.") 
        ask = questionary.confirm("Do you want to continue?").ask()
        if not ask:
            print("Exiting without processing.")
            return 

        threads = []
        for store_info in data.get("stores", []):
            store = store_info.get("store", {})
            store_id = store.get("id")
            thread = Thread(target=process_one_store, args=(store_id, thread_per_store))
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()
        logger.info("Finished processing all stores.")
        print(f"Total regions processed: {cnt['total']}")
        print(f"Regions needing compaction: {cnt['need compaction']}")
        print(f"Regions skipped: {cnt['skipped']}")
        log(f"Total regions processed: {cnt['total']}") 

    except subprocess.CalledProcessError as e:
        print(f"Command failed with error:\n{e.stderr}", file=sys.stderr)
    except json.JSONDecodeError:
        print("Failed to parse JSON output.", file=sys.stderr)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)


if __name__ == "__main__":
    store_id = args.store_id
    if store_id > 0:
        process_one_store(store_id, thread_per_store)
    else:
        compact_all_stores() 
