import io
import json
import re
from urlparse import parse_qs, urlparse
from celery import chain
from django.conf import settings

from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
import requests
import sys


class Command(BaseCommand):
    args = '<wetransfer_urls>'
    help = """
    You should have a we transfer address similar to
    https://www.wetransfer.com/downloads/XXXXXXXXXX/YYYYYYYYY/ZZZZZZZZ

    So execute:
    python wetransfer.py -u
    https://www.wetransfer.com/downloads/XXXXXXXXXXXXXXXXXXXXXXXXX/YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY/ZZZZZ

    """

    option_list = BaseCommand.option_list + (
        make_option('--delete',
                    action='store_true',
                    dest='delete',
                    default=False,
                    help='Delete all records and dataset before saving'),
    )

    DOWNLOAD_URL_PARAMS_PREFIX = "downloads/"
    CHUNK_SIZE = 1024

    def download(self, file_id, recipient_id, security_hash):
        url = "https://www.wetransfer.com/api/v1/transfers/{0}/download?recipient_id={1}&security_hash={2}&password=&ie=false".format(
            file_id, recipient_id, security_hash)
        r = requests.get(url)
        download_data = json.loads(r.content)

        print("Downloading {0}...".format(url))
        if 'direct_link' in download_data:
            content_info_string = \
            parse_qs(urlparse(download_data['direct_link']).query)['response-content-disposition'][0]
            file_name = re.findall('filename="(.*?)"', content_info_string)[0].encode('ascii', 'ignore')
            r = requests.get(download_data['direct_link'], stream=True)
        else:
            file_name = download_data['fields']['filename']
            r = requests.post(download_data['formdata']['action'], data=download_data["fields"], stream=True)

        file_size = int(r.headers["Content-Length"])
        output_file = open(file_name, 'w')
        counter = 0
        for chunk in r.iter_content(chunk_size=self.CHUNK_SIZE):
            if chunk:
                output_file.write(chunk)
                output_file.flush()
                sys.stdout.write(
                    '\r{0}% {1}/{2}'.format((counter * self.CHUNK_SIZE) * 100 / file_size, counter * self.CHUNK_SIZE,
                                            file_size))
                counter += 1

        sys.stdout.write('\r100% {0}/{1}\n'.format(file_size, file_size))
        output_file.close()
        print "Finished! {0}".format(file_name)

    def extract_params(self, url):
        """
            Extracts params from url
        """
        params = url.split(self.DOWNLOAD_URL_PARAMS_PREFIX)[1].split('/')
        [file_id, recipient_id, security_hash] = ['', '', '']
        if len(params) > 2:
            # The url is similar to https://www.wetransfer.com/downloads/XXXXXXXXXX/YYYYYYYYY/ZZZZZZZZ
            [file_id, recipient_id, security_hash] = params
        else:
            # The url is similar to https://www.wetransfer.com/downloads/XXXXXXXXXX/ZZZZZZZZ
            # In this case we have no recipient_id
            [file_id, security_hash] = params

        return [file_id, recipient_id, security_hash]

    def extract_url_redirection(self, url):
        """
            Follow the url redirection if necesary
        """
        return requests.get(url).url

    def handle(self, *args, **options):
        urls = args
        for url in urls:
            url = self.extract_url_redirection(url)
            [file_id, recipient_id, security_hash] = self.extract_params(url)
            self.download(file_id, recipient_id, security_hash)
        self.stdout.write('Successfully written {} wetransfer files'.format(len(urls)))
