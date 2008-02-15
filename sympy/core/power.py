
from basic import Basic, S, C
from sympify import _sympify
from methods import ArithMeths, RelMeths
from cache import cacheit

from symbol import Symbol, Wild, Temporary
# from numbers import Number, Rational, Integer     /cyclic/
# from add import Add   /cyclic/
# from mul import Mul   /cyclic/

def integer_nthroot(y, n):
    """
    Usage
    =====
        Return a tuple containing x = floor(y**(1/n))
        and a boolean indicating whether the result is exact (that is,
        whether x**n == y).

    Examples
    ========

        >>> integer_nthroot(16,2)
        (4, True)
        >>> integer_nthroot(26,2)
        (5, False)
        >>> integer_nthroot(1234567**7, 7)
        (1234567L, True)
        >>> integer_nthroot(1234567**7+1, 7)
        (1234567L, False)
    """

    y = int(y); n = int(n)
    if y < 0: raise ValueError, "y must not be negative"
    if n < 1: raise ValueError, "n must be positive"
    if y in (0, 1): return y, True
    if n == 1: return y, True

    # Search with Newton's method, starting from floating-point
    # approximation. Care must be taken to avoid overflow.
    from math import log as _log
    guess = 2**int(_log(y, 2)/n)
    xprev, x = -1, guess
    while abs(x - xprev) > 1:
        t = x**(n-1)
        xprev, x = x, x - (t*x-y)//(n*t)
    # Compensate
    while x**n > y:
        x -= 1
    return x, x**n == y


