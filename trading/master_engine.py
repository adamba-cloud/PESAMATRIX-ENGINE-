from database import log_trade

def execute_trade(symbol, side, entry, sl, tp):
    # 1. validate signal
    # 2. apply strategy rules
    # 3. execute trade (or simulate)
    
    result = {
        "symbol": symbol,
        "side": side,
        "entry": entry,
        "status": "executed"
    }

    log_trade(symbol, side, entry, sl, tp, "executed")

    return result
