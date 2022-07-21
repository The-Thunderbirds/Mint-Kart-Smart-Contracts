import smartpy as sp
FA2 = sp.io.import_script_from_url("https://smartpy.io/templates/FA2.py")


################### Error Messages ###################

class FA2ErrorMessage:
    PREFIX = "FA2_"
    NOT_ADMIN = "{}NOT_ADMIN".format(PREFIX)
    NOT_SELLER = "{}NOT_SELLER".format(PREFIX)
    NOT_ALLOWED = "{}NOT_ALLOWED".format(PREFIX)
    TOKEN_UNDEFINED = "{}TOKEN_UNDEFINED".format(PREFIX)
    DUPLICATE_TOKEN_ID = "{}DUPLICATE_TOKEN_ID".format(PREFIX)
    INSUFFICIENT_BALANCE = "{}INSUFFICIENT_BALANCE".format(PREFIX)
    NOT_CUSTOMER_SERVICE = "{}NOT_CUSTOMER_SERVICE".format(PREFIX)
    
class MarketPlaceErrorMessage:
    PREFIX = "MARKETPLACE_"
    NOT_ADMIN = "{}NOT_ADMIN".format(PREFIX)
    NOT_SELLER = "{}NOT_SELLER".format(PREFIX)
    TOKEN_UNDEFINED = "{}TOKEN_UNDEFINED".format(PREFIX)
    DUPLICATE_TWIN = "{}SALE_EXISTS_WITH_GIVEN_TOKEN_ID".format(PREFIX)
    TWINNING_DOESNOT_EXIST = "{}TWINNING_DOESNOT_EXIST".format(PREFIX)
    INSUFFICIENT_BALANCE = "{}INSUFFICIENT_BALANCE".format(PREFIX)
    WARRENTY_EXPIRED = "{}WARRENTY_EXPIRED".format(PREFIX)
    TWINNING_ALREADY_EXIST = "{}TWINNING_ALREADY_EXIST".format(PREFIX)
    ALREADY_REPLACED_ONCE = "{}ALREADY_REPLACED_ONCE".format(PREFIX)
    WARRENTY_NOT_EXPIRED = "{}WARRENTY_NOT_EXPIRED".format(PREFIX)

################### Error Messages End ###################
    
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
            warrenty = sp.TInt,
            mintkart_address = sp.TAddress)

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
            warrenty = sp.TInt)


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

################### FA2 ###################

