#!/usr/bin/env python3
# vi: set et ts=4 sw=4 sts=4:

import argparse
import project_file
from dependency_node import dependency_node,build_batches,build_recursive_dependency_set
from collections.abc import Iterable
import itertools

def build_mrconfig(projects):
    """Resolve all dependencies and build mrconfig for projects"""

    if not isinstance(projects,Iterable):
        raise TypeError("projects needs to be an Itarable of project_file.projects")

    # get all recursive dependencies:
    recursive_dependencies = build_recursive_dependency_set(projects)

    # arrange them in batches:
    batches = build_batches(recursive_dependencies)

    # and flatten them:
    batches = list(itertools.chain.from_iterable(batches))

    string=""
    for p in batches:
        string += "[" + p.directory + "]\n"
        if p.description != "":
            string += "# " + p.description + "\n"
        string += "checkout = " + p.checkout_command() + "\n\n"

    return string

parser = argparse.ArgumentParser(description="Generate an .mrconfig file from a project.yaml file, resolving the dependencies properly")
parser.add_argument("config", metavar="project.yaml", type=str, help="The path to project.yaml file")

args = parser.parse_args()

with open(args.config) as f:
    config = project_file.reader(f)
    print(build_mrconfig(config.default_projects))
