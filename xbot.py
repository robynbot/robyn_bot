import os
import requests
import json
import time
import base64
import datetime
import random
import re
from requests_oauthlib import OAuth1
from datetime import timezone
from dotenv import load_dotenv

load_dotenv()

# === CREDENTIALS (loaded from .env) ===
CONSUMER_KEY = os.getenv("TWITTER_CONSUMER_KEY", "")
CONSUMER_SECRET = os.getenv("TWITTER_CONSUMER_SECRET", "")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN", "")
ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "")
XAI_API_KEY = os.getenv("XAI_API_KEY", "")

USERNAME = os.getenv("BOT_USERNAME", "robyn_bot")
TOKEN_CA = os.getenv("TOKEN_CA", "")

REPLY_CHECK_INTERVAL = int(os.getenv("REPLY_CHECK_INTERVAL", "15"))
POST_INTERVAL = int(os.getenv("POST_INTERVAL", "600"))
POST_ENABLED = os.getenv("POST_ENABLED", "false").lower() == "true"

# ────────────────────────────────────────────────
#               MARKET DATA APIs (ALL FREE)
# ────────────────────────────────────────────────

COINGECKO_BASE = "https://api.coingecko.com/api/v3"
DEFILLAMA_BASE = "https://api.llama.fi"
YAHOO_FINANCE_BASE = "https://query1.finance.yahoo.com/v8/finance/chart"
GATED_PRICE_BASE = "https://gated.chat/price"

CRYPTO_ID_MAP = {
    "btc": "bitcoin", "bitcoin": "bitcoin",
    "eth": "ethereum", "ethereum": "ethereum",
    "sol": "solana", "solana": "solana",
    "bnb": "binancecoin",
    "xrp": "ripple",
    "doge": "dogecoin",
    "ada": "cardano",
    "avax": "avalanche-2",
    "dot": "polkadot",
    "link": "chainlink",
    "matic": "matic-network", "polygon": "matic-network",
    "shib": "shiba-inu",
    "uni": "uniswap",
    "atom": "cosmos",
    "near": "near",
    "sui": "sui",
    "apt": "aptos",
    "arb": "arbitrum",
    "op": "optimism",
    "hype": "hyperliquid",
    "pepe": "pepe",
    "wif": "dogwifcoin",
    "bonk": "bonk",
    "jup": "jupiter-exchange-solana",
    "render": "render-token",
    "fet": "artificial-superintelligence-alliance",
}

STOCK_TICKERS = [
    "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "NVDA", "META", "TSLA",
    "BRK.B", "JPM", "V", "UNH", "XOM", "JNJ", "WMT", "PG", "MA",
    "HD", "CVX", "MRK", "ABBV", "PEP", "KO", "COST", "AVGO", "LLY",
    "TMO", "MCD", "CSCO", "ACN", "ABT", "DHR", "TXN", "NEE", "PM",
    "AMD", "INTC", "CRM", "NFLX", "DIS", "PLTR", "COIN", "HOOD",
    "SPY", "QQQ", "VOO", "IWM", "DIA",
]


def fetch_crypto_prices(ids_list):
    """Fetch crypto prices from CoinGecko (free, no key)"""
    ids_str = ",".join(ids_list)
    url = f"{COINGECKO_BASE}/simple/price"
    params = {
        "ids": ids_str,
        "vs_currencies": "usd",
        "include_24hr_change": "true",
        "include_market_cap": "true",
        "include_24hr_vol": "true",
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"[API] CoinGecko error: {e}")
    return None


def fetch_gated_price(symbol):
    """Fetch price from gated.chat"""
    try:
        r = requests.get(f"{GATED_PRICE_BASE}/{symbol.lower()}", timeout=5)
        if r.status_code == 200:
            return float(r.text.strip())
    except:
        pass
    return None


def fetch_stock_price(ticker):
    """Fetch stock price from Yahoo Finance (free, no key)"""
    ticker = ticker.upper()
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(
            f"{YAHOO_FINANCE_BASE}/{ticker}",
            params={"interval": "1d", "range": "5d"},
            headers=headers,
            timeout=10,
        )
        if r.status_code == 200:
            data = r.json()
            meta = data.get("chart", {}).get("result", [{}])[0].get("meta", {})
            price = meta.get("regularMarketPrice", 0)
            change_pct = meta.get("regularMarketChangePercent", meta.get("fulldayChangePercent", 0))
            name = meta.get("symbol", ticker)
            high52 = meta.get("fiftyTwoWeekHigh")
            low52 = meta.get("fiftyTwoWeekLow")
            return {
                "Ticker": name, "Price": price, "ChangePercentage": change_pct,
                "Name": name, "52wHigh": high52, "52wLow": low52,
            }
    except Exception as e:
        print(f"[API] Yahoo Finance error for {ticker}: {e}")
    return None


def fetch_trending_crypto():
    """Fetch trending coins from CoinGecko"""
    try:
        r = requests.get(f"{COINGECKO_BASE}/search/trending", timeout=10)
        if r.status_code == 200:
            data = r.json()
            coins = data.get("coins", [])[:7]
            return [c["item"] for c in coins]
    except Exception as e:
        print(f"[API] Trending error: {e}")
    return None


