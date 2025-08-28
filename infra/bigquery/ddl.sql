-- Datasets
CREATE SCHEMA IF NOT EXISTS `${GCP_PROJECT}.${BQ_DATASET_RAW}`;

CREATE SCHEMA IF NOT EXISTS `${GCP_PROJECT}.${BQ_DATASET_CURATED}`;

-- Unified Equities OHLCV Table (EODHD + Twelve Data + any vendor)
CREATE TABLE IF NOT EXISTS `${GCP_PROJECT}.${BQ_DATASET_RAW}.eq_ohlcv` (
    symbol STRING NOT NULL,
    mic STRING NOT NULL, -- Market Identifier Code (XETR, LSE, NASDAQ, etc.)
    vendor STRING NOT NULL, -- Data vendor (eodhd, twelve_data, etc.)
    interval STRING NOT NULL, -- Time interval (1min, 5min, 1h, 1d, etc.)
    ts_utc TIMESTAMP NOT NULL, -- UTC timestamp only
    open FLOAT64,
    high FLOAT64,
    low FLOAT64,
    close FLOAT64,
    volume INT64,
    ingest_time TIMESTAMP,
)
PARTITION BY
    DATE(ts_utc) CLUSTER BY symbol,
    interval,
    vendor;

-- FX Rates Table
CREATE TABLE IF NOT EXISTS `${GCP_PROJECT}.${BQ_DATASET_RAW}.fx_ohlcv` (
    symbol STRING NOT NULL, -- Currency pair (EUR/USD, GBP/USD, etc.)
    vendor STRING NOT NULL,
    interval STRING NOT NULL,
    ts_utc TIMESTAMP NOT NULL,
    open FLOAT64,
    high FLOAT64,
    low FLOAT64,
    close FLOAT64,
    ingest_time TIMESTAMP,
)
PARTITION BY
    DATE(ts_utc) CLUSTER BY symbol,
    interval,
    vendor;

-- Crypto Prices Table
CREATE TABLE IF NOT EXISTS `${GCP_PROJECT}.${BQ_DATASET_RAW}.crypto_ohlcv` (
    symbol STRING NOT NULL, -- Crypto pair (BTC/USD, ETH/USD, etc.)
    vendor STRING NOT NULL,
    interval STRING NOT NULL,
    ts_utc TIMESTAMP NOT NULL,
    open FLOAT64,
    high FLOAT64,
    low FLOAT64,
    close FLOAT64,
    volume FLOAT64,
    ingest_time TIMESTAMP,
)
PARTITION BY
    DATE(ts_utc) CLUSTER BY symbol,
    interval,
    vendor;

-- Corporate Actions Table (Splits, Dividends, Adjustments)
CREATE TABLE IF NOT EXISTS `${GCP_PROJECT}.${BQ_DATASET_RAW}.corporate_actions` (
    symbol STRING NOT NULL,
    mic STRING NOT NULL,
    ex_date DATE NOT NULL, -- Ex-dividend date
    split_ratio FLOAT64, -- Split ratio (e.g., 2.0 for 2:1 split)
    cash_dividend FLOAT64, -- Cash dividend per share
    adj_factor FLOAT64 NOT NULL, -- Cumulative adjustment factor
    vendor STRING NOT NULL,
    ingest_time TIMESTAMP,
)
PARTITION BY
    DATE(ex_date) CLUSTER BY symbol,
    mic;

-- Vendor Symbol Mapping Table
CREATE TABLE IF NOT EXISTS `${GCP_PROJECT}.${BQ_DATASET_RAW}.vendor_symbol_map` (
    vendor STRING NOT NULL,
    vendor_symbol STRING NOT NULL, -- Symbol as known by vendor
    symbol STRING NOT NULL, -- Canonical symbol (TICKER.MIC)
    mic STRING NOT NULL, -- Market Identifier Code
    exchange_name STRING, -- Human readable exchange name
    asset_type STRING, -- equity, fx, crypto
    is_active BOOLEAN DEFAULT TRUE,
    ingest_time TIMESTAMP,
) CLUSTER BY vendor,
symbol;

-- Curated Views
CREATE VIEW IF NOT EXISTS `${GCP_PROJECT}.${BQ_DATASET_CURATED}.v_daily_close` AS
SELECT
    symbol,
    mic,
    ANY_VALUE(close) KEEP (
        DENSE_RANK LAST
        ORDER BY ingest_time
    ) AS close,
    ANY_VALUE(volume) KEEP (
        DENSE_RANK LAST
        ORDER BY ingest_time
    ) AS volume,
    MAX(ts_utc) AS latest_ts_utc,
    vendor
