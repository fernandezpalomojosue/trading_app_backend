"""
AI Rate Limiter

Per-user rate limiting for AI strategy generation.
Designed for endpoint-level enforcement (not inside service).

Simple in-memory implementation. For production with multiple servers,
consider Redis-backed rate limiting.
"""

import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict
from uuid import UUID


@dataclass
class RateLimitEntry:
    """Track requests for a single user."""
    count: int = 0
    window_start: float = 0.0


class AIRateLimiter:
    """
    In-memory per-user rate limiter.
    
    Usage (at endpoint level):
        @router.post("/generate")
        async def generate(request, current_user, rate_limiter: AIRateLimiter = Depends(...)):
            if not await rate_limiter.check_rate_limit(current_user.id):
                raise HTTPException(429, "Rate limit exceeded")
            await rate_limiter.record_request(current_user.id)
            # ... proceed with generation
    """
    
    def __init__(self, max_requests: int = 5, window_seconds: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests allowed per window
            window_seconds: Time window duration in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # user_id -> request tracking
        self._storage: Dict[str, RateLimitEntry] = defaultdict(RateLimitEntry)
    
    async def check_rate_limit(self, user_id: UUID) -> bool:
        """
        Check if user has remaining quota.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if request is allowed, False if rate limited
        """
        user_key = str(user_id)
        now = time.time()
        
        entry = self._storage[user_key]
        
        # Reset if window expired
        if now - entry.window_start > self.window_seconds:
            return True  # Window reset, allow request
        
        # Check quota
        return entry.count < self.max_requests
    
    async def record_request(self, user_id: UUID) -> None:
        """
        Record a request for rate limiting.
        
        Args:
            user_id: User identifier
        """
        user_key = str(user_id)
        now = time.time()
        
        entry = self._storage[user_key]
        
        # Reset if window expired
        if now - entry.window_start > self.window_seconds:
            entry.count = 0
            entry.window_start = now
        
        entry.count += 1
    
    def get_remaining_quota(self, user_id: UUID) -> int:
        """
        Get remaining requests for user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Number of remaining requests in current window
        """
        user_key = str(user_id)
        now = time.time()
        
        entry = self._storage[user_key]
        
        # Reset if window expired
        if now - entry.window_start > self.window_seconds:
            return self.max_requests
        
        remaining = self.max_requests - entry.count
        return max(0, remaining)
    
    def get_retry_after(self, user_id: UUID) -> int:
        """
        Get seconds until rate limit resets.
        
        Args:
            user_id: User identifier
            
        Returns:
            Seconds until window resets
        """
        user_key = str(user_id)
        now = time.time()
        
        entry = self._storage[user_key]
        elapsed = now - entry.window_start
        remaining = self.window_seconds - elapsed
        
        return max(0, int(remaining))
