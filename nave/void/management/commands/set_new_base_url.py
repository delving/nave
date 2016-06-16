# -*- coding: utf-8 -*- 
import os
from os.path import expanduser
import tempfile
import zipfile

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    args = '<old_base_url path>'
    help = """Update base_url in Narthex File Store.
New base url is assumed to be in settings.py - RDF_BASE_URL.
Params: <old_base_url path>
    """
    
    home = expanduser("~")

    @staticmethod
    def update_zip(zipname, old_base_url, new_base_url, files_to_update=['narthex_facts.txt', 'mapping_edm.xml']):
        # generate a temp file
        tmpfd, tmpname = tempfile.mkstemp(dir=os.path.dirname(zipname))
        os.close(tmpfd)
        replace_dict = {}

        # create a temp copy of the archive without filename
        with zipfile.ZipFile(zipname, 'r') as zin:
            with zipfile.ZipFile(tmpname, 'w') as zout:
                zout.comment = zin.comment # preserve the comment
                for item in zin.infolist():
                    print(item.filename)
                    if item.filename not in files_to_update:
                        zout.writestr(item, zin.read(item.filename))
                    else:
                        clean_out = zin.read(item.filename)
                        replace_dict[item.filename] = clean_out.replace(
                            bytes(old_base_url, encoding="utf-8"),
                            bytes(new_base_url, encoding="utf-8"),
                        )

        # replace with the temp archive
        os.remove(zipname)
        os.rename(tmpname, zipname)

        # now add filename with its new data
        with zipfile.ZipFile(zipname, mode='a', compression=zipfile.ZIP_DEFLATED) as zf:
            for k, v in replace_dict.items():
                print(k)
                zf.writestr(k, v)

    def update_base_url_in_narthex_sip_zips(self, old, new, dataset_path):
        for root, dirs, files in os.walk(dataset_path):
            if root.endswith('sips'):
                for fname in files:
                    if fname.endswith('.sip.zip'):
                        zip_path = os.path.join(root, fname)
                        print("processing {}".format(fname))
                        self.update_zip(zip_path, old, new)

    def handle(self, *args, **options):
        old_base_url = args[0]
        if not old_base_url.startswith("http://"):
            old_base_url = "http://{}".format(old_base_url)
        new_base_url = settings.RDF_BASE_URL
        ds_path = os.path.join(self.home, "NarthexFiles", settings.ORG_ID, "datasets")
        if len(args) > 1:
            ds_path = args[1]

        self.update_base_url_in_narthex_sip_zips(old_base_url, new_base_url, ds_path)

        self.stdout.write('Replaced {} with {}'.format(old_base_url, new_base_url))
