# -*- coding: utf-8 -*-
from .primitive_meta import PrimitiveMeta
from abc import abstractmethod
from collections import namedtuple
from contracts import contract
from contracts.utils import indent, raise_desc
from decent_logs import WithInternalLog
from mcdp_posets import LowerSet  # @UnusedImport
from mcdp_posets import (Map, Ncomp, NotBelongs, Poset, PosetProduct, Space,
    SpaceProduct, UpperSet, UpperSets, poset_minima)
from mocdp.exceptions import do_extra_checks
from mocdp import ATTRIBUTE_NDP_RECURSIVE_NAME
from copy import deepcopy


__all__ = [
    'PrimitiveDP',
    'NotFeasible',
    'Feasible',
    'NotSolvableNeedsApprox',
    'EmptyDP',
]



class NotFeasible(Exception):
    pass

class Feasible(Exception):
    pass

class NotSolvableNeedsApprox(Exception):
    pass

class WrongUseOfUncertain(Exception):
    pass

class PrimitiveDP(WithInternalLog):
    """ 
        There are F, R, I.
        
        solve : F -> U(R)
        get_implementations_f_r: F x R -> set(I)
            (note that F is not optimal by each I, merely feasible...)
                
        evaluate: I -> L(F), U(R)
        
        future:
            solve : F -> U(R)
        
        f' is feasible for I if f' \in eval(I).f
    
    """
    __metaclass__ = PrimitiveMeta

    @contract(F=Space, R=Poset, I=Space)
    def __init__(self, F, R, I):
        self._inited = True
        self.F = F
        self.R = R
        self.I = I
        self.M = I

    @abstractmethod
    @contract(returns=UpperSet)
    def solve(self, f):
        '''
            Given one f point, returns an UpperSet of resources.
        '''
        pass

    @abstractmethod
    @contract(returns='tuple($LowerSet, $UpperSet)')
    def evaluate(self, i):
        """ Evaluates an implementation. """

    def get_implementations_f_r(self, f, r):  # @UnusedVariable
        """ Returns the set of implementations that realize the pair (f, r).
            Returns a non-empty set or raises NotFeasible. """
        M = self.get_imp_space_mod_res()

        if isinstance(M, SpaceProduct) and len(M) == 0:
            m = ()
            # self.check_feasible(f, m , r)
            return set([m])

        raise NotImplementedError(type(self).__name__)

    def evaluate_f_m(self, func, m):
        """ Returns the minimal resources needed
            by the particular implementation m 
        
            raises NotFeasible
        """
        M = self.get_imp_space_mod_res()
        if do_extra_checks():
            self.F.belongs(func)
            M.belongs(m)
        if isinstance(M, SpaceProduct) and m == ():
            rs = self.solve(func)
            minimals = list(rs.minimals)
            if len(minimals) == 1:
                return minimals[0]
            else:
                msg = 'Cannot use default evaluate_f_m() because multiple miminals.'
                raise_desc(NotImplementedError, msg,
                           classname=type(self),
                           func=func, M=M, m=m, minimals=rs.minimals)
        else:
            msg = 'Cannot use default evaluate_f_m()'
            raise_desc(NotImplementedError, msg,
                       classname=type(self), func=func, M=M, m=m,)



    def _assert_inited(self):
        if not '_inited' in self.__dict__:
            msg = 'Class %s not inited.' % (type(self))
            raise Exception(msg)

    @contract(returns=Space)
    def get_fun_space(self):
        return self.F

    @contract(returns=Poset)
    def get_res_space(self):
        return self.R

    @contract(returns=Space)
    def get_imp_space(self):
        I = self.I
        # This is a mess
        #
        # The first time the dp is created there is no attribute
        # So we need to redo it
        # if not hasattr(self, 'Imarked'):
        if not hasattr(self, 'Imarked') or not hasattr(self.Imarked, ATTRIBUTE_NDP_RECURSIVE_NAME):
            self.Imarked = deepcopy(I)
            if hasattr(self, ATTRIBUTE_NDP_RECURSIVE_NAME):
                x = getattr(self, ATTRIBUTE_NDP_RECURSIVE_NAME)
                setattr(self.Imarked, ATTRIBUTE_NDP_RECURSIVE_NAME, x)

        return self.Imarked

    @contract(returns=Space)
    def get_imp_space_mod_res(self):
        return self.get_imp_space()

    @contract(returns=Poset)
    def get_tradeoff_space(self):
        return UpperSets(self.R)

    def is_feasible(self, f, i, r):
        if do_extra_checks():
            self.F.belongs(f)
            self.I.belongs(i)
            self.R.belongs(r)
        try:
            self.check_feasible(f, i, r)
        except NotFeasible:
            return False
        else:
            return True

    def check_unfeasible(self, f, i, r):

        if do_extra_checks():
            self.F.belongs(f)
            self.I.belongs(i)
            self.R.belongs(r)

        lf, ur = self.evaluate(i)
        try:
            lf.belongs(f)
            ur.belongs(r)
        except NotBelongs:
            pass
        else:
            msg = 'check_feasible failed.'
            raise_desc(NotFeasible, msg, f=f, i=i, r=r, lf=lf, ur=ur)

    def check_feasible(self, f, m, r):
        if do_extra_checks():
            self.F.belongs(f)
            self.M.belongs(m)
            self.R.belongs(r)
        lf, ur = self.evaluate(m)
        try:
            lf.belongs(f)
            ur.belongs(r)
        except NotBelongs:
            msg = 'check_feasible failed.'
            raise_desc(NotFeasible, msg, f=f, m=m, r=r, lf=lf, ur=ur)

    @contract(returns=UpperSet)
    def solve_trace(self, func, tracer):  # @UnusedVariable
        return self.solve(func)

    @contract(ufunc=UpperSet)
    def solveU(self, ufunc):
        if do_extra_checks():
            UF = UpperSets(self.get_fun_space())
            UF.belongs(ufunc)
        
        res = set([])
        for m in ufunc.minimals:
            u = self.solve(m)
            res.update(u.minimals)
        ressp = self.get_res_space()
        minima = poset_minima(res, ressp.leq)
        return ressp.Us(minima)

    def get_normal_form(self):
        """
            S is a Poset
            alpha: U(F) x S -> U(R)
            beta:  U(F) x S -> S 
        """
        One = PosetProduct(())
