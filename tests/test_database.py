import unittest

from sqlalchemy import BigInteger, String

from app.database import Base
from app.models import Player


class PlayerModelTests(unittest.TestCase):
    def test_player_table_has_bigint_id_and_bounded_name(self) -> None:
        table = Base.metadata.tables[Player.__tablename__]

        self.assertEqual(list(table.columns.keys()), ["id", "name"])
        self.assertIsInstance(table.c.id.type, BigInteger)
        self.assertTrue(table.c.id.primary_key)
        self.assertTrue(table.c.id.autoincrement)
        self.assertIsInstance(table.c.name.type, String)
        self.assertEqual(table.c.name.type.length, 255)
        self.assertFalse(table.c.name.nullable)
        self.assertFalse(table.c.name.primary_key)
