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
    """
    Process raw market results into a standardized format.
    
    Args:
        results: List of raw market data results
        max_results: Maximum number of results to return (None for all)
        
    Returns:
        List of processed market data
    """
    processed = []
    for r in results:
        try:
            if all(k in r for k in ["T", "c", "o", "v"]):
                change = r["c"] - r["o"]
                change_percent = (change / r["o"]) * 100 if r["o"] > 0 else 0
                
                processed.append({
                    "symbol": r["T"],
                    "open": r["o"],
                    "high": r["h"],
                    "low": r["l"],
                    "close": r["c"],
                    "volume": r["v"],
                    "vwap": r.get("vw"),
                    "change": round(change, 4),
                    "change_percent": round(change_percent, 2)
                })
        except (TypeError, KeyError) as e:
            continue
    
    # Sort by volume in descending order
    processed.sort(key=lambda x: x["volume"], reverse=True)
    
    # Apply max results if specified
    if max_results is not None:
        return processed[:max_results]
    
    return processed


def get_paginated_results(
    data: List[Any], 
    offset: int = 0, 
    limit: Optional[int] = None
) -> List[Any]:
    """
    Get a paginated subset of data.
    
    Args:
        data: List of items to paginate
        offset: Number of items to skip
        limit: Maximum number of items to return (None for all remaining)
        
    Returns:
        Paginated subset of the data
    """
    if limit is None:
        return data[offset:]
    return data[offset:offset + limit]


def get_top_assets(
    processed_results: List[Dict[str, Any]], 
    top_n: int = 10
) -> dict:
    """
    Get top gainers, losers, and most active assets.
    
    Args:
        processed_results: List of processed market data
        top_n: Number of top items to return for each category
        
    Returns:
        Dictionary with top gainers, losers, and most active assets
    """
    top_gainers = sorted(
        processed_results,
        key=lambda x: x["change_percent"],
        reverse=True
    )[:top_n]
    
    top_losers = sorted(
        processed_results,
        key=lambda x: x["change_percent"]
    )[:top_n]
    
    most_active = processed_results[:top_n]
    
    return {
        "top_gainers": top_gainers,
        "top_losers": top_losers,
        "most_active": most_active
    }
