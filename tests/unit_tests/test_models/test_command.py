"""Test remote command models (POST /v1/global/remote/command)."""

from pytoyoda.models.endpoints.command import CommandType, RemoteCommandModel


class TestCommandType:
    """CommandType enum values."""

    def test_window_close_value(self) -> None:
        """WINDOW_CLOSE is the verified-working "power-window-close" command.

        See https://github.com/pytoyoda/pytoyoda/issues/274: on some
        vehicles/regions WINDOW_ON/WINDOW_OFF are rejected, but closing the
        windows via this value works.
        """
        assert CommandType.WINDOW_CLOSE == "power-window-close"

    def test_sound_horn_and_buzzer_warning_values(self) -> None:
        """SOUND_HORN/BUZZER_WARNING are verified-working alternatives to FIND_VEHICLE."""
        assert CommandType.SOUND_HORN == "sound-horn"
        assert CommandType.BUZZER_WARNING == "buzzer-warning"

    def test_legacy_values_still_present(self) -> None:
        """WINDOW_ON/WINDOW_OFF/FIND_VEHICLE are kept for other vehicles/regions."""
        assert CommandType.WINDOW_ON == "power-window-on"
        assert CommandType.WINDOW_OFF == "power-window-off"
        assert CommandType.FIND_VEHICLE == "find-vehicle"


class TestRemoteCommandModel:
    """RemoteCommandModel request body serialization."""

    def test_serializes_command_value(self) -> None:
        """Command serializes to its bare string value, not the enum member."""
        model = RemoteCommandModel(command=CommandType.WINDOW_CLOSE)
        assert model.model_dump(exclude_unset=True, by_alias=True) == {
            "command": "power-window-close"
        }

    def test_serializes_with_beep_count(self) -> None:
        """beepCount is included (by alias) when set via its alias."""
        model = RemoteCommandModel.model_validate(
            {"command": CommandType.SOUND_HORN, "beepCount": 2}
        )
        assert model.model_dump(exclude_unset=True, by_alias=True) == {
            "command": "sound-horn",
            "beepCount": 2,
        }
