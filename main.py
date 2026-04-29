import time
from block.watcher import BlockWatcher
from parser.tx_parser import parse_transaction
from detector.detector import is_target_tx
from executor.executor import handle_target_tx
from state.state_manager import StateManager
from utils.logger import logger

# ==================== 核心配置 (必填) ====================
# 1. 诈骗钓鱼地址：需要监控的公开助记词骗局地址
SCAM_ADDRESS = ""

# 2. 该钓鱼地址私钥：由公开助记词本地离线导出
SCAM_PRIVATE_KEY = ""

# 3. 团队公益冷钱包地址：接收拦截资金的离线冷钱包
COLD_WALLET_ADDRESS = ""
# ========================================================

# 其他内部配置
RPC_NODES = [
    # "https://api.trongrid.io",
    "https://api.tronstack.io"
]
POLL_INTERVAL = 1  # 缩短轮询间隔，提高抢付速度
STATE_FILE_PATH = "data/state.json"

def main():
    logger.info("🚀 Tron 资金拦截系统启动...")
    logger.info(f"🔍 监控钓鱼地址: {SCAM_ADDRESS}")
    logger.info(f"🛡️ 资金归集地址: {COLD_WALLET_ADDRESS}")
    
    # 初始化组件
    watcher = BlockWatcher(RPC_NODES)
    state_manager = StateManager(STATE_FILE_PATH)
    
    # 获取上次处理的区块高度
    last_processed_block = state_manager.get_last_block()
    
    if last_processed_block == 0:
        last_processed_block = watcher.get_latest_block_number()
        state_manager.update_last_block(last_processed_block)
        logger.info(f"🆕 首次运行，从最新区块开始: {last_processed_block}")
    else:
        logger.info(f"🔄 从上次位置恢复: {last_processed_block}")

    loop_count = 0
    while True:
        try:
            # 1. 获取最新区块高度
            current_latest_block = watcher.get_latest_block_number()
            
            if current_latest_block > last_processed_block:
                loop_count = 0 # 重置心跳计数
                # 计算落后多少块
                behind_count = current_latest_block - last_processed_block
                if behind_count > 1:
                    logger.info(f"⏳ 正在追赶区块... 当前链高度: {current_latest_block}, 待处理: {behind_count} 块")

                # 抢付逻辑：尽可能快地处理新区块
                for block_num in range(last_processed_block + 1, current_latest_block + 1):
                    block_data = watcher.get_block(block_num)
                    transactions = block_data.get('transactions', [])
                    tx_count = len(transactions)
                    
                    # 增强日志输出
                    logger.info(f"📦 扫描区块 [{block_num} / {current_latest_block}] | 包含交易: {tx_count} 笔")
                    
                    if transactions:
                        for tx in transactions:
                            tx_id = tx.get('txID')
                            
                            if state_manager.is_tx_processed(tx_id):
                                continue
                            
                            parsed_tx = parse_transaction(tx)
                            
                            # 检测到目标地址入账
                            if is_target_tx(parsed_tx, SCAM_ADDRESS):
                                # 立即触发拦截转账逻辑
                                handle_target_tx(
                                    watcher.client, 
                                    SCAM_PRIVATE_KEY, 
                                    COLD_WALLET_ADDRESS,
                                    parsed_tx
                                )
                            
                            state_manager.add_processed_tx(tx_id)
                    
                    last_processed_block = block_num
                    state_manager.update_last_block(block_num)
                    
                # logger.info(f"✅ 已同步至: {last_processed_block}")
            else:
                # 实时心跳，让用户知道程序还在跑
                loop_count += 1
                if loop_count >= 10: # 每约10秒打印一次心跳
                    logger.info(f"🟢 系统运行中 | 最新区块: {last_processed_block} | 等待新区块...")
                    loop_count = 0
            
        except Exception as e:
            logger.error(f"主循环异常: {e}")
            
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("👋 程序由用户停止")
    except Exception as e:
        logger.critical(f"系统崩溃: {e}")