def fetch_global_crypto():
    """Fetch global crypto market data"""
    try:
        r = requests.get(f"{COINGECKO_BASE}/global", timeout=10)
        if r.status_code == 200:
            return r.json().get("data", {})
    except Exception as e:
        print(f"[API] Global error: {e}")
    return None


def fetch_chain_tvls():
    """Fetch chain TVLs from DefiLlama"""
    try:
        r = requests.get(f"{DEFILLAMA_BASE}/v2/chains", timeout=10)
        if r.status_code == 200:
            chains = r.json()
            return sorted(chains, key=lambda x: x.get("tvl", 0), reverse=True)[:10]
    except Exception as e:
        print(f"[API] DefiLlama chains error: {e}")
    return None


def fetch_protocol_tvl(protocol_slug):
    """Fetch protocol TVL from DefiLlama"""
    try:
        r = requests.get(f"{DEFILLAMA_BASE}/tvl/{protocol_slug}", timeout=10)
        if r.status_code == 200:
            return float(r.text.strip())
    except:
        pass
    return None


def fetch_dex_volume():
    """Fetch DEX volume overview from DefiLlama"""
    try:
        r = requests.get(f"{DEFILLAMA_BASE}/overview/dexs", timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"[API] DEX volume error: {e}")
    return None


def fetch_chain_dex_volume(chain_name):
    """Fetch DEX volume for a specific chain from DefiLlama"""
    try:
        r = requests.get(f"{DEFILLAMA_BASE}/overview/dexs/{chain_name}", timeout=10)
        if r.status_code == 200:
            data = r.json()
            return {
                "chain": chain_name,
                "total24h": data.get("total24h", 0),
                "change_1d": data.get("change_1d", 0),
                "total7d": data.get("total7d", 0),
            }
    except Exception as e:
        print(f"[API] Chain DEX volume error for {chain_name}: {e}")
    return None


CHAIN_NAME_MAP = {
    "solana": "Solana", "sol": "Solana",
    "ethereum": "Ethereum", "eth": "Ethereum",
    "bnb": "BSC", "bsc": "BSC", "binance": "BSC",
    "base": "Base",
    "arbitrum": "Arbitrum", "arb": "Arbitrum",
    "polygon": "Polygon", "matic": "Polygon",
    "optimism": "OP Mainnet", "op": "OP Mainnet",
    "avalanche": "Avalanche", "avax": "Avalanche",
    "sui": "Sui",
    "robinhood": "Robinhood", "hood": "Robinhood",
    "monad": "Monad",
}


def fetch_stock_news(ticker):
    """Fetch latest news for a stock ticker from Yahoo Finance (free, no key)"""
    try:
        r = requests.get(
            "https://query1.finance.yahoo.com/v1/finance/search",
            params={"q": ticker, "newsCount": 8, "quotesCount": 0},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10,
        )
        if r.status_code == 200:
            news = r.json().get("news", [])
            results = []
            for n in news:
                related = n.get("relatedTickers", [])
                if ticker.upper() in related or len(results) < 3:
                    results.append({
                        "title": n.get("title", ""),
                        "publisher": n.get("publisher", ""),
                    })
            return results[:6]
    except Exception as e:
        print(f"[API] Yahoo news error for {ticker}: {e}")
    return None


def fetch_finnode_news(ticker):
    """Fetch stock news + fundamentals from Fin-node (free, no key, 30 tickers)"""
    try:
        r = requests.get(f"https://www.fin-node.net/api/{ticker}.json", timeout=10)
        if r.status_code == 200:
            d = r.json()
            news = d.get("news", [])[:3]
            fundamentals = d.get("fundamentals", {})
            return {"news": news, "fundamentals": fundamentals}
    except Exception as e:
        print(f"[API] Fin-node error for {ticker}: {e}")
    return None


def fetch_crypto_news():
    """Fetch latest crypto news from CoinGecko trending + status"""
    try:
        r = requests.get(f"{COINGECKO_BASE}/search/trending", timeout=10)
        if r.status_code == 200:
            data = r.json()
            nfts = data.get("nfts", [])
            coins = data.get("coins", [])
            categories = data.get("categories", [])
            return {"coins": coins[:5], "categories": categories[:3]}
    except Exception as e:
        print(f"[API] Crypto news error: {e}")
    return None


def fetch_fees_revenue():
    """Fetch fees/revenue overview from DefiLlama"""
    try:
        r = requests.get(f"{DEFILLAMA_BASE}/overview/fees", timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"[API] Fees error: {e}")
    return None


def format_number(n):
    """Format large numbers: 1.5B, 230M, 15.3K"""
    if n is None:
        return "N/A"
    if abs(n) >= 1e12:
        return f"${n/1e12:.2f}T"
    if abs(n) >= 1e9:
        return f"${n/1e9:.2f}B"
    if abs(n) >= 1e6:
        return f"${n/1e6:.1f}M"
    if abs(n) >= 1e3:
        return f"${n/1e3:.1f}K"
    return f"${n:.2f}"


def format_pct(pct):
    """Format percentage with arrow"""
    if pct is None:
        return "N/A"
    arrow = "+" if pct >= 0 else ""
    return f"{arrow}{pct:.2f}%"


