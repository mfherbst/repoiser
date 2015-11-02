#!/bin/bash

. $(dirname $0)/common.lib.sh || exit 1

usage() {
	cat <<- EOF
	$(basename "$0") [ --help | -h | <Options> ]

	Test the libraries and projects in an .mrconfig file

	--config <.mrconfig>
	Specify the .mrconfig to use in order to obtain the list of
	repositories to test, default: $(default_config)

	--exclude <repo1>:<repo2>: ...
	Exclude all repos matching these patterns when running the tests

	--only <repo1>:<repo2>: ...
	Only run the tests for the repos matching these patterns

	EOF
}

cleanup() {
	cleanup_failedfile || exit 1
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

create_failedfile
trap cleanup EXIT

for repo in $(get_repos "$CONFIGFILE" "$EXCLUDE" "$ONLY"); do
	if ! have_build "$repo"; then
		echo "skipping testing $repo (no build folder)"
		continue
	fi
	run_test "$repo"
done

exit # exit code determined by cleanup_failedfile
