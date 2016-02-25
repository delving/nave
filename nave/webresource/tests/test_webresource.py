import os
import shutil

from webresource.webresource import WebResource, SOURCE_DIR, CACHE_DIR, THUMBNAIL_DIR, DEEPZOOM_DIR

spec_name = "test-spec"
test_uri = "urn:{}/123.jpg".format(spec_name)
test_cache_uri = "http://example.com/123.jpg"


def test__create_webresource__with_defaults():
    webresource = WebResource(spec=spec_name)
    assert webresource is not None
    assert webresource.base_dir == "/tmp"
    assert webresource.settings is not None
    assert webresource.org_id == "vagrant"


def test__webresource__get_spec_dir(tmpdir):
    test_base = str(tmpdir)
    webresource = WebResource(spec=spec_name, base_dir=test_base)
    spec_dir = webresource.get_spec_dir
    assert spec_dir is not None
    assert spec_dir.endswith(spec_name)
    assert webresource.org_id in spec_dir


def test__create_dataset_webresource_dir(tmpdir):
    test_base = str(tmpdir)
    webresource = WebResource(spec=spec_name, base_dir=test_base)
    assert webresource is not None
    assert webresource.base_dir == test_base
    assert len(os.listdir(test_base)) == 0
    assert not webresource.exist_webresource_dirs
    webresource.create_dataset_webresource_dirs()
    assert len(os.listdir(test_base)) != 0
    assert os.listdir(test_base) == [webresource.org_id]
    assert os.path.exists(
        os.path.join(webresource.get_spec_dir, THUMBNAIL_DIR)
    )
    assert webresource.exist_webresource_dirs


def test__webresource__create_hash():
    webresource = WebResource(spec=spec_name)
    sha256 = webresource.get_hash(test_uri)
    assert sha256
    assert sha256.startswith('d23a')


def test__webresource__get_derivative_base_path():
    webresource = WebResource(spec=spec_name)
    d_path = webresource.get_derivative_base_path(test_uri)
    assert d_path
    assert len(d_path.split('/')) == 6
    assert d_path.startswith(THUMBNAIL_DIR)
    assert webresource.get_derivative_base_path(
        test_uri,
        kind=DEEPZOOM_DIR
    ).startswith(DEEPZOOM_DIR)


def test__webresource__is_cached():
    webresource = WebResource(spec=spec_name, uri=test_uri)
    assert not webresource.is_cached
    webresource = WebResource(spec=spec_name, uri=test_cache_uri)
    assert webresource.is_cached


def test__webresource__path_to_uri(tmpdir, settings):
    test_base = str(tmpdir)
    test_path = os.path.join(test_base, settings.ORG_ID, spec_name, SOURCE_DIR, "123.jpg")
    webresource = WebResource(spec=spec_name, base_dir=test_base, path=test_path)
    assert webresource.path_to_uri == test_uri
    # TODO: implement test for cache url too


def test__webresource__clean_uri():
    webresource = WebResource(spec=spec_name, uri=test_uri)
    assert not webresource.clean_uri.startswith("urn:")

    webresource = WebResource(spec=spec_name, uri=test_cache_uri)
    assert webresource.clean_uri.startswith("http://")


def test__webresource__uri_to_path(tmpdir, settings):
    test_base = str(tmpdir)
    test_path = os.path.join(test_base, settings.ORG_ID, spec_name, SOURCE_DIR, "123.jpg")
    webresource = WebResource(spec=spec_name, base_dir=test_base, uri=test_uri)
    assert webresource.uri_to_path is not None
    assert webresource.uri_to_path == test_path

    webresource = WebResource(spec=spec_name, base_dir=test_base, uri=test_cache_uri)
    assert webresource.is_cached
    assert webresource.uri_to_path is not None
    assert webresource.uri_to_path != test_path


def test__webresource__source_path_exists(tmpdir, settings):
    test_base = str(tmpdir)
    webresource = WebResource(spec=spec_name, base_dir=test_base, uri=test_uri)
    webresource.create_dataset_webresource_dirs()
    test_image = os.path.join(os.path.dirname(__file__), 'nasa_ares_logo.png')
    shutil.copy(test_image, webresource.uri_to_path)
    assert os.path.exists(webresource.uri_to_path)
    assert webresource.exists_source

    webresource = WebResource(spec=spec_name, base_dir=test_base, uri='urn:{}/fake_image.jpg'.format(webresource.spec))
    assert not os.path.exists(webresource.uri_to_path)
    assert not webresource.exists_source


def test__webresource__get_deepzoom_uri(settings):
    webresource = WebResource(spec=spec_name, uri=test_uri)
    deepzoom_uri = webresource.get_deepzoom_uri
    assert deepzoom_uri is not None
    assert settings.RDF_BASE_URL in deepzoom_uri
    assert webresource.get_derivative_base_path(kind=DEEPZOOM_DIR) in deepzoom_uri
    assert deepzoom_uri.endswith(".tif.dzi")