class Pow(Basic, ArithMeths, RelMeths):

    precedence = Basic.Pow_precedence

    @cacheit
    def __new__(cls, a, b, **assumptions):
        a = _sympify(a)
        b = _sympify(b)
        if b is S.Zero:
            return S.One
        if b is S.One:
            return a
        obj = a._eval_power(b)
        if obj is None:
            obj = Basic.__new__(cls, a, b, **assumptions)
        return obj

    @property
    def base(self):
        return self._args[0]

    @property
    def exp(self):
        return self._args[1]

    def _eval_power(self, other):
        if isinstance(other, Number):
            if self.base.is_real:
                if isinstance(self.exp, Number):
                    # (a ** 2) ** 3 -> a ** (2 * 3)
                    return Pow(self.base, self.exp * other)
            if isinstance(other, Rational):
                if self.exp.is_even and Integer(other.q).is_even:
                    return abs( Pow(self.base, self.exp * other))
                return Pow(self.base, self.exp * other)
            if isinstance(other, Integer):
                # (a ** b) ** 3 -> a ** (3 * b)
                return Pow(self.base, self.exp * other)
        elif isinstance(other, (Add, Mul)):
            # (a**b)**c = a**(b*c)
            return Pow(self.base, self.exp * other)

        if other.atoms(Wild):
            return Pow(self.base, self.exp * other)
        return

    def _eval_is_commutative(self):
        c1 = self.base.is_commutative
        if c1 is None: return
        c2 = self.base.is_commutative
        if c2 is None: return
        return c1 and c2

    def _eval_is_comparable(self):
        c1 = self.base.is_comparable
        if c1 is None: return
        c2 = self.base.is_comparable
        if c2 is None: return
        return c1 and c2

    def _eval_is_even(self):
        if self.exp.is_integer and self.exp.is_positive:
            if self.base.is_even:
                return True
            if self.exp.is_integer:
                return False

    def _eval_is_positive(self):
        if self.base.is_positive:
            if self.exp.is_real:
                return True
        elif self.base.is_negative:
            if self.exp.is_even:
                return True
            if self.exp.is_odd:
                return False
        elif self.base.is_nonpositive:
            if self.exp.is_odd:
                return False

    def _eval_is_negative(self):
        if self.base.is_negative:
            if self.exp.is_odd:
                return True
            if self.exp.is_even:
                return False
        elif self.base.is_positive:
            if self.exp.is_real:
                return False
        elif self.base.is_nonnegative:
            if self.exp.is_real:
                return False
        elif self.base.is_nonpositive:
            if self.exp.is_even:
                return False
        elif self.base.is_real:
            if self.exp.is_even:
                return False

    def _eval_is_integer(self):
        c1 = self.base.is_integer
        if c1 is None: return
        c2 = self.exp.is_integer
        if c2 is None: return
        if c1 and c2:
            if self.exp.is_nonnegative or self.exp.is_positive:
                return True
            if self.exp.is_negative:
                return False

    def _eval_is_real(self):
        c1 = self.base.is_real
        if c1 is None: return
        c2 = self.exp.is_real
        if c2 is None: return
        if c1 and c2:
            if self.base.is_positive:
                return True
            if self.base.is_negative:
                if self.exp.is_integer:
                    return True

    def _eval_is_odd(self):
        if not (self.base.is_integer and self.exp.is_nonnegative): return
        return self.base.is_odd

    def _eval_is_bounded(self):
        if self.exp.is_negative:
            if self.base.is_infinitesimal:
                return False
            if self.base.is_unbounded:
                return True
        c1 = self.base.is_bounded
        if c1 is None: return
        c2 = self.exp.is_bounded
        if c2 is None: return
        if c1 and c2:
            if self.exp.is_nonnegative:
                return True

    def tostr(self, level=0):
        precedence = self.precedence
        b = self.base.tostr(precedence)
        if self.exp is S.NegativeOne:
            r = '1/%s' % (b)
        else:
            r = '%s**%s' % (b,self.exp.tostr(precedence))
        if precedence <= level:
            return '(%s)' % (r)
        return r

    def _eval_subs(self, old, new):
        if self==old: return new
        if isinstance(old, self.__class__) and self.base==old.base:
            coeff1,terms1 = self.exp.as_coeff_terms()
            coeff2,terms2 = old.exp.as_coeff_terms()
            if terms1==terms2: return new ** (coeff1/coeff2) # (x**(2*y)).subs(x**(3*y),z) -> z**(2/3*y)
        if isinstance(old, C.exp):
            coeff1,terms1 = old.args[0].as_coeff_terms()
            coeff2,terms2 = (self.exp * C.log(self.base)).as_coeff_terms()
            if terms1==terms2: return new ** (coeff1/coeff2) # (x**(2*y)).subs(exp(3*y*log(x)),z) -> z**(2/3*y)
        return self.base.subs(old, new) ** self.exp.subs(old, new)

    def as_powers_dict(self):
        return { self.base : self.exp }

    def as_base_exp(self):
        if isinstance(self.base, Rational) and self.base.p==1:
            return 1/self.base, -self.exp
        return self.base, self.exp

    def _eval_conjugate(self):
        from sympy.functions.elementary.complexes import conjugate as c
        return c(self.base)**self.exp

    def _eval_expand_complex(self, *args):
        if isinstance(self.exp, Integer):
            exp = self.exp
            re, im = self.base.as_real_imag()
            if exp >= 0:
                base = re + S.ImaginaryUnit*im
            else:
                mag = re**2 + im**2
                base = re/mag - S.ImaginaryUnit*(im/mag)
                exp = -exp
            return (base**exp).expand()
        elif isinstance(self.exp, Rational):
            # NOTE: This is not totally correct since for x**(p/q) with
            #       x being imaginary there are actually q roots, but
            #       only a single one is returned from here.
            re, im = self.base.as_real_imag()

            r = (re**2 + im**2)**S.Half
            t = C.atan(im / re)

            if im == 0 and re < 0:
                t = S.Pi

            rp, tp = r**self.exp, t*self.exp

            return rp*C.cos(tp) + rp*C.sin(tp)*S.ImaginaryUnit
        else:
            return C.re(self) + S.ImaginaryUnit*C.im(self)

    def _eval_expand_basic(self):
        """
        (a*b)**n -> a**n * b**n
        (a+b+..) ** n -> a**n + n*a**(n-1)*b + .., n is positive integer
        """
        b = self.base._eval_expand_basic()
        e = self.exp._eval_expand_basic()

        if b is None:
            base = self.base
        else:
            base = b

        if e is None:
            exp = self.exp
        else:
            exp = e

        if e is not None or b is not None:
            result = base**exp

            if isinstance(result, Pow):
                base, exp = result.base, result.exp
            else:
                return result
        else:
            result = None

        if isinstance(exp, Integer) and exp.p > 0 and isinstance(base, Add):
            n = int(exp)

            if base.is_commutative:
                order_terms, other_terms = [], []

                for order in base.args:
                    if isinstance(order, C.Order):
                        order_terms.append(order)
                    else:
                        other_terms.append(order)

                if order_terms:
                    # (f(x) + O(x^n))^m -> f(x)^m + m*f(x)^{m-1} *O(x^n)
                    f = Add(*other_terms)
                    g = (f**(n-1)).expand()

                    return (f*g).expand() + n*g*Add(*order_terms)

                if base.is_number:
                    # Efficiently expand expressions of the form (a + b*I)**n
                    # where 'a' and 'b' are real numbers and 'n' is integer.
                    a, b = base.as_real_imag()

                    if isinstance(a, Rational) and isinstance(b, Rational):
                        if not isinstance(a, Integer):
                            if not isinstance(b, Integer):
                                k = (a.q * b.q) ** n
                                a, b = a.p*b.q, a.q*b.p
                            else:
                                k = a.q ** n
                                a, b = a.p, a.q*b
                        elif not isinstance(b, Integer):
                            k = b.q ** n
                            a, b = a*b.q, b.p
                        else:
                            k = 1

                        a, b, c, d = int(a), int(b), 1, 0

                        while n:
                            if n & 1:
                                c, d = a*c-b*d, b*c+a*d
                                n -= 1
                            a, b = a*a-b*b, 2*a*b
                            n //= 2

                        I = S.ImaginaryUnit

                        if k == 1:
                            return c + I*d
                        else:
                            return Integer(c)/k + I*d/k

                # Consider polynomial:
                #
                #   P(x) = sum_{i=0}^n p_i x^k
                #
                # and its m-th exponent:
                #
                #   P(x)^m = sum_{k=0}^{m n} a(m,k) x^k
                #
                # The coefficients a(m,k) can be computed using
                # the J.C.P. Miller Pure Recurrence:
                #
                #  a(m,k) = 1/(k p_0) sum_{i=1}^n p_i ((m+1)i-k) a(m,k-i)
                #
                # where a(m,0) = p_0^m.
                #
                # For more information refer to:
                #
                # [1] D.E.Knuth, The Art of Computer Programming:
                #     Seminumerical Algorithms, v.2, Addison
                #     Wesley, Reading, 1981, pp. 751

                p = other_terms
                m = len(p)-1
                cache = {0: p[0] ** n}
                p0 = [t/p[0] for t in p]
                l = [cache[0]]
                for k in xrange(1, n * m + 1):
                    a = []
                    for i in xrange(1,m+1):
                        if i<=k:
                            a.append(Mul(Rational((n+1)*i-k,k), p0[i], cache[k-i]).expand())
                    a = Add(*a)
                    cache[k] = a
                    l.append(a)
                return Add(*l)
            else:
                if n == 2:
                    return Add(*[f*g for f in base.args for g in base.args])
                else:
                    return Mul(base, Pow(base, n-1).expand()).expand()
        elif isinstance(exp, Add) and isinstance(base, Number):
            #  a + b      a  b
            # n      --> n  n  , where n, a, b are Numbers

            coeff, tail = S.One, S.Zero

            for term in exp.args:
                if isinstance(term, Number):
                    coeff *= base**term
                else:
                    tail += term

            return coeff * base**tail
        else:
            return result

    def _eval_derivative(self, s):
        dbase = self.base.diff(s)
        dexp = self.exp.diff(s)
        return self * (dexp * C.log(self.base) + dbase * self.exp/self.base)

    _eval_evalf = Basic._seq_eval_evalf

    def _calc_splitter(self, d):
        if d.has_key(self):
            return d[self]
        base = self.base._calc_splitter(d)
        exp = self.exp._calc_splitter(d)
        if isinstance(exp, Integer):
            if abs(exp.p)>2:
                n = exp.p//2
                r = exp.p - n
                if n!=r:
                    p1 = (base ** n)._calc_splitter(d)
                    p2 = (base ** r)._calc_splitter(d)
                    r = p1*p2
                else:
                    r = (base ** n)._calc_splitter(d) ** 2
            elif exp.p==-2:
                r = (1/base)._calc_splitter(d) ** 2
            else:
                r = base ** exp
        else:
            r = base ** exp
        if d.has_key(r):
            return d[r]
        s = d[r] = Temporary()
        return s

    @cacheit
    def count_ops(self, symbolic=True):
        if symbolic:
            return Add(*[t.count_ops(symbolic) for t in self[:]]) + Symbol('POW')
        return Add(*[t.count_ops(symbolic) for t in self.args[:]]) + 1

    def _eval_integral(self, s):
        if not self.exp.has(s):
            if self.base==s:
                n = self.exp+1
                return self.base ** n/n
            y = Symbol('y',dummy=True)
            x,ix = self.base.solve4linearsymbol(y,symbols=set([s]))
            if isinstance(x, Symbol):
                dx = 1/self.base.diff(x)
                if not dx.has(s):
                    return (y**self.exp*dx).integral(y).subs(y, self.base)

    def _eval_defined_integral(self, s, a, b):
        if not self.exp.has(s):
            if self.base==s:
                n = self.exp+1
                return (b**n-a**n)/n
            x,ix = self.base.solve4linearsymbol(s)
            if isinstance(x, Symbol):
                dx = ix.diff(x)
                if isinstance(dx, Number):
                    y = Symbol('y',dummy=True)
                    return (y**self.exp*dx).integral(y==[self.base.subs(s,a), self.base.subs(s,b)])

    def _eval_is_polynomial(self, syms):
        if self.exp.has(*syms):
            return False

        if self.base.has(*syms):
            # it would be nice to have is_nni working
            return self.base._eval_is_polynomial(syms) and \
                   self.exp.is_nonnegative and \
                   self.exp.is_integer
        else:
            return True

    def as_numer_denom(self):
        base, exp = self.as_base_exp()
        c,t = exp.as_coeff_terms()
        n,d = base.as_numer_denom()
        if c.is_negative:
            exp = -exp
            n,d = d,n
        return n ** exp, d ** exp

    def matches(pattern, expr, repl_dict={}, evaluate=False):
        Basic.matches.__doc__
        if evaluate:
            pat = pattern
            for old,new in repl_dict.items():
                pat = pat.subs(old, new)
            if pat!=pattern:
                return pat.matches(expr, repl_dict)

        expr = _sympify(expr)
        b, e = expr.as_base_exp()

        # special case, pattern = 1 and expr.exp can match to 0
        if expr is S.One:
            d = repl_dict.copy()
            d = pattern.exp.matches(S.Zero, d, evaluate=False)
            if d is not None:
                return d

        d = repl_dict.copy()
        d = pattern.base.matches(b, d, evaluate=False)
        if d is None:
            return None

        d = pattern.exp.matches(e, d, evaluate=True)
        if d is None:
            return Basic.matches(pattern, expr, repl_dict, evaluate)
        return d

    def _eval_oseries(self, order):
        """
        f**g + O(h) == (f+O(k))**g -> .. -> f**g + O(f**(g-1)*k), hence O(k)==O(h*f**(1-g)).
        If f->0 as x->0 then
        """
        x = order.symbols[0]
        e = self.exp
        b = self.base
        ln = C.log
        exp = C.exp
        if e.has(x):
            return exp(e * ln(b)).oseries(order)
        if b==x: return self
        b0 = b.limit(x,0)
        if b0 is S.Zero or b0.is_unbounded:
            lt = b.as_leading_term(x)
            o = order * lt**(1-e)
            bs = b.oseries(o)
            if isinstance(bs, Add):
                # bs -> lt + rest -> lt * (1 + (bs/lt - 1))
                return lt**e * ((bs/lt).expand()**e).oseries(order * lt**(-e))
            return bs**e
        o = order * (b0**-e)
        # b -> b0 + (b-b0) -> b0 * (1 + (b/b0-1))
        z = (b/b0-1)
        r = self._compute_oseries(z, o, self.taylor_term, lambda z: 1+z) * b0**e
        return r

    def _eval_as_leading_term(self, x):
        if not self.exp.has(x):
            return self.base.as_leading_term(x) ** self.exp
        return C.exp(self.exp * C.log(self.base)).as_leading_term(x)

    @cacheit
    def taylor_term(self, n, x, *previous_terms): # of (1+x)**e
        if n<0: return S.Zero
        x = _sympify(x)
        return C.Binomial(self.exp, n) * x**n

    def _sage_(self):
        return self[0]._sage_() ** self[1]._sage_()


# /cyclic/
import methods as _
_.Pow =     Pow
del _

import mul as _
_.Pow =     Pow
del _

import numbers as _
_.Pow =     Pow
del _
