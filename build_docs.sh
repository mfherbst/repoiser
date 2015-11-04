#!/bin/bash

. $(dirname $0)/common.lib.sh || exit 1

usage() {
	cat <<- EOF
	$(basename "$0") [ --help | -h | <Options> ]

	Build the documentation for all projects in an .mrconfig file

	--config <.mrconfig>
	Specify the .mrconfig to use in order to obtain the list of
	repositories to test, default: $(default_config)

	--exclude <repo1>:<repo2>: ...
	Exclude all repos matching these patterns when running the tests

	--only <repo1>:<repo2>: ...
	Only run the tests for the repos matching these patterns
	EOF
}

#--------------------------------------------------------------------

CONFIGFILE=$(default_config)
EXCLUDE=""
ONLY=""

while [ "$1" ]; do
	case "$1" in 
		"--help"|"-h")
			usage
			exit 0
			;;
		"--config")
			shift
			[ -f "$1" ] || die "Cannot find file: $1"
			CONFIGFILE="$1"
			;;
		"--exclude")
			shift
			EXCLUDE="$1"
			;;
		"--only")
			shift
			ONLY="$1"
			;;
		*)
			die "Unrecognised option: $1"
			;;
	esac
	shift
done

if ! type doxygen &> /dev/null; then
	echo "Could not find doxygen executable. Please install doxygen." >&2
	exit 1
fi


for repo in $(get_repos "$CONFIGFILE" "$EXCLUDE" "$ONLY"); do
	if have_doxyfile "$repo"; then
		run_doxygen "$repo" "verbose"
	else
		echo "Skipping building docs for $repo since there was not a unique Doxyfile"
	fi
done

exit 0
