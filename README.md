# Robyn (@robyn_bot)

A data-driven quant trader bot for X (Twitter). Robyn monitors mentions, fetches live market data, and replies with sharp, AI-generated market commentary powered by Grok.

## What It Does

- **Monitors mentions** — checks for @robyn_bot tags every 15 seconds
- **Fetches live market data** — crypto prices (CoinGecko), stock prices (Yahoo Finance), DeFi TVL (DefiLlama), DEX volume, trending coins
- **AI replies** — uses Grok (xAI) to generate data-driven responses under 280 chars
- **Auto-posting** — optional scheduled market updates to timeline
- **Smart data parsing** — detects tickers ($BTC, $NVDA), stock names (nvidia, tesla), and market keywords in mentions, then pulls relevant data before generating a reply

## Data Sources (All Free, No API Keys Needed)

| Source | Data |
|--------|------|
| CoinGecko | Crypto prices, 24h change, market cap, volume, trending coins |
| Yahoo Finance | Stock prices, 52-week range, earnings, news headlines |
| DefiLlama | Chain TVL, protocol TVL, DEX volume, fees/revenue |
| Gated.chat | Solana token prices |

## Setup

### 1. Clone & Install

```bash
git clone https://github.com/YOUR_USERNAME/robyn-bot.git
cd robyn-bot
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

- **X API keys** — get from [developer.x.com](https://developer.x.com/en/portal)
- **xAI API key** — get from [console.x.ai](https://console.x.ai)

### 3. Run

```bash
python xbot.py
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `BOT_USERNAME` | `robyn_bot` | X handle to monitor mentions for |
| `REPLY_CHECK_INTERVAL` | `15` | Seconds between mention checks |
| `POST_INTERVAL` | `600` | Seconds between auto-posts |
| `POST_ENABLED` | `false` | Enable/disable auto-posting |
| `TOKEN_CA` | *(empty)* | Token contract address (shared when asked) |

## How It Works

```
Mention detected → Parse text for tickers/keywords
                 → Fetch live market data (crypto, stocks, DeFi)
                 → Build data context string
                 → Send to Grok with system prompt + data
                 → Post AI reply (under 280 chars)
```

### Supported Queries

Robyn can handle mentions about:

- **Crypto prices** — "what's BTC at?" / "$ETH price" / "how's SOL doing"
- **Stock prices** — "$NVDA" / "how's apple stock" / "TSLA price"
- **Why moved** — "why did NVDA pump?" → fetches news headlines + synthesizes
- **DeFi data** — "solana TVL" / "DEX volume" / "top chains"
- **Trending** — "what's trending" / "what's hot in crypto"
- **Market overview** — "market update" / "how are markets"

### Supported Assets

- **60+ crypto** — BTC, ETH, SOL, DOGE, PEPE, WIF, SUI, APT, and more
- **50+ stocks** — AAPL, NVDA, TSLA, GOOGL, META, AMD, PLTR, SPY, QQQ, etc.
- **DeFi chains** — Ethereum, Solana, BSC, Base, Arbitrum, Polygon, Robinhood, etc.

## Tech Stack

- **Python 3.10+**
- **Grok (xAI)** — AI model for generating replies (`grok-4-1-fast-reasoning`)
- **X API v2** — tweet search, reply, post
- **requests + requests-oauthlib** — HTTP + OAuth1
- **python-dotenv** — environment variable management

## License

MIT
