"""
Agentpy Lists Module
Content: Lists for objects, environments, and agents
"""

import numpy as np


class AttrList:
    """ Iterator of attributes from an :class:`AgentList`.

    Calls are forwarded to each entry and return a list of return values.
    Boolean operators are applied to each entry and return a list of bools.
    Arithmetic operators are applied to each entry and return a new list.
    Item assignments are forwarded to the object in the original list.
    See :class:`AgentList` for examples.
    """

    def __init__(self, source, attr=None):
        self.source = source
        self._iter_source = None
        self.attr = attr

    def __repr__(self):
        if self.attr is None:
            return f"AttrList: {list(self)}"
        else:
            return f"AttrList of '{self.attr}': {list(self)}"
        #if self.attr is None:
        #    return f"AttrList: {list.__repr__(self)}"
        #else:
        #    return f"AttrList of attribute '{self.attr}': " \
        #           f"{list.__repr__(self)}"

    def __iter__(self):
        """ Iterate through source list based on attribute. """
        if self.attr:
            a = self.attr
            return iter([getattr(o, a) for o in self.source])
            #for el in self.source:
            #    yield getattr(el, a)
        else:
            return iter(self.source)
            #for el in self.source:
            #    yield el  # return iter(self.source)

    def __getitem__(self, key):
        """ Get item from source list. """
        return getattr(self.source[key], self.attr)

    def __setitem__(self, key, value):
        """ Set item to source list. """
        setattr(self.source[key], self.attr, value)

    def __call__(self, *args, **kwargs):
        return [func_obj(*args, **kwargs) for func_obj in self]

    def __eq__(self, other):
        # TODO doesn't work with second attrlist
        return [obj == other for obj in self]

    def __ne__(self, other):
        return [obj != other for obj in self]

    def __lt__(self, other):
        return [obj < other for obj in self]

    def __le__(self, other):
        return [obj <= other for obj in self]

    def __gt__(self, other):
        return [obj > other for obj in self]

    def __ge__(self, other):
        return [obj >= other for obj in self]

    def __add__(self, v):
        if isinstance(v, AttrList):
            return AttrList([x + y for x, y in zip(self, v)])
        else:
            return AttrList([x + v for x in self])

    def __sub__(self, v):
        if isinstance(v, AttrList):
            return AttrList([x - y for x, y in zip(self, v)])
        else:
            return AttrList([x - v for x in self])

    def __mul__(self, v):
        if isinstance(v, AttrList):
            return AttrList([x * y for x, y in zip(self, v)])
        else:
            return AttrList([x * v for x in self])

    def __truediv__(self, v):
        if isinstance(v, AttrList):
            return AttrList([x / y for x, y in zip(self, v)])
        else:
            return AttrList([x / v for x in self])

    def __iadd__(self, v):
        return self + v

    def __isub__(self, v):
        return self - v

    def __imul__(self, v):
        return self * v

    def __itruediv__(self, v):
        return self / v