class MintkartFA2(FA2.FA2):

    def __init__(self, config, metadata, admin):
        FA2.FA2.__init__(self, config, metadata, admin)
        self.update_initial_storage(
            sellers = sp.set([admin]),
            customer_service = sp.set([admin]),
            allowances = sp.big_map(l = {}, tkey = Allowances.get_key_type(), tvalue = Allowances.get_value_type()))

    """ [tokenId, metadata, itemId, warrenty, mintkart_address] """
    @sp.entry_point
    def mint(self, params):
        sp.set_type_expr(params, Mint.get_params_type())
        sp.verify((self.data.sellers).contains(sp.sender), message = FA2ErrorMessage.NOT_SELLER)
        sp.verify(~ self.token_id_set.contains(self.data.all_tokens, params.tokenId), message = FA2ErrorMessage.DUPLICATE_TOKEN_ID)
        
        self.token_id_set.add(self.data.all_tokens, params.tokenId)
        
        user = self.ledger_key.make(sp.sender, params.tokenId)
        self.data.ledger[user] = FA2.Ledger_value.make(1)

        self.data.token_metadata[params.tokenId] = sp.record(
            token_id    = params.tokenId,
            token_info  = params.metadata
        )
        if self.config.store_total_supply:
            self.data.total_supply[params.tokenId] = 1

        allowances_key = Allowances.make_key(sp.sender, params.mintkart_address, params.tokenId)
        self.data.allowances[allowances_key] = 1

        mintkart = sp.contract(Twin.get_create_params_type(), params.mintkart_address, entry_point = "create_twin").open_some()
        sp.transfer(sp.record(
                        itemId = params.itemId, 
                        tokenId = params.tokenId,
                        seller = sp.sender,
                        warrenty = params.warrenty),
                    sp.mutez(0), 
                    mintkart)

    """ [from_, tokenId, to_] """
    @sp.entry_point
    def single_transfer(self, params):
        sp.set_type_expr(params, Transfer.get_params_type())
        allowances_key = sp.local('allowances_key', 
                            Allowances.make_key(
                                        params.from_,
                                        sp.sender,
                                        params.tokenId))
        sp.verify(
            (sp.sender == params.from_) |  ((self.data.allowances.get(allowances_key.value, 0) 
            >= 1)), message = FA2ErrorMessage.NOT_SELLER)
        sp.verify(self.data.all_tokens.contains(params.tokenId), message = FA2ErrorMessage.TOKEN_UNDEFINED)

        from_user = self.ledger_key.make(params.from_, params.tokenId)
        to_user = self.ledger_key.make(params.to_, params.tokenId)

        current_balance = self.data.ledger.get(from_user, sp.record(balance = 0)).balance
        sp.verify( current_balance >= 1, message = FA2ErrorMessage.INSUFFICIENT_BALANCE)
        
        self.data.ledger[to_user] = FA2.Ledger_value.make(1)
        del self.data.ledger[from_user]
        
        sp.if sp.sender != params.from_:
            del self.data.allowances[allowances_key.value]

    """ [tokenId, oldItemId, newItemId, mintkart_address] """
    @sp.entry_point
    def init_replace_item(self, params):
        sp.set_type_expr(params, Replace.get_init_type())
        
        sp.verify((self.data.customer_service).contains(sp.sender), message = FA2ErrorMessage.NOT_CUSTOMER_SERVICE)
        sp.verify(self.token_id_set.contains(self.data.all_tokens, params.tokenId), message = FA2ErrorMessage.TOKEN_UNDEFINED)

        mintkart = sp.contract(Replace.get_create_type(), params.mintkart_address, entry_point = "replace_item").open_some()
        sp.transfer(sp.record(  tokenId = params.tokenId,
                                oldItemId = params.oldItemId, 
                                newItemId = params.newItemId), 
                            sp.mutez(0), 
                            mintkart)

    """ [tokenId, owner, mintkart_address] """
    @sp.entry_point
    def init_burn(self, params):
        sp.set_type_expr(params, Burn.get_params_type())

        sp.verify(self.token_id_set.contains(self.data.all_tokens, params.tokenId), message = FA2ErrorMessage.TOKEN_UNDEFINED)

        mintkart = sp.contract(Burn.get_create_params_type(), params.mintkart_address, entry_point = "burn").open_some()
        sp.transfer(sp.record(tokenId = params.tokenId), 
                            sp.mutez(0), 
                            mintkart)

        user = self.ledger_key.make(sp.sender, params.tokenId)
        allowances_key = Allowances.make_key(sp.sender, params.mintkart_address, params.tokenId)

        self.data.all_tokens.remove(params.tokenId)
        del self.data.ledger[user]
        del self.data.token_metadata[params.tokenId]
        del self.data.allowances[allowances_key]
        if self.config.store_total_supply:
            del self.data.total_supply[params.tokenId]

    """ [seller] """
    @sp.entry_point
    def add_seller(self, params):
        sp.set_type_expr(params, Sellers.get_add_params_type())
        sp.verify(self.data.administrator == sp.sender, message = FA2ErrorMessage.NOT_ADMIN)
        self.data.sellers.add(params.seller)

    """ [seller] """
    @sp.entry_point
    def remove_seller(self,params):
        sp.set_type_expr(params, Sellers.get_remove_params_type())
        sp.verify(self.data.administrator == sp.sender, message = FA2ErrorMessage.NOT_ADMIN)
        sp.verify(params.seller != self.data.administrator, message = FA2ErrorMessage.NOT_ALLOWED)    
        self.data.sellers.remove(params.seller)

    """ [customer_service] """
    @sp.entry_point
    def add_customer_service(self, params):
        sp.set_type_expr(params, CustomerService.get_add_params_type())
        sp.verify(self.data.administrator == sp.sender, message = FA2ErrorMessage.NOT_ADMIN)
        self.data.customer_service.add(params.customer_service)

    """ [customer_service] """
    @sp.entry_point
    def remove_customer_service(self,params):
        sp.set_type_expr(params, CustomerService.get_remove_params_type())
        sp.verify(self.data.administrator == sp.sender, message = FA2ErrorMessage.NOT_ADMIN)
        sp.verify(params.seller != self.data.administrator, message = FA2ErrorMessage.NOT_ALLOWED)    
        self.data.customer_service.add(params.customer_service)

    """ [address] """
    @sp.onchain_view(name = "is_seller")
    def is_seller(self, address):
        sp.result((self.data.sellers).contains(address))

