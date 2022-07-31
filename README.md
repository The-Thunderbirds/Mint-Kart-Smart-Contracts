# NFT-Twinning-Smart-Contracts

## Smart Contracts

- Language Used: Smartpy
- Blockchain: Tezos
- Testnet: Jakartanet
- Number of contracts: 2
- Contracts: 
  - MintkartFA2 contract
  - Mintkart contract 
- Contract Addresses:
  - MintkartFA2: KT1ACE6u6tY8owf7oBVnk8w7EouLNiwMALc5
  - Mintkart: KT1AgsSUecHJVwiBxzJo7JYogVwF6ti4bkXR
- Tezos smart contract explorers:
  - MintkartFA2: https://jakarta.tzstats.com/KT1ACE6u6tY8owf7oBVnk8w7EouLNiwMALc5
  - Mintkart: https://jakarta.tzstats.com/KT1AgsSUecHJVwiBxzJo7JYogVwF6ti4bkXR
- FA2 Contract
  - Storage: 
    - administrator: Address of the main admin of the smart contract
    - admins: List of all admin addresses added via add-admin route
    - all_tokens: List of all token IDs minted
    - ledger: Maintains a map between address + tokenID to balance i.e. {address, tokenId} : balance (i.e. balance of a address for a given tokenId)
    - metadata: Metadata of the smart contract
    - paused: If true, then smart contracts won't be executing any functions if calls are made
    - token_metadata: Maintains a map between tokenId and its metadata, i.e. tokenID : {artifactUri, name, symbol etc}
    - total_supply: Maintains a map between tokenId and its total supply available, i.e. tokenID : Its amount mentioned during its mint
  - Entry points:
    - mint: 
       - Params: [tzToAddress, tokenId, hasMultipleQuantity, quantity, metadata]
       - Given address to which the token need to be minted, the tokenID itself, data related to the quantity of the token and the metadata of the token, the entry point mints the token.
    - single_transfer:
        - Params: [from_, tokenId, quantity, to_]
        - Given the tokenID and the quantity to be transferred, and the address to which the token need to be transferred to, this entry point transfers the token. It is transferred from the from_ address field.
    - init_sale:
       - Params: [market_place_address, tokenId, price, quantity]
       - It is used as the initializer of a sale. Refer to the FLOW section for more details.

- Market Place Contract
  - Storage:
    - fa2_contract_address: Address of FA2 contract
    - metadata : Metadata of the contract
    - sales: Maintains a map between tokenID and its sale details, i.e. 
    - tokenID : ( tokenId = int, price = int, saleCreatedBy = string, hasMultipleQuantity = bool, quantity = int, createdOn = datetime)
  - Entry points:
    - set_fa2_contract_addr:
        - Params: [address]
        - Setter function, which sets the fa2 contract associated with the current marketplace contract
     - create_sale: 
        - Params: [tokenId, price, quantity, owner, hasMultipleQuantity]
        - Given a tokenID, it adds it to the list of tokens available for sale. In this, it is assigned the price and the quantity to be kept for sale.
    - update_sale:
      - Params: [tokenId, price, quantity]
      - Given a tokenID, it updates the specified token in the token list that is for sale. Through this, one can update the price and the quantity that is kept for sale.
    - remove_sale:
      - Params: [tokenId]
      - Given a tokenID, it completely removes it from the sales listing.
    - buy:
      - Params: [tokenId, buyer, quantity]
      - Given the tokenID and the quantity of that token, it transfers the specified to the ‘buyer’ address field.


## Gamification
