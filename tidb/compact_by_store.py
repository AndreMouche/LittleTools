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
#import questionary
import threading
import heapq 


parser = argparse.ArgumentParser(description='Compact TiKV regions by store ID or all stores in parallel.')
parser.add_argument('--pd', type=str, default='127.0.0.1:2379', help='PD address (default:127.0.0.1:2379)')
parser.add_argument('--version', type=str, default='v7.5.2', help='TiKV version (default:v7.5.2)') 
parser.add_argument('--store-id', type=int, default="-1", help='Store ID to process (default:-1. list storeinfo only) 0 means process all stores in parallel ') 
parser.add_argument('--start-key', type=str, default="", help='Start key for regions to compact (default: empty string)')
parser.add_argument('--end-key', type=str, default="", help='End key for regions to compact (default: empty string)') 
parser.add_argument('--concurrency', "-c",type=int, default=2, help='Number of concurrent threads per store (default:2)')


args = parser.parse_args()
pd = args.pd 
version = args.version 
thread_per_store = args.concurrency 

#pd_ctl = " /opt/other-binary/pd-ctl  --cacert ./tls/ca.crt --cert ./tls/tls.crt --key ./tls/tls.key "
#tikv_ctl = " /opt/other-binary/tikv-ctl --ca-path ./tls/ca.crt --cert-path ./tls/tls.crt --key-path ./tls/tls.key "
tikv_ctl = f"tiup ctl:{version} tikv"
pd_ctl = f"tiup ctl:{version} pd"



import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
    #filename='app.log',
    #filemode='a'
)
logger = logging.getLogger(__name__)

class Statistics:
    def __init__(self):
        self.lock = threading.Lock() 
        self.compact_regions = 0
        self.skipped_regions = 0
        self.checked_regions = 0 

    def add_checked(self):
        self.lock.acquire()
        try:
            self.checked_regions += 1
        finally:
            self.lock.release()

    def add_compact(self):
        self.lock.acquire()
        try:
            self.compact_regions += 1
        finally:
            self.lock.release() 

    def add_skip(self):
        self.lock.acquire()
        try:
            self.skipped_regions += 1
        finally:
            self.lock.release() 

class RegionProperties:
    def __init__(self, region_id, mvcc_num_deletes, mvcc_num_rows, writecf_num_deletes, writecf_num_entries):
        self.region_id = region_id
        self.mvcc_num_deletes = mvcc_num_deletes
        self.mvcc_num_rows = mvcc_num_rows
        self.writecf_num_deletes = writecf_num_deletes
        self.writecf_num_entries = writecf_num_entries
    
    def if_need_compact(self):
        if self.writecf_num_entries == 0:
            return False
        redundant_versions = float(self.writecf_num_entries) - float(self.mvcc_num_rows) + float(self.mvcc_num_deletes)
        if (float(redundant_versions) / float(self.writecf_num_entries) > .2 or
            float(self.writecf_num_deletes) / float(self.writecf_num_entries) > .2):
            return True
        else:
            return False

class Region: 
    def __init__(self, region_id, start_key, end_key):
        self.region_id = region_id
        self.start_key = start_key
        self.end_key = end_key 
    
    def __lt__(self, other):
        return self.start_key < other.start_key 

