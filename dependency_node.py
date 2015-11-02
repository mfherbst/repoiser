# vi: set et ts=4 sw=4 sts=4:

from abc import ABCMeta, abstractmethod
from collections.abc import Iterable

class CyclicGraphException(Exception):
    """
    Exception thrown when a circular dependency is detected when parsing the dependency graph
    """
    def __init__(self,message):
        super(CyclicGraphException, self).__init__(message)

class DepedencyResolutionError(Exception):
    """
    Exception thrown when some dependencies could nod be resolved
    attribute deps containes the list of unresolved dependencies
    """
    def __init__(self,deps):
        super(DepedencyResolutionError, self).__init__("Some dependencies could not be resolved")
        self.deps = deps

class dependency_node: #(metaclass=ABCMeta):
    """A node of an dependency graph that only supports downward traversal
    i.e. traversal towards the nodes it depends upon."""

#    @abstractmethod
    def depends_on(self):
        """return an iterable of all nodes which the current one directly depends upon"""
        pass

#    @abstractmethod
    def is_fulfilled(self):
        """Is this dependency fulfilled"""
        pass

    # ------------------------------------------

    class _AbortApply(Exception):
        """
        Exception thrown if an apply call is to be aborted
        """
        def __init__(self,value):
            super(dependency_node._AbortApply, self).__init__("apply call has been aborted.")
            self.value = value

    def apply_dependencies(self,f,*args,op=(lambda x,y: None), init=None):
        """
        Apply the method f to all dependencies in turn.

        f should take an object of type dependency_node as first argument
        all other *args are passed on to f.

        Each time the result of the method is accumulated using the 
        acc function. The inital value is init.
        It is assumed that acc is symmetric.
        Per default acc just accepts any input and returns None and 
        init is None as well.

        Note that the function is not applied to the root node
        """
        return self._apply_all_inner(self,f,*args,op=op, is_root_node=True,init=init)

    def _apply_all_inner(self,root,f,*args,
            op=(lambda x,y: None), init=None, is_root_node=False):
        """
        root:    reference to the root node (to check for circles)

        f:       function to apply
        args:    args for the function f
        is_root_node:  is the current self the root node?

        op:      accumulator operation to use
        init:    value accumulator should be initialised with
        """

        val = init

        # check if current self is the root, althogh we already traversed the tree
        if (not is_root_node and self == root):
            raise CyclicGraphException("Circular dependencies detected.")

        # do depth-first tree traversal:
        for dep in self.depends_on():
            val =  dep._apply_all_inner(root,f,*args, op=op, init=val)

        if is_root_node:
            # f should not be applied to the root node
            return val
        else:
            return op(val, f(self,*args) )

    def has_dependencies(self):
        if self.depends_on() is None:
            return False
        elif len(self.depends_on()) == 0:
            return False
        return True

    def dependencies_fulfilled(self):
        """check whether all dependencies are fulfilled"""

        # The dependency of a node is fulfilled if it is enabled and
        # 
        check = lambda c: c.is_fulfilled()

        def acc_op(x,y):
            if x and y:
                return True
            else:
                raise dependency_node._AbortApply(False)

        try:
            return self.apply_dependencies(check,op=acc_op, init=True)
        except dependency_node._AbortApply as a:
            return a.value

    def depends_on_recursive(self):
        """Get a set of all direct or indirect dependencies"""
        depends = lambda s: s.depends_on()
        union = lambda s,t : s.union(t)
        return self.apply_dependencies(depends,op=union,init=self.depends_on())

    def build_batches(self):
        """
        Parse the dependency tree of this dependency node and return
        a list of sets of dependency_node objects.

        Each set represents a batch of dependencies that should be fulfilled
        before proceeding to the next set/batch, usually this is because one or
        more of the items in the next batch requires items of the first batch
        as a dependency.

        The current node (self) will be at the very top, ie. the last batch to be
        processed.

        Effectively calls the global dependency_node.build_batches function
        with self.depends_on_recursive() as the argument
        """
        return build_batches(self.depends_on_recursive().union({self}))

def build_recursive_dependency_set(root_nodes,include_roots=True):
    """
    Build a set of nodes that contains the given nodes and all their dependencies

    include_roots=False   do not include the root nodes given in the iterable nodes
    """
    if not isinstance(root_nodes,Iterable):
        raise TypeError("root_nodes needs to be an Itarable of dependency_nodes")

    recursive_dependencies = set()
    for p in root_nodes:
        if not isinstance(p,dependency_node):
            raise TypeError("root_nodes needs to be an Itarable of dependency_nodes")
        
        # add recursive dependencies to set
        recursive_dependencies.update(p.depends_on_recursive())

    if include_roots:
        recursive_dependencies.update(root_nodes)

    return recursive_dependencies

def build_batches(nodes):
    """
    Parse the dependency tree of this dependency node and return
    a list of sets of dependency_node objects.

    Each set represents a batch of dependencies that should be fulfilled
    before proceeding to the next set/batch, usually this is because one or
    more of the items in the next batch requires items of the first batch
    as a dependency.

    The current node (self) will be at the very top, ie. the last batch to be
    processed.
    """
    # This code is adapted from
    # https://breakingcode.wordpress.com/2013/03/11/an-example-dependency-resolution-algorithm-in-python/

    if not isinstance(nodes,Iterable):
        raise TypeError("nodes has to be an iterable of dependency_node objects")

    # object to store the return
    ret = []

    # build a dict from the input nodes to the set of dependencies,
    # which are currently unresolved
    nodes_to_unres_deps = dict( (node, set(node.depends_on()) ) for node in nodes )

    while len(nodes_to_unres_deps) > 0:
        # get the set of all nodes with no dependencies and which describe themself fulfilled dependencies:
        ready = { node for node, dependencies in nodes_to_unres_deps.items() if (len(dependencies) == 0 and node.is_fulfilled()) }

        # If there are none, we have a circular dependency somewhere
        if len(ready) == 0:
            raise DepedencyResolutionError(nodes_to_unres_deps.keys)

        # mark the ready guys as fulfilled dependencies:
        for node in ready:
            # remove the nodes
            del nodes_to_unres_deps[node]
        for deps in nodes_to_unres_deps.values():
            # update the dependencies
            deps.difference_update(ready)

        # add the batches to the list:
        ret.append( { node for node in ready } )

    return ret
