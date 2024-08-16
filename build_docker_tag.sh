#!/bin/bash

# Get git information and build docker image

if [[ $# -gt 0 ]] ; then
    echo "usage: $0 [-h]"
    echo "Builds a docker image from tagged source, and embeds git info. Run from source directory."
    echo
    echo "For a tagged commit vX.Y.Z, the docker image will be tagged as X.Y.Z."
    echo
    exit 1
fi

# Get git information
status=$( git status -s )

# status should be empty if the repository is clean
if [[ ! -z "$status" ]] ; then
    echo "Repository is not clean - see git status"
    exit 1
fi

gitRemote=$( git remote get-url origin )

# Get the git hash or tag
hash=$( git rev-parse HEAD )

# See if there's a tag
gitTag=$( git describe --tags --abbrev=0 --exact-match $hash 2>/dev/null || echo "" )

if [[ -z "$gitTag" ]]; then
    echo "No tag found for commit $hash"
    exit 1
fi

# Check that the git tag satisfies the format vX.Y.Z
if [[ ! $gitTag =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Tag $gitTag does not match vX.Y.Z format"
    exit 1
fi

dockerVersion=${gitTag:1}

dockerTag="cookpa/synthseg-mask:${dockerVersion}"

# Build the docker image
docker build -t "$dockerTag" . \
    --build-arg GIT_REMOTE="$gitRemote" \
    --build-arg GIT_COMMIT="$gitTag" \
    --build-arg DOCKER_IMAGE_TAG="$dockerTag" \
    --build-arg DOCKER_IMAGE_VERSION="$dockerVersion"

if [[ $? -ne 0 ]] ; then
    echo "Docker build failed - see output above"
    exit 1
else
    echo
    echo "Build successful: $dockerTag"
    echo
fi
