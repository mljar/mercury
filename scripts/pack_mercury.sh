#!/bin/bash

echo 'Pack Mercury'

rm -rf mercury/frontend-dist
cd frontend
yarn install
yarn local-build

cd ..
rm mercury/*.sqlite*

python setup.py sdist
