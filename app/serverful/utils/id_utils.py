from uuid import uuid4

def new_product_id():
    return "prd-"+uuid4()

def new_user_id():
    return "usr-"+uuid4()

def new_transaction_id():
    return "txn-"+uuid4()

def new_order_id():
    return "ord-"+uuid4()

def new_event_id():
    return "evt-"+uuid4()

def new_message_id():
    return "msg-"+uuid4()