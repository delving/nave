# -*- coding: utf-8 -*- 
import os
import tempfile
import zipfile
from os.path import expanduser

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    args = '<old schema version> <new schema version>'
    help = 'Update factory version number in Narthex File Store'

    home = expanduser("~")

    def update_zip(self, zipname, old_version, new_version, files_to_update=None):
        if files_to_update is None:
            files_to_update = ['narthex_facts.txt', 'mapping_edm.xml']

        # generate a temp file
        print(zipname, old_version, new_version)
        tmpfd, tmpname = tempfile.mkstemp(dir=os.path.dirname(zipname))
        os.close(tmpfd)
        replace_dict = {}

        rec_def_type = new_version.split('_')[0]
        factory_home = ds_path = os.path.join(self.home, "NarthexFiles", settings.FABRIC.get('ORG_ID'), "factory",
                                              rec_def_type)

        xml_fname = "{}_record-definition.xml".format(new_version)
        xsd_fname = "{}_validation.xsd".format(new_version)

        xml = os.path.join(factory_home, xml_fname)
        xsd = os.path.join(factory_home, xsd_fname)

        # create a temp copy of the archive without filename
        with zipfile.ZipFile(zipname, 'r') as zin:
            with zipfile.ZipFile(tmpname, 'w') as zout:
                zout.comment = zin.comment  # preserve the comment
                for item in zin.infolist():
                    if item.filename.endswith("_validation.xsd") or item.filename.endswith('_record-definition.xml'):
                        continue
                    elif item.filename not in files_to_update:
                        zout.writestr(item, zin.read(item.filename))
                    else:
                        clean_out = zin.read(item.filename)
                        replace_dict[item.filename] = clean_out.replace(
                                bytes(old_version, encoding="utf-8"),
                                bytes(new_version, encoding="utf-8"),
                        )

        # replace with the temp archive
        os.remove(zipname)
        os.rename(tmpname, zipname)

        # now add filename with its new data
        with zipfile.ZipFile(zipname, mode='a', compression=zipfile.ZIP_DEFLATED) as zf:
            for k, v in replace_dict.items():
                zf.writestr(k, v)
            zf.write(xml, xml_fname)
            zf.write(xsd, xsd_fname)

    def update_version_number_in_narthex_sip_zips(self, old, new, dataset_path):
        for root, dirs, files in os.walk(dataset_path):
            if root.endswith('sips'):
                for fname in files:
                    if fname.endswith('.sip.zip'):
                        zip_path = os.path.join(root, fname)
                        print("processing {}".format(fname))
                        self.update_zip(zip_path, old, new)

    def handle(self, *args, **options):
        old_version = args[0]
        new_version = args[1]
        ds_path = os.path.join(self.home, "NarthexFiles", settings.FABRIC.get('ORG_ID'))

        self.update_version_number_in_narthex_sip_zips(old_version, new_version, ds_path)

        self.stdout.write('Replaced {} with {}'.format(old_version, new_version))
