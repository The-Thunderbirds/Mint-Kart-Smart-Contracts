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

    def newItem(tokenId, itemId, warranty, mintkart_address):
        return sp.record(
            tokenId = tokenId,
            itemId = itemId,
            warranty = warranty,
            mintkart_address = mintkart_address,
            metadata = {
                "name" : sp.utils.bytes_of_string("Item Name"),
                "symbol" : sp.utils.bytes_of_string("MINTKART"),
                "decimals" : sp.utils.bytes_of_string("0"),
                "artifactUri" : sp.utils.bytes_of_string("ipfs://QmdByT2kNwSLdYfASoWEXyZhRYgLtvBnzJYBM1zvZXhCnS"),
                "displayUri" : sp.utils.bytes_of_string("ipfs://QmdByT2kNwSLdYfASoWEXyZhRYgLtvBnzJYBM1zvZXhCnS"),
                "thumbnailUri" : sp.utils.bytes_of_string("ipfs://QmXJSgZeKS9aZrHkp81hRtZpWWGCkkBma9d6eeUPfJsLEV"),
                "metadata" : sp.utils.bytes_of_string("ipfs://QmYP9i9axHywpMEaAcCopZz3DvAXvR7Bg7srNvrRbNUBTh")
            }
        )
    
    sc.p("Customer Service 1 registers as service person. Admins verifies him and adds him as a authenticated customer service.")
    params = sp.record(customer_service = customer_service1.address)
    sc += fa2.add_customer_service(params).run(sender = admin, amount = sp.tez(5))

    sc.p("Customer Service 2 registers as service person. But admin doesn't verify.")
    params = sp.record(customer_service = customer_service2.address)
    sc += fa2.add_customer_service(params).run(sender = admin, amount = sp.tez(5))

    sc.p("Customer Service 2 registers as service person. And admin verifies.")
    params = sp.record(customer_service = customer_service2.address)
    sc += fa2.add_customer_service(params).run(sender = admin, amount = sp.tez(5))


    sc.p("Seller 1 registers in mintfolio. Admins verifies him and adds him as a authenticated seller.")
    params = sp.record(seller = seller1.address)
    sc += fa2.add_seller(params).run(sender = admin, amount = sp.tez(5))

    sc.p("Seller 2 registers in the same way. But admin doesn't verify.")
    params = sp.record(seller = seller2.address)
    sc += fa2.add_seller(params).run(sender = seller1, amount = sp.tez(5), valid = False)

    sc.p("Seller 2 registers in the same way. And admin verifies.")
    params = sp.record(seller = seller2.address)
    sc += fa2.add_seller(params).run(sender = admin, amount = sp.tez(5))


    sc.p("Seller 1 adds new items for sale.")
    params = [newItem(1, sp.string("item-id-1"), 5000, mp.address), newItem(2, sp.string("item-id-2"), 10000, mp.address)]
    sc += fa2.mint(params).run(sender = seller1)

    sc.p("Seller 2 adds a new item for sale.")
    params = [newItem(3, sp.string("item-id-3"), 15000, mp.address), newItem(4, sp.string("item-id-4"), 20000, mp.address)]
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


    sc.p("Some random address tries to burn the NFT if the warranty is expired.")
    params = sp.record(tokenId = 1, mintkart_address = mp.address)
    sc += fa2.init_burn(params).run(sender = admin, valid = False)

################### Tests End ###################