import json
import itertools
import logging
import argparse
import os

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
def save_manual_mutation(contract_address, index, mutation):
    path = f"./manual_push_mutation/{contract_address}/"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(f"./{path}/{index}.graphql", 'w') as file:
        file.write(mutation)


def load_update_items(contract_address):
    with open(f'update_lists/{contract_address}_item_list.json', 'r') as file:
        items = json.load(file)
    return sorted(items,key=lambda x: x["node"]["asset"]["tokenId"])


# Parse args
def get_script_arguments():
    parser = argparse.ArgumentParser(description='Usage example: python manual_mutation.py -c "0x6c94954d0b265f657a4a1b35dfaa8b73d1a3f199"')
    parser.add_argument('-c','--contract-address',required=True,type=str,help='Contract address of NFT collection.')
    parser.add_argument('-b','--batch_size',type=int,default=1000,help="(optional) Number of Queues to batch in one request on '--update_metadata'. Default is 1000.")
    args = parser.parse_args()
    logger.info(args)
    return args


def create_mutation(contract_address, items, batch_size):
    index = 0
    for item_chunk in chunks(items, batch_size):
        index += 1
        mutation_string = ""
        # Create query detail
        for item in item_chunk:
            try:
                item_id = item["node"]["asset"]["relayId"]
                alias = "_" + str(item["node"]["asset"]["tokenId"])
            except:
                logger.warning(f'Item ID not Found for: {item["node"]["asset"]["name"]})')
                
            mutation_string += f'{alias}: assets {{refresh(asset: "{item_id}")}}'

        mutation = f'mutation {{{mutation_string}}}'
        # uri_query = query + "&variables="
        save_manual_mutation(contract_address, index, mutation)

def main():
    logging.basicConfig(format='%(asctime)s - Opensea Meta Updater - [Manual Mutation Generator] - %(levelname)s - %(message)s', level=logging.INFO)
    args = get_script_arguments()

    items = load_update_items(args.contract_address)
    create_mutation(args.contract_address, items, args.batch_size)
    logger.info("Completed")


if __name__ == '__main__':
    main()


