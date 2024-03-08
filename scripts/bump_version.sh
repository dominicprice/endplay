#!/usr/bin/env bash

usage() {
	echo "usage: bump_version.sh [-h] -p|-m|-M"
	exit 1
}

PATCH=""
MINOR=""
MAJOR=""

while [ -n "$1" ]; do
	case "$1" in
	-h)
		usage
		exit 0
		;;
	-p) PATCH="yes" ;;
	-m) MINOR="yes" ;;
	-M) MAJOR="yes" ;;
	*)
		usage
		exit 1
		;;
	esac
	shift
done

ENDPLAY_VERSION="$(poetry version -s)"

# display version
if [ -z "$PATCH$MINOR$MAJOR" ]; then
	echo "$ENDPLAY_VERSION"
	exit 0
fi

if [ -n "$(git status --porcelain)" ]; then
	echo "git worktree is not clean, commit all changes before updating version"
	exit 1
fi

# bump version
IFS='.' read -r -a PARTS <<<"$ENDPLAY_VERSION"
if [ -n "$MAJOR" ]; then
	PARTS[0]=$((PARTS[0] + 1))
	PARTS[1]=0
	PARTS[2]=0
elif [ -n "$MINOR" ]; then
	PARTS[1]=$((PARTS[1] + 1))
	PARTS[2]=0
elif [ -n "$PATCH" ]; then
	PARTS[2]=$((PARTS[2] + 1))
else
	usage
	exit 1
fi
VERSION="${PARTS[0]}.${PARTS[1]}.${PARTS[2]}"

# update pyproject.toml
(poetry version "$VERSION")

# update config.py
sed -i "s/^__version__ = .*/__version__ = \"${PARTS[0]}.${PARTS[1]}.${PARTS[2]}\"/g" 'src/endplay/config.py'
sed -i "s/^__version_info__ = .*/__version_info__ = (${PARTS[0]}, ${PARTS[1]}, ${PARTS[2]})/g" 'src/endplay/config.py'

# commit version and create git tag
git add pyproject.toml
git commit -m "bump version to $VERSION [skip ci]"
git tag -a "v$VERSION" -m "Version $VERSION"
