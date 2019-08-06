import sqlite3
global c, conn

conn = sqlite3.connect('jerbot-neo.db')
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
    :param values: Tuple of values to insert into new table.
    :return: False if data could not be inserted, True if inserted
    """
    c.execute(f'INSERT INTO {table} VALUES {values}')
    conn.commit()


def query(query: tuple):
    """
    Queries from the database.
    :param query: Tuple containing the query for the database.
    :return: fetchall() from query
    """
    c.execute(query)
    return c.fetchall()