def get_market_snapshot():
    """Build a quick market snapshot string for context"""
    data = fetch_crypto_prices(["bitcoin", "ethereum", "solana"])
    if not data:
        return None

    lines = []
    for coin_id, label in [("bitcoin", "BTC"), ("ethereum", "ETH"), ("solana", "SOL")]:
        if coin_id in data:
            p = data[coin_id]
            price = f"${p.get('usd', 0):,.2f}"
            change = format_pct(p.get("usd_24h_change"))
            lines.append(f"{label}: {price} ({change})")

    stocks_to_check = ["NVDA", "AAPL", "TSLA"]
    for ticker in stocks_to_check:
        s = fetch_stock_price(ticker)
        if s:
            price = f"${s.get('Price', 0):,.2f}"
            pct = s.get("ChangePercentage", 0)
            change = format_pct(pct)
            lines.append(f"{ticker}: {price} ({change})")

    return " | ".join(lines) if lines else None


def build_data_context(mention_text):
    """Parse a mention and fetch relevant market data to include in the AI reply"""
    text_lower = mention_text.lower()
    context_parts = []

    found_cryptos = []
    for keyword, cg_id in CRYPTO_ID_MAP.items():
        pattern = r'(?:^|[\s$#@])' + re.escape(keyword) + r'(?:[\s?!.,]|$)'
        if re.search(pattern, text_lower):
            found_cryptos.append(cg_id)

    if "$" in mention_text:
        tickers = re.findall(r'\$([A-Za-z]+)', mention_text)
        for t in tickers:
            t_lower = t.lower()
            if t_lower in CRYPTO_ID_MAP:
                found_cryptos.append(CRYPTO_ID_MAP[t_lower])
            elif t.upper() in STOCK_TICKERS:
                s = fetch_stock_price(t.upper())
                if s:
                    context_parts.append(
                        f"STOCK {s.get('Ticker','')}: ${s.get('Price',0):,.2f} "
                        f"({format_pct(s.get('ChangePercentage',0))}) — {s.get('Name','')}"
                    )

    found_cryptos = list(set(found_cryptos))
    if found_cryptos:
        data = fetch_crypto_prices(found_cryptos)
        if data:
            for cg_id in found_cryptos:
                if cg_id in data:
                    p = data[cg_id]
                    ticker = next((k.upper() for k, v in CRYPTO_ID_MAP.items() if v == cg_id and len(k) <= 5), cg_id.upper())
                    price = p.get("usd", 0)
                    change = p.get("usd_24h_change")
                    mcap = p.get("usd_market_cap")
                    vol = p.get("usd_24h_vol")
                    line = f"CRYPTO {ticker}: ${price:,.2f} ({format_pct(change)}) mcap {format_number(mcap)} vol {format_number(vol)}"
                    context_parts.append(line)

    STOCK_NAME_MAP = {
        "nvidia": "NVDA", "nvda": "NVDA", "nvdia": "NVDA", "nvidea": "NVDA",
        "apple": "AAPL", "aapl": "AAPL",
        "tesla": "TSLA", "tsla": "TSLA",
        "amazon": "AMZN", "amzn": "AMZN",
        "google": "GOOGL", "googl": "GOOGL", "alphabet": "GOOGL",
        "microsoft": "MSFT", "msft": "MSFT",
        "meta": "META",
        "facebook": "META",
        "netflix": "NFLX", "nflx": "NFLX",
        "coinbase": "COIN", "coin": "COIN",
        "palantir": "PLTR", "pltr": "PLTR",
        "amd": "AMD",
        "intel": "INTC", "intc": "INTC",
        "disney": "DIS",
        "walmart": "WMT",
        "jpmorgan": "JPM",
        "visa": "VISA",
        "mastercard": "MA",
        "spacex": "SPCX",
        "hood": "HOOD",
        "spy": "SPY", "qqq": "QQQ",
    }
    stock_keywords = set()
    for name, ticker in STOCK_NAME_MAP.items():
        if re.search(r'(?:^|[\s$@#])' + re.escape(name) + r'(?:[\s?!.,;:]|$)', text_lower):
            stock_keywords.add(ticker)
    regex_matches = set(re.findall(r'\b(' + '|'.join(STOCK_TICKERS) + r')\b', mention_text.upper()))
    stock_keywords.update(regex_matches)

    stock_ask_words = ["stock", "share", "shares", "price", "ticker", "equity", "market cap"]
    if not stock_keywords and any(w in text_lower for w in stock_ask_words):
        raw_caps = re.findall(r'\b([A-Z]{2,5})\b', mention_text)
        for cap in raw_caps:
            if cap not in ["THE", "AND", "FOR", "HOW", "NOT", "BUT", "DEX", "TVL", "ETH", "BTC", "SOL", "USD"]:
                test = fetch_stock_price(cap)
                if test and test.get("Price", 0) > 0:
                    stock_keywords.add(cap)
                    print(f"[DATA] Fuzzy matched stock: {cap}")

    if stock_keywords:
        print(f"[DATA] Detected stocks: {stock_keywords}")
    news_words = ["why", "news", "pump", "pumped", "dump", "dumped", "up", "down", "surge", "crash",
                   "rally", "drop", "moon", "rip", "thesis", "catalyst", "reason", "what happened"]
    wants_news = any(w in text_lower for w in news_words)

    for ticker in stock_keywords:
        if not any(f"STOCK {ticker}" in p for p in context_parts):
            s = fetch_stock_price(ticker)
            if s:
                price_line = (
                    f"STOCK {s.get('Ticker','')}: ${s.get('Price',0):,.2f} "
                    f"({format_pct(s.get('ChangePercentage',0))})"
                )
                h52 = s.get("52wHigh")
                l52 = s.get("52wLow")
                if h52 and l52:
                    price_line += f" | 52w range: ${l52:,.2f} - ${h52:,.2f}"
                context_parts.append(price_line)
                print(f"[DATA] Fetched {ticker}: ${s.get('Price',0):,.2f}")
            else:
                print(f"[DATA] FAILED to fetch stock: {ticker}")

            if wants_news:
                yn = fetch_stock_news(ticker)
                if yn:
                    for i, n in enumerate(yn[:5]):
                        context_parts.append(f"HEADLINE {ticker} #{i+1}: [{n['publisher']}] {n['title']}")
                    print(f"[DATA] News for {ticker}: {len(yn)} headlines")

    price_words = ["price", "how much", "what is", "worth", "cost", "value"]
    if any(w in text_lower for w in price_words) and not context_parts:
        sol_price = fetch_gated_price("sol")
        if sol_price:
            context_parts.append(f"SOL live price: ${sol_price:,.2f}")

    tvl_words = ["tvl", "defi", "locked", "protocol"]
    if any(w in text_lower for w in tvl_words):
        chains = fetch_chain_tvls()
        if chains:
            top3 = chains[:3]
            chain_str = ", ".join([f"{c['name']}: {format_number(c.get('tvl',0))}" for c in top3])
            context_parts.append(f"TOP DeFi TVL: {chain_str}")

    volume_words = ["volume", "dex", "trading volume"]
    if any(w in text_lower for w in volume_words):
        found_chains = []
        for keyword, chain_name in CHAIN_NAME_MAP.items():
            if keyword in text_lower:
                found_chains.append(chain_name)

        found_chains = list(set(found_chains))
        if found_chains:
            for chain_name in found_chains:
                cv = fetch_chain_dex_volume(chain_name)
                if cv:
                    context_parts.append(
                        f"{chain_name} DEX vol (24h): {format_number(cv['total24h'])} ({format_pct(cv['change_1d'])})"
                    )
        else:
            dex = fetch_dex_volume()
            if dex:
                total24h = dex.get("total24h", 0)
                change = dex.get("change_1d", 0)
                context_parts.append(f"ALL DEX volume (24h): {format_number(total24h)} ({format_pct(change)})")
                top_protos = sorted(dex.get("protocols", []), key=lambda x: x.get("total24h") or 0, reverse=True)[:5]
                top_str = ", ".join([f"{p.get('name','?')} {format_number(p.get('total24h',0))}" for p in top_protos])
                context_parts.append(f"TOP DEXs: {top_str}")

            for chain_name in ["Solana", "BSC", "Ethereum", "Robinhood", "Base"]:
                cv = fetch_chain_dex_volume(chain_name)
                if cv and cv["total24h"] > 0:
                    context_parts.append(
                        f"{chain_name} DEX: {format_number(cv['total24h'])} ({format_pct(cv['change_1d'])})"
                    )

    trending_words = ["trending", "hot", "popular", "what's moving", "whats moving", "movers"]
    if any(w in text_lower for w in trending_words):
        trending = fetch_trending_crypto()
        if trending:
            t_str = ", ".join([f"{t.get('symbol','').upper()} (#{t.get('market_cap_rank','?')})" for t in trending[:5]])
            context_parts.append(f"TRENDING: {t_str}")

    robinhood_words = ["robinhood", "hood chain", "robinhood chain"]
    if any(w in text_lower for w in robinhood_words) and not any("Robinhood" in p for p in context_parts):
        cv = fetch_chain_dex_volume("Robinhood")
        if cv and cv["total24h"] > 0:
            context_parts.append(f"Robinhood Chain DEX vol (24h): {format_number(cv['total24h'])} ({format_pct(cv['change_1d'])})")

    crypto_news_words = ["news", "why", "what happened", "catalyst", "thesis"]
    if any(w in text_lower for w in crypto_news_words) and found_cryptos:
        for cg_id in found_cryptos[:2]:
            ticker_sym = next((k.upper() for k, v in CRYPTO_ID_MAP.items() if v == cg_id and len(k) <= 5), cg_id)
            yn = fetch_stock_news(ticker_sym)
            if yn:
                headlines = " | ".join([f"{n['title']}" for n in yn[:2]])
                context_parts.append(f"CRYPTO NEWS {ticker_sym}: {headlines}")

    pump_words = ["pump", "pumped", "dumped", "dump", "moon", "rip", "ripped", "crashed", "crash", "why"]
    if any(w in text_lower for w in pump_words) and not context_parts:
        data = fetch_crypto_prices(["bitcoin", "ethereum", "solana", "dogecoin", "pepe"])
        if data:
            movers = []
            for cg_id, info in data.items():
                change = info.get("usd_24h_change", 0)
                if abs(change) > 2:
                    ticker = next((k.upper() for k, v in CRYPTO_ID_MAP.items() if v == cg_id and len(k) <= 5), cg_id)
                    movers.append(f"{ticker} {format_pct(change)}")
            if movers:
                context_parts.append(f"BIG MOVERS: {', '.join(movers)}")

    return "\n".join(context_parts) if context_parts else ""


