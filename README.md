# Opensea Meta Updater

This is a Python script to queue metadata update on all items inside a collection.  
Inspired by [RUG.WTF](https://rug.wtf/)'s dynamic NFT art.  

It can query all items and queue metadata update on 10,000 items in around 250 seconds!

> Recently, Opensea has tightened the security around their GraphQL API. Therefore update.py script might be blocked by the cloudflare. In this only way to push the updates is to use the manual_mutation.py and copy paste the generated mutations to the browser console and run them. (This will only work if you already have generated the items list.)  
> Fix for this change are in progress.

<p align="center">
  <img src="https://storage.googleapis.com/opensea-static/Logomark/OpenSea-Full-Logo%20(dark)%20-%20thumb.png" width="500">
</p>

## Functionality
### update.py
- Queue metadata update on all items in the collection.
> Reminder: It will take some time for the metadata to get updated on Opensea client since this process is for requesting (queuing) metadata update. 
### check.py
- Checks the metadata update progress on Opensea end.
- Check duplicates and null item's token ID for detailed analysis on respose data.

## Installation

Simply run:
```bash
git clone https://github.com/ttakumat/opensea-meta-updater.git
cd opensea-meta-updater
pip install -r requirements.txt
```

## Usage

### update.py

#### 1. Query Items in Collection  
Query all items using collection's **contract address**.  
>　*You only have to run this once per collection since queried item will be saved.*
```bash
python update.py --create-list -c "{contract_address}"
```
#### 2. Queue Metadata Update
Queue metadata update on all items in collection.
```bash
python update.py --update_metadata -c "{contract_address}"
```
#### Alternatively, 
You can do both in one command.
```bash
python update.py --create-list --update_metadata -c "{contract_address}"
```
#### Arguments   

| arguments              | description                                                                                                                                                                                                      |
|------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| -h, --help             | show help and exit                                                                                                                                                                                               |
| --create-list          | This creates a json file with necessary data (metadata & item ID) to request updates on metadata in Opensea. This should only used once per contract unless new NFTs are minted. Requires: "--contract_address". |
| --update_metadata      | POST metadata update queue to Opensea. Requires: "--contract_address".                                                                                                                                           |
| -c, --contract-address | Contract address of NFT collection                                                                                                                                                                               |
| -b, --batch_size       | (optional) Number of Queues to batch in one request on '--update_metadata'. Default is 1000.                                                                                                                     |

---

### check.py

#### Track Opensea's metadata update progress
```bash
python check.py -c "{contract_address}" -s "{new_IPFS_hash}"
```
#### Get stats on items stored locally
```bash
python check.py -c "{contract_address}" -s "{new_IPFS_hash}" -n --uri-check-only
```

#### Arguments

| arguments              | description                                                                |
|------------------------|----------------------------------------------------------------------------|
| -h, --help             | show help and exit                                                         |
| -u, --uri-check-only   | Use this to check new URI counts from saved file. Requires: "-s"("--hash") |
| -c, --contract-address | Contract address of NFT collection.                                        |
| -s, --hash             | (optional) Use this to count metadata with new URI.                        |
| -n, --null-ids         | (optional) Use this to show token id of missing items.                     |
| --cool-down            | (optional) Seconds to wait when API rate limit is reached. Default is 1.   |
| --delay                | (optional) Interval of each API call. Default is 0.2.                      |

## Examples

### update.py

#### 1. Query Items in Collection  
```bash
python update.py --create-list -c "0x6c94954d0b265f657a4a1b35dfaa8b73d1a3f199"
```
#### 2. Queue Metadata Update
```bash
python update.py --update_metadata -c "0x6c94954d0b265f657a4a1b35dfaa8b73d1a3f199"
```
#### 3. Query Items and Queue Metadata Update
```bash
python update.py --create-list --update_metadata -c "0x6c94954d0b265f657a4a1b35dfaa8b73d1a3f199"
```

---

### check.py

#### Track Opensea metadata update progress
```bash
python check.py -c "0x6c94954d0b265f657a4a1b35dfaa8b73d1a3f199" -s "QmT5uADipP1xmWSXXx9r7Bnzrb5gwNnuLdH8ohP3ue3qw9"
```
#### Get stats on items stored locally
```bash
python check.py -c "0x6c94954d0b265f657a4a1b35dfaa8b73d1a3f199" -s "QmT5uADipP1xmWSXXx9r7Bnzrb5gwNnuLdH8ohP3ue3qw9" -n --uri-check-only
```

## Changelog
*2021/08/11*
- Fixed queries returning duplicate items
- Added check.py for checking metadata update progress on opensea side
- Simplified code
- More detailed log message
- Optimized delay and cool down time between API call

*2021/08/09*
- Initial Release
- Create update items list
- Send update Queue

## Donate
If you found this library useful and want to support my work feel free to donate.
- ETH: 0x50Eb12BF8911f792F41b94C60584c30372661dF1

## Contributing
Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## License
[MIT](https://choosealicense.com/licenses/mit/)