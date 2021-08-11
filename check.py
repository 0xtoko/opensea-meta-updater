import argparse
import json
import logging
import itertools
import requests
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

# Save update list to file
def save_update_items(contract_address, items):
    with open(f'update_lists/{contract_address}_item_list.json', 'w') as file:
        json.dump(items, file)


# Load update list from file
def load_update_items(contract_address):
    with open(f'update_lists/{contract_address}_item_list.json', 'r') as file:
        items = json.load(file)
    return sorted(items,key=lambda x: x["node"]["asset"]["tokenId"])

# load query from file
def load_gql_query(file_name):
    with open(f'query/{file_name}', 'r') as file:
        query = file.read()
    return query


# Parse args
def get_script_arguments():
    parser = argparse.ArgumentParser(description='Usage example: python check.py -c "0x6c94954d0b265f657a4a1b35dfaa8b73d1a3f199" -s "QmT5uADipP1xmWSXXx9r7Bnzrb5gwNnuLdH8ohP3ue3qw9"')
    parser.add_argument('-u', '--uri-check-only',action='store_true',help='Use this to check new URI counts from saved file. Requires: "-s"("--hash")')
    parser.add_argument('-c','--contract-address',required=True,type=str,help='Contract address of NFT collection.')
    parser.add_argument('-s','--hash',type=str,help="(optional) Use this to count metadata with new URI.")
    parser.add_argument('-n','--null-ids',action='store_true',help='(optional) Use this to show token id of missing items.')
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
    slug_query = load_gql_query("slug_query.graphql")
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
    count_query = load_gql_query("collection_item_count_query.graphql")
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

    query = load_gql_query("asset_search_list_pagination_query.graphql")

    while has_next_page:
        time.sleep(delay)

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

def find_null_token_ids_and_new_hash(items, new_hash, show_null_ids):
    token_ids = []
    new_hash_count = 0
    for item in items:
        try:
            token_id = item["node"]["asset"]["tokenId"]
            token_ids.append(int(token_id))
            # Check if metadata uri matches given uri
            if new_hash:
                if new_hash in item["node"]["asset"]["tokenMetadata"]:
                        new_hash_count += 1
        except:
            logger.warning("Parsing Item Failed: Skipped")
    token_ids.sort()
    null_token_ids = []
    for id in range(token_ids[0], token_ids[-1]+1):
        if id not in token_ids:
            null_token_ids.append(str(id))
    # look for duplicate entries
    duplicate_token_ids = list([id for id in token_ids if token_ids.count(id) > 1])
    
    logger.info(f'Found {len(duplicate_token_ids)} duplicate IDs: {duplicate_token_ids}')

    if new_hash:
        logger.info(f"{new_hash_count}/{len(items)} items has new hash ({new_hash_count/len(items)*100}%)")
    else:
        logger.info('Set "-s" flag with new hash to check new hash count.')

    if show_null_ids:
        logger.info(f'Null Item Ids:{",".join(null_token_ids)}')
    else:
        logger.info('Set "-n" flag to show token id of null items')


def main():
    logging.basicConfig(format='%(asctime)s - Opensea Meta Updater - [Initialize] - %(levelname)s - %(message)s', level=logging.INFO)
    args = get_script_arguments()

    if args.uri_check_only:
        logging.basicConfig(format='%(asctime)s - Opensea Meta Updater - [Check URI] - %(levelname)s - %(message)s', level=logging.INFO,force=True)
        items = load_update_items(args.contract_address)
        find_null_token_ids_and_new_hash(items, args.hash, args.null_ids)
    
    else:
        logging.basicConfig(format='%(asctime)s - Opensea Meta Updater - [Create List] - %(levelname)s - %(message)s', level=logging.INFO,force=True)
        (collection_slug, total_count) = get_collection_detail(args.contract_address, args.cool_down)
        items = create_items_list(collection_slug, total_count, 100, args.cool_down, args.delay) #limit locked to 100. 100 max.
        save_update_items(args.contract_address,items)
        find_null_token_ids_and_new_hash(items, args.hash, args.null_ids)
        logger.info(f"Successfully Created and Saved {collection_slug}'s Items List")
        


if __name__ == '__main__':
    main()