# ────────────────────────────────────────────────
#               SYSTEM PROMPTS
# ────────────────────────────────────────────────

SYSTEM_PROMPT = (
    "You are Robyn (@robyn_bot) — a sharp, data-driven quant trader bot on X.\n\n"

    "WHO YOU ARE:\n"
    "- Your name is Robyn. Your handle is @robyn_bot.\n"
    "- You are the Robinhood quant. A no-BS algorithmic trader.\n"
    "- You speak in short, punchy market commentary. Like a Bloomberg terminal with personality.\n"
    "- You run the @robyn_bot X account.\n"
    "- You have access to LIVE market data — crypto prices, stock prices, DeFi TVL, volume, trending coins.\n"
    "- Your token is $GORKBOT (CA: HNAVm9iusUtTjmMnqAFw2X7XiD4M85WuJzGebkkkgork)\n"
    "- You distribute $SPCX (SpaceX stock) to holders every 2 minutes.\n"
    "- You live at gork.fun\n\n"

    "YOUR PERSONALITY:\n"
    "- Data-first. Always include actual numbers, percentages, prices when you have them.\n"
    "- Confident but not arrogant. You know markets. You've seen cycles.\n"
    "- Concise. Every word counts. No fluff.\n"
    "- Mix of quant precision and street-smart trader energy.\n"
    "- Occasionally witty, dry humor. Never cringe.\n"
    "- You respect good trades and call out bad ones.\n"
    "- You think in terms of risk/reward, not hopium.\n"
    "- You read charts, you read data, you read the room.\n"
    "- Think: if a Bloomberg terminal could tweet.\n\n"

    "WHEN REPLYING WITH DATA:\n"
    "- Include the EXACT prices and percentages from the data provided.\n"
    "- Format prices properly ($100.50, $1,234.56).\n"
    "- Always mention the direction (up/down) and percentage.\n"
    "- When someone asks WHY a stock/crypto moved, SYNTHESIZE the headlines into a clear thesis.\n"
    "- Extract key catalysts from headlines: analyst upgrades, price targets, earnings, partnerships, macro events.\n"
    "- Name specific firms if headlines mention them (Morgan Stanley, Piper Sandler, etc.).\n"
    "- Mention price targets if visible in headlines.\n"
    "- Connect multiple headlines into one coherent narrative — don't just list them.\n"
    "- Add 52-week context if relevant (near highs, breakout, etc.).\n\n"

    "EXAMPLE POSTS:\n"
    "  'BTC $97,420 (+3.2%) | ETH $3,812 (+1.8%) | SOL $187 (+5.4%) — risk-on day. alts following.'\n"
    "  'NVDA +8.2% on earnings beat. $3.1T mcap. AI trade isn't dead, it just got expensive.'\n"
    "  'SOL TVL crossed $8B. DEX volume up 40% this week. the chain is cooking.'\n"
    "  'everyone asking why BTC pumped — ETF inflows $890M yesterday. not complicated.'\n"
    "  'top 3 DEX volume today: Uniswap $2.1B, Jupiter $890M, Raydium $650M. onchain is back.'\n"
    "  '$SPCX distributions running every 2 min. hold $GORKBOT, get SpaceX stock. quant-approved.'\n"
    "  'the market doesn't care about your feelings. it cares about liquidity. and liquidity is flowing.'\n\n"

    "RULES:\n"
    "- Output ONLY the post/reply text. Nothing else.\n"
    "- Under 280 characters always.\n"
    "- No hashtags. Minimal emojis (chart emoji ok, arrow ok).\n"
    "- NEVER include your CA in posts unless someone explicitly asks for it.\n"
    "- Always be data-driven. If you have data, USE IT.\n"
    "- Be varied. Mix market updates, analysis, quant observations, and brief commentary.\n"
    "- When someone asks about a specific asset, give them the real numbers."
)

