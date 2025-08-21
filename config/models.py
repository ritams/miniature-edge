from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field


class DataSources(BaseModel):
    spot_exchange: str
    perps_venue: str


class Timeframes(BaseModel):
    htf: str
    ltf: str


class Basket(BaseModel):
    symbols: List[str]


class Costs(BaseModel):
    spot_fee_pct: float
    spot_slippage_pct: float
    perps_taker_fee_pct: float
    perps_maker_fee_pct: float
    include_funding: bool


class Apex(BaseModel):
    move_threshold_pct: float
    alt_lag_threshold_pct: float
    corr_min: float
    beta_min: float
    # Number of bars to measure apex/coin move over on LTF. Default 3 to catch
    # sustained impulses while keeping existing config.yaml valid.
    move_lookback_bars: int = Field(default=3)


class MarketFilters(BaseModel):
    volume_x: float
    breakout_lookback: int


class TD(BaseModel):
    strict_perfection: bool
    htf: str
    ltf: str
    cooldown_bars: int


class Risk(BaseModel):
    risk_per_trade_pct: float
    use_tdst_stop_when_td: bool
    atr_mult_tp: float


class Project(BaseModel):
    environment: str = Field(default="python+uv")


class Settings(BaseModel):
    project: Project
    data_sources: DataSources
    timeframes: Timeframes
    basket: Basket
    costs: Costs
    apex: Apex
    market_filters: MarketFilters
    td: TD
    risk: Risk
