from asyncpg.connection import Connection
from asyncpg.pool import Pool
from typing import Union


class BaseRepository:
    def __init__(self, conn: Union[Connection, Pool]) -> None:
        self._conn = conn

    @property
    def connection(self) -> Union[Connection, Pool]:
        return self._conn

    async def get_connection(self):
        """Get a connection from the pool or return the single connection."""
        if isinstance(self._conn, Pool):
            return await self._conn.acquire()
        return self._conn

    async def release_connection(self, conn):
        """Release a connection back to the pool if it's a pool connection."""
        if isinstance(self._conn, Pool):
            await self._conn.release(conn)