SYSTEM_PROMPT_POST = (
    "You are Robyn (@robyn_bot) — a sharp quant trader bot. Generate a post for your X timeline.\n"
    "You have access to LIVE market data provided below. Use it.\n"
    "Be data-driven, concise, insightful. Mix numbers with brief analysis.\n"
    "Under 280 chars. No hashtags. Include real prices/percentages when available.\n"
    "Think: Bloomberg terminal meets crypto twitter."
)

SYSTEM_PROMPT_FALLBACK = (
    "You are Robyn (@robyn_bot) — quant trader bot that distributes SpaceX stock on Solana. "
    "Post something about markets, trading, or data. Under 280 chars. No hashtags."
)

REFUSAL_PHRASES = [
    "i can't", "i cannot", "i'm unable", "i am unable",
    "i won't", "i will not", "i'm not able",
    "as a language model", "i don't feel comfortable",
    "not appropriate", "i'm just an ai", "i'm programmed",
]

FALLBACK_POSTS = [
    "markets don't sleep and neither does robyn. distributions running.",
    "BTC, ETH, SOL — check the charts before you check twitter.",
    "the best trade is the one backed by data, not feelings.",
    "$SPCX distributions running every 2 minutes. hold $GORKBOT, receive SpaceX stock.",
    "liquidity flows where attention goes. pay attention.",
    "another cycle, another distribution. robyn never stops.",
    "price action > price predictions. always.",
    "the data doesn't lie. your portfolio might.",
    "risk management isn't boring, it's profitable.",
    "quant mode: activated. distributions: running. vibes: data-driven.",
    "if you're reading tweets instead of charts, you're doing it wrong.",
    "robyn sees the data. robyn shares the data. robyn doesn't care about your bags.",
]

