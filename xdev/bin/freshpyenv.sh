#!/usr/bin/env bash
__libdoc__="
NAME
     freshpyenv -- quick python environment for testing packages in docker

SYNOPSIS
     freshpyenv [COMMAND] [-i IMAGE_NAME] [-h]

DESCRIPTION
    Create a fresh environment to test a Python package

OPTIONS
     COMMAND:
         Defaults to 'start'. Can also be 'images'

     -i, --image=IMAGE_NAME
          The docker image to use

     -v, --version
            print the version information

     -h, --help
            view this help message

EXAMPLES
    ~/code/xdev/xdev/bin/freshpyenv.sh images
    ~/code/xdev/xdev/bin/freshpyenv.sh --help
    ~/code/xdev/xdev/bin/freshpyenv.sh --image python:3.10

AUTHOR
     Jon Crall <erotemic@gmail.com.com>
"
if [[ ${BASH_SOURCE[0]} == "$0" ]]; then
	# Running as a script
	set -euo pipefail
fi
if [[ "${FRESHPYENV_TRACE+x}" != "" ]]; then
	set -x
fi
__devdoc__='
For a "developer install" hack it like this:

python -c "import xdev, ubelt; ubelt.symlink((ubelt.Path(xdev.__file__).parent / \"bin/freshpyenv.sh\"), ubelt.Path(ubelt.find_exe(\"freshpyenv.sh\")).delete(), verbose=1)"
'


# print this script's usage message to stderr
usage() {
	cat <<-EOF >&2
		usage: freshpyenv [COMMAND] [-i image] [-h]
	EOF
}

warn() {
	local fmt="$1"
	shift
	# shellcheck disable=SC2059
	printf "freshpyenv: $fmt\n" "$@" >&2
}


readonly FRESH_PYENV_VERSION="0.1.0"


# Default settings
IMAGE_NAME="__default__"
COMMAND="start"


inside_docker_setup(){
    echo 'Setup fresh docker env'

    set -x
    # Will need to chmod things afterwords
    export PIP_CACHE_DIR=/pip_cache
    echo $PIP_CACHE_DIR
    chmod -R o+rw $PIP_CACHE_DIR
    chmod -R o+rw $PIP_CACHE_DIR
    chmod -R g+rw $PIP_CACHE_DIR
    USER=$(whoami)
    chown -R "$USER" $PIP_CACHE_DIR
    git clone /io "$HOME"/repo

    cd "$HOME"/repo

    # If we are on manylinux, we should give the user the ability to choose the
    # python version.
    if [ -f /opt/python/cp311-cp311/bin/python ]; then
        PYEXE=/opt/python/cp311-cp311/bin/python
    else
        PYEXE=python
    fi

    # Make a virtualenv
    PYVER=$("$PYEXE" -c "import sys; print('{}{}'.format(*sys.version_info[0:2]))")
    export PYVER
    "$PYEXE" -m pip install virtualenv
    "$PYEXE" -m virtualenv "venv$PYVER"

    set +x

    # Write the venv setup to the bashrc so it is activated when
    # the interactive session starts
    echo "source \"venv$PYVER/bin/activate\"" >> "$HOME"/.bashrc

    #pip install pip -U
    #pip install pip setuptools -U

    echo "
Fresh development environment has been setup. 

You can now run some variant to install your repo.

# FULL STRICT VARIANT
pip install -e .[all-strict,headless-strict] -v

# FULL LOOSE VARIANT
pip install -e .[all,headless] -v

# MINIMAL STRICT VARIANT
pip install -e .[runtime-strict,tests-strict] -v

# MINIMAL LOOSE VARIANT
pip install -e .[tests] -v
"
}


list_available_images(){
    echo "Listing generally known images"
    echo "
    * pypy
    * python:3.10
    * quay.io/pypa/manylinux2014_x86_64
    "

    echo "Listing known images in local gitlab-ci.yml"
    cat .gitlab-ci.yml | yq -r 'with_entries(select(.key | startswith(".image")))'
}




start_docker(){
    SCRIPT_DPATH=$( cd -- "$( dirname -- "$(realpath -- "${BASH_SOURCE[0]}")" )" &> /dev/null && pwd )
    if [[ "$IMAGE_NAME" == "__default__" ]]; then
        IMAGE_NAME=$(cat .gitlab-ci.yml | yq -r '.".image_python3_10"')
    fi
    docker run \
        --volume "$PWD":/io:ro \
        --volume "$SCRIPT_DPATH":/_scriptdir:ro \
        --volume "$HOME"/.cache/pip:/pip_cache \
        -it "$IMAGE_NAME" \
        /bin/bash -c "source _scriptdir/freshpyenv.sh && inside_docker_setup && /bin/bash"
}

freshpyenv_main(){

    echo "Parse args"
	# parse COMMAND line options
	while [[ "${1:-}" != '' ]]; do
		case $1 in
		images)
            COMMAND="images"
            echo "COMMAND = $COMMAND"
			;;
		-i | --image)
			IMAGE_NAME=$2
			shift
            ;;
		--image=*)
			IMAGE_NAME=${1#*=}
            ;;
		-v | --version)
			printf 'freshpyenv %s\n' "$FRESH_PYENV_VERSION"
			exit 0
			;;
		-h | --help | -\?)
            echo "$__libdoc__"
			exit 0
			;;
		--*)
			warn 'unknown option -- %s' "${1#--}"
			usage
			exit 1
			;;
		*)
			warn 'unknown option -- %s' "${1#-}"
			usage
			exit 1
			;;
		esac
		shift
	done

    echo "Parsed arguments"
    echo " * COMMAND = $COMMAND"
    echo " * IMAGE_NAME = $IMAGE_NAME"

    if [[ "$COMMAND" == "start" ]]; then
        start_docker
    elif [[ "$COMMAND" == "images" ]]; then
        list_available_images
    else
        echo "Unknown COMMAND = $COMMAND"
        exit 1
    fi
}


# bpkg convention
# https://github.com/bpkg/bpkg
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
	# We are sourcing the library
	#export -f freshpyenv_main
	echo "Sourcing the library"
	#export -p
else
	# Executing file as a script
    echo "Running main"
	freshpyenv_main "${@}"
	exit $?
fi
