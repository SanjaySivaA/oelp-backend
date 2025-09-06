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
Authentication libs - passlib, python-jose  
```py
pip install "passlib[bcrypt]" python-jose
```

`config.py` - loads from `.env`

For `pgvector` import
```py
    pip install pgvector
```

For enabling vector in database connect to the database and
```sql
    CREATE EXTENSION IF NOT EXISTS vector;
```

Alembic
```py
    pip install alembic
```

Generated a migration using(Probably don't have to do it again)  
It makes a script to apply changes to the database?
```
    alembic revision --autogenerate -m "Initial migration"
```
Applying changes(running the script)
```
    alembic upgrade head
```
**Generate the script and apply migration whenever `models.py` is changed.**


## Stuff used

- **pydantic-settings** - loading from `.env`
- **SQLAlchemy** - ORM
- **psycopg** - database driver
- **pydantic** - validation
