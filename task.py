#! /usr/bin/env python3
# vi: set et ts=4 sw=4 sts=4:
import dependency_node

class task(dependency_node.dependency_node):
    """
    Small test class to test the dependency node interface

    Can be given an arbitrary payload as the task to be done
    """

    def __init__(self,payload,*deps):
        self.__deps = set(deps)
        self.__payload = payload
        self.__enabled = True

    def set_dependencies(self,*deps):
        self.__deps = set(deps)

    def is_enabled(self):
        return self.__enabled
    
    def is_fulfilled(self):
        return self.is_enabled()

    def enable(self):
        self.__enabled = True

    def disable(self):
        self.__enabled = False

    def depends_on(self):
        """return an iterable of all nodes which the current one directly depends upon"""
        return self.__deps

    def payload(self):
        return self.__payload

    def __repr__(self):
        string = str(self.payload())  + "["
        if self.is_fulfilled():
            string += "X"
        else:
            string += " "
        string += "]"

        if not self.has_dependencies():
            return string
    
        return string + " -> " + str(self.depends_on()) 

    def enable_all(self):
        """
        Enable this task and all dependencies
        """
        # enable all dependencies:
        self.apply_dependencies(task.enable)

        # enable the root:
        self.enable()

if __name__ == "__main__":
    def __test(prestring,actual,expected):
        if (expected != actual):
            raise SystemExit(prestring+ ": " + str(actual) + " where " + str(expected) + " was expected.")

    a = task("a")
    b = task("b",a)
    c = task("c",b,a)

    # per default all should be enabled:
    __test("a enabled default",a.is_enabled(),True)
    __test("b enabled default",b.is_enabled(),True)
    __test("c enabled default",c.is_enabled(),True)

    # hence all dependencies are fulfilled
    __test("a.dependencies_fulfilled",a.dependencies_fulfilled(),True)
    __test("b.dependencies_fulfilled",b.dependencies_fulfilled(),True)
    __test("c.dependencies_fulfilled",c.dependencies_fulfilled(),True)

    # now disable b:
    b.disable()
    __test("a.dependencies_fulfilled",a.dependencies_fulfilled(),True)
    __test("b.dependencies_fulfilled",b.dependencies_fulfilled(),True)
    __test("c.dependencies_fulfilled",c.dependencies_fulfilled(),False)

    # now enable all guys again:
    c.enable_all()
    __test("a.dependencies_fulfilled",c.dependencies_fulfilled(),True)

    # test the batches builder:
    __test("c.build_batches())", c.build_batches(),[ {a},{b},{c}])

    d = task("d",b)
    __test("batches for union(c.deps d.deps)", dependency_node.build_batches( c.depends_on_recursive().union(d.depends_on_recursive()).union({c,d})), [{a},{b},{c,d}])

    # have an example with a cyclic dependency:
    e = task("e",a)
    a.set_dependencies(e)
    try:
        __test("a.dependencies_fulfilled",a.dependencies_fulfilled(),None)
        raise SystemExit("Did not detect an CyclicGraphException as required")
    except dependency_node.CyclicGraphException as g:
        pass

