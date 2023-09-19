"""Common mocks for Viseron tests."""


import datetime
from typing import Any, Callable, Generator
from unittest.mock import MagicMock

import pytest
from sqlalchemy import insert
from sqlalchemy.orm import Session

from viseron.components.storage.models import Files, FilesMeta, Recordings


class MockComponent:
    """Representation of a fake component."""

    def __init__(self, component, setup_component=None):
        """Initialize the mock component."""
        self.__name__ = f"viseron.components.{component}"
        self.__file__ = f"viseron/components/{component}"

        self.name = component
        if setup_component is not None:
            self.setup_component = setup_component


class MockCamera(MagicMock):
    """Representation of a fake camera."""

    def __init__(  # pylint: disable=dangerous-default-value
        self,
        identifier="test_camera_identifier",
        resolution=(1920, 1080),
        extension="mp4",
        access_tokens=["test_access_token", "test_access_token_2"],
        **kwargs,
    ):
        """Initialize the mock camera."""
        super().__init__(
            recorder=MagicMock(),
            identifier=identifier,
            resolution=resolution,
            extension=extension,
            access_tokens=access_tokens,
            **kwargs,
        )


def return_any(cls):
    """Mock any return value."""

    class Any(cls):
        """Mock any return value."""

        def __eq__(self, other):
            return True

    return Any()


class BaseTestWithRecordings:
    """Test class that provides a database with recordings."""

    _get_db_session: Callable[[], Session]
    _now: datetime.datetime

    def insert_data(self, get_session: Callable[[], Session]):
        """Insert data used tests."""
        with get_session() as session:
            for i in range(15):
                timestamp = self._now + datetime.timedelta(seconds=5 * i)
                filename = f"{int(timestamp.timestamp())}.m4s"
                session.execute(
                    insert(Files).values(
                        tier_id=0,
                        camera_identifier="test",
                        category="recorder",
                        path=f"/test/{filename}",
                        directory="test",
                        filename=filename,
                        size=10,
                        created_at=timestamp,
                    )
                )
                session.execute(
                    insert(FilesMeta).values(
                        path=f"/test/{filename}",
                        meta={"m3u8": {"EXTINF": 5}},
                        created_at=timestamp,
                    )
                )
            session.execute(
                insert(Recordings).values(
                    camera_identifier="test",
                    start_time=self._now + datetime.timedelta(seconds=17),
                    end_time=self._now + datetime.timedelta(seconds=27),
                    created_at=self._now + datetime.timedelta(seconds=17),
                    thumbnail_path="/test/test1.jpg",
                )
            )
            session.execute(
                insert(Recordings).values(
                    camera_identifier="test",
                    start_time=self._now + datetime.timedelta(seconds=35),
                    end_time=self._now + datetime.timedelta(seconds=55),
                    created_at=self._now + datetime.timedelta(seconds=35),
                    thumbnail_path="/test/test2.jpg",
                )
            )
            session.commit()
            yield

    @pytest.fixture(autouse=True, scope="function")
    def setup_get_db_session(
        self, get_db_session: Callable[[], Session]
    ) -> Generator[None, Any, None]:
        """Insert data used by all tests."""
        BaseTestWithRecordings._get_db_session = get_db_session
        BaseTestWithRecordings._now = datetime.datetime.now()
        yield from self.insert_data(get_db_session)
