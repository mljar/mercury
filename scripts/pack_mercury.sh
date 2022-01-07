#!/bin/bash

echo 'Pack Mercury'

cd frontend
yarn install
yarn local-build

cd ..
rm mercury/*.sqlite*

python setup.py sdist