#         UOne = UpperSets(One)
#         S = UOne
        S = One

        class DefaultAlphaMap(Map):
            def __init__(self, dp):
                self.dp = dp
                F = dp.get_fun_space()
                R = dp.get_res_space()
                UF = UpperSets(F)
                dom = PosetProduct((UF, S))
                cod = UpperSets(R)
                Map.__init__(self, dom, cod)

            def _call(self, x):
                F, _s = x
                Res = self.dp.solveU(F)
                return Res


        class DefaultBeta(Map):
            def __init__(self, dp):
                self.dp = dp
                F = dp.get_fun_space()
                UF = UpperSets(F)
                dom = PosetProduct((UF, S))
                cod = S
                Map.__init__(self, dom, cod)

            def _call(self, x):
                _F, s = x

                # print('Beta() for %s' % (self.dp))
                # print(' f = %s s = %s -> unchanged ' % (_F, s))
                return s

        alpha = DefaultAlphaMap(self)
        beta = DefaultBeta(self)

        return NormalForm(S=S, alpha=alpha, beta=beta)

    def get_normal_form_approx(self):
        gamma = DefaultGamma(self)
        delta = DefaultDelta(self)
        S = PosetProduct(())
        return NormalFormApprox(S=S, gamma=gamma, delta=delta)


    def __repr__(self):
        return '%s(%s→%s)' % (type(self).__name__, self.F, self.R)

    def _add_extra_info(self):
        s = ""

        if hasattr(self, ATTRIBUTE_NDP_RECURSIVE_NAME):
            x = getattr(self, ATTRIBUTE_NDP_RECURSIVE_NAME)
            s += ' named: ' + x.__str__()

        s3 = self.get_imp_space().__repr__()
        s += ' I = %s' % s3

        from mocdp.comp.recursive_name_labeling import get_names_used
        if isinstance(self.I, SpaceProduct):
            names = get_names_used(self.I)
            # names = filter(None, names)
            if names:
                s += ' names: %s' % names
        return s

    def repr_long(self):
        s = self.__repr__()
        return s + self._add_extra_info()

    def _children(self):  # XXX: is this still used?
        l = []
        if hasattr(self, 'dp1'):
            l.append(self.dp1)
        if hasattr(self, 'dp2'):
            l.append(self.dp2)
        return tuple(l)

    def tree_long(self, n=None):
        if n is None: n = 120
        s = type(self).__name__
        S, _, _ = self.get_normal_form()
        u = lambda x: x.decode('utf-8')
        ulen = lambda x: len(u(x))

        def clip(x, n):
            s = str(x)
            unicode_string = s.decode("utf-8")
            l = len(unicode_string)
            s = s + ' ' * (n - l)
            if len(u(s)) > n:
                x = u(s)
                x = x[:n - 3] + '...'
                s = x.encode('utf-8')
            return s

        s2 = '   [F = %s  R = %s  M = %s  S = %s]' % (clip(self.F, 13),
                       clip(self.R, 10), clip(self.M, 15),
                           clip(S, 28))

        head = s + ' ' * (n - ulen(s) - ulen(s2)) + s2

        for x in self._children():
            head += '\n' + indent(x.tree_long(n - 2), '  ')

        return head


