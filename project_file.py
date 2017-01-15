# vi: set et ts=4 sw=4 sts=4:

import yaml
from collections.abc import Iterable
import dependency_node

class InvalidYAMLObject(Exception):
    """
    Exception thrown when YAML produced an invalid object due to a syntax error
    in the config
    """
    def __init__(self,message):
        super(InvalidYAMLObject, self).__init__(message)

############################################################################

class source(yaml.YAMLObject):
    yaml_tag = "!Source"
    yaml_loader = yaml.SafeLoader

    def __getstate__(self):
        return { "name": self.name, "type":self.type, "path_pattern": self.path_pattern, "description": self.description };

    def __setstate__(self,state):
        # TODO this is a lof of python magic
        #      and might stop working at some point
        #
        # the problem here is that pyyaml does set the class values
        # via data.__dict__.update(state) where state is a dictionary
        # so the error checking via the properties is circumvented.
        # 
        # it does however check whether this serialisation function is
        # defined. If it is, than it is called.

        try:
            key = "name"
            self.name = state[key]

            key = "type"
            self.type = state[key]

            key = "path_pattern"
            self.path_pattern = state[key]

            key = "description"
            self.description = state.get(key)
        except KeyError:
            raise InvalidYAMLObject("Could not find property \""+key+"\".")
        except TypeError as e:
            raise InvalidYAMLObject("Invalid type for property \"" + key +"\": " + str(e))
        except ValueError as e:
            raise InvalidYAMLObject("Invalid value for property \"" + key +"\": " + str(e))

    def __init__(self, name, type, path_pattern, description=""):
        self.name = name
        self.type = type
        self.path_pattern = path_pattern
        self.description = description

        #self.normalise()

    def __repr__(self):
        return "{0}(name={1}, type={2}, path_pattern={3}, description={4})".format(
                    self.__class__.__name__,
                    self.name,
                    self.type,
                    self.path_pattern,
                    self.description
                    )

    # --------------------------------------------------------------------

    @property
    def name(self):
        """The name of the source"""
        return self.__name

    @name.setter
    def name(self,val):
        if not isinstance(val,str):
            raise TypeError("name can only be a string")
        self.__name = val

    @property
    def type(self):
        """The type of the source"""
        return self.__type

    @type.setter
    def type(self,val):
        if not isinstance(val,str):
            raise TypeError("type can only be a string")
        if (val == "git" or val == "svn" ):
            self.__type = val
        else:
            raise ValueError("type has to be either \"git\" or \"svn\"")

    @property
    def path_pattern(self):
        """The name of the source"""
        return self.__path_pattern 

    @path_pattern.setter
    def path_pattern(self,val):
        if not isinstance(val,str):
            raise TypeError("path_pattern can only be a string")
        self.__path_pattern = val

    @property
    def description(self):
        """The name of the source"""
        return self.__description

    @description.setter
    def description(self,val):
        if val is None:
            self.__description = ""
            return

        if not isinstance(val,str):
            raise TypeError("description can only be a string")
        self.__description = val

    # --------------------------------------------------------------------

    def default_branch(self):
        if self.type == "git":
            return "master"
        elif self.type == "svn":
            return "trunk"
        else:
            raise ValueError("Unknown Value for self.type: " + self.type)

    def checkout_command(self,params):
        """
        Generate the final checkout command to be executed substituting
        a few parameters.

        Valid parameters are:
            PROJECT         The name of the project
            BRANCH          The branch to check out
            DIRECTORY       The directory to checkout to.

        We substitute ${PARAMETER} --> value and add the branch directive
        """

        string = self.path_pattern

        for subst in [ "PROJECT" ]:
            string = string.replace("${" + subst + "}" ,str(params.get(subst)));

        # folder into which the checkout should happen
        folder = params["DIRECTORY"]
        
        if self.type == "git":
            string = "git clone '" + string + "' '" + folder + "'"
            if (params["BRANCH"] != self.default_branch()):
                string += "; git checkout '" + params["BRANCH"] + "'"
        elif self.type == "svn":
            string = "svn checkout '" + string
            if (params["BRANCH"] == self.default_branch()):
                string += "/" +  self.default_branch()
            elif (params["BRANCH"] == ""):
                pass
            else:
                string += "/branches/" + params["BRANCH"]
            string += "' '" + folder + "'"
        return string

