# Legacy database artifacts

The runnable application uses only the async SQLAlchemy engine in
`app/database.py`. The Python files in this directory are compatibility shims
and do not create another engine.

`skillswap_db.backup` is the original PostgreSQL custom-format dump retained as
an archival hackathon artifact. It is not loaded by the application.
