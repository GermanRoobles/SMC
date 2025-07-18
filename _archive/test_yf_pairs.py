import yfinance as yf

# Lista de pares en formato USDT y yfinance
pairs = [
    "BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "EUR/USD", "GBP/USD", "XAU/USD", "SP500",
    "FARTCOIN/USDT", "BNB/USDT", "ADA/USDT", "DOGE/USDT", "SUI/USDT", "HBAR/USDT"
]

def to_yf_symbol(pair):
    if pair.endswith("/USDT"):
        return pair.replace("/USDT", "-USD")
    if pair == "SP500":
        return "^GSPC"
    if pair == "XAU/USD":
        return "GC=F"
    if pair == "EUR/USD":
        return "EURUSD=X"
    if pair == "GBP/USD":
        return "GBPUSD=X"
    return pair

results = {}
for pair in pairs:
    yf_symbol = to_yf_symbol(pair)
    try:
        data = yf.download(yf_symbol, period="1d", interval="15m")
        valid = not data.empty
    except Exception as e:
        valid = False
    results[pair] = valid

for pair, valid in results.items():
    print(f"{pair}: {'✅' if valid else '❌'}")
