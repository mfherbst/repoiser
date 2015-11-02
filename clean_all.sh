#!/bin/bash

. $(dirname $0)/common.lib.sh || exit 1

usage() {
	cat <<- EOF
	$(basename "$0") [ --help | -h | <Options> ]

	Remove the build folder for all libraries and projects in 
	an .mrconfig file.

	--config <.mrconfig>
	Specify the .mrconfig to use in order to obtain the list of
	repositories to test, default: $(default_config)

	--exclude <repo1>:<repo2>: ...
	Exclude the repos matching these patterns when doing the tasks

	--only <repo1>:<repo2>: ...
	Only do the tasks on the repos matching these patterns
	EOF
}

#--------------------------------------------------------------------

CONFIGFILE=$(default_config)	# config file to use
EXCLUDE=""			# repos to exclude
ONLY=""				# only work on these repos

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

for repo in $(get_repos "$CONFIGFILE" "$EXCLUDE" "$ONLY"); do
	if have_build "$repo"; then
		rm -r "$(get_build_dir "$repo")"
	fi
done
exit 0
