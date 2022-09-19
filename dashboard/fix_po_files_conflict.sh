echo "Warning! It removes any translations added in this branch. Use only if untranslated strings are added"

parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )

cd "$parent_path"

git fetch origin master
git checkout origin/master -- ./src/locales/en/messages.po
git checkout origin/master -- ./src/locales/ja/messages.po
npm run extract
