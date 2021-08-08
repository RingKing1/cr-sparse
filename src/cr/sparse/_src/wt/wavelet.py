# Copyright 2021 CR.Sparse Development Team
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from enum import Enum, auto
from typing import NamedTuple, List, Dict, Tuple

import jax.numpy as jnp

from .families import FAMILY, wname_to_family_order, is_discrete_wavelet
from .coeffs import db, sym, coif, bior, dmey, sqrt2

class SYMMETRY(Enum):
    UNKNOWN = -1
    ASYMMETRIC = 0
    NEAR_SYMMETRIC = 1
    SYMMETRIC = 2
    ANTI_SYMMETRIC = 3



class BaseWavelet(NamedTuple):
    """Represents basic information about a wavelet
    """
    support_width: int = 0
    symmetry: SYMMETRY = SYMMETRY.UNKNOWN
    orthogonal: bool = False
    biorthogonal: bool = False
    compact_support: bool = False
    name: FAMILY = None
    family_name: str = None
    short_name: str = None

class DiscreteWavelet(NamedTuple):
    """Represents information about a discrete wavelet
    """
    support_width: int = -1
    """Length of the support for finite support wavelets"""
    symmetry: SYMMETRY = SYMMETRY.UNKNOWN
    """Indicates the kind of symmetry inside the wavelet"""
    orthogonal: bool = False
    """Indicates if the wavelet is orthogonal"""
    biorthogonal: bool = False
    """Indicates if the wavelet is biorthogonal"""
    compact_support: bool = False
    """Indicates if the wavelet has compact support"""
    name: str = ''
    """Name of the wavelet"""
    family_name: str = ''
    """Name of the wavelet family"""
    short_name: str = ''
    """Short name of the wavelet family"""
    dec_hi: jnp.DeviceArray = None
    """Decomposition high pass filter"""
    dec_lo: jnp.DeviceArray = None
    """Decomposition low pass filter"""
    rec_hi: jnp.DeviceArray = None
    """Reconstruction high pass filter"""
    rec_lo: jnp.DeviceArray = None
    """Reconstruction low pass filter"""
    dec_len: int = 0
    """Length of decomposition filters"""
    rec_len: int = 0
    """Length of reconstruction filters"""
    vanishing_moments_psi: int = 0
    """Number of vanishing moments of the wavelet function"""
    vanishing_moments_phi: int = 0
    """Number of vanishing moments of the scaling function"""

    def __str__(self):
        s = []
        for x in [
            u"Wavelet %s"           % self.name,
            u"  Family name:    %s" % self.family_name,
            u"  Short name:     %s" % self.short_name,
            u"  Filters length: %d" % self.dec_len,
            u"  Orthogonal:     %s" % self.orthogonal,
            u"  Biorthogonal:   %s" % self.biorthogonal,
            u"  Symmetry:       %s" % self.symmetry.name.lower(),
            u"  DWT:            True",
            u"  CWT:            False"
            ]:
            s.append(x.rstrip())
        return u'\n'.join(s)


def qmf(h):
    """Returns the quadrature mirror filter of a given filter"""
    g = h[::-1]
    g = g.at[1::2].set(-g[1::2])
    return g

def orthogonal_filter_bank(scaling_filter):
    """Returns the orthogonal filter bank for a given scaling filter"""
    # scaling filter must be even
    if not (scaling_filter.shape[0] % 2) == 0:
        raise ValueError('scaling_filter must be of even length.')
    # normalize
    rec_lo = sqrt2 * scaling_filter / jnp.sum(scaling_filter)
    dec_lo = rec_lo[::-1]
    rec_hi = qmf(rec_lo)
    dec_hi = rec_hi[::-1]
    return (dec_lo, dec_hi, rec_lo, rec_hi)

def filter_bank_(rec_lo):
    """Construct a filter bank from the saved values in coeffs.py"""
    dec_lo = rec_lo[::-1]
    rec_hi = qmf(rec_lo)
    dec_hi = rec_hi[::-1]
    return (dec_lo, dec_hi, rec_lo, rec_hi)

def mirror(h):
    n = h.shape[0]
    modulation = (-1)**jnp.arange(1, n+1)
    return modulation * h

def negate_evens(g):
    return g.at[0::2].set(-g[0::2])

def negate_odds(g):
    return g.at[1::2].set(-g[1::2])


def bior_index(n, m):
    idx = max = None
    if n == 1:
        idx = m // 2
        max = 5
    elif n == 2:
        idx = m // 2 -1 
        max = 8
    elif n == 3:
        idx = m // 2
        max = 9
    elif n == 4 or n == 5:
        if n == m:
            idx = 0
            max = m
    elif n == 6:
        if m == 8:
            idx = 0
            max = 8
    else:
        pass
    return idx, max


