# -*- coding: utf-8 -*-
from contracts import contract
from contracts.utils import raise_desc, check_isinstance
from mcdp.development import do_extra_checks, mcdp_dev_warning

from .finite_collection import FiniteCollection
from .finite_collection_as_space import FiniteCollectionAsSpace
from .poset import NotBounded, NotLeq, Poset
from .space import NotBelongs, NotEqual, Space


__all__ = [
    'FiniteCollectionsInclusion',
]

class FiniteCollectionsInclusion(Poset):
    """ 
        Lattice of finite collections. 
    
        The bottom is the empty set.
        The top is the entire set.
        
        The elements are represented as instances of the
        class FiniteCollection.
        
    """

    @contract(S=Space)
    def __init__(self, S):
        self.S = S

    def witness(self):
        w = self.S.witness()
        elements = [w]
        S = self.S
        return FiniteCollection(elements=elements, S=S)

 
    def meet(self, a, b): 
        """ Set intersection """
        check_isinstance(a, FiniteCollection)
        check_isinstance(b, FiniteCollection)
        intersection = a.elements & b.elements # frozenset
        return FiniteCollection(elements=set(intersection), S=self.S)

    def join(self, a, b): 
        """ Set union """
        check_isinstance(a, FiniteCollection)
        check_isinstance(b, FiniteCollection)
        intersection = a.elements | b.elements  # frozenset
        return FiniteCollection(elements=set(intersection), S=self.S)
    
    
    def get_maximal_elements(self):
        top = self.get_top()
        return set([top])
    
    # This can only be implemented if we can enumerate the elements of Space
    def get_top(self):
        if isinstance(self.S, FiniteCollectionAsSpace):
            res = FiniteCollection(elements=self.S.elements,
                                    S=self.S)
            if do_extra_checks():
                self.belongs(res)

            return res

        mcdp_dev_warning('Maybe should use a TooMuchComputation error.')
        msg = 'Cannot enumerate the elements of this space.'
        raise_desc(NotBounded, msg, space=self.S)

    def get_bottom(self):
        return FiniteCollection(set([]), self.S)

    def __eq__(self, other):
        return isinstance(other, FiniteCollectionsInclusion) and self.S == other.S

    def belongs(self, x):
        if not isinstance(x, FiniteCollection):
            msg = 'Not a finite collection.'
            raise_desc(NotBelongs, msg, x=x)
        if not x.S == self.S:
            msg = 'Different spaces: %s ≠ %s' % (self.S, x.S)
            raise_desc(NotBelongs, msg, x=x)

    def check_equal(self, a, b):
        m1 = a.elements
        m2 = b.elements
        if not (m1 == m2):
            raise NotEqual('%s ≠ %s' % (m1, m2))

    def check_leq(self, a, b):
        e1 = a.elements
        e2 = b.elements
        res = e1.issubset(e2)
        if not res:
            msg = 'Not included'
            raise_desc(NotLeq, msg, e1=e1, e2=e2)

    def format(self, x):
        contents = ", ".join(self.S.format(m)
                        for m in sorted(x.elements))

        return "{%s}" % contents

    def __repr__(self):
        return "set-of(%r)" % self.S
