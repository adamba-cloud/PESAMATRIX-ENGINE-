def execute_trade(symbol, side, entry, sl, tp):
    return {
        "status": "success",
        "symbol": symbol,
        "side": side,
        "entry": entry,
        "sl": sl,
        "tp": tp
    }