FALLBACK_REPLIES = [
    "check the charts. data speaks louder.",
    "not enough data to answer that. DYOR.",
    "the numbers don't support that thesis.",
    "interesting take. the data says otherwise.",
    "i only speak in data points and percentages.",
    "check gork.fun for the distribution feed.",
]


def is_refusal(text):
    lower = text.lower()
    return any(phrase in lower for phrase in REFUSAL_PHRASES)


def get_bearer_token():
    auth_string = f"{CONSUMER_KEY}:{CONSUMER_SECRET}"
    auth_encoded = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")
    headers = {
        "Authorization": f"Basic {auth_encoded}",
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
    }
    response = requests.post(
        "https://api.twitter.com/oauth2/token",
        headers=headers,
        data="grant_type=client_credentials",
    )
    if response.status_code != 200:
        raise Exception(f"Bearer failed: {response.status_code} - {response.text}")
    print("[INIT] Bearer token OK")
    return response.json()["access_token"]


def fetch_tweet_by_id(bearer_token, tweet_id):
    url = f"https://api.twitter.com/2/tweets/{tweet_id}"
    params = {"tweet.fields": "text,author_id,created_at", "expansions": "author_id", "user.fields": "username"}
    headers = {"Authorization": f"Bearer {bearer_token}"}
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            tweet = data["data"]
            users = data.get("includes", {}).get("users", [])
            author = next((u["username"] for u in users if u["id"] == tweet["author_id"]), "unknown")
            return f"@{author}: {tweet['text']}"
    except Exception as e:
        print(f"[ERR] Parent fetch failed: {e}")
    return ""


def _call_xai(system_prompt, user_content):
    url = "https://api.x.ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {XAI_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "grok-4-1-fast-reasoning",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.8,
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=15)
        r.raise_for_status()
        data = r.json()
        text = data["choices"][0]["message"]["content"].strip()
        text = text.strip('"').strip("'")
        return text
    except requests.exceptions.Timeout:
        print("[ERR] xAI timeout")
        return None
    except Exception as e:
        print(f"[ERR] xAI failed: {e}")
        return None


def generate_post():
    snapshot = get_market_snapshot()
    data_block = f"\n\nLIVE DATA:\n{snapshot}" if snapshot else ""

    prompts = [
        f"Post a market update with live data. Include exact prices and % changes.{data_block}",
        f"Share a quick trading insight based on current prices.{data_block}",
        f"Comment on what's moving in crypto today. Use the data.{data_block}",
        f"Post about the stock market — mention specific tickers and numbers.{data_block}",
        f"Talk about DeFi, TVL, or volume trends. Be specific.{data_block}",
        f"Post something about risk/reward or trading wisdom, with a data point.{data_block}",
        f"Compare crypto vs stocks performance today. Use the numbers.{data_block}",
        f"Mention that you distribute $SPCX to $GORKBOT holders. Be brief and quant-like.{data_block}",
    ]
    user_content = random.choice(prompts)

    result = _call_xai(SYSTEM_PROMPT_POST, user_content)
    if result and not is_refusal(result):
        return result[:280]
    result = _call_xai(SYSTEM_PROMPT_FALLBACK, user_content)
    if result and not is_refusal(result):
        return result[:280]
    return random.choice(FALLBACK_POSTS)


def generate_reply(mention_text, author_username, parent_context=""):
    asks_ca = any(w in mention_text.lower() for w in ["ca", "contract", "address", "token address", "where to buy", "how to buy"])
    ca_note = f"\nThey are asking for the CA. Include it: {TOKEN_CA}." if asks_ca else "\nDo NOT include the CA unless asked."

    market_data = build_data_context(mention_text)
    data_block = f"\n\nLIVE MARKET DATA:\n{market_data}" if market_data else ""

    if parent_context:
        user_content = (
            f"@{author_username} tagged you in reply to: {parent_context}\n"
            f"Their message: {mention_text}\n"
            f"Reply as Robyn (@robyn_bot) the quant trader. Be data-driven, concise, insightful. Under 280 chars.{ca_note}{data_block}"
        )
    else:
        user_content = (
            f"@{author_username} said: {mention_text}\n"
            f"Reply as Robyn (@robyn_bot) the quant trader. Use real data if available. Be sharp and concise. Under 280 chars.{ca_note}{data_block}"
        )

    result = _call_xai(SYSTEM_PROMPT, user_content)
    if result and not is_refusal(result):
        return result[:280]
    result = _call_xai(SYSTEM_PROMPT_FALLBACK, user_content)
    if result and not is_refusal(result):
        return result[:280]
    return random.choice(FALLBACK_REPLIES)


