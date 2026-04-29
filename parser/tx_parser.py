from utils.logger import logger
from tronpy.keys import to_base58check_address

def parse_transaction(tx):
    """
    解析交易数据
    返回格式: { "tx_id": str, "from": str, "to": str, "amount": float }
    如果解析失败或不是转账交易，返回 None
    """
    try:
        tx_id = tx.get('txID')
        raw_data = tx.get('raw_data', {})
        contract = raw_data.get('contract', [])
        
        if not contract:
            return None
            
        # 获取第一个合约内容
        contract_data = contract[0]
        contract_type = contract_data.get('type')
        
        # 只处理 TRX 普通转账 (TransferContract)
        if contract_type == 'TransferContract':
            parameter = contract_data.get('parameter', {}).get('value', {})
            owner_address = parameter.get('owner_address')
            to_address = parameter.get('to_address')
            amount_sun = parameter.get('amount', 0)
            
            # 转换为 Base58 地址以便于比较和记录
            from_addr = to_base58check_address(owner_address) if owner_address else "Unknown"
            to_addr = to_base58check_address(to_address) if to_address else "Unknown"
            
            return {
                "tx_id": tx_id,
                "from": from_addr,
                "to": to_addr,
                "amount": amount_sun / 1_000_000.0  # 转为 TRX
            }
            
        return None
    except Exception as e:
        logger.error(f"解析交易出错: {e}")
        return None