class EmptyDP(PrimitiveDP):
    """ 
        This is a DP for which implementations = functions.
         
    """

    def __init__(self, F, R):
        I = F
        PrimitiveDP.__init__(self, F=F, R=R, I=I)

    def evaluate(self, i):
        if do_extra_checks():
            self.I.belongs(i)
        f = i
        rs = self.solve(f)
        fs = LowerSet(set([f]), self.F)
        return fs, rs

    def get_implementations_f_r(self, f, r):  # @UnusedVariable
        i = f
        return set([i])


class ApproximableDP(PrimitiveDP):
    """ these will throw NotSolvableNeedsApprox for solve() """

    @abstractmethod
    @contract(n='int,>=0', returns=PrimitiveDP)
    def get_lower_bound(self, n):
        pass

    @abstractmethod
    @contract(n='int,>=0', returns=PrimitiveDP)
    def get_upper_bound(self, n):
        pass


NormalForm = namedtuple('NormalForm', ['S', 'alpha', 'beta'])

NormalFormApprox = namedtuple('NormalFormApprox', ['S', 'gamma', 'delta'])




class DefaultGamma(Map):
    """
    
        F x S, Nl, Nu
    """
    def __init__(self, dp):
        self.dp = dp
        F = dp.get_fun_space()
        R = dp.get_res_space()
        UF = UpperSets(F)
        UR = UpperSets(R)
        S = PosetProduct(())
        N = Ncomp()
        dom = PosetProduct((UF, S, N, N))
        cod = PosetProduct((UR, UR))
        Map.__init__(self, dom, cod)

    def _call(self, x):
        F, _s, nl, nu = x
        Res = self.dp.solveU_approx(F, nl, nu)
        return Res


class DefaultDelta(Map):
    def __init__(self, dp):
        self.dp = dp
        F = dp.get_fun_space()
        UF = UpperSets(F)

        S = PosetProduct(())
        N = Ncomp()
        dom = PosetProduct((UF, S, N, N))
        cod = PosetProduct((S, S))
        Map.__init__(self, dom, cod)

    def _call(self, x):
        _F, s, _nl, _nu = x
        # print('Beta() for %s' % (self.dp))
        # print(' f = %s s = %s -> unchanged ' % (_F, s))
        return s, s
