# -*- coding: utf-8 -*-
from .poset import NotLeq, Poset
from .space_product import SpaceProduct
from contracts import contract
from contracts.utils import indent, raise_desc
from mocdp.exceptions import do_extra_checks
import itertools
import collections

__all__ = [
    'PosetProduct',
]


class PosetProduct(SpaceProduct, Poset):
    """ A product of Posets with the product order. """

    @contract(subs='seq($Poset)')
    def __init__(self, subs):
        if not isinstance(subs, collections.Iterable):
            msg = 'PosetProduct expects a sequence of Posets.'
            raise_desc(ValueError, msg, subs=subs)
        subs = tuple(subs)
        SpaceProduct.__init__(self, subs)

    def leq(self, a, b):
        if do_extra_checks():
            self.belongs(a)
            self.belongs(b)

        for sub, x, y in zip(self.subs, a, b):
            if not sub.leq(x, y):
                return False
        return True

    def join(self, a, b):
        assert isinstance(a, tuple), a
        assert isinstance(b, tuple), b
        res = []
        for sub, x, y in zip(self.subs, a, b):
            res.append(sub.join(x, y))
        return tuple(res)

    def meet(self, a, b):
        res = []
        for sub, x, y in zip(self.subs, a, b):
            res.append(sub.meet(x, y))
        return tuple(res)

    def check_leq(self, a, b):
        if do_extra_checks():
            self.belongs(a)
            self.belongs(b)
        problems = []
        for i, (sub, x, y) in enumerate(zip(self.subs, a, b)):
            try:
                sub.check_leq(x, y)
            except NotLeq as e:
                msg = '#%d (%s): %s ≰ %s.' % (i, sub, x, y)
                msg += '\n' + indent(str(e).strip(), '| ')
                problems.append(msg)
        if problems:
            msg = 'Leq does not hold.\n'
            msg = "\n".join(problems)
            raise_desc(NotLeq, msg, self=self, a=a, b=b)

    def get_top(self):
        return tuple([s.get_top() for s in self.subs])

    def get_bottom(self):
        return tuple([s.get_bottom() for s in self.subs])

    def get_minimal_elements(self):
        s = [_.get_minimal_elements() for _ in self.subs]
        return set(itertools.product(*tuple(s)))

    def get_test_chain(self, n):
        """
            Returns a test chain of length n
        """
        chains = [s.get_test_chain(n) for s in self.subs]
        res = zip(*tuple(chains))
        return res


