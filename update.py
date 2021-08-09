import argparse
import json
import logging
import itertools
import requests
from bs4 import BeautifulSoup
from operator import itemgetter
import queue
from threading import Thread
import time

logger = logging.getLogger(__name__)

# Process items in chunks
def chunks(iterable, size):
    it = iter(iterable)
    while True:
        chunk = tuple(itertools.islice(it, size))
        if not chunk:
            break
        yield chunk


# Save update list
def save_update_items(contract_address, items):
    with open(f'update_lists/{contract_address}_item_list.json', 'w') as file:
        json.dump(items, file)


# Load update list
def load_update_items(contract_address):
    with open(f'update_lists/{contract_address}_item_list.json', 'r') as file:
        items = json.load(file)
    return sorted(items,key=lambda x: x["node"]["asset"]["tokenId"])


# Parse args
def get_script_arguments():
    parser = argparse.ArgumentParser(description='Usage example: python update.py --create-list --update_metadata -c "0x6c94954d0b265f657a4a1b35dfaa8b73d1a3f199"')
    parser.add_argument('--create-list',action='store_true',help='This creates a json file with necessary data (metadata & item ID) to request updates on metadata in Opensea. This should only used once per contract unless new NFTs are minted. Requires: "--contract_address".')
    parser.add_argument('--update_metadata',action='store_true',help='POST metadata update queue to Opensea. Requires: "--contract_address".')
    parser.add_argument('-c','--contract-address',required=True,type=str,help='Contract address of NFT collection.')
    parser.add_argument('-b','--batch_size',type=int,default=1000,help="(optional) Number of Queues to batch in one request on '--update_metadata'. Default is 1000.")
    parser.add_argument('--cool-down',type=int,default=1,help='(optional) Seconds to wait when API rate limit is reached. Default is 1.')
    parser.add_argument('--delay',type=int,default=0.2,help='(optional) Interval of each API call. Default is 0.2.')
    args = parser.parse_args()
    logger.info(args)
    return args

# Query collectionSlug and total number of items from Contract address
def get_collection_detail(contract_address, cool_down):
    url = "https://api.opensea.io/graphql/"
    # bypass cloudflare
    header={
        "Content-Type": "application/json",
        "User-Agent": "PostmanRuntime/7.26.8"
    }
    # Graphql Query: Get collectionSlug
    slug_query = """
    query NavSearchQuery($query: String!) {
        collections(first: 1, query: $query, sortBy: SEVEN_DAY_VOLUME, includeHidden: true) {
            edges {
                node {
                    slug
                }
            }
        }
    }
    """
    slug_variables = {
        "query": f"{contract_address}"
    }
    slug_param = {'query': slug_query, 'variables': slug_variables}
    # Make http POST
    slug_response = requests.post(url, json=slug_param, headers=header)
    if slug_response.status_code != 200:
        logger.warning(slug_response.text)
        logger.warning("Terminating Process: Check contract address")
        return ((),)
    
    try:
        slug_data = slug_response.json()
        slug_result = slug_data["data"]["collections"]["edges"][0]
        collection_slug = slug_result["node"]["slug"]
    except:
        logger.warning("Terminating Process: No CollectionSlug Found")
        return((),)
    
    logger.info(f"Found Collection: {collection_slug}")
    
    # wait for rate limit cooldown
    time.sleep(cool_down)

    # Graphql Query: Get number of items in collection
    count_query = """
    query ($collections: [CollectionSlug!]) {
        search(collections: $collections, first: 1) {
            totalCount
        }
    }
    """
    count_variables = {
        "collections": [f"{collection_slug}"]
    }
    count_param = {'query': count_query, 'variables': count_variables}
    # Make http POST
    count_response = requests.post(url, json=count_param, headers=header)
    if count_response.status_code != 200:
        logger.warning(count_response.text)
        logger.warning("Terminating Process: POST Request Error")
        return ((),)

    try:
        count_data = count_response.json()
        count_result = count_data["data"]["search"]["totalCount"]
    except:
        logger.warning("Terminating Process: No totalCount Found")
        return((),)
    
    logger.info(f"Total items in Collection: {count_result}")
    
    return (collection_slug, count_result)
    