def build_discrete_wavelet(family: FAMILY, order: int):
    nv = family.value
    if nv is FAMILY.HAAR.value:
        dec_lo, dec_hi, rec_lo, rec_hi = filter_bank_(db[0])
        w = DiscreteWavelet(support_width=1,
            symmetry=SYMMETRY.ASYMMETRIC,
            orthogonal=True,
            biorthogonal=True,
            compact_support=True,
            name="Haar",
            family_name = "Haar",
            short_name="haar", 
            dec_hi=dec_hi,
            dec_lo=dec_lo,
            rec_hi=rec_hi,
            rec_lo=rec_lo,
            dec_len=2,
            rec_len=2,
            vanishing_moments_psi=1,
            vanishing_moments_phi=0)
        return w
    if nv == FAMILY.DB.value:
        index = order - 1
        if index >= len(db):
            return None
        filters_length = 2 * order
        dec_len = rec_len = filters_length
        dec_lo, dec_hi, rec_lo, rec_hi = filter_bank_(db[index])
        w = DiscreteWavelet(support_width=2*order-1,
            symmetry=SYMMETRY.ASYMMETRIC,
            orthogonal=True,
            biorthogonal=True,
            compact_support=True,
            name=f'db{order}',
            family_name = "Daubechies",
            short_name="db", 
            dec_hi=dec_hi,
            dec_lo=dec_lo,
            rec_hi=rec_hi,
            rec_lo=rec_lo,
            dec_len=dec_len,
            rec_len=rec_len,
            vanishing_moments_psi=order,
            vanishing_moments_phi=0)
        return w
    if nv == FAMILY.SYM.value:
        index = order - 2
        if index >= len(sym):
            return None
        filters_length = 2 * order
        dec_len = rec_len = filters_length
        dec_lo, dec_hi, rec_lo, rec_hi = filter_bank_(sym[index])
        w = DiscreteWavelet(support_width=2*order-1,
            symmetry=SYMMETRY.NEAR_SYMMETRIC,
            orthogonal=True,
            biorthogonal=True,
            compact_support=True,
            name=f'sym{order}',
            family_name = "Symlets",
            short_name="sym", 
            dec_hi=dec_hi,
            dec_lo=dec_lo,
            rec_hi=rec_hi,
            rec_lo=rec_lo,
            dec_len=dec_len,
            rec_len=rec_len,
            vanishing_moments_psi=order,
            vanishing_moments_phi=0)
        return w
    if nv == FAMILY.COIF.value:
        index = order - 1
        if index >= len(coif):
            return None
        filters_length = 6 * order
        dec_len = rec_len = filters_length
        dec_lo, dec_hi, rec_lo, rec_hi = filter_bank_(coif[index]*sqrt2)
        w = DiscreteWavelet(support_width=6*order-1,
            symmetry=SYMMETRY.NEAR_SYMMETRIC,
            orthogonal=True,
            biorthogonal=True,
            compact_support=True,
            name=f'coif{order}',
            family_name = "Coiflets",
            short_name="coif", 
            dec_hi=dec_hi,
            dec_lo=dec_lo,
            rec_hi=rec_hi,
            rec_lo=rec_lo,
            dec_len=dec_len,
            rec_len=rec_len,
            vanishing_moments_psi=2*order,
            vanishing_moments_phi=2*order-1)
        return w
    if nv == FAMILY.BIOR.value:
        n = order // 10
        m = order % 10
        idx, max = bior_index(n, m)
        if idx is None or max is None:
            return None
        arr = bior[n-1]
        if idx >= len(arr):
            return None
        filters_length = 2*m if n == 1 else 2*m + 2
        dec_len = rec_len = filters_length
        start = max - m
        rec_lo = arr[0][start:start+rec_len]
        dec_lo = arr[idx+1][::-1]
        rec_hi = negate_odds(dec_lo)
        dec_hi = negate_evens(rec_lo)
        w = DiscreteWavelet(support_width=6*order-1,
            symmetry=SYMMETRY.SYMMETRIC,
            orthogonal=False,
            biorthogonal=True,
            compact_support=True,
            name=f'bior{n}.{m}',
            family_name = "Biorthogonal",
            short_name="bior", 
            dec_hi=dec_hi,
            dec_lo=dec_lo,
            rec_hi=rec_hi,
            rec_lo=rec_lo,
            dec_len=dec_len,
            rec_len=rec_len,
            vanishing_moments_psi=2*order,
            vanishing_moments_phi=2*order-1)
        return w
    if nv == FAMILY.RBIO.value:
        n = order // 10
        m = order % 10
        idx, max = bior_index(n, m)
        if idx is None or max is None:
            return None
        arr = bior[n-1]
        if idx >= len(arr):
            return None
        filters_length = 2*m if n == 1 else 2*m + 2
        dec_len = rec_len = filters_length
        start = max - m
        dec_lo = arr[0][start:start+rec_len][::-1]
        rec_lo = arr[idx+1]
        rec_hi = negate_odds(dec_lo)
        dec_hi = negate_evens(rec_lo)
        w = DiscreteWavelet(support_width=6*order-1,
            symmetry=SYMMETRY.SYMMETRIC,
            orthogonal=False,
            biorthogonal=True,
            compact_support=True,
            name=f'rbio{n}.{m}',
            family_name = "Reverse biorthogonal",
            short_name="rbio", 
            dec_hi=dec_hi,
            dec_lo=dec_lo,
            rec_hi=rec_hi,
            rec_lo=rec_lo,
            dec_len=dec_len,
            rec_len=rec_len,
            vanishing_moments_psi=2*order,
            vanishing_moments_phi=2*order-1)
        return w
    if nv is FAMILY.DMEY.value:
        dec_len = rec_len = filters_length = 62
        dec_lo, dec_hi, rec_lo, rec_hi = filter_bank_(dmey)
        w = DiscreteWavelet(support_width=1,
            symmetry=SYMMETRY.SYMMETRIC,
            orthogonal=True,
            biorthogonal=True,
            compact_support=True,
            name="dmey",
            family_name = "Discrete Meyer (FIR Approximation)",
            short_name="dmey", 
            dec_hi=dec_hi,
            dec_lo=dec_lo,
            rec_hi=rec_hi,
            rec_lo=rec_lo,
            dec_len=dec_len,
            rec_len=rec_len,
            vanishing_moments_psi=-1,
            vanishing_moments_phi=-1)
        return w
    return None

def build_wavelet(name):
    """Builds a wavelet object by its name
    """
    name = name.lower()
    family, order = wname_to_family_order(name)
    if is_discrete_wavelet(family):
        return build_discrete_wavelet(family, order)
    # other wavelet types are not supported for now
    return None