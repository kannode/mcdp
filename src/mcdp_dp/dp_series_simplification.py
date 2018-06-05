# -*- coding: utf-8 -*-
from abc import ABCMeta, abstractmethod

from contracts import contract
from contracts.utils import raise_desc, raise_wrapped, check_isinstance
from mcdp import logger
from mcdp.development import do_extra_checks, mcdp_dev_warning
from mcdp.exceptions import DPInternalError
from mcdp_posets import PosetProduct
from mcdp_utils_indexing.get_it_test import compose_indices, get_id_indices

from .dp_constant import Constant
from .dp_flatten import Mux, get_R_from_F_coords
from .dp_identity import Identity
from .dp_limit import Limit
from .dp_parallel import Parallel
from .dp_parallel_simplification import make_parallel
from .dp_series import Series

__all__ = [
    'make_series',
]


class SeriesSimplificationRule(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def applies(self, dp1, dp2):
        """ Returns true if it applies. """

    def execute(self, dp1, dp2):
        """ Returns the simplified version. """
        #         try:
        res = self._execute(dp1, dp2)
        #         except DPInternalError:
        #             raise
        #         except BaseException as e:
        #             msg = 'Error while executing Series simplification rule.'
        #             raise_wrapped(DPInternalError, e, msg, rule=self)

        #         print('\n\nExecuting simplification %s' % (type(self).__name__))
        #         print('dp1----\n%s' % dp1.repr_long())
        #         print('dp2----\n%s' % dp2.repr_long())
        #         print('result-----\n%s' % res.repr_long())

        if do_extra_checks():
            dp0 = Series(dp1, dp2)
            try:
                check_same_spaces(dp0, res)
            except AssertionError as e:
                msg = 'Invalid Series simplification rule.'
                raise_wrapped(DPInternalError, e, msg, rule=self)

        return res

    @abstractmethod
    def _execute(self, dp1, dp2):
        """ Returns an equivalent DP to Series(dp1, dp2) """


class RuleEvaluateMuxTimesLimit(SeriesSimplificationRule):
    """

        if

            Series(a, b)

        and

            a = Mux
            b = Limit

        then we can just evaluate it pointwise.

    """

    def applies(self, dp1, dp2):
        return isinstance(dp1, Mux) and isinstance(dp2, Limit)

    def _execute(self, dp1, dp2):
        check_isinstance(dp1, Mux)
        check_isinstance(dp2, Limit)
        r = dp2.get_value()
        f = dp1.amap_dual(r)
        F = dp1.get_fun_space()

        res = Limit(F, f)
        #         print('dp1: %s -> %s   dp2: %s -> %s ' % (dp1.get_fun_space(),dp1.get_res_space(),
        #                                                   dp2.get_fun_space(), dp2.get_res_space()))
        #         print('res: %s -> %s' % (res.get_fun_space(), res.get_res_space()))
        return res


class RuleEvaluateConstantTimesMux(SeriesSimplificationRule):
    """

        if

            Series(a, b)

        and

            a = Constant
            b = Mux

        then we can just evaluate it pointwise.


    """

    def applies(self, dp1, dp2):
        return isinstance(dp1, Constant) and isinstance(dp2, Mux)

    def _execute(self, dp1, dp2):
        check_isinstance(dp1, Constant)
        check_isinstance(dp2, Mux)
        f = dp1.get_value()
        r = dp2.amap(f)
        R = dp2.get_res_space()
        return Constant(R, r)


# TODO: do the dual rule


class RuleSimplifyLift(SeriesSimplificationRule):
    """
                        |- A
        Mux([x, [y]]) --|
                        |- B

                        |-- A
        Mux([x, y]) ----|
                        |-- Mux([()]) - B

    """

    def applies(self, dp1, dp2):
        if not isinstance(dp2, Parallel):
            return False

        if not isinstance(dp1, Mux):
            return False

        coords = dp1.coords
        if not (isinstance(coords, list) and len(coords) == 2):
            return False
        if isinstance(coords[1], list) and len(coords[1]) == 1:
            return True

    def _execute(self, dp1, dp2):
        assert isinstance(dp1, Mux)
        assert isinstance(dp2, Parallel)
        assert isinstance(dp1.coords, list) and len(dp1.coords) == 2
        assert isinstance(dp1.coords[1], list) and len(dp1.coords[1]) == 1
        x = dp1.coords[0]
        y = dp1.coords[1][0]

        m1 = Mux(dp1.get_fun_space(), [x, y])

        F2 = m1.get_res_space()[1]
        m2 = Mux(F2, [()])

        P = make_parallel(dp2.dp1, make_series(m2, dp2.dp2))

        #         res = make_series(m1, P)
        res = Series(m1, P)
        return res


class RuleLoop1a(SeriesSimplificationRule):
    """

        TODO: this is only implemented for a special case.

        - | DP | - |m|
        / |____| -
         `-------`

        where m and DP[-1] are a Mux

        - | DP | - |m| ----
        / |____| -- Id ---
         `-----------------`

        Series( Loop(dp), m ) =

        Series( Loop(Series(dp, Par(m, Id))) )

    """

    def applies(self, dp1, dp2):
        from .dp_loop2 import DPLoop2

        # second must be Mux
        if not isinstance(dp2, Mux):
            return False

        # first must be Loop
        if not isinstance(dp1, DPLoop2):
            return False

        # the last one inside Loop must be Mux, otherwise it
        # doesn't simplify
        dp1s = unwrap_series(dp1.dp1)
        if not isinstance(dp1s[-1], Mux):
            return False

        if dp2.coords == 0:
            pass
        else:
            msg = 'Could not implement simplification' \
                  ' for dp2.coords = {}'.format(dp2.coords)
            logger.debug(msg)
            return False

        return True

    def _execute(self, dp1, dp2):
        from .dp_loop2 import DPLoop2
        assert isinstance(dp2, Mux)
        assert isinstance(dp1, DPLoop2)

        # I want to create this:
        #   -- |m| ---
        #   --  Id ---

        if dp2.coords == 0:
            coords = [(0, 0), 1]
        else:
            raise_desc(NotImplementedError, "not implemented", dp1=dp1, dp2=dp2)

        m1 = Mux(dp1.dp1.get_res_space(), coords)
        res = DPLoop2(make_series(dp1.dp1, m1))

        return res


class RuleLoop1b(SeriesSimplificationRule):
    """

        TODO: this is only implemented for a special case,
        with m.coords = [()]

        |m| - | DP | -
            / |____| -
            `-------`

        where m and DP[0] are a Mux

        --- |m| -- | DP | ----
        /-- Id  -- |____| -----
         `-----------------`

        Series( m, Loop(dp)) =

        Series( Loop(Series(Par(m, Id), dp)) )

    """

    def applies(self, dp1, dp2):
        # first must be Mux
        if not isinstance(dp1, Mux):
            return False

        # second must be Loop
        from mcdp_dp.dp_loop2 import DPLoop2
        if not isinstance(dp2, DPLoop2):
            return False

        # the first one inside Loop must be Mux, otherwise it
        # doesn't simplify
        dp1s = unwrap_series(dp2.dp1)
        if not isinstance(dp1s[0], Mux):
            return False

        if dp1.coords == [()]:
            pass
        else:
            msg = 'Could not implement simplification' \
                  ' for dp1.coords = {}'.format(dp1.coords)
            logger.debug(msg)
            return False

        return True

    def _execute(self, dp1, dp2):
        from mcdp_dp.dp_loop2 import DPLoop2
        assert isinstance(dp1, Mux)
        assert isinstance(dp2, DPLoop2)

        # I want to create this:
        #  P   -- |m| --- (Px)
        #  F2  --  Id --- F2

        if dp1.coords == [()]:
            coords = [[0], 1]
        else:
            raise_desc(NotImplementedError, "not implemented", dp1=dp1, dp2=dp2)

        dp0 = dp2.dp1

        F = dp0.get_fun_space()
        F2 = F[1]
        F1 = F[0]
        P = F1[0]
        m1F = PosetProduct((P, F2))
        # print('m1F: %s' % m1F)
        m1 = Mux(m1F, coords)

        # print 'm1', m1.tree_long()
        res = DPLoop2(make_series(m1, dp0))

        return res


class RuleSimplifyLiftB(SeriesSimplificationRule):
    """
                        |- A
        Mux([[x], y]) --|
                        |- B

                        |-- Mux([()]) - A
        Mux([x, y]) ----|
                        |-- B

    """

    def applies(self, dp1, dp2):
        if not isinstance(dp2, Parallel):
            return False

        if not isinstance(dp1, Mux):
            return False

        coords = dp1.coords
        if not (isinstance(coords, list) and len(coords) == 2):
            return False
        if isinstance(coords[0], list) and len(coords[0]) == 1:
            return True

    def _execute(self, dp1, dp2):
        assert isinstance(dp1, Mux)
        assert isinstance(dp2, Parallel)
        assert isinstance(dp1.coords, list) and len(dp1.coords) == 2
        assert isinstance(dp1.coords[0], list) and len(dp1.coords[0]) == 1
        x = dp1.coords[0][0]
        y = dp1.coords[1]

        m1 = Mux(dp1.get_fun_space(), [x, y])

        F1 = m1.get_res_space()[0]
        m2 = Mux(F1, [()])

        P = make_parallel(make_series(m2, dp2.dp1), dp2.dp2)

        # res = make_series(m1, P)
        res = Series(m1, P)
        return res


def is_two_permutation(F, coords):
    if not isinstance(F, PosetProduct) or not len(F) == 2:
        return False
    if coords == [1, 0]:
        return True
    if coords == [(1,), 0]:
        return True
    return False


class RuleMuxComposition(SeriesSimplificationRule):
    def applies(self, dp1, dp2):
        return isinstance(dp1, Mux) and isinstance(dp2, Mux)

    def _execute(self, dp1, dp2):
        assert isinstance(dp1, Mux)
        assert isinstance(dp2, Mux)
        return mux_composition(dp1, dp2)


#
# class RuleCommutativeF(SeriesSimplificationRule):
#     """
#         Commutative operators in functions.
#
#
#     """
#     def applies(self, dp1, dp2):
#         return isinstance(dp1, Mux) and isinstance(dp2, Mux)
#
#     def _execute(self, dp1, dp2):
#         assert isinstance(dp1, Mux)
#         assert isinstance(dp2, Mux)
#         return mux_composition(dp1, dp2)


class RuleSimplifyPermPar(SeriesSimplificationRule):
    """
                      |- A - |
        Mux([1, 0]) --|      | ---
                      |- B - |

                      |- B - |
        --------------|      | --- Mux([1, 0])
                      |- A - |


    """

    def applies(self, dp1, dp2):
        if not isinstance(dp2, Parallel):
            return False

        if not isinstance(dp1, Mux) or \
                not is_two_permutation(dp1.get_fun_space(), dp1.coords):
            return False

        return True

    def _execute(self, dp1, dp2):
        assert isinstance(dp1, Mux)
        F = dp1.get_fun_space()
        assert is_two_permutation(F, dp1.coords)

        # invert
        P = make_parallel(dp2.dp2, dp2.dp1)

        m2 = Mux(P.get_res_space(), [1, 0])
        res = make_series(P, m2)
        return res


class RuleJoinPar(SeriesSimplificationRule):
    """


                      |- A - |     | - C
        --------------|      | --- |
                      |- B - |     | - D


                         |- A C
                     ----|
                         | - B D

    """

    def applies(self, dp1, dp2):
        return isinstance(dp1, Parallel) and isinstance(dp2, Parallel)

    def _execute(self, dp1, dp2):
        A = dp1.dp1
        B = dp1.dp2
        C = dp2.dp1
        D = dp2.dp2
        return make_parallel(make_series(A, C), make_series(B, D))


def equiv_to_identity(dp):
    if isinstance(dp, Identity):
        return True
    if isinstance(dp, Mux):
        if dp.coords == ():
            return True
        s = simplify_indices_F(dp.get_fun_space(), dp.coords)
        if s == ():
            return True
    return False


# def is_equiv_to_terminator(dp):
#     if isinstance(dp, Terminator):
#         return True
#     return False

rules = [
    RuleSimplifyLift(),
    RuleSimplifyLiftB(),
    RuleSimplifyPermPar(),
    RuleMuxComposition(),
    RuleJoinPar(),
    RuleLoop1a(),
    RuleLoop1b(),
    #     RuleEvaluateParIfConstant(),
    #     RuleEvaluateParIfLimit(),
    RuleEvaluateConstantTimesMux(),
    RuleEvaluateMuxTimesLimit(),
]

disable_optimization = False


def make_series(dp1, dp2):
    """ Creates a Series if needed.
        Simplifies the identity and muxes """
    if disable_optimization:  # pragma: no cover
        return Series(dp1, dp2)
    # first, check that the series would be created correctly

    # Series(X(F,R), Terminator(R)) => Terminator(F)
    # but X not loop

    #     if is_equiv_to_terminator(dp2) and isinstance(dp1, Mux):
    #         res = Terminator(dp1.get_fun_space())
    #         assert res.get_fun_space() == dp1.get_fun_space()
    #         return res

    if equiv_to_identity(dp1):
        return dp2

    if equiv_to_identity(dp2):
        return dp1

    if isinstance(dp1, Parallel) and isinstance(dp2, Parallel):
        a = make_series(dp1.dp1, dp2.dp1)
        b = make_series(dp1.dp2, dp2.dp2)
        return make_parallel(a, b)

    # TODO: comment this, you get an error
    if isinstance(dp1, Mux) and isinstance(dp2, Mux):
        return mux_composition(dp1, dp2)

    if isinstance(dp1, Mux):

        def has_null_fun(dp):
            F = dp.get_fun_space()
            return isinstance(F, PosetProduct) and len(F) == 0

        if isinstance(dp2, Parallel):
            if isinstance(dp2.dp1, Identity) and has_null_fun(dp2.dp1):
                assert len(dp1.coords) == 2  # because it is followed by parallel
                assert dp1.coords[0] == []  # because it's null
                x = dp1.coords[1]
                A = Mux(dp1.get_fun_space(), x)
                B = dp2.dp2
                C = Mux(B.get_res_space(), [[], ()])
                return make_series(make_series(A, B), C)

            if isinstance(dp2.dp2, Identity) and has_null_fun(dp2.dp2):
                assert len(dp1.coords) == 2  # because it is followed by parallel
                assert dp1.coords[1] == []  # because it's null
                x = dp1.coords[0]
                A = Mux(dp1.get_fun_space(), x)
                B = dp2.dp1
                C = Mux(B.get_res_space(), [(), []])
                return make_series(make_series(A, B), C)

        if isinstance(dp2, Series):
            dps = unwrap_series(dp2)

            def has_null_identity(dp):
                assert isinstance(dp, Parallel)
                if isinstance(dp.dp1, Identity) and has_null_fun(dp.dp1):
                    return True
                if isinstance(dp.dp2, Identity) and has_null_fun(dp.dp2):
                    return True
                return False

            if isinstance(dps[0], Parallel) and has_null_identity(dps[0]):
                first = make_series(dp1, dps[0])
                rest = reduce(make_series, dps[1:])
                return make_series(first, rest)

    # bring the mux outside the parallel
    #                   | - Mux(c) - p1
    #  Mux([a,b]) ----> |
    #                   | -
    #                     | - p1
    #  Mux([a*c,b]) ----> |
    #                     |
    if isinstance(dp1, Mux) and isinstance(dp2, Parallel) \
            and isinstance(unwrap_series(dp2.dp1)[0], Mux):

        unwrapped = unwrap_series(dp2.dp1)
        first_mux = unwrapped[0]
        assert isinstance(first_mux, Mux)

        coords = dp1.coords
        assert isinstance(coords, list) and len(coords) == 2, coords

        F = dp1.get_fun_space()
        coords2 = [compose_indices(F, coords[0], first_mux.coords, list), coords[1]]
        m2 = Mux(F, coords2)

        rest = wrap_series(first_mux.get_res_space(), unwrapped[1:])

        res = make_series(m2, make_parallel(rest, dp2.dp2))

        if do_extra_checks():
            check_same_spaces(Series(dp1, dp2), res)
        return res

    if isinstance(dp1, Mux) and isinstance(dp2, Parallel) \
            and isinstance(unwrap_series(dp2.dp2)[0], Mux):

        unwrapped = unwrap_series(dp2.dp2)
        first_mux = unwrapped[0]
        assert isinstance(first_mux, Mux)

        coords = dp1.coords
        assert isinstance(coords, list) and len(coords) == 2, coords

        F = dp1.get_fun_space()
        coords2 = [coords[0], compose_indices(F, coords[1], first_mux.coords, list)]
        m2 = Mux(F, coords2)

        rest = wrap_series(first_mux.get_res_space(), unwrapped[1:])

        res = make_series(m2, make_parallel(dp2.dp1, rest))

        if do_extra_checks():
            check_same_spaces(Series(dp1, dp2), res)
        return res

    #     print('Cannot simplify:')
    #     print(' dp1: %s' % dp1)
    #     print(' dp2: %s' % dp2)
    #     print('\n- '.join([str(x) for x in unwrap_series(a)]))

    dp1s = unwrap_series(dp1)
    dp2s = unwrap_series(dp2)

    for rule in rules:
        # [dp1s[:-1] dp1s[-1]] --- [dp2s[0] dp2s[1:]]
        if rule.applies(dp1s[-1], dp2s[0]):
            # logger.debug('Applying series simplification rule %s' % type(rule).__name__)
            r = rule.execute(dp1s[-1], dp2s[0])
            try:
                check_same_fun(r, dp1s[-1])
                check_same_res(r, dp2s[0])
            except Exception as e:
                msg = 'Invalid result of simplification rule.'
                raise_wrapped(DPInternalError, e, msg, rule=rule,
                              result=r.repr_long())

            first = wrap_series(dp1.get_fun_space(), dp1s[:-1])
            rest = wrap_series(dp2s[0].get_fun_space(), dp2s[1:])
            return make_series(first, make_series(r, rest))

    return Series(dp1, dp2)


def check_same_fun(dp1, dp2):
    """ Checks that the two dps have same F """
    F1 = dp1.get_fun_space()
    F2 = dp2.get_fun_space()

    if not (F1 == F2):  # pragma: no cover
        msg = 'F not preserved'
        raise_desc(AssertionError, msg, F1=F1, F2=F2)


def check_same_res(dp1, dp2):
    """ Checks that the two dps have same F """
    R1 = dp1.get_res_space()
    R2 = dp2.get_res_space()

    if not (R1 == R2):  # pragma: no cover
        msg = 'R not preserved'
        raise_desc(AssertionError, msg, R1=R1, R2=R2)


def check_same_spaces(dp1, dp2):
    check_same_fun(dp1, dp2)
    check_same_res(dp1, dp2)


def unwrap_series(dp):
    if not isinstance(dp, Series):
        return [dp]
    else:
        return unwrap_series(dp.dp1) + unwrap_series(dp.dp2)


def unwrap_as_series_start_last(dp):
    dpu = unwrap_series(dp)
    dpu_last = dpu[-1]
    dpu_start = wrap_series(dp.get_fun_space(), dpu[:-1])
    return dpu_start, dpu_last


def wrap_series(F0, dps):
    if len(dps) == 0:
        return Identity(F0)
    else:
        return make_series(dps[0], wrap_series(dps[0].get_res_space(), dps[1:]))


def simplify_indices_F(F, coords):
    # Safety check: Clearly if it's not the identity it cannot be equal to ()
    R = get_R_from_F_coords(F, coords)
    if not (R == F):
        return coords

    # generic test
    i0 = get_id_indices(F)
    # compose
    i0coords = compose_indices(F, i0, coords, list)
    if i0 == i0coords:
        return ()

    mcdp_dev_warning('simplify_indices_F(): Note that none of this is ever taken(!).')
    if coords == [0] and len(F) == 1:
        return ()
    if coords == [0, 1] and len(F) == 2:
        return ()
    if coords == [0, (1,)] and len(F) == 2:
        return ()
    if coords == [0, 1, 2] and len(F) == 3:
        return ()

    mcdp_dev_warning('need a double check here')
    if coords == [[(0, 0)], [(1, 0)]]:
        return ()

    if coords == [[(0, 0)], [(1, 0), (1, 1)]]:
        return ()

    # [[(0, 1)], [(1, 0), (0, 0)]]
    return coords


@contract(dp1=Mux, dp2=Mux)
def mux_composition(dp1, dp2):
    try:
        dp0 = Series(dp1, dp2)

        F = dp1.get_fun_space()
        c1 = dp1.coords
        c2 = dp2.coords
        coords = compose_indices(F, c1, c2, list)
        coords = simplify_indices_F(F, coords)

        res = Mux(F, coords)
        assert res.get_res_space() == dp0.get_res_space()

        return res
    except DPInternalError as e:  # pragma: no cover
        msg = 'Cannot create shortcut.'
        raise_wrapped(DPInternalError, e, msg,
                      dp1=dp1.repr_long(), dp2=dp2.repr_long())
