#!/bin/bash

. $(dirname $0)/common.lib.sh || exit 1

usage() {
	cat <<- EOF
	$(basename "$0") [ --help | -h | <Options> ] <project.yaml>

	Generate the .mrconfig file which contains the libraries and projects
	to be checked out. This .mrconfig file is generated from a <project.yaml> 
	file which describes the projects to be checked out and their dependencies.

	--config <.mrconfig>
	Specify the name of the .mrconfig file to be generated. This name is stored
	in the file .default_config, such that the other scripts in this bundle
	automatically know where to look for the .mrconfig, default: $(default_config)
	EOF
}

preliminary_checks() {
	ERRORS=0
	if ! type mr &> /dev/null; then
		echo "The mr program is not installed. " >&2
		echo "Please ask your administrator to install the \"mr\" package" >&2
		echo
		ERRORS=1
	fi

	if [ -f "$CONFIGFILE" ]; then
		echo "Configfile \"$CONFIGFILE\" already exists." >&2
		echo "Please choose a different file name using --config or delete it" >&2
		echo
		ERRORS=1
	fi

	if [ "$ERRORS" == "1" ]; then
		echo "Some fatal errors occurred. Check above messages." >&2
		exit 1
	fi
	return 0
}


config_hd_projects() {
	# generate the part of the config that checks out stuff from Heidelberg
	# $1: Checkout pattern to use, e.g. git clone 'ssh://gitte@ccsvn.iwr.uni-heidelberg.de:42022/${LIBRARY}.git'
	# ${PROJECT} gets substituted by the apropriate project

	for project in libwfa libadc adcman; do 
		# TODO do some dependancy resolutios
		# dependancy file is projects.deps
		:
	done
}

#--------------------------------------------------------------------

PROJ_YAML=""
CONFIGFILE=$(default_config)

while [ "$1" ] ; do
	case "$1" in 
		-h|--help)
			usage
			exit 0
			;;
		--config)
			shift
			CONFIGFILE=$1
			;;

		*)
			if [ -f "$1" ]; then
				PROJ_YAML="$1"
			else
				echo "Unrecognised option or invalid file: $1" >&2
				exit 1
			fi
			;;
	esac
	shift
done

if [ -z "$PROJ_YAML" ]; then
	echo "Please specify a <project.yaml> file." >&2
	exit 1
fi

if [ !  -r "$PROJ_YAML" ]; then
	echo "Invalid <project.yaml> file: $PROJ_YAML" >&2
	exit 1
fi

# check if mr exists, we do not overwrite ...
preliminary_checks

$(dirname $0)/generate_mrconfig.py "$PROJ_YAML" > "$CONFIGFILE" || exit $?

# Since generation was successful, store this
echo "$CONFIGFILE" > .default_config

read -p "Should the repositories be checked out using \"mr update --config $CONFIGFILE\"?  (Y/n)" RET
[ -z "$RET" ] && RET="y"
if [ "$RET" == "y" ]; then
	mr --config "$CONFIGFILE" update
	exit $?
fi
exit 0
