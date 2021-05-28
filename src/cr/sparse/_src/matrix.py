# Copyright 2021 Carnot Research Pvt Ltd
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

from .util import promote_arg_dtypes


def transpose(a):
    return jnp.swapaxes(a, -1, -2)

def hermitian(a):
    return jnp.conjugate(jnp.swapaxes(a, -1, -2))

def is_matrix(A):
    return A.ndim == 2

def is_square(A):
    shape = A.shape
    return A.ndim == 2 and shape[0] == shape[1]

def is_symmetric(A):
    shape = A.shape
    if A.ndim != 2: 
        return False
    return jnp.array_equal(A, A.T)

def is_hermitian(A):
    shape = A.shape
    if A.ndim != 2: 
        return False
    return jnp.array_equal(A, hermitian(A))

def is_positive_definite(A):
    if not is_symmetric(A):
        return False
    A = promote_arg_dtypes(A)
    return jnp.all(jnp.real(jnp.linalg.eigvals(A)) > 0)


def has_orthogonal_columns(A):
    G = A.T @ A
    m = G.shape[0]
    I = jnp.eye(m)
    return jnp.allclose(G, I, atol=m*1e-6)


def has_orthogonal_rows(A):
    G = A @ A.T
    m = G.shape[0]
    I = jnp.eye(m)
    return jnp.allclose(G, I, atol=m*1e-6)

def has_unitary_columns(A):
    G = hermitian(A) @ A
    m = G.shape[0]
    I = jnp.eye(m)
    return jnp.allclose(G, I, atol=m*1e-6)

def has_unitary_rows(A):
    G = A @ hermitian(A)
    m = G.shape[0]
    I = jnp.eye(m)
    return jnp.allclose(G, I, atol=m*1e-6)