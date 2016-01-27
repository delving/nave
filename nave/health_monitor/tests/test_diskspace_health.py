from health_check.backends.base import ServiceReturnedUnexpectedResult, ServiceUnavailable
import pytest

from health_monitor.plugin_health_check import DiskSpaceHealth


def test__disk_space__enough_free_space():
    plugin = DiskSpaceHealth()
    assert plugin.get_disk_space_status(total=249124880384, used=77308284928, free=171554451456)


def test__disk_space__warning_disk_space():
    plugin = DiskSpaceHealth()
    with pytest.raises(ServiceReturnedUnexpectedResult):
        plugin.get_disk_space_status(total=249124880384, used=186843660288, free=62281220096)


def test__disk_space__not_enough_free_space():
    plugin = DiskSpaceHealth()
    with pytest.raises(ServiceUnavailable):
        plugin.get_disk_space_status(total=249124880384, used=236668636364, free=12456244019)

