#!/usr/bin/env bash



cd deploy

rm id_rsa > /dev/null
cp ~/.ssh/id_rsa
chmod 0600 id_rsa


