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
    
class MarketPlaceErrorMessage:
    PREFIX = "MARKETPLACE_"
    NOT_ADMIN = "{}NOT_ADMIN".format(PREFIX)
    NOT_SELLER = "{}NOT_SELLER".format(PREFIX)
    TOKEN_UNDEFINED = "{}TOKEN_UNDEFINED".format(PREFIX)
    DUPLICATE_TWIN = "{}SALE_EXISTS_WITH_GIVEN_TOKEN_ID".format(PREFIX)
    TWINNING_DOESNOT_EXIST = "{}TWINNING_DOESNOT_EXIST".format(PREFIX)
    INSUFFICIENT_BALANCE = "{}INSUFFICIENT_BALANCE".format(PREFIX)


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


class Buy:
    def get_type():
        return sp.TRecord(
            tokenId = sp.TNat,
            buyer = sp.TAddress)


class NFTMetadata:
    def get_type():
        return sp.TMap(sp.TString, sp.TBytes)

class Mint:
    def get_params_type():
        return sp.TRecord(
            tokenId = sp.TNat,
            metadata = NFTMetadata.get_type(),
            itemId = sp.TString,
            warrenty = sp.TNat,
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
            warrenty = sp.TNat,
            createdOn = sp.TTimestamp,
            claimedOn = sp.TTimestamp)
    def get_create_params_type():
        return sp.TRecord(
            itemId = sp.TString, 
            tokenId = sp.TNat,
            seller = sp.TAddress,
            warrenty = sp.TNat)

################### Helpers End ###################

################### FA2 ###################

class MintkartFA2(FA2.FA2):

    def __init__(self, config, metadata, admin):
        FA2.FA2.__init__(self, config, metadata, admin)
        self.update_initial_storage(
            sellers = sp.set([admin]),
            allowances = sp.big_map(l = {}, tkey = Allowances.get_key_type(), tvalue = Allowances.get_value_type()))

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

    """ [address] """
    @sp.onchain_view(name = "is_seller")
    def is_seller(self, address):
        sp.result((self.data.sellers).contains(address))

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


################### FA2 End ###################

################### Market Place ###################

class Mintkart(sp.Contract):
    def __init__(self, fa2_contract_address, metadata):
        self.init(
            fa2_contract_address = fa2_contract_address,
            metadata = metadata,
            twins = sp.big_map(
                l = {},
                tkey = sp.TString, 
                tvalue = Twin.get_type())
            )

    """ [address] """
    @sp.private_lambda(with_operations=True, with_storage="read-only", wrap_call=True)
    def is_seller(self, address):
        sp.result(sp.view("is_seller", self.data.fa2_contract_address, address, t = sp.TBool).open_some("Invalid is_seller view"))

    """ [address] """
    @sp.entry_point
    def set_fa2_contract_addr(self, params):
        sp.set_type(params, sp.TRecord(address = sp.TAddress))
        sp.verify(self.is_seller(sp.sender), message = MarketPlaceErrorMessage.NOT_ADMIN)
        self.data.fa2_contract_address = params.address

    """ [itemId, tokenId, seller, warrenty] """
    @sp.entry_point
    def create_twin(self, params):
        sp.verify(sp.sender == self.data.fa2_contract_address, message = MarketPlaceErrorMessage.NOT_ADMIN)
        sp.verify(~ self.data.twins.contains(params.itemId), message = MarketPlaceErrorMessage.DUPLICATE_TWIN)
        self.data.twins[params.itemId] = sp.record(
            tokenId = params.tokenId,
            seller = params.seller,
            warrenty = params.warrenty,
            createdOn = sp.now,
            claimedOn = sp.timestamp(0))

    """ [itemId, buyer] """
    @sp.entry_point
    def buy(self, params):
        sp.set_type_expr(params, Buy.get_type())
        sp.verify(self.is_seller(sp.sender), message = MarketPlaceErrorMessage.NOT_ADMIN)
        sp.verify(self.data.twins.contains(params.itemId), message = MarketPlaceErrorMessage.TWINNING_DOESNOT_EXIST)
        twin = self.data.twins[params.itemId]
        fa2_contract = sp.contract(Transfer.get_params_type(), self.data.fa2_contract_address, entry_point = "single_transfer").open_some()
        sp.transfer(sp.record(from_ = twin.seller, 
                                tokenId = twin.tokenId,
                                to_ = params.buyer), 
                            sp.mutez(0), 
                            fa2_contract)
        twin.claimedOn = sp.now
        self.data.twins[params.itemId] = twin
        
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
    admin1 = sp.test_account("admin1")
    admin2 = sp.test_account("admin2")
    user1 = sp.test_account("user1")
    user2 = sp.test_account("user2")

    sc = sp.test_scenario()
    sc.h1("Mintkart")
    sc.table_of_contents()

    sc.h2("Accounts")
    sc.show([admin,admin1,admin2,user1,user2])

    sc.h2("MintkartFA2")
    fa2 = MintkartFA2(
        FA2.FA2_config(non_fungible=True, assume_consecutive_token_ids=False, store_total_supply=False),
        admin=admin.address,
        metadata = sp.utils.metadata_of_url("https://example.com"))
    sc += fa2

    sc.h2("Mintkart")
    mp = Mintkart(
        fa2_contract_address = fa2.address, 
        metadata = sp.utils.metadata_of_url("ipfs://QmcxDJ66gGNKRy6setAbVuoidCPgFTZm3iTtNnajHVUu4p"))
    sc += mp

    def newNFT(toAddr, tokenId, hasMultipleQuantity, quantity):
        return sp.record(
            tzToAddress = toAddr,
            tokenId = tokenId,
            hasMultipleQuantity = hasMultipleQuantity,
            quantity = quantity,
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
    def newSale(tokenId, quantity, price):
        return sp.record(
            market_place_address = mp.address,
            tokenId = tokenId,
            quantity = quantity,
            price = price)
    
    # sc.p("admin adds admin1 and admin2 as admins")
    # params = sp.record(admins = sp.set([admin1.address, admin2.address]))
    # sc += fa2.add_admin(params).run(sender = admin)

    
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
        fa2_contract_address = sp.address("KT1WWiutcYhtHzPHWs2d91G8PuB561ZaWg6s"),
        metadata=sp.utils.metadata_of_url("ipfs://QmcEzRJ6Z1fwV9SxnbmWVGrmTdhSzfykcLQbDRe95Gx1yh")
    )
)

################### Compilation End ###################
