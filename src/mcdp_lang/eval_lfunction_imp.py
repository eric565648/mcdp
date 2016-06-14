# -*- coding: utf-8 -*-
from .parts import CDPLanguage
from contracts import contract
from contracts.utils import raise_desc
from mocdp.comp import Connection, dpwrap
from mocdp.comp.context import CFunction, get_name_for_res_node
from mocdp.dp import InvMult2, InvPlus2, Limit
from mocdp.dp.dp_mult_inv import InvPlus2Nat
from mocdp.exceptions import DPInternalError, DPSemanticError
from mcdp_lang.utils_lists import get_odd_ops, unwrap_list
from mcdp_posets import mult_table
from mcdp_posets.nat import Nat
from mcdp_posets.rcomp_units import RcompUnits
from mcdp_lang.parse_actions import add_where_information
from mcdp_lang.helpers import get_valuewithunits_as_function


CDP = CDPLanguage

__all__ = ['eval_lfunction']

@contract(returns=CFunction)
def eval_lfunction(lf, context):
    with add_where_information(lf.where):

        if isinstance(lf, CDP.Function):
            return context.make_function(dp=lf.dp.value, s=lf.s.value)

        if isinstance(lf, CDP.InvMult):
            ops = get_odd_ops(unwrap_list(lf.ops))
            if len(ops) != 2:
                raise DPInternalError('Only 2 expected')

            fs = []

            for op_i in ops:
                fi = eval_lfunction(op_i, context)
                fs.append(fi)

            assert len(fs) == 2

            Fs = map(context.get_ftype, fs)
            R = mult_table(Fs[0], Fs[1])


            dp = InvMult2(R, tuple(Fs))
            ndp = dpwrap(dp, '_input', ['_f0', '_f1'])

            name = context.new_name('_invmult')
            context.add_ndp(name, ndp)

            c1 = Connection(dp2=fs[0].dp, s2=fs[0].s, dp1=name, s1='_f0')
            c2 = Connection(dp2=fs[1].dp, s2=fs[1].s, dp1=name, s1='_f1')
            context.add_connection(c1)
            context.add_connection(c2)

            res = context.make_function(name, '_input')
            return res

        if isinstance(lf, CDP.InvPlus):
            return eval_lfunction_invplus(lf, context)

        if isinstance(lf, CDP.NewResource):
            rname = lf.name
            try:
                dummy_ndp = context.get_ndp_res(rname)
            except ValueError as e:
                msg = 'New resource name %r not declared.' % rname
                msg += '\n%s' % str(e)
                raise DPSemanticError(msg, where=lf.where)

            return context.make_function(get_name_for_res_node(rname),
                            dummy_ndp.get_fnames()[0])

        if isinstance(lf, CDP.MakeTuple):
            from .eval_lfunction_imp_maketuple import eval_MakeTuple_as_lfunction
            return eval_MakeTuple_as_lfunction(lf, context)

        from mocdp.comp.context import ValueWithUnits

        if isinstance(lf, CDP.VariableRef):
            if lf.name in context.constants:
                c = context.constants[lf.name]
                assert isinstance(c, ValueWithUnits)
                return get_valuewithunits_as_function(c, context)

            # Not implemented for resources yet?
#             elif lf.name in context.var2resource:
#                 return context.var2resource[rvalue.name]

            try:
                dummy_ndp = context.get_ndp_res(lf.name)
            except ValueError as e:
                msg = 'New resource name %r not declared.' % lf.name
                msg += '\n%s' % str(e)
                raise DPSemanticError(msg, where=lf.where)

            s = dummy_ndp.get_rnames()[0]
            return context.make_function(get_name_for_res_node(lf.name), s)


        constants = (CDP.Collection, CDP.SimpleValue, CDP.SpaceCustomValue,
                     CDP.Top, CDP.Bottom)

        if isinstance(lf, constants):
            from mcdp_lang.eval_constant_imp import eval_constant
            res = eval_constant(lf, context)
            assert isinstance(res, ValueWithUnits)
            return get_valuewithunits_as_function(res, context)

#         if isinstance(lf, CDP.Constant):
#
#             from mcdp_lang.eval_constant_imp import eval_constant
#
#
#             return context.make_function(n, sn)

        msg = 'eval_lfunction() cannot evaluate as a function.'
        raise_desc(DPInternalError, msg, lf=lf)


def eval_lfunction_invplus(lf, context):
    ops = get_odd_ops(unwrap_list(lf.ops))
    if len(ops) != 2:
        raise DPInternalError('Only 2 expected')

    fs = []

    for op_i in ops:
        fi = eval_lfunction(op_i, context)
        fs.append(fi)

    assert len(fs) == 2

    Fs = map(context.get_ftype, fs)
    R = Fs[0]

    if all(isinstance(_, RcompUnits) for _ in Fs):
        dp = InvPlus2(R, tuple(Fs))
    elif all(isinstance(_, Nat) for _ in Fs):
        dp = InvPlus2Nat(R, tuple(Fs))
    else:
        msg = 'Cannot find operator for mixed values'
        raise_desc(DPInternalError, msg, Fs=Fs)
    

    ndp = dpwrap(dp, '_input', ['_f0', '_f1'])

    name = context.new_name('_invplus')
    context.add_ndp(name, ndp)

    c1 = Connection(dp2=fs[0].dp, s2=fs[0].s, dp1=name, s1='_f0')
    c2 = Connection(dp2=fs[1].dp, s2=fs[1].s, dp1=name, s1='_f1')
    context.add_connection(c1)
    context.add_connection(c2)

    res = context.make_function(name, '_input')
    return res