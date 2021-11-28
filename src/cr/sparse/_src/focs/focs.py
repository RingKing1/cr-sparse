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

from .defs import FOCSOptions, FOCSState

import jax.numpy as jnp

import cr.sparse as crs
import cr.sparse.opt as opt
import cr.sparse.lop as lop

"""
Temporary notes:

apply_smooth is just smoothF with operator counting
apply_projector is just projectorF with operator counting
"""



def focs(smooth_f, prox_h, A, b, x0, options: FOCSOptions = FOCSOptions()):
    """First order conic solver driver routine
    """
    #print(options)
    # add the offset b to the input of smooth function f
    smooth_f = opt.smooth_func_translate(smooth_f, b)

    def init():
        in_shape = A.input_shape
        out_shape = A.output_shape
        x = x0

        # need to check if x is feasible
        C_x = prox_h.func(x)
        if jnp.isinf(C_x):
            # this is outside the domain. Let's project it back
            x, C_x = prox_h.prox_vec_val(x)

        # Compute A @ x
        A_x = A.times(x)
        g_Ax, f_x = smooth_f.grad_val(A_x)
        g_x = jnp.zeros_like(x)

        # y related variables
        y = x
        A_y = A_x
        C_y = jnp.inf
        f_y = f_x
        g_y = g_x
        g_Ay = g_Ax

        # z related variables
        z = x
        A_z = A_x
        C_z = C_x
        f_z = f_x
        g_z = g_x
        g_Az = g_Ax

        norm_x = crs.arr_rnorm(x)
        norm_dx = norm_x

        state = FOCSState(L=options.L0, theta=jnp.inf,
            x=x, A_x=A_x, g_Ax=g_Ax, g_x=g_x, f_x=f_x, C_x=C_x,
            y=y, A_y=A_y, g_Ay=g_Ay, g_y=g_y, f_y=f_y, C_y=C_y,
            z=z, A_z=A_z, g_Az=g_Az, g_z=g_z, f_z=f_z, C_z=C_z,
            norm_x=norm_x, norm_dx=norm_dx,
            iterations=0
        )
        return state

    state = init()
    #print(state)

    def advance_theta(theta_old,L,L_old):
        return 2/(1+jnp.sqrt(1+4*(L/L_old)/theta_old**2))

    def backtrack_L(x, A_x, g_Ax, y, A_y, g_Ay):
        """Improves the estimate of L
        """
        xy = x - y
        xy_sq = crs.arr_rnorm_sqr( xy )
        localL = 2 * crs.arr_rdot( A_x - A_y, g_Ax - g_Ay ) / xy_sq
        L = jnp.minimum(options.Lexact, localL )
        L = jnp.minimum(options.Lexact, jnp.maximum( localL, L / options.beta ) )
        return L

    def body_func(state):
        # update L
        L = state.L * options.alpha
        # update theta
        theta = advance_theta( state.theta, L, state.L)
        #print(L, theta)
        # update y
        y = (1 - theta) * state.x + theta * state.z
        # compute A @ y
        A_y = A.times(y)
        # compute gradient and value of f at A_y + b
        g_Ay, f_y = smooth_f.grad_val(A_y)
        # compute A^H g_Ay
        g_y = A.trans(g_Ay)
        # Scaled gradient
        step = 1 / ( theta * L )
        print(f'step={step:.2f}')
        # update z 
        z, C_z = prox_h.prox_vec_val(state.z - step * g_y, step)
        # compute A @ z
        A_z = A.times(z)
        # update x
        x = (1 - theta) * state.x + theta * z
        # compute A @ x
        A_x = A.times(x)
        # compute gradient and value of f at A_x + b
        g_Ax, f_x = smooth_f.grad_val(A_x)
        # improve the estimate of L
        L = backtrack_L(x, A_x, g_Ax, y, A_y, g_Ay)
        # compute parameters for convergence
        norm_x = crs.arr_rnorm(x)
        norm_dx = crs.arr_rnorm(x - state.x)

        state = FOCSState(L=L, theta=theta,
            x=x, A_x=A_x, g_Ax=g_Ax, g_x=state.g_x, f_x=f_x, C_x=state.C_x,
            y=y, A_y=A_y, g_Ay=g_Ay, g_y=g_y, f_y=f_y, C_y=state.C_y,
            z=z, A_z=A_z, g_Az=state.g_Az, g_z=state.g_z, f_z=state.f_z, C_z=C_z,
            norm_x=norm_x, norm_dx=norm_dx,
            iterations=state.iterations + 1
        )
        return state

    def outer_cond_func(state):
        a = state.iterations < options.max_iters
        b = state.norm_dx >= options.tol * jnp.maximum( state.norm_x, 1 )
        return jnp.logical_and(a, b)

    print(state.at_str)
    state = body_func(state)
    print(state.at_str)
    while outer_cond_func(state):
        state = body_func(state)
        print(state.at_str)
    return state