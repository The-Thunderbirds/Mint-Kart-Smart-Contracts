import smartpy as sp
FA2 = sp.io.import_script_from_url("https://smartpy.io/templates/FA2.py")

################### FA2 ###################

class MintkartFA2(FA2.FA2):

    def __init__(self, config, metadata, admin):
        FA2.FA2.__init__(self, config, metadata, admin)
        self.update_initial_storage(
            sellers = sp.set([admin]),
            customer_service = sp.set([admin]),
            allowances = sp.big_map(l = {}, tkey = Allowances.get_key_type(), tvalue = Allowances.get_value_type()))

    """ [tokenId, metadata, itemId, warranty, mintkart_address] """
    @sp.entry_point
    def mint(self, params):
        sp.set_type_expr(params, Mint.get_batch_params_type())
        sp.verify((self.data.sellers).contains(sp.sender), message = FA2ErrorMessage.NOT_SELLER)
        
        sp.for _params in params:
            sp.verify(~ self.token_id_set.contains(self.data.all_tokens, _params.tokenId), message = FA2ErrorMessage.DUPLICATE_TOKEN_ID)
            
            self.token_id_set.add(self.data.all_tokens, _params.tokenId)
            
            user = self.ledger_key.make(sp.sender, _params.tokenId)
            self.data.ledger[user] = FA2.Ledger_value.make(1)

            self.data.token_metadata[_params.tokenId] = sp.record(
                token_id    = _params.tokenId,
                token_info  = _params.metadata
            )
            if self.config.store_total_supply:
                self.data.total_supply[_params.tokenId] = 1

            allowances_key = Allowances.make_key(sp.sender, _params.mintkart_address, _params.tokenId)
            self.data.allowances[allowances_key] = 1

            mintkart = sp.contract(Twin.get_create_params_type(), _params.mintkart_address, entry_point = "create_twin").open_some()
            sp.transfer(sp.record(
                            itemId = _params.itemId, 
                            tokenId = _params.tokenId,
                            seller = sp.sender,
                            warranty = _params.warranty),
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

    """ [tokenId, mintkart_address] """
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
        sp.send(params.seller, sp.tez(5), message = 'use this for gas payments')

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
        sp.send(params.customer_service, sp.tez(5), message = 'use this for gas payments')

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