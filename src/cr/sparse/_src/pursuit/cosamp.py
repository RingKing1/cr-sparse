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


import jax.numpy as jnp
from jax import vmap, jit, lax


from .defs import RecoverySolution

from .util import largest_indices

EXTRA_FACTOR = 2


def solve(Phi, y, K, max_iters=6, res_norm_rtol=1e-3):
    """Solves the sparse recovery problem :math:`y = \Phi x + e` using Compressive Sampling Matching Pursuit
    """
    ## Initialize some constants for the algorithm
    M, N = Phi.shape
    K2 = EXTRA_FACTOR * K
    K3 = K + K2
    # Let's conduct first iteration of OMP
    # squared norm of the signal
    y_norm_sqr = y.T @ y

    max_r_norm_sqr = y_norm_sqr * (res_norm_rtol ** 2) 

    def init():
        # compute the correlations of atoms with signal y
        h = Phi.T @ y
        # Pick largest 3K indices [this is first iteration]
        I_3k = largest_indices(h, K3)
        # Pick corresponding atoms to form the 3K wide subdictionary
        Phi_3I = Phi[:, I_3k]
        # Solve least squares over the selected indices
        x_3I, r_3I_norms, rank_3I, s_3I = jnp.linalg.lstsq(Phi_3I, y)
        # pick the K largest indices
        Ia = largest_indices(x_3I, K)
        # Identify indices for corresponding atoms
        I = I_3k[Ia]
        # Corresponding non-zero entries in the sparse approximation
        x_I = x_3I[Ia]
        # Form the subdictionary of corresponding atoms
        Phi_I = Phi[:, I]
        # Compute new residual
        r = y - Phi_I @ x_I
        # Compute residual norm squared
        r_norm_sqr = r.T @ r
        # Assemble the algorithm state at the end of first iteration
        return RecoverySolution(x_I=x_I, I=I, r=r, r_norm_sqr=r_norm_sqr, iterations=1)

    def iteration(state):
        # Index set of atoms for current solution
        I = state.I
        # Current iteration number
        iterations = state.iterations
        # compute the correlations of dictionary atoms with the residual
        h = Phi.T @ state.r
        # Ignore the previously selected atoms
        h = h.at[I].set(0)
        # Pick largest 2K indices
        I_2k = largest_indices(h, K2)
        # Combine with previous K indices to form a set of 3K indices
        I_3k = jnp.hstack((I, I_2k))
        # Pick corresponding atoms to form the 3K wide subdictionary
        Phi_3I = Phi[:, I_3k]
        # Solve least squares over the selected indices
        x_3I, r_3I_norms, rank_3I, s_3I = jnp.linalg.lstsq(Phi_3I, y)
        # pick the K largest indices
        Ia = largest_indices(x_3I, K)
        # Identify indices for corresponding atoms
        I = I_3k[Ia]
        # Corresponding non-zero entries in the sparse approximation
        x_I = x_3I[Ia]
        # Form the subdictionary of corresponding atoms
        Phi_I = Phi[:, I]
        # Compute new residual
        r = y - Phi_I @ x_I
        # Compute residual norm squared
        r_norm_sqr = r.T @ r
        return RecoverySolution(x_I=x_I, I=I, r=r, r_norm_sqr=r_norm_sqr, iterations=iterations+1)

    def cond(state):
        # limit on residual norm and number of iterations
        return jnp.logical_and(state.r_norm_sqr > max_r_norm_sqr, state.iterations < max_iters)

    state = lax.while_loop(cond, iteration, init())
    return state