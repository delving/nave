import os

from webresource import WebResource

spec_name = "test-spec"
test_uri = "urn:{}/123.jpg".format(spec_name)


def test__create_webresource__with_defaults():
    webresource = WebResource(spec=spec_name)
    assert webresource is not None
    assert webresource.base_dir == "/tmp"
    assert webresource.settings is not None
    assert webresource.org_id == "test"


def test__webresource__get_spec_dir(tmpdir):
    test_base = str(tmpdir)
    webresource = WebResource(spec="test-spec", base_dir=test_base)
    spec_dir = webresource.get_spec_dir
    assert spec_dir
    assert spec_dir.endswith(spec_name)
    assert webresource.org_id in spec_dir


def test__create_dataset_webresource_dir(tmpdir):
    test_base = str(tmpdir)
    webresource = WebResource(spec=spec_name, base_dir=test_base)
    assert webresource is not None
    assert webresource.base_dir == test_base
    assert len(os.listdir(test_base)) == 0
    webresource.create_dataset_webresource_dirs()
    assert len(os.listdir(test_base)) != 0
    assert os.listdir(test_base) == [webresource.org_id]
    assert os.path.exists(
        os.path.join(webresource.get_spec_dir, "derivatives/thumbnails")
    )


def test__webresource__create_hash():
    webresource = WebResource(spec=spec_name)
    sha256 = webresource.get_hash(test_uri)
    assert sha256
    assert sha256.startswith('d23a')


def test__webresource__get_derivative_base_path():
    webresource = WebResource(spec=spec_name)
    d_path = webresource.get_derivative_base_path(test_uri)
    assert d_path
    assert len(d_path.split('/')) == 5
    assert d_path.startswith("thumbnails")
    assert webresource.get_derivative_base_path(
        test_uri,
        kind="deepzoom"
    ).startswith("deepzoom")