############################################################################

class project_policy(yaml.YAMLObject):
    yaml_tag = "!ProjectPolicy"
    yaml_loader = yaml.SafeLoader

    def __getstate__(self):
        return { "name": self.name, "source":self.source, "description": self.description, 
                "branch" : self.branch };

    def __setstate__(self,state):
        # TODO see comment on source above

        try:
            key = "name"
            self.name = state[key]

            key = "source"
            self.source = state[key]

            key = "description"
            self.description = state.get(key)

            key = "branch"
            self.branch = state.get(key)
        except KeyError:
            raise InvalidYAMLObject("Could not find property \""+key+"\".")
        except TypeError as e:
            raise InvalidYAMLObject("Invalid type for property \"" + key +"\": " + str(e))
        except ValueError as e:
            raise InvalidYAMLObject("Invalid value for property \"" + key +"\": " + str(e))

    def __repr__(self):
        return "{0}(name={1}, source={2}, description={3}, branch={4})".format(
                    self.__class__.__name__,
                    self.name,
                    self.source,
                    self.description,
                    self.branch
                    )

    def __init__(self,name,source,description="", branch=None):
        self.name = name
        self.source = source
        self.description = description
        self.branch = branch

    # --------------------------------------------------------------------

    @property
    def name(self):
        """The name of the source"""
        return self.__name

    @name.setter
    def name(self,val):
        if not isinstance(val,str):
            raise TypeError("name can only be a string")
        self.__name = val

    @property
    def source(self):
        """The source to use"""
        return self.__source

    @source.setter
    def source(self,val):
        if not isinstance(val,source):
            raise TypeError("source has to be a !Source and cannot be a string")
        self.__source = val

    @property
    def description(self):
        """The name of the source"""
        return self.__description

    @description.setter
    def description(self,val):
        if val is None:
            self.__description = ""
            return

        if not isinstance(val,str):
            raise TypeError("description can only be a string")
        self.__description = val

    @property
    def branch(self):
        """The branch to check out"""
        if (self.__branch is None):
            return self.__source.default_branch()
        else:
            return self.__branch

    @branch.setter
    def branch(self,val):
        if val is None or isinstance(val,str):
            self.__branch = val
        else:
            raise TypeError("branch can only be None or a string")

    # --------------------------------------------------------------------

    def checkout_command(self,params):
        """
        Calls self.source.checkout_command(params)
        """
        return self.source.checkout_command(params)

############################################################################

