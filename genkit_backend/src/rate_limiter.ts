/**
 * Sliding-window RPM governor enforcing FinOps zero-spend quota ceilings (<= 15 RPM).
 */
export interface RateLimitDecision {
  allowed: boolean;
  remaining: number;
  retryAfterSeconds: number;
  limit: number;
}

export class SlidingWindowRpmLimiter {
  private readonly maxRequests: number;
  private readonly windowMs: number;
  private readonly nowFn: () => number;
  private timestamps: number[] = [];

  constructor(
    maxRequests = 15,
    windowMs = 60_000,
    nowFn: () => number = () => Date.now()
  ) {
    // Hard FinOps cap: never exceed 15 RPM even if misconfigured.
    this.maxRequests = Math.max(1, Math.min(15, Math.floor(maxRequests)));
    this.windowMs = Math.max(1_000, Math.floor(windowMs));
    this.nowFn = nowFn;
  }

  private prune(now: number): void {
    const cutoff = now - this.windowMs;
    while (this.timestamps.length > 0 && this.timestamps[0] <= cutoff) {
      this.timestamps.shift();
    }
  }

  peekRemaining(): number {
    this.prune(this.nowFn());
    return Math.max(0, this.maxRequests - this.timestamps.length);
  }

  tryAcquire(): RateLimitDecision {
    const now = this.nowFn();
    this.prune(now);

    if (this.timestamps.length < this.maxRequests) {
      this.timestamps.push(now);
      return {
        allowed: true,
        remaining: Math.max(0, this.maxRequests - this.timestamps.length),
        retryAfterSeconds: 0,
        limit: this.maxRequests,
      };
    }

    const oldest = this.timestamps[0];
    const waitMs = Math.max(1_000, oldest + this.windowMs - now);
    return {
      allowed: false,
      remaining: 0,
      retryAfterSeconds: Math.ceil(waitMs / 1000),
      limit: this.maxRequests,
    };
  }
}
