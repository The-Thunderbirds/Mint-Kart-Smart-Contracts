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
    WARRANTY_EXPIRED = "{}WARRANTY_EXPIRED".format(PREFIX)
    TWINNING_ALREADY_EXIST = "{}TWINNING_ALREADY_EXIST".format(PREFIX)
    ALREADY_REPLACED_ONCE = "{}ALREADY_REPLACED_ONCE".format(PREFIX)
    WARRANTY_NOT_EXPIRED = "{}WARRANTY_NOT_EXPIRED".format(PREFIX)

################### Error Messages End ###################