class project(yaml.YAMLObject,dependency_node.dependency_node):
    yaml_tag = "!Project"
    yaml_loader = yaml.SafeLoader

    def __getstate__(self):
        return { "name": self.name, "directory": self.directory, "project_policy":self.project_policy, 
                "description": self.description, "dependencies" : list(self.dependencies),
                "branch" : self.branch };

    def __setstate__(self,state):
        # TODO see comment on Source above

        try:
            key = "name"
            self.name = state[key]

            key = "directory"
            self.directory = state.get(key)

            key = "project_policy"
            self.project_policy = state[key]

            key = "branch"
            self.branch = state.get(key)

            key = "dependencies"
            self.dependencies = state.get(key)

            key = "description"
            self.description = state.get(key)

            key = "is_enabled"
            self.is_enabled = state.get(key)
        except KeyError:
            raise InvalidYAMLObject("Could not find property \""+key+"\".")
        except TypeError as e:
            raise InvalidYAMLObject("Invalid type for property \"" + key +"\": " + str(e))
        except ValueError as e:
            raise InvalidYAMLObject("Invalid value for property \"" + key +"\": " + str(e))

    def __init__(self, name, project_policy, dependencies=[], description="", branch="", is_enabled=True):
        self.name = name
        self.project_policy=project_policy
        self.dependencies = dependencies            # also allow None
        self.description = description
        self.branch = branch
        self.is_enabled = is_enabled

    def __repr__(self):
        str1 = "{0}(name={1}, directory={2}, project_policy={3}, description={4}, branch={5}, is_enabled={6}, dependencies=".format(
                self.__class__.__name__,
                self.name,
                self.directory,
                self.project_policy,
                self.description,
                self.branch,
                self.is_enabled
                )
        for dep in self.dependencies:
            str1 += " " + str(dep)
        return str1 + " )"

    # --------------------------------------------------------------------
    # stuff needed for the dependency_node interface

    def is_fulfilled(self):
        """
        Are all conditions for this dependency fulfilled
        """
        return self.is_enabled

    def depends_on(self):
        """return an iterable of all nodes which the current one directly depends upon"""
        return self.dependencies

    # --------------------------------------------------------------------

    def enable(self):
        """
        Enable checkout of this project
        """
        self.__is_enabled = True

    def disable(self):
        """
        Disalbe checkout of this project
        """
        self.__is_enabled = False

    def enable_all(self):
        """
        Enable checkout of this project and all dependencies
        """
        # enable all dependencies:
        self.apply_dependencies(task.enable)

        # enable the root:
        self.enable()

    # --------------------------------------------------------------------

    @property
    def name(self):
        """The name of the source"""
        return self.__name

    @name.setter
    def name(self,val):
        if not isinstance(val,str):
            raise TypeError("name can only be a string")
        self.__name = val

    @property
    def directory(self):
        """The directory to checkout to"""
        if self.__directory is None:
            return self.__name
        else:
            return self.__directory

    @directory.setter
    def directory(self,val):
        if val is None:
            self.__directory = None
        else:
            if not isinstance(val,str):
                raise TypeError("directory can only be a string")
            self.__directory = val

    @property
    def project_policy(self):
        """The project_policy to use"""
        return self.__project_policy

    @project_policy.setter
    def project_policy(self,val):
        if not isinstance(val,project_policy):
            raise TypeError("source has to be a !ProjectPolicy and cannot be a string")
        self.__project_policy = val

    @property
    def description(self):
        """The name of the source"""
        return self.__description

    @description.setter
    def description(self,val):
        if val is None:
            self.__description = ""
            return

        if not isinstance(val,str):
            raise TypeError("description can only be a string")
        self.__description = val

    @property
    def is_enabled(self):
        """The name of the source"""
        return self.__is_enabled

    @is_enabled.setter
    def is_enabled(self,val):
        if val is None:
            self.__is_enabled = True
            return

        if not isinstance(val,bool):
            raise TypeError("is_enabled can only be a bool")
        self.__is_enabled = val

    @property
    def dependencies(self):
        """The other projects dependent on this project"""
        return self.__dependencies

    @dependencies.setter
    def dependencies(self,val):
        if val is None:
            self.__dependencies = []
        elif not isinstance(val,Iterable):
            raise TypeError("All members of the dependency list have to be of type !Project not string")
        else:
            for i in val:
                if not isinstance(i,project):
                    raise TypeError("All members of the dependency list have to be of type !Project not string")
            self.__dependencies = set(val)

    @property
    def branch(self):
        """The branch to check out"""
        if (self.__branch is None):
            return self.project_policy.branch
        else:
            return self.__branch

    @branch.setter
    def branch(self,val):
        if val is None or isinstance(val,str):
            self.__branch = val
        else:
            raise TypeError("branch can only be None or a string")

    # --------------------------------------------------------------------

    def checkout_command(self):
        params = {
                "BRANCH": self.branch,
                "PROJECT": self.name,
                "DIRECTORY": self.directory,
                }
        return self.project_policy.checkout_command(params);

############################################################################

class reader:
    def __init__(self,stream):
        try:
            d = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            string = "Could not parse config file: " + str(exc)

            if hasattr(exc, 'problem_mark'):
                mark = exc.problem_mark
                raise ValueError(string + ": Error at ({0}:{1})".format(mark.line +1,mark.column+1))
            else:
                raise ValueError(string)

        self.__version = d["version"]
        
        if (self.version == "1.0"):
            self.__deal_with_1_0(d)
        else:
            raise ValueError("Unknown config version: " + self.version)

    def __deal_with_1_0(self,d):
        self.__sources = d["sources"]
        self.__policies = d["project_policies"]
        self.__projects = d["projects"]
        self.__default_projects = d["default_projects"]

    @property
    def version(self):
        """The version of the projects file"""
        return self.__version

    @property
    def sources(self):
        """The sources given in the projects file"""
        return self.__sources

    @property
    def project_policies(self):
        """The project policies given in the projects file"""
        return self.__policies

    @property
    def projects(self):
        """The projects given in the projects file"""
        return self.__projects

    @property
    def default_projects(self):
        """The default projects selected for preparation"""
        return self.__default_projects
