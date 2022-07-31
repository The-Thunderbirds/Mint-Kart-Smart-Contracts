################### Helpers ###################

class Sellers:
    def get_type():
        return sp.TSet(sp.TAddress)

    def get_add_params_type():
        return sp.TRecord(sellers = sp.TAddress)

    def get_remove_params_type():
        return sp.TRecord(sellers = sp.TAddress)

    def is_seller(sellers, sender):
        return sellers.contains(sender)

class CustomerService:
    def get_type():
        return sp.TSet(sp.TAddress)
    
    def get_add_params_type():
        return sp.TRecord(customer_service = sp.TAddress)

    def get_remove_params_type():
        return sp.TRecord(customer_service = sp.TAddress)

class Buy:
    def get_type():
        return sp.TRecord(
            tokenId = sp.TNat,
            buyer = sp.TAddress)

class NFTMetadata:
    def get_type():
        return sp.TMap(sp.TString, sp.TBytes)
    
    def get_key_type():
        return sp.TString
    
    def get_value_type():
        return sp.TBytes

class Mint:
    def get_params_type():
        return sp.TRecord(
            tokenId = sp.TNat,
            metadata = NFTMetadata.get_type(),
            itemId = sp.TString,
            warranty = sp.TInt,
            mintkart_address = sp.TAddress)

    def get_batch_params_type():
        return sp.TList(Mint.get_params_type())

class Transfer:
    def get_params_type():
        return sp.TRecord(
            from_ = sp.TAddress, 
            tokenId = sp.TNat,
            to_ = sp.TAddress)

class Allowances:
    def get_key_type():
        return sp.TRecord(
            owner = sp.TAddress,
            operator = sp.TAddress,
            tokenId = sp.TNat)
    
    def get_value_type():
        return sp.TNat
    
    def make_key(owner, operator, tokenId):
        return sp.record(
            owner = owner,
            operator = operator,
            tokenId = tokenId)

class Twin:
    def get_type():
        return sp.TRecord(
            tokenId = sp.TNat,
            seller = sp.TAddress,
            createdOn = sp.TTimestamp)
    def get_create_params_type():
        return sp.TRecord(
            itemId = sp.TString, 
            tokenId = sp.TNat,
            seller = sp.TAddress,
            warranty = sp.TInt)


class Replace:
    def get_init_type():
        return sp.TRecord(
            tokenId = sp.TNat, 
            oldItemId = sp.TString, 
            newItemId = sp.TString, 
            mintkart_address = sp.TAddress)

    def get_create_type():
        return sp.TRecord(
            tokenId = sp.TNat,
            oldItemId = sp.TString, 
            newItemId = sp.TString)

class Burn:
    def get_params_type():
        return sp.TRecord(
            tokenId = sp.TNat,
            owner = sp.TAddress,
            mintkart_address = sp.TAddress)

    def get_create_params_type():
        return sp.TRecord(
            tokenId = sp.TNat)            

################### Helpers End ###################