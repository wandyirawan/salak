# Salak Search — Architecture Decision

## Goal
Search feature for Salak inventory app on potato VPS (2 CPU, 1-2GB RAM) that scales to EC2 mid-tier later.

## Current Approach: PostgreSQL ILIKE + GIN Index (Phase 1) ✅

✅ Applied via migration `004_add_search_index.sql`
✅ GIN trigram index on `products.name` and `products.sku`
✅ `ILIKE '%search%'` — no extra services, zero extra RAM

## Future: SQLite FTS5 (Phase 2)

When product count hits 10k+, add background index:

```
POST /products → FastAPI → PostgreSQL → HTTP 200
                ↓
                Background worker (thread)
                ↓
                SQLite FTS5 (26MB/30k docs)
```

### FTS5 Setup
```sql
CREATE VIRTUAL TABLE IF NOT EXISTS fts_products
USING fts5(id, name, sku, description, tokenize='porter unicode61');
PRAGMA journal_mode=WAL;
```

### Worker Thread
```python
def fts_worker():
    q = NanoQueue("postgresql://...")
    while True:
        task = q.dequeue()
        # sync to FTS5
        conn.execute("INSERT OR REPLACE INTO fts_products ...", task["id"])
```

## Future: Meilisearch (Phase 3)

On EC2 with 4+ CPU and spare RAM:

```env
MEILISEARCH_ENABLED=true
```

Swap SQLite FTS5 → Meilisearch behind same abstract interface. No code changes to routes.

## Dual-Mode Config

```python
# config.py
MEILISEARCH_ENABLED = os.getenv("MEILISEARCH_ENABLED", "false").lower() == "true"

# search/base.py — abstract class
class SearchEngine(ABC):
    @abstractmethod
    def search(self, query: str) -> list: ...

# search/sqlite_fts.py / search/meilisearch.py — implementations
engine = MeiliSearch() if MEILISEARCH_ENABLED else SQLiteFTS()
```

## Performance Expectations (2 CPU VPS)

| Metric | ILIKE (now) | FTS5 (next) | Meilisearch (future) |
|--------|-------------|-------------|----------------------|
| Search latency | ~2ms | <15ms | <5ms |
| Extra RAM | 0 | ~30MB | 500MB+ |
| Extra services | 0 | 0 (in-process) | 1 (sidecar) |
| Sync lag | 0 (direct) | ~50ms (queue) | ~50ms (queue) |

## Files to Create (when moving to Phase 2)

```
search/
├── __init__.py
├── base.py            # abstract class
├── sqlite_fts.py      # FTS5 implementation
└── meilisearch.py     # Meilisearch implementation
queue/
└── worker.py          # background thread
config.py              # MEILISEARCH_ENABLED reader
```

## Decision Log

| Date | Decision |
|------|----------|
| 2026-05-17 | Phase 1: PostgreSQL ILIKE + GIN trigram index. Migration 004 applied. ✅ |
| TBD | Phase 2: SQLite FTS5 + nano-queue when products > 10k |
| TBD | Phase 3: Meilisearch on EC2 |
