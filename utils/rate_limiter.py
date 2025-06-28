"""
Rate limiting utilities to respect registry policies.
"""

import asyncio
import time
from typing import Dict, DefaultDict
from collections import defaultdict
import structlog

from config import Config

logger = structlog.get_logger(__name__)


class TokenBucket:
    """Token bucket implementation for rate limiting."""
    
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill = time.time()
        self.lock = asyncio.Lock()
    
    async def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens from bucket."""
        async with self.lock:
            self._refill()
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def _refill(self):
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        self.last_refill = now
        
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)


class RateLimiter:
    """Rate limiter with per-client and global limits."""
    
    def __init__(self, config: Config):
        self.config = config
        
        # Per-client rate limiting
        self.client_buckets: Dict[str, TokenBucket] = {}
        
        # Global rate limiting
        self.global_bucket = TokenBucket(
            capacity=config.global_rate_limit_burst,
            refill_rate=config.global_rate_limit_per_second
        )
        
        # Request tracking
        self.request_counts: DefaultDict[str, int] = defaultdict(int)
        self.request_windows: DefaultDict[str, float] = defaultdict(float)
        
        # Cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def acquire(self, client_id: str, tokens: int = 1) -> bool:
        """Acquire rate limit tokens for a client."""
        try:
            # Check global rate limit first
            if not await self.global_bucket.consume(tokens):
                logger.warning("Global rate limit exceeded", client_id=client_id)
                return False
            
            # Check per-client rate limit
            client_bucket = self._get_client_bucket(client_id)
            if not await client_bucket.consume(tokens):
                logger.warning("Client rate limit exceeded", client_id=client_id)
                return False
            
            # Update request tracking
            await self._update_request_tracking(client_id)
            
            logger.debug("Rate limit acquired", client_id=client_id, tokens=tokens)
            return True
            
        except Exception as e:
            logger.error("Rate limiter error", client_id=client_id, error=str(e))
            # Fail open for availability
            return True
    
    async def release(self, client_id: str):
        """Release resources after request completion."""
        # Currently no-op, but could be used for request completion tracking
        pass
    
    def _get_client_bucket(self, client_id: str) -> TokenBucket:
        """Get or create token bucket for client."""
        if client_id not in self.client_buckets:
            self.client_buckets[client_id] = TokenBucket(
                capacity=self.config.client_rate_limit_burst,
                refill_rate=self.config.client_rate_limit_per_second
            )
        return self.client_buckets[client_id]
    
    async def _update_request_tracking(self, client_id: str):
        """Update request tracking for analytics."""
        now = time.time()
        window_start = self.request_windows[client_id]
        
        # Reset counter if window expired (1 minute windows)
        if now - window_start > 60:
            self.request_counts[client_id] = 0
            self.request_windows[client_id] = now
        
        self.request_counts[client_id] += 1
    
    async def get_stats(self, client_id: str = None) -> Dict[str, Any]:
        """Get rate limiting statistics."""
        if client_id:
            # Per-client stats
            bucket = self.client_buckets.get(client_id)
            return {
                'client_id': client_id,
                'tokens_available': bucket.tokens if bucket else 0,
                'tokens_capacity': bucket.capacity if bucket else 0,
                'requests_in_window': self.request_counts[client_id],
                'window_start': self.request_windows[client_id]
            }
        else:
            # Global stats
            return {
                'global_tokens_available': self.global_bucket.tokens,
                'global_tokens_capacity': self.global_bucket.capacity,
                'active_clients': len(self.client_buckets),
                'total_requests': sum(self.request_counts.values())
            }
    
    async def _cleanup_loop(self):
        """Background cleanup of inactive clients."""
        try:
            while True:
                await asyncio.sleep(300)  # Run every 5 minutes
                await self._cleanup_inactive_clients()
        except asyncio.CancelledError:
            logger.info("Rate limiter cleanup task cancelled")
        except Exception as e:
            logger.error("Rate limiter cleanup error", error=str(e))
    
    async def _cleanup_inactive_clients(self):
        """Remove inactive client buckets."""
        now = time.time()
        inactive_clients = []
        
        for client_id, window_start in self.request_windows.items():
            # Remove clients inactive for more than 1 hour
            if now - window_start > 3600:
                inactive_clients.append(client_id)
        
        for client_id in inactive_clients:
            if client_id in self.client_buckets:
                del self.client_buckets[client_id]
            if client_id in self.request_counts:
                del self.request_counts[client_id]
            if client_id in self.request_windows:
                del self.request_windows[client_id]
        
        if inactive_clients:
            logger.info("Cleaned up inactive clients", 
                       count=len(inactive_clients))
    
    async def close(self):
        """Close rate limiter and cleanup resources."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Rate limiter closed")