class StoreRegions:
    def __init__(self, store_id,address,start_key,end_key):
        self.store_id = store_id
        self.start_key = start_key 
        self.end_key = end_key
        self.address = address 
        self.lock = threading.Lock() 
        self.regions = [] 
    
    def load_all_regions(self):
        start_time = time.time() 
        thread_prefix = f"{self.store_id}_thread_load_all_regions"
        # Load all regions from TiKV store 
        # tiup ctl:v7.5.2 tikv --host ' 
        try:
            # tiup ctl:v7.5.2 tikv --host '127.0.0.1:20161' raft region  --start="7480000000000000FF0C00000000000000F8"
            #  /opt/other-binary/tikv-ctl   --ca-path ./tls/ca.crt --cert-path ./tls/tls.crt --key-path ./tls/tls.key --host db-tikv-2.db-tikv-peer.tidb10121348356836280592.svc:20160  raft region --start="" --limit=100
            cmd = f'{tikv_ctl}  --host {self.address} raft region --all-regions --skip-tombstone --start="{self.start_key}" --end="{self.end_key}" --limit=0' 
            logger.info(f"{thread_prefix} Running command to load all regions: {cmd}") 

            result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
            regions_data = json.loads(result.stdout)
            if not regions_data or not regions_data.get("region_infos"):
                logger.info(f"{thread_prefix} No more regions to process for store {self.store_id}.")
                return None 
            
            logger.info(f"{thread_prefix} Loaded {len(regions_data.get('region_infos'))} regions for store {self.store_id},cost {time.time() - start_time:.3f} seconds.") 
            for region_id,region_info in regions_data.get("region_infos").items():
                region = region_info.get("region_local_state", {}).get("region",{})
                logger.debug(f"{thread_prefix} region:{region}")
                start_key = region.get("start_key", "") 
                end_key = region.get("end_key")  
                state = region.get("state", {})
                if state  != "Normal":
                    logger.debug(f"{thread_prefix} Skipping region {region_id} in store {self.store_id} due to state: {state}")
                    continue
                cur_region = Region(region_id, start_key, end_key) 
                heapq.heappush(self.regions, cur_region)  # Use heapq to maintain sorted order by start_key 
        except subprocess.CalledProcessError as e:
            logger.warning(f"{thread_prefix} Command failed with error:\n{e.stderr}")
            self.finished = True
        except json.JSONDecodeError:
            logger.warning("{thread_prefix} Failed to parse JSON output.")
            self.finished = True
        except Exception as e:
            logger.warning(f"{thread_prefix} maybe no more regions:Unexpected error: {e}")
            self.finished = True
        finally:
            logger.info(f"{thread_prefix} Finished loading and sorting all regions for store {self.store_id}. Total regions loaded: {len(self.regions)},cost {time.time() - start_time:.3f} seconds.")

    def load_next_batch_regions(self,limit=100): 
        self.lock.acquire() 
        try:
            regions = [] 
            while self.regions:
                region = heapq.heappop(self.regions) 
                regions.append(region) 
                if len(regions) >= limit:
                    break 
            return regions 
        finally:
            self.lock.release() 
        
# Function to get region properties from TiKV store
def new_region_properties(region_id,store_address,thread_prefix):
    # Get region properties from TiKV store
    try:
        cmd = f'{tikv_ctl}  --host {store_address} region-properties -r {region_id}'
        logger.debug(f"{thread_prefix} Running command to get region properties for {region_id}: {cmd}") 
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True) 
        if result.returncode != 0:
            logger.error(f"{thread_prefix} Failed to get region properties for {region_id} on {store_address}: {result.stderr}")
            return None
        
        result_dict = {}
        for line in result.stdout.split('\n'):
            if len(line) > 0:
                key, value = line.split(': ')
                result_dict[key] = value
                logger.debug(f"{key}: {value}")
        
        return RegionProperties(
            region_id,
            float(result_dict['mvcc.num_deletes']),
            float(result_dict['mvcc.num_rows']),
            float(result_dict['writecf.num_deletes']),
            float(result_dict['writecf.num_entries'])
        )
    except subprocess.CalledProcessError as e:
        logger.error(f"{thread_prefix} Failed to get region properties for {region_id} on {store_address}: {e.stderr}")
        return None 

