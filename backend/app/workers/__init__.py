"""Background worker processes for the App-Buildify platform.

Workers run either as in-process asyncio tasks during the platform's
``lifespan`` startup (when ``NOTIFICATION_WORKER_INPROCESS=true`` in
monolith mode) or as standalone processes (distributed mode, or
monolith mode with the env var off). See ADR-002 for placement rules.
"""
