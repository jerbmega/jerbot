import asqlite
import os


async def create_table(database: str, table: str, keys: tuple):
    """
    Creates a table if it does not exist.
    - database: String corresponding to the database to operate on.
    - table: String corresponding to a table in the SQLite database.
    - keys: Tuple of keys for new table.
    """
    async with asqlite.connect(f"db/{database}.db") as conn:
        async with conn.cursor() as cursor:
            # Quick crash course:
            # - We're using SQLite 3 via an async wrapper, asqlite
            # - Parenthesis are needed to properly use these values because of the quirks associated with being async
            # - [0] is needed to get the actual result in this case
            does_exist = (
                await (
                    await cursor.execute(
                        f"SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{table}'"
                    )
                ).fetchone()
            )[0]
            if not does_exist:
                await cursor.execute(f"CREATE TABLE {table} {keys}")
                await conn.commit()


async def del_table(database: str):
    """
    Delete a table
    - database: String corresponding to the database to delete.
    """
    try:
        os.remove(f"db/{database}.db")
    except FileNotFoundError:
        pass


async def drop_table(database: str, table: str):
    """
    Drops a table from the database.
    - database: String corresponding to the database to operate on.
    - table: String corresponding to a table in the SQLite database.
    Returns True if table was successfully dropped.
    """
    async with asqlite.connect(f"db/{database}.db") as conn:
        async with conn.cursor() as cursor:
            try:
                await cursor.execute(f"DROP TABLE {table}")
                await conn.commit()
                return True
            except asqlite.OperationalError:
                return False


async def insert(
    database: str, table: str, values: tuple or str, replacements: tuple = None
):
    """
    Inserts values into a table.
    - database: String corresponding to the database to operate on.
    - table: String corresponding to a table in the SQLite database.
    - values: Tuple of values to insert into the table.
    - replacements: Optional tuple. Used if values specified are for replacement for advanced operations.
    """
    async with asqlite.connect(f"db/{database}.db") as conn:
        async with conn.cursor() as cursor:
            if replacements:
                await cursor.execute(
                    f"INSERT INTO {table} VALUES {values}", replacements
                )
            else:
                await cursor.execute(f"INSERT INTO {table} VALUES {values}")
            await conn.commit()


async def remove(database: str, table: str, exp: str):
    """
    Removes values from a table.
    - database: String corresponding to the database to operate on.
    - table: String corresponding to a table in the SQLite database.
    - exp: Expression for deletion.
    """
    async with asqlite.connect(f"db/{database}.db") as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(f"DELETE FROM {table} WHERE {exp}")
            await conn.commit()


async def update(database: str, table: str, exp: str):
    """
    Updates value in the table.
    - database: String corresponding to the database to operate on.
    - table: String corresponding to a table in the SQLite database.
    - exp: Expression for updating.
    """
    async with asqlite.connect(f"db/{database}.db") as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(f"UPDATE {table} SET {exp}")
            await conn.commit()


async def query(database: str, query: str):
    """
    Queries from the database in read-only mode.
    - database: String corresponding to the database to operate on.
    - query: String containing the query for the database.
    Returns query as a tuple if multiple variables were queried, or raw query otherwise
    """
    async with asqlite.connect(f"file:./db/{database}.db?mode=ro", uri=True) as conn:
        async with conn.cursor() as cursor:
            result = await (await cursor.execute(query)).fetchone()
            if not result:
                return None
            result = tuple(result)
            if len(result) == 1:
                result = result[0]
            return result


async def queryall(database: str, query: str):
    """
    Queries from the database in read-only mode.
    - database: String corresponding to the database to operate on.
    - query: String containing the query for the database.
    Returns a list of matching queries as tuples if multiple variables were queried, or raw list of matching queries otherwise
    """
    async with asqlite.connect(f"file:./db/{database}.db?mode=ro", uri=True) as conn:
        async with conn.cursor() as cursor:
            result = await (await cursor.execute(query)).fetchall()
            if not result:
                return None
            result = [tuple(elem) for elem in result]
            for i in range(len(result)):
                if len(result[i]) == 1:
                    result[i] = result[i][0]
            return result
