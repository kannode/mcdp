from abc import ABCMeta, abstractmethod
from contracts import contract
from mocdp.configuration import get_conftools_nameddps
from mocdp.posets import PosetProduct


__all__ = [
    'NotConnected',
    'NamedDP',
    'dp_from_ndp',
]

class NotConnected(Exception):
    pass


class NamedDP():
    """ A DP with names """
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_dp(self):
        pass

    @abstractmethod
    def check_fully_connected(self):
        # Raise notConnected
        pass

    def is_fully_connected(self):
        try:
            self.check_fully_connected()
        except NotConnected:
            return False
        else:
            return True

    @abstractmethod
    @contract(returns='list(str)')
    def get_fnames(self):
        pass

    @abstractmethod
    @contract(returns='list(str)')
    def get_rnames(self):
        pass

    @abstractmethod
    @contract(rname=str)
    def get_rtype(self, rname):
        pass

    @abstractmethod
    @contract(fname=str)
    def get_ftype(self, fname):
        pass

    def repr_long(self):
        return self.__repr__()

    def get_ftypes(self, signals):
        # Returns the product space
        types = [self.get_ftype(s) for s in signals]
        return PosetProduct(tuple(types))

    def get_rtypes(self, signals):
        # Returns the product space
        types = [self.get_rtype(s) for s in signals]
        return PosetProduct(tuple(types))


def dp_from_ndp(ndp):
    """ Unwrap """
    _, ndp = get_conftools_nameddps().instance_smarter(ndp)
    # unwrap
    return ndp.get_dp()