# This will create update list of collection which includes data needed to queue metadata update
def create_items_list(collection_slug, total_count, limit, cool_down, delay):
    complete_items = []
    total_null_count = 0
    url = "https://api.opensea.io/graphql/"
    next_curser = ""
    has_next_page = True

    # bypass cloudflare
    header={
        "Content-Type": "application/json",
        "User-Agent": "PostmanRuntime/7.26.8"
    }

    while has_next_page:
        time.sleep(delay)

        query = """
        query AssetSearchListPaginationQuery(
        $collections: [CollectionSlug!]
        $count: Int
        $cursor: String
        ) {
            ...AssetSearchListPagination_data
        }

        fragment AssetSearchListPagination_data on Query {
        search(after: $cursor,collections: $collections, first: $count) {
            edges {
                node {
                    ...AssetSearchList_data
                }
            }
            totalCount
                pageInfo {
                    endCursor
                    hasNextPage
                }
            }
        }

        fragment AssetSearchList_data on SearchResultType {
            asset {
                assetContract {
                    address
                    chain
                    id
                }
                collection {
                    id
                }
                relayId
                tokenId
                ...AssetSelectionItem_data
                ...asset_url
                id
            }
        }

        fragment AssetSelectionItem_data on AssetType {
            imageUrl
            name
            relayId
        }

        fragment asset_url on AssetType {
            assetContract {
                address
                chain
                id
            }
            tokenId
        }
        """

        variables = {
        "collections": [
            f"{collection_slug}"
        ],
        "count": limit,
        "cursor": f"{next_curser}"
        }
        param = {'query': query, 'variables': variables}

        # Flag for http request result
        success = False

        while not success:
            # Make http POST
            response = requests.post(url, json=param, headers=header)
            # Check for HTTP error
            if response.status_code != 200:
                logger.warning(response.text)

                # Rate Limit Cooldown Counter
                for _ in range(cool_down, 0, -1):
                    time.sleep(1)
            
            # Request Success: Escape HTTP request loop
            else:
                success = True
            
        try:
            data = response.json()
            search_result = data["data"]["search"]
            items = search_result["edges"]
            # Remove null assets
            filtered_items = list(filter(lambda x: x["node"]["asset"] != None, items))
            # Log number of null assets
            if len(filtered_items) < len(items):
                null_count = len(items)-len(filtered_items)
                total_null_count += null_count
                logger.warning(f"Found {null_count} null Asset.")

            complete_items.extend(filtered_items)
            # Check if next page is available
            has_next_page = search_result["pageInfo"]["hasNextPage"]
            if has_next_page:
                next_curser = search_result["pageInfo"]["endCursor"]
        
        except:
            logger.warning(f"{response.text}")
            logger.warning("Error Ignored")
            has_next_page = False

        logger.info(f"{len(complete_items)}/{total_count} items completed")
    
    logger.info(f"{total_null_count} items returned 'null'")

    return complete_items

# This will queue metadata update to Opensea
def queue_metadata_update(items, batch_size, cool_down, delay):
    url = "https://api.opensea.io/graphql/"
    # bypass cloudflare
    header={
        "Content-Type": "application/json",
        "User-Agent": "PostmanRuntime/7.26.8"
    }

    total_update_count = 0
    total_fail_count = 0
    # Batch items to send in one request
    for item_chunk in chunks(items, batch_size):

        query_string = ""
        # Create query detail
        for item in item_chunk:
            try:
                item_id = item["node"]["asset"]["relayId"]
                alias = "_" + str(item["node"]["asset"]["tokenId"])
            except:
                logger.warning(f'Item ID not Found for: {item["node"]["asset"]["name"]})')
                
            query_string += f'{alias}: assets {{refresh(asset: "{item_id}")}}'

        query = f'mutation {{{query_string}}}'
        param = {'query': query}

        # Flag for http request result
        success = False

        while not success:
            # Make http POST
            response = requests.post(url, json=param, headers=header)
            # Check for HTTP error
            if response.status_code != 200:
                logger.warning(response.text)

                # Rate Limit Cooldown Counter
                for _ in range(cool_down, 0, -1):
                    time.sleep(1)

            # Request Success: Escape HTTP request loop
            else:
                success = True
        
        fail_count = 0

        # Parse response to check for unsuccessful update
        try:
            data = response.json()
            results = data["data"]
            for result_alias in results:
                status = results[result_alias]["refresh"]
                if status != True:
                    logger.warning(f"Failed to queue item with token id: {result_alias[1:]}")
                    fail_count += 1
        except:
            logger.warning("Failed to parse queue result json")

        time.sleep(delay)
        # Show progress
        total_update_count += len(item_chunk)-fail_count
        logger.info(f"Queued Update: {total_update_count}/{len(items)}")
    
    logger.info(f"Successfully Queued {len(items)-total_fail_count}/{len(items)}")



def main():
    logging.basicConfig(format='%(asctime)s - Opensea Meta Updater - [Initialize] - %(levelname)s - %(message)s', level=logging.INFO)
    args = get_script_arguments()

    if args.create_list:
        logging.basicConfig(format='%(asctime)s - Opensea Meta Updater - [Create List] - %(levelname)s - %(message)s', level=logging.INFO,force=True)
        (collection_slug, total_count) = get_collection_detail(args.contract_address, args.cool_down)
        items = create_items_list(collection_slug, total_count, 100, args.cool_down, args.delay) #limit locked to 100. 100 max.
        save_update_items(args.contract_address,items)
        logger.info(f"Successfully Created and Saved {collection_slug}'s Items List")
    
    if args.update_metadata:
        logging.basicConfig(format='%(asctime)s - Opensea Meta Updater - [Post Update] - %(levelname)s - %(message)s', level=logging.INFO,force=True)
        items = load_update_items(args.contract_address)
        queue_metadata_update(items, args.batch_size, args.cool_down, args.delay)


if __name__ == '__main__':
    main()
