import base64
from io import BytesIO
import unittest

from PIL import Image
from sqlalchemy import BigInteger, String, Text

from app.database import Base
from app.models import Player
from app.schemas import PlayerCreate, PlayerUpdate


class PlayerModelTests(unittest.TestCase):
    def test_player_table_has_bigint_id_and_bounded_name(self) -> None:
        table = Base.metadata.tables[Player.__tablename__]

        self.assertEqual(list(table.columns.keys()), ["id", "name", "avatar"])
        self.assertIsInstance(table.c.id.type, BigInteger)
        self.assertTrue(table.c.id.primary_key)
        self.assertTrue(table.c.id.autoincrement)
        self.assertIsInstance(table.c.name.type, String)
        self.assertEqual(table.c.name.type.length, 255)
        self.assertFalse(table.c.name.nullable)
        self.assertFalse(table.c.name.primary_key)
        self.assertIsInstance(table.c.avatar.type, Text)
        self.assertTrue(table.c.avatar.nullable)

    def test_player_schemas_enforce_name_bounds(self) -> None:
        player = PlayerCreate(name="Magnus")
        update = PlayerUpdate(name="Nora")

        self.assertEqual(player.name, "Magnus")
        self.assertEqual(update.name, "Nora")
        with self.assertRaises(ValueError):
            PlayerCreate(name="")
        with self.assertRaises(ValueError):
            PlayerCreate(name="x" * 256)

    def test_player_avatar_is_normalized_to_a_square_png_data_uri(self) -> None:
        source = BytesIO()
        Image.new("RGB", (320, 160), color=(120, 40, 20)).save(
            source,
            format="JPEG",
        )
        data_uri = (
            "data:image/jpeg;base64,"
            + base64.b64encode(source.getvalue()).decode("ascii")
        )

        player = PlayerCreate(name="Nora", avatar=data_uri)

        self.assertTrue(player.avatar.startswith("data:image/png;base64,"))
        normalized_bytes = base64.b64decode(player.avatar.split(",", 1)[1])
        with Image.open(BytesIO(normalized_bytes)) as image:
            self.assertEqual(image.format, "PNG")
            self.assertEqual(image.size, (200, 200))

    def test_player_avatar_rejects_unsupported_or_invalid_images(self) -> None:
        invalid = "data:image/svg+xml;base64,PHN2Zz48L3N2Zz4="
        corrupt = "data:image/png;base64,not-base64"

        with self.assertRaises(ValueError):
            PlayerCreate(name="Nora", avatar=invalid)
        with self.assertRaises(ValueError):
            PlayerCreate(name="Nora", avatar=corrupt)

    def test_player_avatar_can_be_removed_on_update(self) -> None:
        update = PlayerUpdate(avatar=None)

        self.assertIsNone(update.avatar)
        self.assertIn("avatar", update.model_fields_set)
