#!/bin/bash

echo 'Dual Pack Mercury'

# clear dist directories
rm -rf mercury/frontend-dist
rm -rf mercury/frontend-single-site-dist

cd frontend
yarn install
yarn local-build

# change in the code
cp src/Root.tsx src/Root_backup
sed 's/<Routes/<SingleRoute/g' src/Root_backup > src/Root.tsx 
# create new package.json 
mv package.json package_backup
head -4 package_backup > package.json 
echo "  \"homepage\": \"http://mydomain.com/example/to/replace\"," >> package.json
tail -n +5 package_backup >> package.json

# run build for single-site
yarn local-single-site-build

# clean
mv package_backup package.json
mv src/Root_backup src/Root.tsx

cd ..
rm mercury/*.sqlite*

python setup.py sdist
