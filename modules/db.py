import sqlite3
global c, conn

conn = sqlite3.connect('jerbot-neo.db')
conn.row_factory = lambda cursor, row: row[0]
c = conn.cursor()

def try_create_table(table: str, keys: tuple):
    """
    Creates a table if it does not exist.
    :param table: String corresponding to a table in the SQLite database.
    :param keys: Tuple of keys for new table.
    :return: False if table exists or could not be created, True if created
    """
    try:
        c.execute(f'CREATE TABLE {table} {keys}')
        conn.commit()
        return True
    except sqlite3.OperationalError:
        return False


def insert(table: str, values: tuple):
    """
    Inserts values into a table.
    :param table: String corresponding to a table in the SQLite database.
    :param values: Tuple of values to insert into the table.
    :return: False if data could not be inserted, True if inserted
    """
    c.execute(f'INSERT INTO {table} VALUES {values}')
    conn.commit()

def remove(table:str, exp: str):
    """
    Removes values from a table.
    :param table: String corresponding to a table in the SQLite database.
    :param exp: Expression for deletion.
    """
    c.execute(f'DELETE FROM {table} WHERE {exp}')
    conn.commit()

def query(query: str):
    """
    Queries from the database.
    Dangerous. DO NOT EXPOSE to a user command.
    :param query: String containing the query for the database.
    :return: fetchall() from query
    """
    c.execute(query)
    return c.fetchall()
