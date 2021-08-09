# Opensea Meta Updater

This is a Python script to queue metadata update on all items inside a collection.  
Inspired by [RUG.WTF](https://rug.wtf/)'s dynamic NFT art.  

It can query all items and queue metadata update on 10,000 items in around 250 seconds!

<p align="center">
  <img src="https://storage.googleapis.com/opensea-static/Logomark/OpenSea-Full-Logo%20(dark)%20-%20thumb.png" width="500">
</p>

## Functionality
- Query all items in a collection.
- Queue metadata update on all items in a collection.
> Reminder: It will take some time for the metadata to get updated on Opensea client since this process is for requesting (queuing) metadata update. 

## Installation

Simply run:
```bash
git clone https://github.com/ttakumat/opensea-meta-updater.git
cd opensea-meta-updater
pip install -r requirements.txt
```

## Usage
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

## Examples
Update metadata of RUG.WTF's collection.
#### 1. Query Items in Collection  
```bash
python update.py --create-list -c "0x6c94954d0b265f657a4a1b35dfaa8b73d1a3f199"
```
#### 2. Queue Metadata Update
Queue metadata update on all items in collection.
```bash
python update.py --update_metadata -c "0x6c94954d0b265f657a4a1b35dfaa8b73d1a3f199"
```
#### 3. Query Items and Queue Metadata Update
You can do both in one command.
```bash
python update.py --create-list --update_metadata -c "0x6c94954d0b265f657a4a1b35dfaa8b73d1a3f199"
```

## Changelog
*0.1.0* - 2021/08/09
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