################### FA2 End ###################

################### Market Place ###################

class Mintkart(sp.Contract):
    def __init__(self, admin, fa2_contract_address, metadata):
        self.init(
            admin = admin,
            fa2_contract_address = fa2_contract_address,
            metadata = metadata,
            warrenties = sp.big_map(
                l = {},
                tkey = sp.TNat,
                tvalue = sp.TRecord(warrenty = sp.TInt, claimedOn = sp.TTimestamp, burntOn = sp.TTimestamp)),
            replacements = sp.big_map(
                l = {},
                tkey = sp.TNat,
                tvalue = sp.TList(sp.TRecord(fromItem = sp.TString, toItem = sp.TString, replacementTime = sp.TTimestamp))),
            twins = sp.big_map(
                l = {},
                tkey = sp.TString, 
                tvalue = Twin.get_type()))

    """ [itemId, tokenId, seller, warrenty] """
    @sp.entry_point
    def create_twin(self, params):
        sp.verify(sp.sender == self.data.fa2_contract_address, message = MarketPlaceErrorMessage.NOT_ADMIN)
        sp.verify(~ self.data.twins.contains(params.itemId), message = MarketPlaceErrorMessage.DUPLICATE_TWIN)
        self.data.twins[params.itemId] = sp.record(
            tokenId = params.tokenId,
            seller = params.seller,
            createdOn = sp.now)
        self.data.warrenties[params.tokenId] = sp.record(warrenty = params.warrenty, claimedOn = sp.timestamp(0), burntOn = sp.timestamp(0))

    """ [itemId, buyer] """
    @sp.entry_point
    def buy(self, params):
        sp.set_type_expr(params, Buy.get_type())
        sp.verify(self.data.admin == sp.sender, message = MarketPlaceErrorMessage.NOT_SELLER)
        sp.verify(self.data.twins.contains(params.itemId), message = MarketPlaceErrorMessage.TWINNING_DOESNOT_EXIST)
        twin = self.data.twins[params.itemId]
        fa2_contract = sp.contract(Transfer.get_params_type(), self.data.fa2_contract_address, entry_point = "single_transfer").open_some()
        sp.transfer(sp.record(from_ = twin.seller, 
                                tokenId = twin.tokenId,
                                to_ = params.buyer), 
                            sp.mutez(0), 
                            fa2_contract)

        self.data.warrenties[twin.tokenId].claimedOn = sp.now

    """ [tokenId, oldItemId, newItemId] """
    @sp.entry_point
    def replace_item(self, params):
        sp.verify(sp.sender == self.data.fa2_contract_address, message = MarketPlaceErrorMessage.NOT_ADMIN)
        sp.verify(self.data.warrenties.contains(params.tokenId), message = MarketPlaceErrorMessage.TWINNING_DOESNOT_EXIST)

        warrenty_details = self.data.warrenties[params.tokenId]
        sp.verify(sp.now - warrenty_details.claimedOn <= warrenty_details.warrenty, message = MarketPlaceErrorMessage.WARRENTY_EXPIRED)

        sp.if self.data.replacements.contains(params.tokenId):
            self.data.replacements[params.tokenId].push(sp.record(fromItem = params.oldItemId, toItem = params.newItemId, replacementTime = sp.now))
        sp.else:
            self.data.replacements[params.tokenId] = [sp.record(fromItem = params.oldItemId, toItem = params.newItemId, replacementTime = sp.now)]

    """ [tokenId] """
    @sp.entry_point
    def burn(self, params):
        sp.verify(sp.sender == self.data.fa2_contract_address, message = MarketPlaceErrorMessage.NOT_ADMIN)
        sp.verify(self.data.warrenties.contains(params.tokenId), message = MarketPlaceErrorMessage.TWINNING_DOESNOT_EXIST)
        warrenty_details = self.data.warrenties[params.tokenId]
        sp.verify(sp.now - warrenty_details.claimedOn > warrenty_details.warrenty, message = MarketPlaceErrorMessage.WARRENTY_NOT_EXPIRED)

        self.data.warrenties[params.tokenId].burntOn = sp.now

    """ [address] """
    @sp.private_lambda(with_operations=True, with_storage="read-only", wrap_call=True)
    def is_seller(self, address):
        sp.result(sp.view("is_seller", self.data.fa2_contract_address, address, t = sp.TBool).open_some("Invalid is_seller view"))

    """ [address] """
    @sp.entry_point
    def set_fa2_contract_addr(self, params):
        sp.set_type(params, sp.TRecord(address = sp.TAddress))
        sp.verify(self.is_seller(sp.sender), message = MarketPlaceErrorMessage.NOT_SELLER)
        self.data.fa2_contract_address = params.address

    """ [itemId] """
    @sp.entry_point
    def remove_twin(self, params):
        sp.set_type(params, sp.TRecord(itemId = sp.TString))
        sp.verify(self.data.twins.contains(params.itemId), message = MarketPlaceErrorMessage.TWINNING_DOESNOT_EXIST)
        twin = self.data.twins[params.itemId]
        sp.verify(twin.seller == sp.sender, message = MarketPlaceErrorMessage.NOT_SELLER)
        del self.data.twins[params.itemId]