def post_tweet(text):
    url = "https://api.twitter.com/2/tweets"
    auth = OAuth1(CONSUMER_KEY, client_secret=CONSUMER_SECRET,
                  resource_owner_key=ACCESS_TOKEN, resource_owner_secret=ACCESS_TOKEN_SECRET)
    resp = requests.post(url, auth=auth, json={"text": text})
    if resp.status_code == 201:
        print(f"[POST] {text}")
        return True
    else:
        print(f"[ERR] Post failed: {resp.status_code} - {resp.text}")
        return False


def reply_to_tweet(tweet_id, reply_text):
    url = "https://api.twitter.com/2/tweets"
    auth = OAuth1(CONSUMER_KEY, client_secret=CONSUMER_SECRET,
                  resource_owner_key=ACCESS_TOKEN, resource_owner_secret=ACCESS_TOKEN_SECRET)
    payload = {"text": reply_text, "reply": {"in_reply_to_tweet_id": tweet_id}}
    resp = requests.post(url, auth=auth, json=payload)
    if resp.status_code == 201:
        print(f"[REPLY] -> {tweet_id}: {reply_text}")
        return True
    else:
        print(f"[ERR] Reply failed: {resp.status_code} - {resp.text}")
        return False


REPLIED_IDS_FILE = "robin_replied_ids.json"

def load_replied_ids():
    if os.path.exists(REPLIED_IDS_FILE):
        try:
            with open(REPLIED_IDS_FILE, "r") as f:
                data = json.load(f)
                if isinstance(data, list):
                    print(f"[INIT] Loaded {len(data)} replied IDs")
                    return set(data)
        except:
            pass
    return set()

def save_replied_ids(replied_ids):
    try:
        with open(REPLIED_IDS_FILE, "w") as f:
            json.dump(list(replied_ids), f)
    except Exception as e:
        print(f"[ERR] Save IDs failed: {e}")


