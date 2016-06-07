from webresource import utils


def test__create_dataset_folders__success():
    folders = utils.create_dataset_folders("test-spec")
    assert folders