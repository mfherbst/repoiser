# 
# Small helpers
# 
noCPUs() {
	lscpu | awk '$1 == "CPU(s):" { print $2; printed=1; exit }; END { if (printed==0) print 1 }'
}

die () {
	echo $@ >&2
	exit 1
}

#
# Dealing with the failed file
#
cleanup_failedfile() {
	if have_failedfile; then
		FAILED=$(< $FAILEDFILE | sed 's/^/   /g')
		rm "$FAILEDFILE"
	fi

	if [ "$FAILED" ]; then
		echo
		echo -----------------------------------
		echo
		echo "The following tests have failed:"
		echo "$FAILED"
		return 1
	fi
	return 0
}

create_failedfile() {
	# Creates a temporary file to store test results
	# Adds the variable FAILEDFILE to the environment
	# which contains the path to the file
	FAILEDFILE=$(mktemp)	
}

have_failedfile() {
	# test if a FAILEDFILE has been set up
	[ -f "$FAILEDFILE" ]
}

#
# checkout/obtaining the repos:
#

allRepos() {
	get_repos ".mrconfig" "" ""
	echo "The use of the allRepos function is deprecated" >&2
}

default_config() {
	# get the name of the default .mrconfig to use
	if [ -f ".default_config" ] ; then
		cat .default_config
		return
	fi
	echo ".mrconfig"
}

get_repos() {
	# extract all repos from an mrconfig file
	# $1:  the .mrconfig file to use
	# $2:  the repos to exclude
	# $3:  only echo these repos (if they exist, else print error)
	# 
	# echos the repo folders 
	local FILE=$1
	local EXCLUDE=$2
	local ONLY=$3

	if [ ! -f "$FILE" ]; then
		echo "Could not find .mrconfig file $FILE" >&2
		echo "Did you run \"setup_checkout.sh\" ?" >&2
		return 1
	fi

	# TODO implement only and exclude
	# in the form repo:repo2:repo3

	< "$FILE" awk -v "only=$ONLY" -v "exclude=$EXCLUDE" '
		BEGIN {
			split(only,aonly,":")
			split(exclude,aexclude,":")
		}

		function is_excluded(a) {
			for (i in aexclude) {
				if (match(a,aexclude[i])) {
					return 1
				}
			}
			return 0
		}

		function matches_only(a) {
			if (length(aonly) == 0) {
				return 1
			}

			for (i in aonly) {
				if (match(a,aonly[i])) {
					return 1
				}
			}
			return 0
		}

		function conditional_print(a) {
			if (is_excluded(a)) {
				return
			}

			if (matches_only(a)) {
				print a
			}
		}

		/^[[:space:]]*\[/ {
	       		sub(/^\[/,"")
			sub(/\]$/,"")

			conditional_print($0)
		}
		'
	return $?
}

#
# properties of repos
#
have_build() {
	# Do we have a build directory in the repo $1
	[ -d "$1/build" ]
}

get_build_dir() {
	# Echo the name of the build directory of repo $1
	# if there is one 
	# if there is none, returns 1
	
	have_build "$1" || return 1
	echo "$1/build"
}

has_test_failed() {
	# expect the output of the tests on stdin
	# exit 1 if any of the tests failed
	grep -iqE "(fail|error)"
}

#
# actions on repos
#
configure_repo() {
	# $1: folder containing the repository
	# $2 to $@: options for configure script
	# configures a repository in folder $1
	# return status of configure

	local repo=$1
	shift

	if [ ! -d "$repo" ]; then
		echo "Could not find directory $repo" >&2
		return 1
	fi

	(
		echo
		echo "#################################"
		echo "#-- Configuring $(basename "$repo")"
		echo "#################################"

		cd "$repo"

		if [ -x "./configure" ]; then
			./configure $@ 
			RET=$?
		else
			if ! mkdir build; then
				echo "Could not make build directory" >&2
				return 1
			fi
			cd build
			cmake $@ ..
		fi
		return $RET
	)
}

build_repo() {
	# $1: folder containing the repository
	# $2 to $@: options for make 
	# builds a repository in folder $1
	# return status of make
	#
	# sets BUILDANYTHING to 1 if there have been any files built
	# else BUILDANYTHING is set to 0

	local repo=$1
	shift

	# did we build anything?
	BUILDANYTHING=0

	if [ ! -d "$repo" ]; then
		echo "Could not find directory $repo" >&2
		return 1
	fi

	#  create a timestamp to compare to
	TIMESTAMPFILE=$(mktemp)
	(
		echo
		echo "#################################"
		echo "#-- Building $(basename "$repo")"
		echo "#################################"

		cd "$repo/build"
		make $@
	)
	RET=$?
	# do we have any updates:
	find "$repo/build" -type f -newer "$TIMESTAMPFILE" -print -quit | grep -q "^" && BUILDANYTHING=1
	rm "$TIMESTAMPFILE"
	return $RET
}

run_test() {
	# $1: folder containing the repository
	# run the tests for this repository
	#
	# if any of them fails, return 1

	if ! have_failedfile; then
		echo "run_test needs a failedfile to be configured. Run create_failedfile beforehand." >&2
		exit 1
	fi

	local repo=$1

	if [ ! -d "$repo" ]; then
		echo "Could not find directory $repo" >&2
		return 1
	fi

	(
		RET=0

		echo
		echo "#################################"
		echo "#-- Testing $(basename "$repo")"
		echo "#################################"
		cd "$repo/tests"

		#TODO:  call make test or ctest if available 

		find ../build/tests/ -maxdepth 1 -type f -executable | while read line; do
			echo "Running $line ..."
			$line |& tee ${line}.out | sed 's/^/   /g'
			if < ${line}.out has_test_failed; then
				echo "$line" >> "$FAILEDFILE"
				RET=1
			fi
			rm ${line}.out
			sleep 2
			echo
		done
		return $RET
	)
}