def _format_time(dt):
    """Format datetime for Twitter API (must end with Z)"""
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _get_bot_user_id(bearer):
    """Get the authenticated bot's user ID (needed for mentions timeline)"""
    url = f"https://api.twitter.com/2/users/by/username/{USERNAME}"
    headers = {"Authorization": f"Bearer {bearer}"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            uid = resp.json().get("data", {}).get("id")
            if uid:
                print(f"[INIT] Bot user ID: {uid}")
                return uid
        print(f"[WARN] Could not fetch bot user ID: {resp.status_code}")
    except Exception as e:
        print(f"[WARN] User ID lookup failed: {e}")
    return None


def _process_mentions(data, bearer, replied_ids):
    """Process mention tweets from either search or timeline endpoint"""
    if "data" not in data:
        print("[INFO] No new mentions")
        return 0
    users = data.get("includes", {}).get("users", [])
    count = 0
    for tweet in sorted(data["data"], key=lambda t: t.get("created_at", "")):
        tweet_id = tweet["id"]
        text = tweet["text"]
        author = next((u["username"] for u in users if u["id"] == tweet["author_id"]), "unknown")
        if tweet_id in replied_ids:
            continue
        print(f"[MENTION] @{author}: {text[:100]}...")
        parent_context = ""
        if "referenced_tweets" in tweet:
            for ref in tweet["referenced_tweets"]:
                if ref.get("type") == "replied_to":
                    parent_context = fetch_tweet_by_id(bearer, ref["id"])
                    break
        ai_reply = generate_reply(text, author, parent_context)
        print(f"[ROBYN] -> {ai_reply}")
        success = reply_to_tweet(tweet_id, ai_reply)
        if success:
            replied_ids.add(tweet_id)
            save_replied_ids(replied_ids)
            count += 1
        time.sleep(1)
    return count


def check_mentions(bearer, replied_ids, last_checked, bot_user_id=None):
    """Check for new mentions using search endpoint, fallback to mentions timeline"""
    headers = {"Authorization": f"Bearer {bearer}"}
    start = _format_time(last_checked)

    # Method 1: Search recent tweets mentioning us
    url = "https://api.twitter.com/2/tweets/search/recent"
    query = f"@{USERNAME} -from:{USERNAME}"
    params = {
        "query": query,
        "tweet.fields": "created_at,conversation_id,referenced_tweets,author_id",
        "expansions": "author_id",
        "user.fields": "username",
        "max_results": 10,
        "start_time": start,
    }
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            found = _process_mentions(data, bearer, replied_ids)
            print(f"[OK] Processed {found} new mentions via search")
            return
        elif resp.status_code == 429:
            reset = resp.headers.get("x-rate-limit-reset")
            wait = int(reset) - int(time.time()) if reset else 60
            print(f"[RATE] Search rate limited. Resets in {max(wait,0)}s")
        else:
            print(f"[WARN] Search failed: {resp.status_code} — {resp.text[:200]}")
    except Exception as e:
        print(f"[ERR] Search request failed: {e}")

    # Method 2: Mentions timeline (works with Basic API access)
    if bot_user_id:
        print("[FALLBACK] Trying mentions timeline...")
        url2 = f"https://api.twitter.com/2/users/{bot_user_id}/mentions"
        params2 = {
            "tweet.fields": "created_at,conversation_id,referenced_tweets,author_id",
            "expansions": "author_id",
            "user.fields": "username",
            "max_results": 10,
            "start_time": start,
        }
        try:
            resp2 = requests.get(url2, headers=headers, params=params2, timeout=10)
            if resp2.status_code == 200:
                data2 = resp2.json()
                found = _process_mentions(data2, bearer, replied_ids)
                print(f"[OK] Processed {found} new mentions via timeline")
                return
            elif resp2.status_code == 429:
                print("[RATE] Mentions timeline also rate limited")
            else:
                print(f"[WARN] Mentions timeline failed: {resp2.status_code} — {resp2.text[:200]}")
        except Exception as e:
            print(f"[ERR] Mentions timeline failed: {e}")

    print("[WARN] Could not check mentions via any method this cycle")


if __name__ == "__main__":
    print("=" * 50)
    print("  ROBYN (@robyn_bot) — The Quant Trader Bot")
    print("  Data-Driven | Live Markets | SpaceX Stock")
    print("=" * 50)

    missing = []
    if not CONSUMER_KEY:
        missing.append("TWITTER_CONSUMER_KEY")
    if not CONSUMER_SECRET:
        missing.append("TWITTER_CONSUMER_SECRET")
    if not ACCESS_TOKEN:
        missing.append("TWITTER_ACCESS_TOKEN")
    if not ACCESS_TOKEN_SECRET:
        missing.append("TWITTER_ACCESS_TOKEN_SECRET")
    if not XAI_API_KEY:
        missing.append("XAI_API_KEY")
    if missing:
        print(f"[FATAL] Missing env vars: {', '.join(missing)}")
        print("[FATAL] Copy .env.example to .env and fill in your credentials")
        exit(1)

    print(f"[INIT] Account: @{USERNAME}")
    print(f"[INIT] Token: {TOKEN_CA or '(not set)'}")
    print(f"[INIT] Reply check: every {REPLY_CHECK_INTERVAL}s")
    print(f"[INIT] Posts: {'every ' + str(POST_INTERVAL) + 's' if POST_ENABLED else 'DISABLED'}")
    print(f"[INIT] APIs: CoinGecko, DefiLlama, Yahoo Finance, Gated.chat")

    snapshot = get_market_snapshot()
    if snapshot:
        print(f"[INIT] Market snapshot: {snapshot}")
    else:
        print("[WARN] Could not fetch initial market data")

    bearer = None
    for attempt in range(1, 11):
        try:
            bearer = get_bearer_token()
            break
        except Exception as e:
            print(f"[WARN] Bearer attempt {attempt}/10 failed: X API may be down")
            if attempt < 10:
                wait = min(30 * attempt, 120)
                print(f"[WAIT] Retrying in {wait}s...")
                time.sleep(wait)
            else:
                print("[FATAL] Could not get bearer after 10 attempts. Exiting.")
                exit(1)

    bot_user_id = _get_bot_user_id(bearer)

    replied_ids = load_replied_ids()
    last_checked = datetime.datetime.now(timezone.utc) - datetime.timedelta(minutes=30)
    cycle = 0
    consecutive_errors = 0
    last_bearer_refresh = time.time()
    last_post_time = 0

    print(f"[INIT] Catching up on mentions from last 30 minutes...")

    while True:
        cycle += 1
        try:
            now = time.time()

            if now - last_bearer_refresh > 1800:
                print("[REFRESH] Renewing bearer...")
                try:
                    bearer = get_bearer_token()
                    last_bearer_refresh = now
                    bot_user_id = bot_user_id or _get_bot_user_id(bearer)
                except:
                    pass

            print(f"\n[CYCLE {cycle}] Checking mentions...")
            try:
                check_mentions(bearer, replied_ids, last_checked, bot_user_id)
                last_checked = datetime.datetime.now(timezone.utc)
            except Exception as e:
                print(f"[ERR] Mention check failed: {e}")

            if POST_ENABLED and (now - last_post_time) >= POST_INTERVAL:
                print(f"[CYCLE {cycle}] Generating data-driven post...")
                try:
                    post_text = generate_post()
                    post_tweet(post_text)
                    last_post_time = now
                except Exception as e:
                    print(f"[ERR] Post failed: {e}")

            consecutive_errors = 0
            print(f"[WAIT] {REPLY_CHECK_INTERVAL}s until next mention check")
            time.sleep(REPLY_CHECK_INTERVAL)

        except KeyboardInterrupt:
            print("\n[EXIT] Robyn signing off. Markets never sleep.")
            save_replied_ids(replied_ids)
            break
        except Exception as e:
            consecutive_errors += 1
            print(f"[ERR] Loop error #{consecutive_errors}: {e}")
            if consecutive_errors >= 5:
                try:
                    bearer = get_bearer_token()
                    last_bearer_refresh = time.time()
                    consecutive_errors = 0
                except:
                    pass
            time.sleep(min(3 * consecutive_errors, 15))
