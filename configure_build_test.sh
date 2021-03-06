#!/bin/bash

. $(dirname $0)/common.lib.sh || exit 1

usage() {
	cat <<- EOF
	$(basename "$0") [ --help | -h | <Options> ]

	Configure, make and test the libraries and projects in an .mrconfig file

	--config <.mrconfig>
	Specify the .mrconfig to use in order to obtain the list of
	repositories to test, default: $(default_config)

	-j <N>
	--jobs <N>
	The number of jobs to use for building, default on this machine: $(noCPUs)

	-k
	--keep-going
	If configuring/making a repo fails, do not exit, but proceed to the next
	on the list
	Cancels the effect of -S, the last one counts.

	-S
	--no-keep-going
	--strict
	--stop
	Stop compiling/making as soon as an error happens
	Cancels the effect of a -k, the last one counts.

	--tests
	Always run the tests (even if no file changed during the make)

	--doxygen
	--docs
	Build the doxygen documentation as well if it is available.

	--dry-run
	Only perform a dry run (print what is done, but don't do it)
	(TODO: not fully implemented: Currently just prints a summary and exits)

	--conf-opt "<options for configure / cmake>"
	Pass these options to configure or cmake. Note that they have to be a
	single string.

	--exclude <repo1>:<repo2>: ...
	Exclude the repos matching these patterns when doing the tasks

	--only <repo1>:<repo2>: ...
	Only do the tasks on the repos matching these patterns
	EOF
}

cleanup() {
	cleanup_failedfile || exit 1
}

print_settings() {
	cat <<- EOF
	Options to configure:        $CONF_OPT
	Options to make:             $MAKE_OPT  (use -n, -j, -k, -S to change)
	Strict / keep going:         $STRICT / $KEEP_GOING    (use -S, -k to change)
	Generate docs with doxygen:  $DOXYGEN        (use --docs to change)

	Reading repos from:          $CONFIGFILE
	Repos considered and their order:      (use --exclude or --only to change):
	$(echo "$REPOS" | sed 's/^/    /')

	EOF
}

die_or_keep_going() {
	# die only if keep-going is not set
	[ "$KEEP_GOING" == "n" ] && die $@
	echo $@ >&2
}

#--------------------------------------------------------------------

FORCE_TESTS=n	# force running the tests even if no compilation took place
KEEP_GOING=n	# keep running if errors occurr in compilation
STRICT=n	# stop as soon as error happens
NJOBS=$(noCPUs)			# number of jobs to use
CONFIGFILE=$(default_config)	# config file to use
EXCLUDE=""			# repos to exclude
ONLY=""				# only work on these repos
CONF_OPT=""			# configure options
MAKE_OPT="-j $NJOBS -k"		# make options
DRYRUN="n"			# just have a dry run
DOXYGEN=n			# build doxygen documentation

while [ "$1" ]; do
	case "$1" in 
		--help|-h)
			usage
			exit 0
			;;
		--keep-going|-k) 
			KEEP_GOING=y
			STRICT=n
			;;
		--no-keep-going|-S|--strict|--stop)
			KEEP_GOING=n
			STRICT=y
			;;
		--tests)
			FORCE_TESTS=y
			;;
		--jobs|-j)
			shift
			NJOBS=$1
			;;
		--config)
			shift
			[ -f "$1" ] || die "Cannot find file: $1"
			CONFIGFILE="$1"
			;;
		--exclude)
			shift
			EXCLUDE="$1"
			;;
		--doxygen|--docs)
			DOXYGEN=y
			;;
		--only)
			shift
			ONLY="$1"
			;;
		--conf-opt)
			shift
			CONF_OPT="$1"
			;;
		--dry-run|-n)
			DRYRUN=y
			;;
		*)
			die "Unrecognised option: $1"
			;;

	esac
shift
done

# build the make options:
MAKE_OPT="-j $NJOBS"
if [ "$STRICT" == "y" ]; then
	MAKE_OPT="$MAKE_OPT -S"
else
	MAKE_OPT="$MAKE_OPT -k"
fi
[ "$DRYRUN" == "y" ] && MAKE_OPT="$MAKE_OPT --dry-run"

# get the list of repos we consider:
REPOS=$(get_repos "$CONFIGFILE" "$EXCLUDE" "$ONLY") || die "Could not obtain list of repos"

print_settings
[ "$DRYRUN" == "y" ] && exit 0

create_failedfile
trap cleanup EXIT

echo
echo ----------------------------------
echo

for repo in $REPOS; do
	if [ ! -d "$repo" ]; then
		die "Could not find directory $repo"
		continue
	fi

	# configure:
	if ! have_build "$repo"; then
		if ! configure_repo "$repo" $CONF_OPT; then
			die_or_keep_going "Could not configure repository $repo."
			continue
		fi
	fi	

	# now build:
	if ! build_repo "$repo" $MAKE_OPT; then
		die_or_keep_going "Could not build repo $repo"
		continue
	fi

	# if there have been updates (i.e. if any files were made):	
	if [[ "$BUILDANYTHING" == "1" || "$FORCE_TESTS" == "y" ]]; then
		run_test "$repo"
	else 
		echo
		echo "skipping tests for $repo (use --tests to force tests)"
	fi

	if [ "$DOXYGEN" == "y" ] && have_doxyfile "$repo"; then
		run_doxygen "$repo"
	fi
done

exit # exit code determined by cleanup_failedfile