FROM
    `${GCP_PROJECT}.${BQ_DATASET_RAW}.eq_ohlcv`
WHERE
    interval = '1d' -- Daily data only
GROUP BY
    symbol,
    mic,
    vendor;

CREATE VIEW IF NOT EXISTS `${GCP_PROJECT}.${BQ_DATASET_CURATED}.v_intraday_latest` AS
SELECT
    symbol,
    mic,
    interval,
    ANY_VALUE(close) KEEP (
        DENSE_RANK LAST
        ORDER BY ts_utc
    ) AS latest_close,
    ANY_VALUE(high) KEEP (
        DENSE_RANK LAST
        ORDER BY ts_utc
    ) AS latest_high,
    ANY_VALUE(low) KEEP (
        DENSE_RANK LAST
        ORDER BY ts_utc
    ) AS latest_low,
    ANY_VALUE(volume) KEEP (
        DENSE_RANK LAST
        ORDER BY ts_utc
    ) AS latest_volume,
    MAX(ts_utc) AS latest_ts_utc,
    vendor
FROM
    `${GCP_PROJECT}.${BQ_DATASET_RAW}.eq_ohlcv`
WHERE
    interval IN (
        '1min',
        '5min',
        '15min',
        '30min',
        '45min',
        '1h',
        '2h',
        '4h'
    )
GROUP BY
    symbol,
    mic,
    interval,
    vendor;

CREATE VIEW IF NOT EXISTS `${GCP_PROJECT}.${BQ_DATASET_CURATED}.v_fx_latest` AS
SELECT
    symbol,
    interval,
    ANY_VALUE(close) KEEP (
        DENSE_RANK LAST
        ORDER BY ts_utc
    ) AS latest_rate,
    MAX(ts_utc) AS latest_ts_utc,
    vendor
FROM
    `${GCP_PROJECT}.${BQ_DATASET_RAW}.fx_ohlcv`
GROUP BY
    symbol,
    interval,
    vendor;

CREATE VIEW IF NOT EXISTS `${GCP_PROJECT}.${BQ_DATASET_CURATED}.v_crypto_latest` AS
SELECT
    symbol,
    interval,
    ANY_VALUE(close) KEEP (
        DENSE_RANK LAST
        ORDER BY ts_utc
    ) AS latest_price,
    ANY_VALUE(volume) KEEP (
        DENSE_RANK LAST
        ORDER BY ts_utc
    ) AS latest_volume,
    MAX(ts_utc) AS latest_ts_utc,
    vendor
FROM
    `${GCP_PROJECT}.${BQ_DATASET_RAW}.crypto_ohlcv`
GROUP BY
    symbol,
    interval,
    vendor;

-- Adjusted Prices View (incorporates corporate actions)
CREATE VIEW IF NOT EXISTS `${GCP_PROJECT}.${BQ_DATASET_CURATED}.v_adjusted_prices` AS
WITH
    latest_adj_factors AS (
        SELECT
            symbol,
            mic,
            ANY_VALUE(adj_factor) KEEP (
                DENSE_RANK LAST
                ORDER BY ex_date
            ) AS latest_adj_factor
        FROM
            `${GCP_PROJECT}.${BQ_DATASET_RAW}.corporate_actions`
        GROUP BY
            symbol,
            mic
    )
SELECT
    p.symbol,
    p.mic,
    p.vendor,
    p.interval,
    p.ts_utc,
    p.open * COALESCE(a.latest_adj_factor, 1.0) AS adj_open,
    p.high * COALESCE(a.latest_adj_factor, 1.0) AS adj_high,
    p.low * COALESCE(a.latest_adj_factor, 1.0) AS adj_low,
    p.close * COALESCE(a.latest_adj_factor, 1.0) AS adj_close,
    p.volume,
    p.ingest_time,
    COALESCE(a.latest_adj_factor, 1.0) AS adj_factor
FROM
    `${GCP_PROJECT}.${BQ_DATASET_RAW}.eq_ohlcv` p
    LEFT JOIN latest_adj_factors a ON p.symbol = a.symbol
    AND p.mic = a.mic
WHERE
    p.interval = '1d';
-- Daily data for adjustments