class ObjList(list):
    """ List of agentpy objects (models, environments, agents). """

    def __init__(self, iterable=[], model=None):
        super().__init__(iterable)
        super().__setattr__('model', model)

    @property
    def ndim(self):
        # Necessary for numpy.random.Generator.shuffle() to work
        return 1

    def __repr__(self):
        s = 's' if len(self) > 1 else ''
        return f"ObjList [{len(self)} object{s}]"

    def __setattr__(self, name, value):
        if isinstance(value, AttrList):
            # Apply each value to each agent
            for obj, v in zip(self, value):
                setattr(obj, name, v)
        else:
            # Apply single value to all agents
            for obj in self:
                setattr(obj, name, value)

    def __getattr__(self, name):
        """ Return callable list of attributes """
        return AttrList(self, attr=name)

    def call(self, method, check_alive=False, iter_kwargs=None, **kwargs):
        """ Call a method for every agent in the list.

        Arguments:
            method (str): Name of the method.
            check_alive (bool, optional):
                Skip agents that have been deleted (default False).
            iter_kwargs (dict of iterables):
                Keyword arguments that are different for every method call.
                Dictionary entries should be iterables with the same length
                as the AgentList, or the remaining agents will not be called.
            **kwargs:
                Keyword arguments that are the same for every method call.
        """
        if check_alive and iter_kwargs is None:
            return [getattr(obj, method)(**kwargs) for obj in self
                    if obj.alive]
        elif check_alive and iter_kwargs is not None:
            return [getattr(obj, method)(**kwargs,
                                         **{k: v for k, v
                                            in zip(iter_kwargs, kwargv)})
                    for obj, *kwargv in zip(objs, *iter_kwargs.values())
                    if obj.alive]
        elif not check_alive and iter_kwargs is not None:
            return [getattr(obj, method)(**kwargs,
                                         **{k: v for k, v
                                            in zip(iter_kwargs, kwargv)})
                    for obj, *kwargv in zip(objs, *iter_kwargs.values())]
        else:
            return [getattr(obj, method)(*args, **kwargs) for obj in self]

    def _default_generator(self):
        """ Try to find default number generator. """
        if self.model:
            return self.model.random
        elif len(self) > 0 and hasattr(self[0], 'model'):
            return self[0].model.random
        else:
            return np.random.default_rng()

    def select(self, selection):
        """ Returns a new :class:`AgentList` based on `selection`.

        Arguments:
            selection (list of bool): List with same length as the agent list.
                Positions that return True will be selected.
        """
        return AgentList([a for a, s in zip(self, selection) if s],
                         model=self.model)

    def random(self, n=1, replace=False, weights=None, shuffle=True,
               generator=None):
        """ Creates a random sample of agents,
        using :func:`numpy.random.Generator.choice`.
        Argument descriptions are adapted from :obj:`numpy.random`.
        Returns a new :class:`AgentList` with the selected agents.

        Arguments:
            n (int, optional): Number of agents (default 1).
            replace (bool, optional):
                Whether the sample is with or without replacement.
                Default is False, meaning that every agent can
                only be selected once.
            weights (1-D array_like, optional):
                The probabilities associated with each agent.
                If not given the sample assumes a uniform distribution
                over all agents.
            shuffle (bool, optional):
                Whether the sample is shuffled
                when sampling without replacement.
                Default is True, False provides a speedup.
            generator (numpy.random.Generator, optional):
                Random number generator.
                If none is passed, :obj:`Model.random` is used.
                If list has no model, :obj:`np.random` is used.
        """
        if not generator:
            generator = self._default_generator()
        # Choice is not applied to list directly because it would convert it to
        # a numpy array, which takes much more time than the current solution.
        indexes = generator.choice(len(self), size=n, replace=replace,
                                   p=weights, shuffle=shuffle)
        selection = AgentList([self[i] for i in indexes], model=self.model)
        return selection

    def sort(self, var_key, reverse=False):
        """ Sorts the list using :func:`list.sort`, and returns self.

        Arguments:
            var_key (str): Attribute of the lists' objects, based on which
                the list will be sorted from lowest value to highest.
            reverse (bool, optional): Reverse sorting (default False).
        """
        super().sort(key=lambda x: x[var_key], reverse=reverse)
        return self

    def shuffle(self, generator=None):
        """ Shuffles the list randomly, using :func:`generator.shuffle`.
        Returns self.

        Arguments:
            generator (numpy.random.Generator, optional):
                Random number generator.
                If none is passed, :obj:`Model.random` is used.
                If list has no model, :obj:`np.random` is used.
        """
        if not generator:
            generator = self._default_generator()
        generator.shuffle(self)
        return self


class AgentList(ObjList):
    """ List of agents.

    Attribute calls and assignments are applied to all agents
    and return an :class:`AttrList` with attributes of each agent.
    This also works for method calls, which returns a list of return values.
    Arithmetic operators can further be used to manipulate agent attributes,
    and boolean operators can be used to filter list based on agent attributes.

    Examples:

        Prepare an :class:`AgentList` with three agents::

            >>> model = ap.Model()
            >>> agents = model.add_agents(3)
            >>> agents
            AgentList [3 agents]

        The assignment operator can be used to set a variable for each agent.
        When the variable is called, an :class:`AttrList` is returned::

            >>> agents.x = 1
            >>> agents.x
            AttrList of 'x': [1, 1, 1]

        One can also set different variables for each agent
        by passing another :class:`AttrList`::

            >>> agents.y = ap.AttrList([1, 2, 3])
            >>> agents.y
            AttrList of 'y': [1, 2, 3]

        Arithmetic operators can be used in a similar way.
        If an :class:`AttrList` is passed, different values are used for
        each agent. Otherwise, the same value is used for all agents::

            >>> agents.x = agents.x + agents.y
            >>> agents.x
            AttrList of 'x': [2, 3, 4]

            >>> agents.x *= 2
            >>> agents.x
            AttrList of 'x': [4, 6, 8]

        Attributes of specific agents can be changed through setting items::

            >>> agents.x[2] = 10
            >>> agents.x
            AttrList of 'x': [4, 6, 10]

        Boolean operators can be used to select a subset of agents::

            >>> subset = agents(agents.x > 5)
            >>> subset
            AgentList [2 agents]

            >>> subset.x
            AttrList of attribute 'x': [6, 8]
    """

    def __repr__(self):
        return f"AgentList [{len(self)} agent{'s' if len(self) != 1 else ''}]"


class EnvList(ObjList):
    """ List of environments.

    Attribute calls and assignments are applied to all environments
    and return an :class:`AttrList` with attributes of each environment.
    This also works for method calls, which returns a list of return values.
    Arithmetic operators can further be used to manipulate attributes,
    and boolean operators can be used to filter list based on attributes.

    See :class:`AgentList` for examples.
    """

    def __repr__(self):
        s = 's' if len(self) > 1 else ''
        return f"EnvList [{len(self)} environment{s}]"

    def add_agents(self, *args, **kwargs):
        """ Add the same agents to all environments in the list.
        See :func:`Environment.add_agents` for arguments and keywords."""

        if self:
            new_agents = self[0].add_agents(*args, **kwargs)
            if len(self) > 1:
                for env in self[1:]:
                    env.add_agents(new_agents)
