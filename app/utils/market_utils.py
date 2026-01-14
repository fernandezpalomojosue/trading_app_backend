"""
Utility functions for market-related operations.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import HTTPException


def process_market_results(
    results: List[Dict[str, Any]], 
    max_results: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Process raw market results into a standardized format."""
    processed = []
    for r in results:
        try:
            if not isinstance(r, dict) or not all(k in r for k in ["T", "c", "o", "v"]):
                continue
                
            open_price = r["o"]
            close_price = r["c"]
            
            change = close_price - open_price
            change_percent = (change / open_price * 100) if open_price > 0 else 0
            
            processed.append({
                "symbol": r["T"],
                "open": open_price,
                "high": r.get("h", close_price),
                "low": r.get("l", close_price),
                "close": close_price,
                "volume": r["v"],
                "vwap": r.get("vw"),
                "change": round(change, 4),
                "change_percent": round(change_percent, 2)
            })
        except (TypeError, KeyError, ZeroDivisionError):
            continue
    
    processed.sort(key=lambda x: x["volume"], reverse=True)
    
    if max_results is not None:
        return processed[:max_results]
    
    return processed


def get_paginated_results(
    data: List[Any], 
    offset: int = 0, 
    limit: Optional[int] = None
) -> List[Any]:
    """Get a paginated subset of data."""
    if limit is None:
        return data[offset:]
    return data[offset:offset + limit]


def get_top_assets(
    processed_results: List[Dict[str, Any]], 
    top_n: int = 10
) -> dict:
    """Get top gainers, losers, and most active assets."""
    most_active = processed_results[:top_n]
    
    top_gainers = sorted(
        processed_results,
        key=lambda x: x["change_percent"],
        reverse=True
    )[:top_n]
    
    top_losers = sorted(
        processed_results,
        key=lambda x: x["change_percent"]
    )[:top_n]
    
    return {
        "top_gainers": top_gainers,
        "top_losers": top_losers,
        "most_active": most_active
    }