class TiKVStore:
    def __init__(self, store_id, address,start_key,end_key):
        self.store_id = store_id
        self.address = address
        self.statitics = Statistics() 
        self.start_time = time.time() 
        self.regions = StoreRegions(store_id,address,start_key,end_key)  
    
    def compact_one_region(self,region_id,thread_prefix):
        self.statitics.add_compact()
        start_time = time.time()
        def compact_one_cf(cf):
            try:
                compact_cmd = f'{tikv_ctl}  --host {self.address} compact --bottommost force -c {cf} -r {region_id}'
                logger.debug(f"{thread_prefix} Running command to compact {cf} CF for region {region_id}: {compact_cmd}")
                result = subprocess.run(compact_cmd, 
                            shell=True,                 
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
                if result.returncode != 0:
                    logger.error(f"{thread_prefix} Failed to compact {cf} CF for region {region_id} on {self.address}: {result.stderr}")
                    return False
                logger.debug(f"{thread_prefix} Compact {cf} CF for region {region_id} on {self.address} completed successfully.{result.stdout}")
                return True
            except subprocess.CalledProcessError as e:
                logger.error(f"{thread_prefix} Failed to compact {cf} CF for region {region_id} on {self.address}: {e.stderr}")
                return False 

        write_cf = compact_one_cf("write") 
        default_cf = compact_one_cf("default")
        end_time = time.time()
        logger.info(f"Compacted region {region_id} on {self.address} in {end_time - start_time:.3f} seconds. Result: Write CF: {write_cf}, Default CF: {default_cf}")
            

    def check_and_compact_one_region(self, region_id,thread_prefix):
        try:
            self.statitics.add_checked() 
            region_properties = new_region_properties(region_id, self.address,thread_prefix) 
            if not region_properties or region_properties.if_need_compact() == False: 
                self.statitics.add_skip()
                logger.info(f"{thread_prefix} Region {region_id} on {self.address} does not need compaction, skipping.")
                return False
            self.compact_one_region(region_id,thread_prefix) 
            new_properties = new_region_properties(region_id, self.address,thread_prefix) 
            if not new_properties or new_properties.if_need_compact() == False:
                return True 

            # TODO: check if need compact again 
            if new_properties.mvcc_num_deletes != region_properties.mvcc_num_deletes and new_properties.mvcc_num_deletes > 1000:
                logger.warning(f"{thread_prefix} Region {region_id} on {self.address} still has {new_properties.mvcc_num_deletes} deletes after compaction, it may need further attention.")
                self.compact_one_region(region_id,thread_prefix) 
            return True 
        except subprocess.CalledProcessError as e:
            logger.error(f"{thread_prefix} Failed to process region {region_id} on {self.address}: {e.stderr}")
            return False 
    
    
    def process_in_one_thread(self, thread_id): 
        total = 0
        compacted = 0 
        thread_prefix = f"{self.store_id}_thread_{thread_id}" 
        logger.info(f"{thread_prefix}:Thread {thread_id} started processing store {self.store_id}.")
        try:  
            while True:
                start = time.time() 
                regions = self.regions.load_next_batch_regions(limit=100) 
                if not regions or len(regions) == 0: 
                    break
                total += len(regions) 
                for region in regions:
                    region_id = region.region_id 
                    logger.info(f"{thread_prefix}: Processing region {region_id} on store {self.store_id}")
                    if self.check_and_compact_one_region(region_id,thread_prefix):
                        compacted += 1 
                cost = time.time() - start 
                last_key = regions[-1].end_key if regions else "N/A" 
                logger.warning(f"{thread_prefix}: Processed {len(regions)} regions for store {self.store_id},cost {cost:.3f}seconds, compacted {compacted} regions so far. last end-key:{last_key}" )
        except Exception as e:
            logger.error(f"{thread_prefix}:Unexpected error while processing store {self.store_id}: {e}")
        finally:     
            logger.warning(f"{thread_prefix}: Finished processing store {self.store_id}. Total regions processed: {total}, compacted: {compacted}")

    def check_and_compact_with_concurrency(self, concurrency=2):
        try:
            self.regions.load_all_regions() 
            logger.info(f"Starting to process store {self.store_id} with concurrency {concurrency}")
            threads = []
            for id in range(concurrency):
                thread = Thread(target=self.process_in_one_thread,args=(id,))
                threads.append(thread)
                thread.start()
            for thread in threads:
                thread.join()
        except Exception as e:
            logger.warning(f"check_and_compact_with_concurrency:Unexpected error: {e}")
        finally:
            logger.warning(f"Finished processing store {self.store_id}. Total regions processed: {self.statitics.checked_regions}, compacted: {self.statitics.compact_regions}, skipped: {self.statitics.skipped_regions}")

def new_tikv_store_from_json(store_data,start_key,end_key):
    store = store_data["store"]
    store_id = store.get("id")
    store_address = store.get("address") 
    region_count = store_data["status"].get("region_count") 
    labels = store.get("labels", []);
    # TODO:skip tombstone // disconnect
    for label in labels:
        if label.get("key") == "engine":
            label = label.get("value", "unknown") 
            if label == "tiflash":
                logger.warning(f"Skipping store {store_id} with address {store_address} as it is a TiFlash store.")
                return None
            else:
                break
    logger.info(f"New TiKV store {store_id} , address {store_address}, region count {region_count}") 
    return TiKVStore(store_id, store_address,start_key,end_key)

def process_one_store(store_id, concurrency,start_key,end_key): 
    logger.info(f"Processing store {store_id} with concurrency {concurrency}") 
    try:
        cmd = f'{pd_ctl} -u {pd}  store {store_id}'
        logger.info(f"Running command: {cmd}") 
        result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
        store_data = json.loads(result.stdout)
        tikv_store = new_tikv_store_from_json(store_data,start_key,end_key)
        if not tikv_store:
            logger.warning(f"Store {store_id} is a TiFlash store or not found, skipping.")
            return
        tikv_store.check_and_compact_with_concurrency(concurrency) 
    except subprocess.CalledProcessError as e:
        logger.error(f"Maybe no such store-id:Command failed with error:\n{e.stderr}")
    except json.JSONDecodeError:
        logger.error("Maybe no such store-id:Failed to parse JSON output.")
    except Exception as e:
        logger.error(f"Maybe no such store-id:Unexpected error: {e}")
    

# Function to compact all stores in parallel
def compact_all_stores(start_key,end_key,check_stores_only):
    logger.info("Compacting all stores...") 
    try:
        cmd = f'{pd_ctl} -u {pd}  store --state="Up"'
        logger.info("Starting to get stores from PD")
        logger.info(f"Running command: {cmd}")
        # Run the shell command and capture the output
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=True
        )

        # Parse the JSON output
        data = json.loads(result.stdout)
        if not data.get("stores"):
            logger.warning("No stores found or no data returned.")
            return 

        stores = []
        for store_info in data.get("stores", []):
            store = new_tikv_store_from_json(store_info,start_key,end_key)
            if store:
                stores.append(store) 

        if check_stores_only: 
            return
        logger.info(f"Found {len(stores)} stores.We will process them in parallel.") 
        #ask = questionary.confirm("Do you want to continue?").ask()
        #if not ask:
            #print("Exiting without processing.")
            #return 

        threads = []
        for store in stores:
            thread = Thread(target=store.check_and_compact_with_concurrency, args=(thread_per_store,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        logger.info("Finished processing all stores.")
    except subprocess.CalledProcessError as e:
        logger.warning(f"Command failed with error:\n{e.stderr}")
    except json.JSONDecodeError:
        logger.warning("Failed to parse JSON output.")
    except Exception as e:
        logger.warning(f"Unexpected error: {e}")


if __name__ == "__main__":
    store_id = args.store_id    
    start_key = args.start_key
    if start_key:
        logger.info(f"Using start key: {start_key}")
    else:
        logger.info("No start key provided, will start from the beginning.")
    end_key = args.end_key 
    if end_key:
        logger.info(f"Using end key: {end_key}")
    else:
        logger.info("No end key provided, will process until the end.") 
    if  store_id < 0:
        compact_all_stores(start_key,end_key,check_stores_only=True)
        logger.error("Invalid store ID provided. Please provide a valid store ID or 0 to compact all stores.")
        sys.exit(1)
    if store_id > 0:
        logger.info(f"Processing single store with ID: {store_id}")
        process_one_store(store_id, thread_per_store,start_key,end_key)
    else: 
        logger.info("Processing all stores in parallel.")
        compact_all_stores(start_key,end_key,check_stores_only=False) 

