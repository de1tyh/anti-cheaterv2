from utils.logger import logger
from tronpy.keys import PrivateKey
import time

def handle_target_tx(client, private_key_hex, cold_wallet_address, parsed_tx):
    """
    拦截逻辑：检测到资金进入后，立刻将其转移到冷钱包
    """
    tx_id = parsed_tx.get('tx_id')
    amount = parsed_tx.get('amount')
    from_addr = parsed_tx.get('from')
    scam_address = parsed_tx.get('to')
    
    logger.info("=" * 50)
    logger.info(f"🔥 [检测到入账] 目标地址收到资金！")
    logger.info(f"💰 入账金额: {amount} TRX")
    logger.info(f"🆔 原始交易: {tx_id}")
    logger.info(f"📤 发送方: {from_addr}")
    logger.info("=" * 50)

    try:
        # 1. 准备私钥
        priv_key = PrivateKey(bytes.fromhex(private_key_hex))
        
        # 2. 获取当前账户余额 (准备归集)
        # 稍微等待一下，确保入账在链上已确认余额更新
        time.sleep(0.5)
        account_info = client.get_account(scam_address)
        balance_sun = account_info.get('balance', 0)
        
        if balance_sun <= 0:
            logger.warning(f"⚠️ 账户余额不足以归集 (当前余额: {balance_sun/1_000_000} TRX)")
            return

        # 3. 计算归集金额
        # TRX 转账大约消耗 0.3 TRX 左右的带宽费（如果没有带宽）
        # 为了确保成功，我们预留 1 TRX 作为手续费
        fee_buffer_sun = 1_000_000 
        transfer_amount_sun = balance_sun - fee_buffer_sun
        
        if transfer_amount_sun <= 0:
            logger.warning(f"⚠️ 余额扣除手续费后不足以归集")
            return

        logger.info(f"⚡ 正在尝试拦截归集: {transfer_amount_sun/1_000_000} TRX -> {cold_wallet_address}")

        # 4. 构建并发送转账交易
        txn = (
            client.trx.transfer(scam_address, cold_wallet_address, transfer_amount_sun)
            .build()
            .inspect()
            .sign(priv_key)
            .broadcast()
        )
        
        result_tx_id = txn.get('txid')
        logger.info(f"✅ [拦截成功] 资金已转移！归集交易ID: {result_tx_id}")
        logger.info("=" * 50)

    except Exception as e:
        logger.error(f"❌ [拦截失败] 执行转账时发生异常: {e}")
        logger.info("=" * 50)
