# OELP

## Setup

Current files in the virtual environment `/venv` were set up by 
```py
    python3 -m venv venv
    source venv/bin/activate

    pip install "fastapi[all]" uvicorn
```

* `/venv` was added to `.gitignore`.

* Database installation - installed `postgresql` `postgresql-contrib` and optionally `pgAdmin`.  
    - After this made a database and user  in `psql` for the API's use.
    - created a database and granted all permissions in it to the API user.

After this installed ORM and database driver
```py
    pip install "sqlalchemy[asyncio]" psycopg[binary]
```


## Stuff used

- **pydantic-settings** - loading from `.env`
- **SQLAlchemy** - ORM
- **psycopg** - database driver
- **pydantic** - validation

Authentication libs - passlib, python-jose  
```py
pip install "passlib[bcrypt]" python-jose
```

`config.py` - loads from `.env`

For `pgvector` import
```py
    pip install pgvector
```