def is_target_tx(parsed_tx, target_address):
    """
    判断是否为目标地址的入账交易
    """
    if not parsed_tx:
        return False
        
    return parsed_tx.get('to') == target_address
