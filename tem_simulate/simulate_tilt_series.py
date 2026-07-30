"""
TEM Tilt-Series Simulation Platform
=====================================

Simulates the EXACT scenario of the real TIF data:
  - One 3D structure (nanoparticle)
  - P copies sitting on a grid at RANDOM base orientations
  - Each copy imaged at K=41 known tilt angles (-60° to +60°, 3° step)
  - Optional noise, blur, background

The output matches the particle_stacks.npz format so the same
reconstruction code can be used on simulated and real data.

Includes a library of 20+ phantom shapes (from the old simulation code):
  sphere, cube, cylinder, torus, dumbbell, L_shape, helix, etc.

Usage (Jupyter):
    from simulate_tilt_series import simulate, list_phantoms
    list_phantoms()
    data = simulate('cube', n_particles=20, n_voxels=50, noise_std=0.02)
    # → saves sim_particle_stacks.npz
    
    # Then reconstruct:
    python reconstruct_tif.py sim_particle_stacks.npz -N 50 --iters 400

Usage (CLI):
    python simulate_tilt_series.py --phantom cube --n-particles 20 -N 50 --noise 0.02
    python simulate_tilt_series.py --phantom L_shape --n-particles 40 -N 50 --noise 0.03
    python simulate_tilt_series.py --list-phantoms

Author: Zhengnan Li
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from typing import Optional, Tuple
import time

import jax
import jax.numpy as jnp
from jax import random, jit, vmap

print(f"JAX {jax.__version__} | backend: {jax.default_backend()} | "
      f"devices: {jax.devices()}")


# ============================================================
# COORDINATE UTILITIES
# ============================================================

def _grid(n):
    """Create [-1, 1]^3 coordinate grid."""
    c = jnp.linspace(-1, 1, n)
    Z, Y, X = jnp.meshgrid(c, c, c, indexing='ij')
    return X, Y, Z


# ============================================================
# PHANTOM LIBRARY
# ============================================================

# --- Basic solids ---

def phantom_sphere(n, radius=0.4):
    X, Y, Z = _grid(n)
    return (jnp.sqrt(X**2 + Y**2 + Z**2) < radius).astype(float)

def phantom_cube(n, half_side=0.3):
    X, Y, Z = _grid(n)
    return ((jnp.abs(X) < half_side) & (jnp.abs(Y) < half_side) &
            (jnp.abs(Z) < half_side)).astype(float)

def phantom_cylinder(n, radius=0.3, height=0.8):
    X, Y, Z = _grid(n)
    return ((jnp.sqrt(X**2 + Y**2) < radius) &
            (jnp.abs(Z) < height/2)).astype(float)

def phantom_cone(n, base_radius=0.4, height=0.8):
    X, Y, Z = _grid(n)
    z_norm = (Z + height/2) / height
    local_r = base_radius * (1 - jnp.clip(z_norm, 0, 1))
    return ((jnp.sqrt(X**2 + Y**2) < local_r) &
            (Z > -height/2) & (Z < height/2)).astype(float)

def phantom_capsule(n, radius=0.2, height=0.6):
    X, Y, Z = _grid(n)
    R_xy = jnp.sqrt(X**2 + Y**2)
    half = height/2 - radius
    cyl = (R_xy < radius) & (jnp.abs(Z) < half)
    top = (jnp.sqrt(X**2 + Y**2 + (Z-half)**2) < radius) & (Z >= half)
    bot = (jnp.sqrt(X**2 + Y**2 + (Z+half)**2) < radius) & (Z <= -half)
    return (cyl | top | bot).astype(float)

def phantom_torus(n, major=0.4, minor=0.15):
    X, Y, Z = _grid(n)
    R_xy = jnp.sqrt(X**2 + Y**2)
    return (jnp.sqrt((R_xy - major)**2 + Z**2) < minor).astype(float)

# --- Hollow shapes ---

def phantom_hollow_sphere(n, outer=0.4, inner=0.25):
    X, Y, Z = _grid(n)
    R = jnp.sqrt(X**2 + Y**2 + Z**2)
    return ((R < outer) & (R >= inner)).astype(float)

def phantom_tube(n, outer=0.3, inner=0.2, height=0.8):
    X, Y, Z = _grid(n)
    R_xy = jnp.sqrt(X**2 + Y**2)
    return ((R_xy < outer) & (R_xy >= inner) & (jnp.abs(Z) < height/2)).astype(float)

def phantom_core_shell(n, core_r=0.2, shell_r=0.35):
    X, Y, Z = _grid(n)
    R = jnp.sqrt(X**2 + Y**2 + Z**2)
    return (R < core_r).astype(float) * 1.0 + ((R >= core_r) & (R < shell_r)).astype(float) * 0.5

# --- Compound shapes ---

def phantom_dumbbell(n, sr=0.2, rod_r=0.08, rod_len=0.4):
    X, Y, Z = _grid(n)
    off = rod_len/2 + sr*0.8
    s1 = phantom_sphere(n, sr)  # won't work directly, need offset
    # Manual
    R1 = jnp.sqrt(X**2 + Y**2 + (Z - off)**2)
    R2 = jnp.sqrt(X**2 + Y**2 + (Z + off)**2)
    R_xy = jnp.sqrt(X**2 + Y**2)
    s = ((R1 < sr) | (R2 < sr) |
         ((R_xy < rod_r) & (jnp.abs(Z) < off))).astype(float)
    return jnp.clip(s, 0, 1)

def phantom_asymmetric_dumbbell(n, r1=0.25, r2=0.15, rod_r=0.06, rod_len=0.35):
    X, Y, Z = _grid(n)
    off1 = rod_len/2 + r1*0.7
    off2 = rod_len/2 + r2*0.7
    R1 = jnp.sqrt(X**2 + Y**2 + (Z - off1)**2)
    R2 = jnp.sqrt(X**2 + Y**2 + (Z + off2)**2)
    R_xy = jnp.sqrt(X**2 + Y**2)
    s1 = (R1 < r1).astype(float)
    s2 = (R2 < r2).astype(float) * 0.7
    rod = ((R_xy < rod_r) & (jnp.abs(Z) < max(off1, off2))).astype(float) * 0.5
    return jnp.clip(s1 + s2 + rod, 0, 1)

# --- Asymmetric shapes (best for testing orientation recovery) ---

def phantom_L_shape(n, length=0.5, width=0.15, height=0.15):
    X, Y, Z = _grid(n)
    arm1 = ((X > -length/2) & (X < length/2) &
            (jnp.abs(Y) < width/2) & (jnp.abs(Z) < height/2))
    arm2 = ((X > length/2 - width) & (X < length/2) &
            (Y > -width/2) & (Y < length/2) &
            (jnp.abs(Z) < height/2))
    return (arm1 | arm2).astype(float)

def phantom_T_shape(n, top_len=0.6, stem_len=0.5, width=0.12, height=0.12):
    X, Y, Z = _grid(n)
    top = ((jnp.abs(X) < top_len/2) & (jnp.abs(Y) < width/2) &
           (Z > 0) & (Z < height))
    stem = ((jnp.abs(X) < width/2) & (jnp.abs(Y) < width/2) &
            (Z > -stem_len) & (Z < height/2))
    return (top | stem).astype(float)

def phantom_box_notch(n, size=0.35, notch=0.25):
    X, Y, Z = _grid(n)
    box = (jnp.abs(X) < size) & (jnp.abs(Y) < size) & (jnp.abs(Z) < size)
    cut = (X > size - notch) & (Y > size - notch) & (Z > size - notch)
    return (box & ~cut).astype(float)

def phantom_box_slot(n, size=0.35, slot_w=0.15, slot_d=0.25):
    X, Y, Z = _grid(n)
    box = (jnp.abs(X) < size) & (jnp.abs(Y) < size) & (jnp.abs(Z) < size)
    slot = (jnp.abs(X) < slot_w) & (jnp.abs(Y) < slot_w) & (Z > size - slot_d)
    return (box & ~slot).astype(float)

def phantom_star(n, n_arms=6, arm_len=0.4, arm_r=0.08, core_r=0.15):
    X, Y, Z = _grid(n)
    R = jnp.sqrt(X**2 + Y**2 + Z**2)
    vol = (R < core_r).astype(float)
    for i in range(n_arms):
        angle = 2 * jnp.pi * i / n_arms
        dx, dy = jnp.cos(angle), jnp.sin(angle)
        X_rot = X * dx + Y * dy
        Y_rot = -X * dy + Y * dx
        arm = (jnp.sqrt(Y_rot**2 + Z**2) < arm_r) & (X_rot > 0) & (X_rot < arm_len)
        vol = jnp.maximum(vol, arm.astype(float))
    return vol

def phantom_spiral(n, turns=1.5, radius=0.3, tube_r=0.08, pitch=0.3):
    X, Y, Z = _grid(n)
    vol = jnp.zeros((n, n, n))
    t = jnp.linspace(0, turns * 2 * jnp.pi, 150)
    for ti in t:
        hx = radius * jnp.cos(ti)
        hy = radius * jnp.sin(ti)
        hz = pitch * ti / (2 * jnp.pi) - turns * pitch / 2
        dist = jnp.sqrt((X - hx)**2 + (Y - hy)**2 + (Z - hz)**2)
        vol = jnp.maximum(vol, (dist < tube_r).astype(float))
    return vol

def phantom_shepp_logan(n):
    X, Y, Z = _grid(n)
    vol = jnp.zeros((n, n, n))
    ellipsoids = [
        ((0,0,0), (0.69,0.92,0.9), 2.0),
        ((0,0,0), (0.66,0.88,0.87), -0.98),
        ((0.22,0,-0.25), (0.11,0.31,0.22), -0.02),
        ((-0.22,0,-0.25), (0.16,0.41,0.28), -0.02),
        ((0,0.35,-0.25), (0.21,0.25,0.35), 0.01),
        ((0,0.1,-0.25), (0.046,0.046,0.046), 0.01),
    ]
    for center, radii, inten in ellipsoids:
        R = jnp.sqrt(((X-center[0])/radii[0])**2 +
                      ((Y-center[1])/radii[1])**2 +
                      ((Z-center[2])/radii[2])**2)
        vol = vol + (R < 1).astype(float) * inten
    return jnp.clip(vol, 0, 1)

def phantom_random_blobs(n, n_blobs=5, seed=42):
    key = random.PRNGKey(seed)
    X, Y, Z = _grid(n)
    vol = jnp.zeros((n, n, n))
    keys = random.split(key, n_blobs * 3)
    for i in range(n_blobs):
        pos = random.uniform(keys[3*i], (3,), minval=-0.4, maxval=0.4)
        r = random.uniform(keys[3*i+1], minval=0.08, maxval=0.18)
        inten = random.uniform(keys[3*i+2], minval=0.5, maxval=1.0)
        R = jnp.sqrt((X-pos[0])**2 + (Y-pos[1])**2 + (Z-pos[2])**2)
        vol = vol + (R < r).astype(float) * inten
    return jnp.clip(vol, 0, 1)

# --- Nanoparticle-like: truncated octahedron (faceted, like real data!) ---

def phantom_truncated_octahedron(n, size=0.45, trunc=0.3):
    """
    Truncated octahedron — a common nanoparticle shape.
    Looks like the real data: faceted, roughly round but with flat faces.
    """
    X, Y, Z = _grid(n)
    # Octahedron: |x| + |y| + |z| < size
    octa = (jnp.abs(X) + jnp.abs(Y) + jnp.abs(Z)) < size
    # Truncate: also |x|, |y|, |z| < trunc
    trunc_mask = (jnp.abs(X) < trunc) & (jnp.abs(Y) < trunc) & (jnp.abs(Z) < trunc)
    return (octa & trunc_mask).astype(float)

def phantom_cuboctahedron(n, size=0.4):
    """
    Cuboctahedron — another common nanocrystal shape.
    Intersection of cube and octahedron.
    """
    X, Y, Z = _grid(n)
    cube = (jnp.abs(X) < size) & (jnp.abs(Y) < size) & (jnp.abs(Z) < size)
    octa = (jnp.abs(X) + jnp.abs(Y) + jnp.abs(Z)) < size * 1.5
    return (cube & octa).astype(float)

def phantom_icosahedron_approx(n, size=0.4):
    """Approximate icosahedron using multiple half-planes."""
    X, Y, Z = _grid(n)
    phi = (1 + np.sqrt(5)) / 2  # golden ratio
    vol = jnp.ones((n, n, n), dtype=bool)
    # 20-sided approximation using face normals
    normals = [
        (1, 1, 1), (1, 1, -1), (1, -1, 1), (1, -1, -1),
        (-1, 1, 1), (-1, 1, -1), (-1, -1, 1), (-1, -1, -1),
        (0, phi, 1/phi), (0, phi, -1/phi), (0, -phi, 1/phi), (0, -phi, -1/phi),
        (1/phi, 0, phi), (-1/phi, 0, phi), (1/phi, 0, -phi), (-1/phi, 0, -phi),
        (phi, 1/phi, 0), (phi, -1/phi, 0), (-phi, 1/phi, 0), (-phi, -1/phi, 0),
    ]
    for nx, ny, nz in normals:
        norm = np.sqrt(nx**2 + ny**2 + nz**2)
        vol = vol & ((X*nx + Y*ny + Z*nz) / norm < size)
    return vol.astype(float)

# ============================================================
# MORE PHANTOMS
# ============================================================

# --- Faceted nanoparticle shapes ---

def phantom_octahedron(n, size=0.5):
    """Regular octahedron — Oh, common NP facet shape."""
    X, Y, Z = _grid(n)
    return ((jnp.abs(X) + jnp.abs(Y) + jnp.abs(Z)) < size).astype(float)

def phantom_tetrahedron(n, size=0.5):
    """Regular tetrahedron — Td, vertices at alternating cube corners."""
    X, Y, Z = _grid(n)
    n1 = ( X + Y + Z) < size
    n2 = ( X - Y - Z) < size
    n3 = (-X + Y - Z) < size
    n4 = (-X - Y + Z) < size
    return (n1 & n2 & n3 & n4).astype(float)

def phantom_hex_prism(n, radius=0.35, height=0.5):
    """Hexagonal prism — D6h, common for plate-like NPs."""
    X, Y, Z = _grid(n)
    R = jnp.ones((n, n, n), dtype=bool)
    for i in range(6):
        ang = jnp.pi * i / 3
        R = R & ((X * jnp.cos(ang) + Y * jnp.sin(ang)) < radius)
    R = R & (jnp.abs(Z) < height / 2)
    return R.astype(float)

def phantom_pentagonal_bipyramid(n, radius=0.4, height=0.75):
    """Pentagonal bipyramid (decahedron) — D5h, 5-fold NP shape."""
    X, Y, Z = _grid(n)
    z_norm = jnp.abs(Z) / (height / 2)
    local_r = radius * jnp.clip(1 - z_norm, 0, 1)
    pent = jnp.ones((n, n, n), dtype=bool)
    for i in range(5):
        ang = 2 * jnp.pi * i / 5
        pent = pent & ((X * jnp.cos(ang) + Y * jnp.sin(ang)) < local_r)
    return (pent & (jnp.abs(Z) < height / 2)).astype(float)

def phantom_concave_cube(n, size=0.4, cap_r=0.45):
    """Cube with concave (carved) faces — Oh, common in NP synthesis."""
    X, Y, Z = _grid(n)
    cube = (jnp.abs(X) < size) & (jnp.abs(Y) < size) & (jnp.abs(Z) < size)
    caps = jnp.zeros((n, n, n), dtype=bool)
    for fx, fy, fz in [(size,0,0), (-size,0,0), (0,size,0),
                        (0,-size,0), (0,0,size), (0,0,-size)]:
        caps = caps | (jnp.sqrt((X-fx)**2 + (Y-fy)**2 + (Z-fz)**2) < cap_r)
    return (cube & ~caps).astype(float)

def phantom_stellated_octahedron(n, oct_size=0.35, spike_len=0.55, spike_r=0.05):
    """Octahedron with spikes from each vertex — Oh, spiky NP."""
    X, Y, Z = _grid(n)
    core = (jnp.abs(X) + jnp.abs(Y) + jnp.abs(Z)) < oct_size
    vol = core.astype(float)
    for d in [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]:
        proj = X*d[0] + Y*d[1] + Z*d[2]
        perp_sq = X**2 + Y**2 + Z**2 - proj**2
        spike = (perp_sq < spike_r**2) & (proj > 0) & (proj < spike_len)
        vol = jnp.maximum(vol, spike.astype(float))
    return vol

# --- Axial / rod-like ---

def phantom_nanorod(n, radius=0.10, length=0.9):
    """Elongated capsule with rounded ends — D∞h, common rod NP."""
    X, Y, Z = _grid(n)
    R_xy = jnp.sqrt(X**2 + Y**2)
    half = length/2 - radius
    cyl = (R_xy < radius) & (jnp.abs(Z) < half)
    top = (jnp.sqrt(X**2 + Y**2 + (Z-half)**2) < radius) & (Z >= half)
    bot = (jnp.sqrt(X**2 + Y**2 + (Z+half)**2) < radius) & (Z <= -half)
    return (cyl | top | bot).astype(float)

def phantom_pyramid(n, base=0.55, height=0.7):
    """Square-base pyramid — C4v."""
    X, Y, Z = _grid(n)
    z_norm = (Z + height/2) / height
    local_half = (base / 2) * jnp.clip(1 - z_norm, 0, 1)
    return ((jnp.abs(X) < local_half) & (jnp.abs(Y) < local_half) &
            (Z > -height/2) & (Z < height/2)).astype(float)

def phantom_bicone(n, radius=0.35, height=0.8):
    """Bicone (two cones tip-to-tip) — D∞h, hourglass."""
    X, Y, Z = _grid(n)
    z_norm = jnp.abs(Z) / (height / 2)
    local_r = radius * jnp.clip(1 - z_norm, 0, 1)
    R_xy = jnp.sqrt(X**2 + Y**2)
    return ((R_xy < local_r) & (jnp.abs(Z) < height/2)).astype(float)

# --- Polar / Janus ---

def phantom_hemisphere(n, radius=0.45):
    """Hemisphere — C∞v."""
    X, Y, Z = _grid(n)
    return ((jnp.sqrt(X**2 + Y**2 + Z**2) < radius) & (Z > 0)).astype(float)

def phantom_janus(n, radius=0.4):
    """Janus sphere — two hemispheres with different intensity (C∞v)."""
    X, Y, Z = _grid(n)
    R = jnp.sqrt(X**2 + Y**2 + Z**2)
    inside = R < radius
    return (inside & (Z > 0)).astype(float) * 1.0 + \
           (inside & (Z <= 0)).astype(float) * 0.5

def phantom_mushroom(n, stem_r=0.12, stem_h=0.5, cap_r=0.3):
    """Mushroom — cylindrical stem + hemispherical cap (C∞v)."""
    X, Y, Z = _grid(n)
    R_xy = jnp.sqrt(X**2 + Y**2)
    stem = (R_xy < stem_r) & (Z > -stem_h) & (Z < 0)
    cap = (jnp.sqrt(X**2 + Y**2 + Z**2) < cap_r) & (Z >= 0)
    return (stem | cap).astype(float)

# --- Branched / multipod ---

def phantom_tetrapod(n, arm_r=0.08, arm_len=0.55, core_r=0.12):
    """Tetrapod — 4 arms in tetrahedral directions (Td), classic NP."""
    X, Y, Z = _grid(n)
    R = jnp.sqrt(X**2 + Y**2 + Z**2)
    vol = (R < core_r).astype(float)
    dirs = jnp.array([[1,1,1],[1,-1,-1],[-1,1,-1],[-1,-1,1]]) / jnp.sqrt(3.0)
    for d in dirs:
        proj = X*d[0] + Y*d[1] + Z*d[2]
        perp_sq = X**2 + Y**2 + Z**2 - proj**2
        arm = (perp_sq < arm_r**2) & (proj > 0) & (proj < arm_len)
        vol = jnp.maximum(vol, arm.astype(float))
    return vol

def phantom_snowflake_3d(n, arm_r=0.06, arm_len=0.6):
    """3D snowflake — 6 perpendicular arms (Oh)."""
    X, Y, Z = _grid(n)
    arm_x = (jnp.sqrt(Y**2 + Z**2) < arm_r) & (jnp.abs(X) < arm_len)
    arm_y = (jnp.sqrt(X**2 + Z**2) < arm_r) & (jnp.abs(Y) < arm_len)
    arm_z = (jnp.sqrt(X**2 + Y**2) < arm_r) & (jnp.abs(Z) < arm_len)
    return (arm_x | arm_y | arm_z).astype(float)

# --- Asymmetric C1 (best for orientation recovery) ---

def phantom_F_shape(n):
    """Letter F — classic asymmetric test phantom, no symmetries at all."""
    X, Y, Z = _grid(n)
    bar = (jnp.abs(X + 0.15) < 0.08) & (jnp.abs(Y) < 0.5) & (jnp.abs(Z) < 0.1)
    top = (X > -0.23) & (X < 0.35) & (Y > 0.35) & (Y < 0.5) & (jnp.abs(Z) < 0.1)
    mid = (X > -0.23) & (X < 0.2)  & (Y > 0.0)  & (Y < 0.13) & (jnp.abs(Z) < 0.1)
    return (bar | top | mid).astype(float)

def phantom_Y_shape(n, arm_len=0.45, arm_r=0.08):
    """Y-shape — 3 in-plane arms at 120° (C3v)."""
    X, Y, Z = _grid(n)
    vol = jnp.zeros((n, n, n))
    for i in range(3):
        ang = 2*jnp.pi*i/3 + jnp.pi/2
        dx, dy = jnp.cos(ang), jnp.sin(ang)
        proj = X*dx + Y*dy
        perp = -X*dy + Y*dx
        arm = (jnp.sqrt(perp**2 + Z**2) < arm_r) & (proj > 0) & (proj < arm_len)
        vol = jnp.maximum(vol, arm.astype(float))
    return vol

def phantom_crescent(n, R=0.45, r=0.4, offset=0.22):
    """Crescent moon — sphere minus offset sphere (C1)."""
    X, Y, Z = _grid(n)
    full = jnp.sqrt(X**2 + Y**2 + Z**2) < R
    cut  = jnp.sqrt((X - offset)**2 + Y**2 + Z**2) < r
    return (full & ~cut).astype(float)

def phantom_trimer_chain(n, r1=0.18, r2=0.13, r3=0.10):
    """Asymmetric trimer — 3 unequal spheres in a bent chain (strongly C1)."""
    X, Y, Z = _grid(n)
    s1 = jnp.sqrt((X + 0.35)**2 +  Y**2          +  Z**2) < r1
    s2 = jnp.sqrt( X**2          + (Y - 0.10)**2 +  Z**2) < r2
    s3 = jnp.sqrt((X - 0.28)**2  +  Y**2         + (Z - 0.18)**2) < r3
    return (s1 | s2 | s3).astype(float)

def phantom_asym_tetrapod(n, core_r=0.10):
    """Tetrapod with 4 different arm lengths and radii — fully C1."""
    X, Y, Z = _grid(n)
    R = jnp.sqrt(X**2 + Y**2 + Z**2)
    vol = (R < core_r).astype(float)
    arms = [
        ([ 1, 1, 1], 0.55, 0.11),
        ([ 1,-1,-1], 0.40, 0.08),
        ([-1, 1,-1], 0.35, 0.07),
        ([-1,-1, 1], 0.28, 0.05),
    ]
    for dir_vec, length, radius in arms:
        d = jnp.array(dir_vec) / jnp.sqrt(3.0)
        proj = X*d[0] + Y*d[1] + Z*d[2]
        perp_sq = X**2 + Y**2 + Z**2 - proj**2
        arm = (perp_sq < radius**2) & (proj > 0) & (proj < length)
        vol = jnp.maximum(vol, arm.astype(float))
    return vol


# --- Registry ---

PHANTOMS = {
    # Symmetric
    'sphere':           (phantom_sphere,         'O(3)',  'Sphere'),
    'cube':             (phantom_cube,           'Oh',    'Cube'),
    'hollow_sphere':    (phantom_hollow_sphere,  'O(3)',  'Hollow sphere'),
    'core_shell':       (phantom_core_shell,     'O(3)',  'Core-shell'),
    # Axial
    'cylinder':         (phantom_cylinder,       'C∞v',   'Cylinder'),
    'cone':             (phantom_cone,           'C∞v',   'Cone'),
    'tube':             (phantom_tube,           'C∞v',   'Hollow tube'),
    'torus':            (phantom_torus,          'C∞v',   'Torus'),
    'capsule':          (phantom_capsule,        'C∞v',   'Capsule'),
    'dumbbell':         (phantom_dumbbell,       'D∞h',   'Dumbbell'),
    # Discrete symmetry
    'star_3':           (lambda n: phantom_star(n, 3),  'C3v',  '3-arm star'),
    'star_6':           (lambda n: phantom_star(n, 6),  'C6v',  '6-arm star'),
    # Nanoparticle shapes
    'trunc_octahedron': (phantom_truncated_octahedron, 'Oh',  '⭐ Truncated octahedron (faceted NP)'),
    'cuboctahedron':    (phantom_cuboctahedron,  'Oh',    '⭐ Cuboctahedron (faceted NP)'),
    'icosahedron':      (phantom_icosahedron_approx, 'Ih', '⭐ Approx. icosahedron'),
    # Asymmetric (C1) — best for testing orientation recovery
    'asym_dumbbell':    (phantom_asymmetric_dumbbell, 'C1', '⭐ Asymmetric dumbbell'),
    'L_shape':          (phantom_L_shape,        'C1',    '⭐ L-block'),
    'T_shape':          (phantom_T_shape,        'Cs',    'T-block'),
    'spiral':           (phantom_spiral,         'C1',    '⭐ Helix'),
    'box_slot':         (phantom_box_slot,       'C1',    '⭐ Box with slot'),
    'box_notch':        (phantom_box_notch,      'C1',    '⭐ Box with notch'),
    'shepp_logan':      (phantom_shepp_logan,    'C1',    '⭐ Shepp-Logan'),
    'random_blobs':     (phantom_random_blobs,   'C1',    '⭐ Random blobs'),
    # --- Additional faceted NP shapes ---
    'octahedron':         (phantom_octahedron,           'Oh',   'Regular octahedron'),
    'tetrahedron':        (phantom_tetrahedron,          'Td',   '⭐ Regular tetrahedron (faceted NP)'),
    'hex_prism':          (phantom_hex_prism,            'D6h',  'Hexagonal prism (plate NP)'),
    'penta_bipyramid':    (phantom_pentagonal_bipyramid, 'D5h',  '⭐ Pentagonal bipyramid (decahedron)'),
    'concave_cube':       (phantom_concave_cube,         'Oh',   '⭐ Concave cube (carved faces)'),
    'stellated_oct':      (phantom_stellated_octahedron, 'Oh',   '⭐ Stellated octahedron (spiky)'),
    # --- Axial / rod-like ---
    'nanorod':            (phantom_nanorod,              'D∞h',  'Elongated nanorod'),
    'pyramid':            (phantom_pyramid,              'C4v',  'Square pyramid'),
    'bicone':             (phantom_bicone,               'D∞h',  'Bicone / hourglass'),
    # --- Polar / Janus ---
    'hemisphere':         (phantom_hemisphere,           'C∞v',  'Hemisphere'),
    'janus':              (phantom_janus,                'C∞v',  '⭐ Janus sphere (two-tone)'),
    'mushroom':           (phantom_mushroom,             'C∞v',  '⭐ Mushroom'),
    # --- Branched ---
    'tetrapod':           (phantom_tetrapod,             'Td',   '⭐ Tetrapod (4 tetrahedral arms)'),
    'snowflake_3d':       (phantom_snowflake_3d,         'Oh',   '3D snowflake (6 perp arms)'),
    # --- Asymmetric C1 ---
    'F_shape':            (phantom_F_shape,              'C1',   '⭐ Letter F (classic test)'),
    'Y_shape':            (phantom_Y_shape,              'C3v',  'Y-shape'),
    'crescent':           (phantom_crescent,             'C1',   '⭐ Crescent moon'),
    'trimer_chain':       (phantom_trimer_chain,         'C1',   '⭐ Asymmetric trimer chain'),
    'asym_tetrapod':      (phantom_asym_tetrapod,        'C1',   '⭐ Asymmetric tetrapod'),
}


def list_phantoms():
    """Print all available phantoms."""
    print(f"{'Name':<20} {'Symmetry':<8} {'Description'}")
    print("-" * 60)
    for name, (_, sym, desc) in PHANTOMS.items():
        print(f"{name:<20} {sym:<8} {desc}")


def get_phantom(name, n):
    if name not in PHANTOMS:
        available = ', '.join(PHANTOMS.keys())
        raise ValueError(f"Unknown phantom '{name}'. Available: {available}")
    return PHANTOMS[name][0](n)


# ============================================================
# QUATERNION UTILITIES
# ============================================================

def random_quaternions(key, n):
    """Uniform random quaternions on SO(3)."""
    keys = random.split(key, 3)
    u1 = random.uniform(keys[0], (n,))
    u2 = random.uniform(keys[1], (n,)) * 2 * jnp.pi
    u3 = random.uniform(keys[2], (n,)) * 2 * jnp.pi
    return jnp.stack([
        jnp.sqrt(1-u1) * jnp.sin(u2),
        jnp.sqrt(1-u1) * jnp.cos(u2),
        jnp.sqrt(u1) * jnp.sin(u3),
        jnp.sqrt(u1) * jnp.cos(u3),
    ], axis=1)


def quat_to_rotmat(q):
    q = q / (jnp.linalg.norm(q) + 1e-8)
    w, x, y, z = q
    return jnp.array([
        [1-2*(y*y+z*z), 2*(x*y-w*z),   2*(x*z+w*y)],
        [2*(x*y+w*z),   1-2*(x*x+z*z), 2*(y*z-w*x)],
        [2*(x*z-w*y),   2*(y*z+w*x),   1-2*(x*x+y*y)],
    ])


def tilt_Ry(theta):
    c, s = jnp.cos(theta), jnp.sin(theta)
    return jnp.array([[c,0,s],[0,1,0],[-s,0,c]])


# ============================================================
# FORWARD MODEL
# ============================================================

def make_projector(N):
    """Build forward projector: rotate volume, project along Z."""
    coords = jnp.linspace(-1, 1, N)
    Z, Y, X = jnp.meshgrid(coords, coords, coords, indexing='ij')
    grid = jnp.stack([X.ravel(), Y.ravel(), Z.ravel()], axis=0)

    def trilinear(vol, pts):
        x=(pts[0]+1)/2*(N-1); y=(pts[1]+1)/2*(N-1); z=(pts[2]+1)/2*(N-1)
        x=jnp.clip(x,0,N-1.001); y=jnp.clip(y,0,N-1.001); z=jnp.clip(z,0,N-1.001)
        x0=jnp.floor(x).astype(jnp.int32); y0=jnp.floor(y).astype(jnp.int32); z0=jnp.floor(z).astype(jnp.int32)
        x1=jnp.minimum(x0+1,N-1); y1=jnp.minimum(y0+1,N-1); z1=jnp.minimum(z0+1,N-1)
        xd=x-x0; yd=y-y0; zd=z-z0
        c000=vol[z0,y0,x0]; c001=vol[z0,y0,x1]; c010=vol[z0,y1,x0]; c011=vol[z0,y1,x1]
        c100=vol[z1,y0,x0]; c101=vol[z1,y0,x1]; c110=vol[z1,y1,x0]; c111=vol[z1,y1,x1]
        c00=c000*(1-xd)+c001*xd; c01=c010*(1-xd)+c011*xd
        c10=c100*(1-xd)+c101*xd; c11=c110*(1-xd)+c111*xd
        c0=c00*(1-yd)+c01*yd; c1=c10*(1-yd)+c11*yd
        return c0*(1-zd)+c1*zd

    def project_with_R(vol, R):
        src = R.T @ grid
        return jnp.sum(trilinear(vol, src).reshape(N,N,N), axis=0)

    def project_tilt(vol, theta):
        return project_with_R(vol, tilt_Ry(theta))

    def project_particle_tilt(vol, q, theta):
        """Full forward: R_total = R_tilt(θ) @ R_particle(q)"""
        R_p = quat_to_rotmat(q)
        R_t = tilt_Ry(theta)
        R_total = R_t @ R_p
        return project_with_R(vol, R_total)

    return {
        'project_tilt': jit(project_tilt),
        'project_all_tilts': jit(vmap(project_tilt, in_axes=(None, 0))),
        'project_particle_tilt': jit(project_particle_tilt),
    }


# ============================================================
# SIMULATION
# ============================================================

def simulate(phantom_name: str = 'trunc_octahedron',
             n_voxels: int = 50,
             n_particles: int = 20,
             n_tilts: int = 41,
             tilt_range: Tuple[float, float] = (-60.0, 60.0),
             noise_std: float = 0.02,
             intensity_variation: float = 0.1,
             seed: int = 42,
             output: str = "sim_particle_stacks.npz",
             phantom_array: Optional[np.ndarray] = None):
    """
    Simulate TEM tilt series for multiple particles.

    Each particle is the same 3D structure at a random base orientation.
    The tilt series images are generated by:
        image_{p,k} = scale_p * project( R_tilt(θ_k) @ R_particle(q_p), volume ) + noise

    Parameters
    ----------
    phantom_name : name from PHANTOMS registry (ignored if phantom_array is given,
                   but still used as a label in the saved npz / plots)
    n_voxels : volume resolution (N^3)
    n_particles : number of particles (each at random orientation)
    n_tilts : number of tilt angles
    tilt_range : (min_deg, max_deg)
    noise_std : Gaussian noise std (relative to signal)
    intensity_variation : random per-particle intensity variation (±)
    seed : random seed
    output : output npz path
    phantom_array : optional (n_voxels, n_voxels, n_voxels) density volume to use
                    in place of a registry phantom (e.g. a real CT/CBCT volume)

    Returns
    -------
    dict with all simulation data including ground truth
    """
    key = random.PRNGKey(seed)
    N = n_voxels
    P = n_particles
    K = n_tilts

    print(f"\n{'='*60}")
    print(f"SIMULATING TILT SERIES")
    print(f"  Phantom: {phantom_name}")
    print(f"  P={P} particles, K={K} tilts, N={N}")
    print(f"  Tilt: {tilt_range[0]:.0f}° to {tilt_range[1]:.0f}°")
    print(f"  Noise: σ={noise_std}")
    print(f"{'='*60}")

    # Create phantom
    if phantom_array is not None:
        print("\n  Using supplied phantom_array...", end=" ", flush=True)
        phantom = np.asarray(phantom_array, dtype=np.float32)
        if phantom.shape != (N, N, N):
            raise ValueError(
                f"phantom_array shape {phantom.shape} != (N,N,N)=({N},{N},{N})")
    else:
        print("\n  Creating phantom...", end=" ", flush=True)
        phantom = np.array(get_phantom(phantom_name, N))
    print(f"done. Range: [{phantom.min():.2f}, {phantom.max():.2f}]")
    
    # Tilt angles
    angles_deg = np.linspace(tilt_range[0], tilt_range[1], K)
    angles_rad = np.deg2rad(angles_deg)
    angles_jax = jnp.array(angles_rad)
    
    # Random orientations
    key, subkey = random.split(key)
    true_quats = random_quaternions(subkey, P)
    print(f"  Generated {P} random orientations")
    
    # Per-particle intensity scale (simulates real-data intensity variation)
    key, subkey = random.split(key)
    if intensity_variation > 0:
        particle_scales = 1.0 + intensity_variation * np.array(
            random.uniform(subkey, (P,), minval=-1, maxval=1))
    else:
        particle_scales = np.ones(P)
    
    # Build projector
    print("  Building projector...", end=" ", flush=True)
    proj = make_projector(N)
    
    # Warmup
    vol_jax = jnp.array(phantom)
    _ = proj['project_particle_tilt'](vol_jax, true_quats[0], angles_jax[0])
    _.block_until_ready()
    print("done")
    
    # Generate projections
    print(f"  Generating {P}×{K} = {P*K} projections...")
    t0 = time.time()
    
    stacks = np.zeros((P, K, N, N), dtype=np.float32)
    
    for p in range(P):
        q = true_quats[p]
        s = particle_scales[p]
        for k in range(K):
            pred = np.array(proj['project_particle_tilt'](
                vol_jax, q, angles_jax[k]))
            stacks[p, k] = pred * s
        
        if (p+1) % 10 == 0 or p == P-1:
            print(f"    {p+1}/{P} particles done")
    
    elapsed = time.time() - t0
    print(f"  Projections done in {elapsed:.1f}s")
    
    # Add noise
    if noise_std > 0:
        print(f"  Adding noise (σ={noise_std})...")
        key, subkey = random.split(key)
        signal_level = np.mean(np.abs(stacks[stacks > 0]))
        noise = noise_std * signal_level * np.array(
            random.normal(subkey, stacks.shape))
        stacks = stacks + noise
        stacks = np.maximum(stacks, 0)  # non-negative
    
    # Normalize like real data: global per-particle percentile
    print("  Normalizing (per-particle global)...")
    for p in range(P):
        lo = np.percentile(stacks[p], 1)
        hi = np.percentile(stacks[p], 99)
        stacks[p] = np.clip((stacks[p] - lo) / (hi - lo + 1e-8), 0, 1)
    
    # Save in particle_stacks.npz format (compatible with reconstruct_tif.py)
    particle_names = [f"sim_{phantom_name}_{i:03d}" for i in range(P)]
    np.savez_compressed(output,
        stacks=stacks,
        tilt_angles_deg=angles_deg,
        tilt_angles_rad=angles_rad,
        particle_names=np.array(particle_names),
        pixel_size_nm=np.array(0.5),
        # Ground truth (for evaluation)
        true_phantom=phantom,
        true_quaternions=np.array(true_quats),
        true_particle_scales=particle_scales,
        phantom_name=phantom_name,
        noise_std=noise_std,
    )
    print(f"\n  Saved: {output}")
    print(f"  Stacks shape: {stacks.shape}")
    
    # --- Visualize ---
    _plot_simulation(phantom, stacks, angles_deg, true_quats,
                     particle_names, phantom_name, P, K, N)
    
    return {
        'stacks': stacks,
        'phantom': phantom,
        'true_quaternions': np.array(true_quats),
        'angles_deg': angles_deg,
        'angles_rad': angles_rad,
        'particle_names': particle_names,
    }


def _plot_simulation(phantom, stacks, angles_deg, true_quats, names, pname, P, K, N):
    """Generate simulation visualization plots."""
    mid = N // 2
    
    # --- Phantom slices ---
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    vmax = float(phantom.max())
    for ax, (sl, t) in zip(axes, [
        (phantom[mid,:,:], "XY"), (phantom[:,mid,:], "XZ"), (phantom[:,:,mid], "YZ")
    ]):
        ax.imshow(sl, cmap='gray', vmin=0, vmax=vmax, origin='lower')
        ax.set_title(t); ax.axis('off')
    plt.suptitle(f"Ground Truth: {pname} (N={N})")
    plt.tight_layout()
    plt.savefig("sim_phantom.png", dpi=150, bbox_inches='tight')
    plt.close()
    print("  Saved: sim_phantom.png")
    
    # --- Tilt series overview (like tif_overview.png) ---
    n_show_p = min(6, P)
    n_show_t = 7
    tilt_idx = np.linspace(0, K-1, n_show_t).astype(int)
    
    fig, axes = plt.subplots(n_show_p, n_show_t,
                              figsize=(2.5*n_show_t, 2.5*n_show_p))
    if n_show_p == 1:
        axes = axes[np.newaxis, :]
    for pi in range(n_show_p):
        for i, ti in enumerate(tilt_idx):
            axes[pi, i].imshow(stacks[pi, ti], cmap='gray')
            if pi == 0:
                axes[pi, i].set_title(f"{angles_deg[ti]:.0f}°", fontsize=10)
            axes[pi, i].axis('off')
        axes[pi, 0].set_ylabel(names[pi][:12], fontsize=8, rotation=0,
                                labelpad=55, va='center')
    
    plt.suptitle(f"Simulated Tilt Series: {pname}, P={P}, K={K}")
    plt.tight_layout()
    plt.savefig("sim_overview.png", dpi=150, bbox_inches='tight')
    plt.close()
    print("  Saved: sim_overview.png")
    
    # --- Phantom gallery (all shapes at once) ---
    # Skip if just running one simulation


def show_phantom_gallery(n=128):
    """Show all available phantoms."""
    names_list = list(PHANTOMS.keys())
    ncols = 5
    nrows = (len(names_list) + ncols - 1) // ncols
    
    fig, axes = plt.subplots(nrows, ncols, figsize=(2.5*ncols, 2.5*nrows))
    axes = axes.ravel()
    
    for i, name in enumerate(names_list):
        vol = np.array(get_phantom(name, n))
        mid = n // 2
        _, sym, _ = PHANTOMS[name]
        axes[i].imshow(vol[mid], cmap='gray', vmin=0, vmax=max(vol.max(), 0.01))
        color = 'green' if sym == 'C1' else 'blue'
        axes[i].set_title(f'{name}\n({sym})', fontsize=7, color=color)
        axes[i].axis('off')
    
    for j in range(i+1, len(axes)):
        axes[j].axis('off')
    
    plt.suptitle("Phantom Gallery (Green = Asymmetric, best for orientation testing)")
    plt.tight_layout()
    plt.savefig("phantom_gallery.png", dpi=150, bbox_inches='tight')
    plt.close()
    print("Saved: phantom_gallery.png")


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="TEM tilt-series simulation")
    parser.add_argument("--phantom", default="trunc_octahedron",
                        help=f"Phantom name (see --list-phantoms)")
    parser.add_argument("--list-phantoms", action="store_true")
    parser.add_argument("--gallery", action="store_true",
                        help="Generate phantom gallery image")
    parser.add_argument("-N", "--n-voxels", type=int, default=50)
    parser.add_argument("-P", "--n-particles", type=int, default=20)
    parser.add_argument("-K", "--n-tilts", type=int, default=41)
    parser.add_argument("--tilt-min", type=float, default=-60.0)
    parser.add_argument("--tilt-max", type=float, default=60.0)
    parser.add_argument("--noise", type=float, default=0.02)
    parser.add_argument("--intensity-var", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("-o", "--output", default="sim_particle_stacks.npz")
    args = parser.parse_args()
    
    if args.list_phantoms:
        list_phantoms()
    elif args.gallery:
        show_phantom_gallery()
    else:
        simulate(
            phantom_name=args.phantom,
            n_voxels=args.n_voxels,
            n_particles=args.n_particles,
            n_tilts=args.n_tilts,
            tilt_range=(args.tilt_min, args.tilt_max),
            noise_std=args.noise,
            intensity_variation=args.intensity_var,
            seed=args.seed,
            output=args.output,
        )
        print(f"\nNext: reconstruct with:")
        print(f"  python reconstruct_tif.py {args.output} -N {args.n_voxels} --iters 400")
