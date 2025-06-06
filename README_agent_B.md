# 📈 Agent B: Real-Time Market Trader (Part 2)

## Table of Contents

- [1. Prerequisites & Environment Verification](#1-prerequisites--environment-verification)
- [2. Directory Structure & Git Initialization (Agent B)](#2-directory-structure--git-initialization-agent-b)
- [3. Part 2: Agent B (Market Data → Decision → Execution)](#3-part-2-agent-b-market-data--decision--execution)
  - [3.1 Install Additional Dependencies](#31-install-additional-dependencies)
  - [3.2 Real-Time Market Data Ingestion](#32-real-time-market-data-ingestion)
    - [3.2.1 Obtain Binance API Keys](#321-obtain-binance-api-keys)
    - [3.2.2 Write & Test agent_B_data_feed.py](#322-write--test-agent_b_data_feedpy)
    - [3.2.3 Configure agent_B_data_feed.service](#323-configure-agent_b_data_feedservice)
  - [3.3 Decision Model Training](#33-decision-model-training)
    - [3.3.1 Fetch Historical Klines](#331-fetch-historical-klines)
    - [3.3.2 Populate training_data Table](#332-populate-training_data-table)
    - [3.3.3 Fine-Tune facebook/opt-350m (8-bit)](#333-fine-tune-facebookopt-350m-8-bit)
    - [3.3.4 Configure train_decision_model.service](#334-configure-train_decision_modelservice)
  - [3.4 Agent B Core Logic](#34-agent-b-core-logic)
    - [3.4.1 Load Configs & Models](#341-load-configs--models)
    - [3.4.2 Multi-Timeframe Resampling & Indicators](#342-multi-timeframe-resampling--indicators)
    - [3.4.3 Conviction Scoring & OPT Prompting](#343-conviction-scoring--opt-prompting)
    - [3.4.4 Trade Entry & Exit Logic](#344-trade-entry--exit-logic)
    - [3.4.5 News-Based Exits (Agent A)](#345-news-based-exits-agent-a)
    - [3.4.6 Send Charts via Telegram](#346-send-charts-via-telegram)
    - [3.4.7 Populate trades Table](#347-populate-trades-table)
    - [3.4.8 Test agent_B_core.py Manually](#348-test-agent_b_corepy-manually)
    - [3.4.9 Configure agent_B_core.service](#349-configure-agent_b_coreservice)
  - [3.5 Telegram Trade Notifications](#35-telegram-trade-notifications)
    - [3.5.1 Optional Notifier Code](#351-optional-notifier-code)
    - [3.5.2 Configure agent_B_notify.service](#352-configure-agent_b_notifyservice)
  - [3.6 Logging, Backtesting Hooks, Persistence](#36-logging-backtesting-hooks-persistence)
    - [3.6.1 Verify SQLite Tables](#361-verify-sqlite-tables)
    - [3.6.2 Inspect Logs & DB Records](#362-inspect-logs--db-records)
  - [3.7 Checklist & Validation](#37-checklist--validation)

- [4. Testing, Monitoring & Troubleshooting](#4-testing-monitoring--troubleshooting)
- [5. Summary of All Running Services](#5-summary-of-all-running-services)
- [6. What to Do if You Encounter Errors](#6-what-to-do-if-you-encounter-errors)

---

## 🗺️ Project Flowchart: Agent B Overview

```mermaid
flowchart TD
  Start([Start Agent B])
  A[Binance Market Data via WebSocket]
  B[Save market_data_1m → SQLite]
  C[Indicators (RSI, EMA, ADX, BB, VWAP)]
  D[Multi-TF Resampling: 15m, 30m, 2H, 4H]
  E[Conviction Scoring with OPT-350M]
  F{Open Trade?}
  G[Execute Trade\nSet SL/TP/Stagnant Limits]
  H[Monitor Position]
  I{Exit Conditions Met?}
  J[Log Trade to DB (trades table)]
  K[Telegram Notification]
  L[Wait for Next Signal]
  
  Start --> A --> B --> C --> D --> E --> F
  F -- Yes --> G --> H --> I
  I -- Yes --> J --> K --> L --> E
  I -- No --> H
  F -- No --> L --> E
