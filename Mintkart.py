import smartpy as sp
FA2 = sp.io.import_script_from_url("https://smartpy.io/templates/FA2.py")

################### Market Place ###################

class Mintkart(sp.Contract):
    def __init__(self, admin, fa2_contract_address, metadata):
        self.init(
            admin = admin,
            fa2_contract_address = fa2_contract_address,
            metadata = metadata,
            warranties = sp.big_map(
                l = {},
                tkey = sp.TNat,
                tvalue = sp.TRecord(warranty = sp.TInt, type = sp.TNat, claimedOn = sp.TTimestamp, burntOn = sp.TTimestamp)),
            replacements = sp.big_map(
                l = {},
                tkey = sp.TNat,
                tvalue = sp.TList(sp.TRecord(fromItem = sp.TString, toItem = sp.TString, replacementTime = sp.TTimestamp))),
            twins = sp.big_map(
                l = {},
                tkey = sp.TString, 
                tvalue = Twin.get_type()),
            rewards = sp.big_map(
                l = {},
                tkey = sp.TAddress,
                tvalue = sp.TRecord(diamond = sp.TNat, gold = sp.TNat, silver = sp.TNat, bronze = sp.TNat)))

    """ [itemId, tokenId, seller, warranty] """
    @sp.entry_point
    def create_twin(self, params):
        sp.verify(sp.sender == self.data.fa2_contract_address, message = MarketPlaceErrorMessage.NOT_ADMIN)
        sp.verify(~ self.data.twins.contains(params.itemId), message = MarketPlaceErrorMessage.DUPLICATE_TWIN)
        self.data.twins[params.itemId] = sp.record(
            tokenId = params.tokenId,
            seller = params.seller,
            createdOn = sp.now)
        nft_type = (sp.utils.seconds_of_timestamp(sp.now) + sp.len(params.itemId) + params.tokenId) % 4
        self.data.warranties[params.tokenId] = sp.record(warranty = params.warranty, type = nft_type, claimedOn = sp.timestamp(0), burntOn = sp.timestamp(0))

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

        self.data.warranties[twin.tokenId].claimedOn = sp.now
        nft_type = self.data.warranties[twin.tokenId].type
        sp.if self.data.rewards.contains(params.buyer):
            sp.if nft_type == 0:
                self.data.rewards[params.buyer].diamond += 1
            sp.if nft_type == 1:
                self.data.rewards[params.buyer].gold += 1
            sp.if nft_type == 2:
                self.data.rewards[params.buyer].silver += 1
            sp.if nft_type == 3:
                self.data.rewards[params.buyer].bronze += 1
        sp.else:
            sp.if nft_type == 0:
                self.data.rewards[params.buyer] = sp.record(diamond = 1, gold = 0, silver = 0, bronze = 0)
            sp.if nft_type == 1:
                self.data.rewards[params.buyer] = sp.record(diamond = 0, gold = 1, silver = 0, bronze = 0)
            sp.if nft_type == 2:
                self.data.rewards[params.buyer] = sp.record(diamond = 0, gold = 0, silver = 1, bronze = 0)
            sp.if nft_type == 3:
                self.data.rewards[params.buyer] = sp.record(diamond = 0, gold = 0, silver = 0, bronze = 1)

    """ [tokenId, oldItemId, newItemId] """
    @sp.entry_point
    def replace_item(self, params):
        sp.verify(sp.sender == self.data.fa2_contract_address, message = MarketPlaceErrorMessage.NOT_ADMIN)
        sp.verify(self.data.warranties.contains(params.tokenId), message = MarketPlaceErrorMessage.TWINNING_DOESNOT_EXIST)

        warranty_details = self.data.warranties[params.tokenId]
        sp.verify(sp.now - warranty_details.claimedOn <= warranty_details.warranty, message = MarketPlaceErrorMessage.WARRANTY_EXPIRED)

        sp.if self.data.replacements.contains(params.tokenId):
            self.data.replacements[params.tokenId].push(sp.record(fromItem = params.oldItemId, toItem = params.newItemId, replacementTime = sp.now))
        sp.else:
            self.data.replacements[params.tokenId] = [sp.record(fromItem = params.oldItemId, toItem = params.newItemId, replacementTime = sp.now)]

    """ [tokenId] """
    @sp.entry_point
    def burn(self, params):
        sp.verify(sp.sender == self.data.fa2_contract_address, message = MarketPlaceErrorMessage.NOT_ADMIN)
        sp.verify(self.data.warranties.contains(params.tokenId), message = MarketPlaceErrorMessage.TWINNING_DOESNOT_EXIST)
        warranty_details = self.data.warranties[params.tokenId]
        sp.verify(sp.now - warranty_details.claimedOn > warranty_details.warranty, message = MarketPlaceErrorMessage.WARRANTY_NOT_EXPIRED)

        self.data.warranties[params.tokenId].burntOn = sp.now

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