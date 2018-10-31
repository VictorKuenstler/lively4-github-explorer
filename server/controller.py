from psycopg2.sql import SQL
import responder

from server.postgres.postgres_db import PostgresDbDictCursor

api = responder.API()

@api.route('/test')
def test(req, resp):
    with PostgresDbDictCursor() as cursor:
        query = SQL('SELECT * FROM table_sizes')
        cursor.execute(query)
        response = [dict(row) for row in cursor]

    resp.media = response