################### Market Place End ###################


################### Tests ###################

@sp.add_test(name = "Mintkart-Test")
def test():

    admin = sp.test_account("admin")
    seller1 = sp.test_account("seller1")
    seller2 = sp.test_account("seller2")
    customer_service1 = sp.test_account("customer_service1")
    customer_service2 = sp.test_account("customer_service2")
    customer1 = sp.test_account("customer1")
    customer2 = sp.test_account("customer2")

    sc = sp.test_scenario()
    sc.h1("Mintkart")
    sc.table_of_contents()

    sc.h2("Accounts")
    sc.show([admin,seller1,seller2,customer_service1,customer_service2,customer1,customer2])

    sc.h2("MintkartFA2")
    fa2 = MintkartFA2(
        FA2.FA2_config(non_fungible=True, assume_consecutive_token_ids=False, store_total_supply=False),
        admin=admin.address,
        metadata = sp.utils.metadata_of_url("https://example.com"))
    sc += fa2

    sc.h2("Mintkart")
    mp = Mintkart(
        admin = admin.address,
        fa2_contract_address = fa2.address, 
        metadata = sp.utils.metadata_of_url("ipfs://QmcxDJ66gGNKRy6setAbVuoidCPgFTZm3iTtNnajHVUu4p"))
    sc += mp

    def newItem(tokenId, itemId, warrenty, mintkart_address):
        return sp.record(
            tokenId = tokenId,
            itemId = itemId,
            warrenty = warrenty,
            mintkart_address = mintkart_address,
            metadata = {
                "name" : sp.utils.bytes_of_string("Bahubali NFT #3"),
                "symbol" : sp.utils.bytes_of_string("SUPERSTAR"),
                "decimals" : sp.utils.bytes_of_string("0"),
                "artifactUri" : sp.utils.bytes_of_string("ipfs://QmdByT2kNwSLdYfASoWEXyZhRYgLtvBnzJYBM1zvZXhCnS"),
                "displayUri" : sp.utils.bytes_of_string("ipfs://QmdByT2kNwSLdYfASoWEXyZhRYgLtvBnzJYBM1zvZXhCnS"),
                "thumbnailUri" : sp.utils.bytes_of_string("ipfs://QmXJSgZeKS9aZrHkp81hRtZpWWGCkkBma9d6eeUPfJsLEV"),
                "metadata" : sp.utils.bytes_of_string("ipfs://QmYP9i9axHywpMEaAcCopZz3DvAXvR7Bg7srNvrRbNUBTh")
            }
        )
    
    sc.p("Customer Service 1 registers as service person. Admins verifies him and adds him as a authenticated customer service.")
    params = sp.record(customer_service = customer_service1.address)
    sc += fa2.add_customer_service(params).run(sender = admin)

    sc.p("Customer Service 2 registers as service person. But admin doesn't verify.")
    params = sp.record(customer_service = customer_service2.address)
    sc += fa2.add_customer_service(params).run(sender = admin)

    sc.p("Customer Service 2 registers as service person. And admin verifies.")
    params = sp.record(customer_service = customer_service2.address)
    sc += fa2.add_customer_service(params).run(sender = admin)


    sc.p("Seller 1 registers in mintfolio. Admins verifies him and adds him as a authenticated seller.")
    params = sp.record(seller = seller1.address)
    sc += fa2.add_seller(params).run(sender = admin)

    sc.p("Seller 2 registers in the same way. But admin doesn't verify.")
    params = sp.record(seller = seller2.address)
    sc += fa2.add_seller(params).run(sender = seller1, valid = False)

    sc.p("Seller 2 registers in the same way. And admin verifies.")
    params = sp.record(seller = seller2.address)
    sc += fa2.add_seller(params).run(sender = admin)


    sc.p("Seller 1 adds a new item for sale.")
    params = newItem(1, sp.string("item-id-1"), 5000, mp.address)
    sc += fa2.mint(params).run(sender = seller1)

    sc.p("Seller 2 adds a new item for sale.")
    params = newItem(2, sp.string("item-id-2"), 3000, mp.address)
    sc += fa2.mint(params).run(sender = seller2)


    sc.p("Customer 1 buys item 1. But not verified by admin.")
    params = sp.record(itemId = 'item-id-1', buyer = customer1.address)
    sc += mp.buy(params).run(sender = seller1, valid = False)

    sc.p("Customer 1 buys item 1. And is verified by admin.")
    params = sp.record(itemId = 'item-id-1', buyer = customer1.address)
    sc += mp.buy(params).run(sender = admin)
    

    sc.p("Customer 1 applies for replacement of item 1. But verified by some random seller.")
    params = sp.record(tokenId = 1, oldItemId = 'item-id-1', newItemId = 'item-id-1-new', mintkart_address = mp.address)
    sc += fa2.init_replace_item(params).run(sender = seller2, valid = False)

    sc.p("Customer 1 applies for replacement of item 1. And is verified by some customer_service.")
    params = sp.record(tokenId = 1, oldItemId = 'item-id-1', newItemId = 'item-id-1-new', mintkart_address = mp.address)
    sc += fa2.init_replace_item(params).run(sender = customer_service1)


    sc.p("Some random address tries to burn the NFT if the warrenty is expired.")
    params = sp.record(tokenId = 1, owner = customer1.address, mintkart_address = mp.address)
    sc += fa2.init_burn(params).run(sender = admin, valid = False)

################### Tests End ###################

################### Compilation ###################

sp.add_compilation_target(
    "FA2-Mintkart", 
    MintkartFA2(
        admin=sp.address("tz1TpvrMd352n7LZgb3TAd1kE4XZvTLS5EvR"), 
        config = FA2.FA2_config(non_fungible=True, assume_consecutive_token_ids=False, store_total_supply=False),
        metadata=sp.utils.metadata_of_url("ipfs://Qmdy7yYJfunXFiNqVh4zqxxaot1vxQsUiZkBpvekEd8ksW")
    )
)

sp.add_compilation_target(
    "Mintkart",
    Mintkart(
        admin=sp.address("tz1TpvrMd352n7LZgb3TAd1kE4XZvTLS5EvR"),
        fa2_contract_address = sp.address("KT1WWiutcYhtHzPHWs2d91G8PuB561ZaWg6s"),
        metadata=sp.utils.metadata_of_url("ipfs://QmcEzRJ6Z1fwV9SxnbmWVGrmTdhSzfykcLQbDRe95Gx1yh")
    )
)

################### Compilation End ###################
