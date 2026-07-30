"""
TEM Multi-Particle Scene Simulator
=====================================

Simulates a SINGLE 2D TEM micrograph containing many nanoparticles (NPs),
each drawn from the 3D phantom library in simulate_tilt_series.py, composited
onto a shared canvas with controllable overlap, per-particle size/shape
variation, depth-of-field (defocus) blur, SNR, and optical "pollution"
(low-pass haze), plus exported bounding boxes / masks / category labels in
COCO format for ML training.

Physical model
--------------
Each particle is:
  1. assigned a category (a 3D shape name from PHANTOMS) and a random size,
  2. rotated by a random 3D orientation and lightly stretched/sheared
     (shape_variation) to give organic per-particle variety within a class,
  3. projected as a line integral along the beam axis (same weak-phase model
     as simulate_tilt_series.py) and resized to its target pixel footprint,
  4. blurred according to its assigned depth z (defocus_strength * |z|) to
     simulate particles sitting above/below the focal plane,
  5. additively composited onto the canvas (particles are semi-transparent,
     consistent with the line-integral projection model, so vertical/optical
     overlap just adds density rather than occluding).

The whole canvas then gets an optional low-pass "pollution" haze/blur and
Gaussian noise set to a target SNR (dB).

Usage (CLI):
    python simulate_tem_scene.py --shapes sphere,dumbbell,trunc_octahedron \
        --n-particles 40 --overlap-ratio 0.25 --snr-db 15 \
        --defocus-strength 3.0 --pollution-strength 0.2

Usage (Jupyter):
    from simulate_tem_scene import simulate_scene
    scene = simulate_scene(shapes=['sphere', 'dumbbell'], n_particles=30,
                            overlap_ratio=0.3, snr_db=18)

Showcase examples (see sim_tem_scene_example*, sim_tem_scene_demo_*.png at
repo root for the rendered output of each):

  1. Dense bright-field nanocube monolayer, matching a real TEM micrograph of
     self-assembled nanocubes (Fig_5_segmentation.png): tight edge-to-edge
     packing (high overlap-ratio + enough particles to fill every placement
     site), --invert-contrast for dark-particles-on-light-background mass-
     thickness contrast, and a small --max-tilt-deg so particles sit mostly
     face-on (flat on the grid) instead of tumbling in 3D -- avoiding the
     smoothed "shaded 3D ball" look a randomly oriented solid gives.

       python simulate_tem_scene.py --shapes cube --n-particles 560 \
           --canvas-size 480 --size-range 42,46 --shape-variation 0.05 \
           --max-tilt-deg 8 --overlap-ratio 0.55 --phantom-voxels 96 \
           --vertical-density 1.0 --defocus-strength 1.0 --snr-db 30 \
           --pollution-strength 0.02 --invert-contrast --seed 7 \
           --output-prefix sim_tem_scene_example

  2. Multi-category scene with planar overlap AND vertical (Z) stacking:
     vertical-density > 1 piles extra particles at the same XY site on a
     deeper layer, so some instances come out visibly defocused/blurred due
     to genuine sample-thickness stacking rather than just planar crowding.

       python simulate_tem_scene.py \
           --shapes sphere,dumbbell,trunc_octahedron --n-particles 90 \
           --canvas-size 512 --size-range 28,55 --shape-variation 0.2 \
           --overlap-ratio 0.3 --vertical-density 1.8 --layer-spacing 0.7 \
           --defocus-strength 4.0 --snr-db 16 --pollution-strength 0.15 \
           --seed 3 --output-prefix sim_tem_scene_demo_multiclass

  3. Degraded/dirty acquisition: low SNR + heavy "pollution" haze, sparse
     asymmetric particles -- shows bbox/segmentation annotations still track
     particles correctly even under strong noise and low-frequency haze.

       python simulate_tem_scene.py --shapes asym_dumbbell,icosahedron \
           --n-particles 25 --canvas-size 384 --size-range 30,60 \
           --shape-variation 0.25 --overlap-ratio 0.05 --vertical-density 1.0 \
           --defocus-strength 2.0 --snr-db 8 --pollution-strength 0.45 \
           --seed 11 --output-prefix sim_tem_scene_demo_noisy

Author: Zhengnan Li
"""

import argparse
import json

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from scipy.ndimage import affine_transform, gaussian_filter
from scipy.spatial.transform import Rotation
from skimage.transform import resize as sk_resize
from skimage.measure import find_contours

from simulate_tilt_series import PHANTOMS, get_phantom, list_phantoms  # noqa: F401


# ============================================================
# SINGLE-PARTICLE GENERATION
# ============================================================

def _rotate_and_project(vol, R, shape_variation, rng):
    """Rotate/shear a phantom volume and project (sum) along the Z axis."""
    n = vol.shape[0]
    scale = rng.uniform(1 - shape_variation, 1 + shape_variation, size=3)
    shear = rng.normal(0, 0.35 * shape_variation, size=(3, 3))
    np.fill_diagonal(shear, 0.0)
    S = np.diag(scale) + shear

    # world = R @ S @ local  =>  local = S^{-1} @ R.T @ world
    M_forward = R @ S
    M_inverse = np.linalg.inv(M_forward)

    center = (np.array(vol.shape) - 1) / 2.0
    offset = center - M_inverse @ center

    rotated = affine_transform(vol, M_inverse, offset=offset, order=1,
                               mode='constant', cval=0.0)
    return rotated.sum(axis=0) / n  # normalize so intensity is ~resolution-independent


def _random_rotation(max_tilt_deg, rng):
    """
    Sample a random orientation. max_tilt_deg=180 gives a fully uniform random
    3D orientation (particle tumbling freely). A smaller max_tilt_deg instead
    samples a free in-plane spin (about the beam axis) plus a small random
    tilt off that axis, up to max_tilt_deg -- i.e. the particle mostly rests
    face-on to the beam with only a slight wobble. This matches how faceted
    nanoparticles (cubes, etc.) actually settle flat on a TEM grid, instead
    of tumbling in free space; without it, oblique views of a solid convex
    shape create a smooth "shaded 3D ball" gradient across the particle body
    that real flat-mounted TEM particles don't show.
    """
    if max_tilt_deg >= 180:
        return Rotation.random(random_state=rng).as_matrix()
    spin = rng.uniform(0, 2 * np.pi)
    R_spin = Rotation.from_euler('z', spin).as_matrix()
    tilt_axis_angle = rng.uniform(0, 2 * np.pi)
    tilt_mag = np.deg2rad(rng.uniform(0, max_tilt_deg))
    axis = np.array([np.cos(tilt_axis_angle), np.sin(tilt_axis_angle), 0]) * tilt_mag
    R_tilt = Rotation.from_rotvec(axis).as_matrix()
    return R_tilt @ R_spin


def _make_particle_patch(category, phantom_cache, phantom_voxels,
                          size_px, shape_variation, intensity_variation, rng,
                          max_tilt_deg=180):
    """Build one particle's 2D image patch (size_px, size_px) and its binary mask."""
    if category not in phantom_cache:
        phantom_cache[category] = np.array(get_phantom(category, phantom_voxels), dtype=np.float32)
    vol = phantom_cache[category]

    R = _random_rotation(max_tilt_deg, rng)
    proj = _rotate_and_project(vol, R, shape_variation, rng)

    proj = np.clip(proj, 0, None)
    peak = proj.max()
    if peak > 1e-8:
        proj = proj / peak

    intensity = 1.0 + rng.uniform(-intensity_variation, intensity_variation)
    proj = proj * intensity

    patch = sk_resize(proj, (size_px, size_px), order=1, anti_aliasing=True)
    mask = patch > 0.1 * patch.max() if patch.max() > 0 else np.zeros_like(patch, dtype=bool)
    return patch.astype(np.float32), mask


# ============================================================
# PLACEMENT
# ============================================================

def _place_centers(n_particles, canvas_size, mean_size_px, overlap_ratio, rng):
    """
    Jittered-grid placement whose nominal center-to-center spacing implements
    the global overlap-ratio knob:
        spacing = mean_size_px * (1 - overlap_ratio)
      overlap_ratio=0   -> spacing = diameter   (particles just touch, no overlap)
      overlap_ratio=1   -> spacing = 0          (particles fully concentric)
    Jitter is added so not every pair sits at exactly that spacing (this is a
    population-average target, not a rigid per-pair constraint).
    """
    spacing = max(mean_size_px * (1 - overlap_ratio), 1.0)

    def build_grid(spacing):
        n_cols = max(int(np.floor(canvas_size / spacing)), 1)
        n_rows = max(int(np.floor(canvas_size / spacing)), 1)
        return [(r, c) for r in range(n_rows) for c in range(n_cols)]

    grid = build_grid(spacing)
    if len(grid) < n_particles:
        # too many particles for the canvas at this spacing: shrink spacing
        # so the full canvas has enough grid cells to seat every particle
        spacing = canvas_size / np.ceil(np.sqrt(n_particles))
        grid = build_grid(spacing)
        print(f"  [warn] {n_particles} particles too dense for canvas at "
              f"requested overlap; auto-shrunk spacing to {spacing:.1f}px")

    rng.shuffle(grid)

    centers = []
    jitter = spacing * 0.15
    for i in range(n_particles):
        r, c = grid[i]
        cy = (r + 0.5) * spacing + rng.uniform(-jitter, jitter)
        cx = (c + 0.5) * spacing + rng.uniform(-jitter, jitter)
        centers.append((cy, cx))
    return np.array(centers)


# ============================================================
# GLOBAL EFFECTS
# ============================================================

def _apply_pollution(canvas, pollution_strength, rng):
    """Low-pass optical-contamination filter: adds smooth haze + softens the
    whole image, simulating a dirty/misaligned optical path (the 'pollution
    filter' knob, 0 = clean, 1 = heavily hazed/soft)."""
    if pollution_strength <= 0:
        return canvas
    H, W = canvas.shape
    haze = gaussian_filter(rng.normal(size=(H, W)), sigma=0.15 * min(H, W))
    haze = (haze - haze.min()) / (haze.max() - haze.min() + 1e-8)
    canvas = canvas + pollution_strength * 0.6 * haze * canvas.max()
    canvas = gaussian_filter(canvas, sigma=pollution_strength * 2.5)
    return canvas


def _add_noise_for_snr(canvas, snr_db, rng):
    """Additive Gaussian noise calibrated to a target SNR in dB
    (SNR_dB = 20*log10(signal_std / noise_std))."""
    signal_std = canvas.std()
    noise_std = signal_std / (10 ** (snr_db / 20.0)) if signal_std > 0 else 0.0
    noise = rng.normal(0, noise_std, size=canvas.shape)
    return canvas + noise, noise_std


# ============================================================
# SCENE SIMULATION
# ============================================================

def simulate_scene(shapes="trunc_octahedron",
                    shape_weights=None,
                    canvas_size=512,
                    n_particles=40,
                    size_range=(24, 56),
                    phantom_voxels=64,
                    shape_variation=0.15,
                    max_tilt_deg=180.0,
                    overlap_ratio=0.2,
                    vertical_density=1.0,
                    layer_spacing=0.6,
                    focus_jitter=0.05,
                    defocus_strength=3.0,
                    snr_db=18.0,
                    pollution_strength=0.0,
                    invert_contrast=False,
                    seed=42,
                    output_prefix="sim_tem_scene"):
    """
    Simulate one composited multi-particle TEM micrograph with ML-ready
    annotations (COCO-style bbox + polygon mask + category per particle).

    Parameters
    ----------
    shapes : str or list of str
        One phantom name, or a list of phantom names to draw categories from
        (see list_phantoms() for the registry). Each particle is randomly
        assigned one of these as its category.
    shape_weights : optional list of float, same length as shapes
        Sampling weights per category (default: uniform).
    canvas_size : output image size in pixels (square).
    n_particles : number of nanoparticles in the scene.
    size_range : (min_px, max_px) per-particle diameter, sampled uniformly.
    phantom_voxels : 3D generation resolution for each phantom shape.
    shape_variation : 0-1, per-particle random anisotropic stretch/shear
        applied to the 3D shape before projection (organic within-class
        variety; 0 = every particle of a category is a rigid rotation of
        the same shape).
    max_tilt_deg : 180 = particles tumble freely in 3D (uniform random
        orientation). A smaller value (e.g. 15-30) instead keeps particles
        mostly face-on to the beam with only a small random tilt plus free
        in-plane spin, matching faceted nanoparticles resting flat on a TEM
        grid -- avoids the smooth "shaded 3D ball" gradient that oblique
        views of a solid convex shape otherwise produce.
    overlap_ratio : 0 (no overlap, particles just touch) to 1 (fully
        concentric / full overlap) -- global average XY placement density knob.
    vertical_density : mean number of particles stacked in Z per placement
        site (particles-per-unit-depth). 1.0 = a single monolayer sitting
        flat on the grid, all sharing roughly the same focus (matches a
        real TEM grid: particles are "on the grid", so focus/blur is
        roughly uniform). >1 piles additional particles at the same XY
        site but at deeper layers, so some particles fall out of focus and
        their projections overlap due to genuine sample thickness/loading
        rather than just planar crowding.
    layer_spacing : z-distance between successive stacked layers (in the
        same units as defocus_strength scaling); layer 0 (on the grid) sits
        at z=0, layer 1 at z=layer_spacing, etc.
    focus_jitter : small random z jitter (+/-) applied within a layer, e.g.
        for minor unevenness of the support film -- keeps same-layer
        particles at roughly the same focus rather than perfectly identical.
    defocus_strength : knob for depth of field -- Gaussian blur sigma (px)
        applied at |z|=1; particles in deeper layers (farther from the
        focal plane) blur more. 0 = everything always in focus regardless
        of depth.
    snr_db : target signal-to-noise ratio of the final image, in dB.
    pollution_strength : 0-1 knob for a low-pass optical-contamination
        filter/haze applied to the whole image (0 = clean image).
    seed : random seed.
    output_prefix : filenames written are
        {prefix}.png          -- 8-bit viewable micrograph
        {prefix}.npy          -- raw float32 composite (for training)
        {prefix}_coco.json    -- COCO-style annotations
        {prefix}_overlay.png  -- QA visualization with boxes/labels

    Returns
    -------
    dict with 'image', 'instances' (list of per-particle records), 'coco'.
    """
    rng = np.random.default_rng(seed)

    shape_list = [shapes] if isinstance(shapes, str) else list(shapes)
    for s in shape_list:
        if s not in PHANTOMS:
            raise ValueError(f"Unknown phantom '{s}'. Run list_phantoms() for options.")
    if shape_weights is not None:
        shape_weights = np.array(shape_weights, dtype=float)
        shape_weights = shape_weights / shape_weights.sum()

    print(f"\n{'='*60}")
    print("SIMULATING TEM SCENE")
    print(f"  Canvas: {canvas_size}x{canvas_size} | Particles: {n_particles}")
    print(f"  Categories: {shape_list}")
    print(f"  Overlap ratio: {overlap_ratio} | Shape variation: {shape_variation}")
    print(f"  Vertical density: {vertical_density} | Layer spacing: {layer_spacing}")
    print(f"  Defocus strength: {defocus_strength}")
    print(f"  SNR: {snr_db} dB | Pollution: {pollution_strength}")
    print(f"{'='*60}")

    # --- per-particle attributes ---
    categories = rng.choice(shape_list, size=n_particles, p=shape_weights)
    sizes_px = rng.integers(size_range[0], size_range[1] + 1, size=n_particles)
    mean_size_px = float(np.mean(sizes_px))

    # XY placement sites: fewer sites than particles when vertical_density > 1,
    # since multiple particles then stack (in Z) on the same site.
    n_sites = max(1, int(round(n_particles / max(vertical_density, 1e-6))))
    site_centers = _place_centers(n_sites, canvas_size, mean_size_px, overlap_ratio, rng)
    # Evenly distribute particles across sites (not independent random binning,
    # which would spuriously stack particles even at vertical_density=1.0).
    base, remainder = divmod(n_particles, n_sites)
    site_of = np.concatenate([
        np.tile(np.arange(n_sites), base),
        rng.choice(n_sites, remainder, replace=False),
    ])
    rng.shuffle(site_of)

    layer_of = np.zeros(n_particles, dtype=int)
    for s in range(n_sites):
        idxs = np.nonzero(site_of == s)[0]
        layer_of[idxs] = rng.permutation(len(idxs))

    intra_site_jitter = mean_size_px * 0.12
    centers = site_centers[site_of] + rng.uniform(-intra_site_jitter, intra_site_jitter,
                                                   size=(n_particles, 2))
    depths = layer_of * layer_spacing + rng.uniform(-focus_jitter, focus_jitter, size=n_particles)
    print(f"  Sites: {n_sites} (mean stacking {n_particles / n_sites:.2f}x, "
          f"max layer {layer_of.max()})")

    canvas = np.zeros((canvas_size, canvas_size), dtype=np.float32)
    phantom_cache = {}
    instances = []

    print("\n  Generating and compositing particles...", end=" ", flush=True)
    for i in range(n_particles):
        cat = str(categories[i])
        size_px = int(sizes_px[i])
        z = float(depths[i])
        blur_sigma = abs(z) * defocus_strength

        patch, mask = _make_particle_patch(cat, phantom_cache, phantom_voxels,
                                            size_px, shape_variation, 0.15, rng,
                                            max_tilt_deg)
        if blur_sigma > 0:
            patch = gaussian_filter(patch, sigma=blur_sigma)
            mask = patch > 0.1 * patch.max() if patch.max() > 0 else mask

        cy, cx = centers[i]
        y0 = int(round(cy - size_px / 2))
        x0 = int(round(cx - size_px / 2))
        y1, x1 = y0 + size_px, x0 + size_px

        # clip to canvas
        cy0, cx0 = max(y0, 0), max(x0, 0)
        cy1, cx1 = min(y1, canvas_size), min(x1, canvas_size)
        if cy1 <= cy0 or cx1 <= cx0:
            continue  # fully off-canvas

        py0, px0 = cy0 - y0, cx0 - x0
        py1, px1 = py0 + (cy1 - cy0), px0 + (cx1 - cx0)

        vis_mask = mask[py0:py1, px0:px1]
        if vis_mask.sum() < 0.15 * mask.sum():
            continue  # too little of the particle is visible on-canvas; drop it

        canvas[cy0:cy1, cx0:cx1] += patch[py0:py1, px0:px1]

        ys, xs = np.nonzero(vis_mask)
        bbox_x, bbox_y = cx0 + xs.min(), cy0 + ys.min()
        bbox_w, bbox_h = xs.max() - xs.min() + 1, ys.max() - ys.min() + 1
        truncated = (y0 < 0 or x0 < 0 or y1 > canvas_size or x1 > canvas_size)

        contours = find_contours(vis_mask.astype(float), 0.5)
        polygon = []
        if contours:
            longest = max(contours, key=len)
            poly_yx = longest + np.array([cy0, cx0])
            polygon = poly_yx[:, ::-1].ravel().round(1).tolist()  # -> [x,y,x,y,...]

        instances.append(dict(
            id=i + 1, category=cat, size_px=size_px, z_depth=round(z, 3),
            defocus_sigma=round(blur_sigma, 3), truncated=bool(truncated),
            site_id=int(site_of[i]), layer=int(layer_of[i]),
            bbox=[int(bbox_x), int(bbox_y), int(bbox_w), int(bbox_h)],
            area=int(vis_mask.sum()), segmentation=polygon,
        ))
    print(f"done. {len(instances)}/{n_particles} particles kept (visible on canvas).")

    canvas = _apply_pollution(canvas, pollution_strength, rng)
    canvas, noise_std = _add_noise_for_snr(canvas, snr_db, rng)
    print(f"  Noise std for {snr_db} dB SNR: {noise_std:.4f}")

    coco = _to_coco(canvas, instances, shape_list, output_prefix)

    _save_outputs(canvas, instances, coco, output_prefix, invert_contrast)

    return dict(image=canvas, instances=instances, coco=coco)


# ============================================================
# EXPORT (COCO annotations, image, QA overlay)
# ============================================================

def _to_coco(canvas, instances, shape_list, output_prefix):
    cat_ids = {name: k + 1 for k, name in enumerate(shape_list)}
    categories = [{"id": cid, "name": name} for name, cid in cat_ids.items()]
    annotations = []
    for inst in instances:
        annotations.append({
            "id": inst["id"],
            "image_id": 1,
            "category_id": cat_ids[inst["category"]],
            "bbox": inst["bbox"],
            "area": inst["area"],
            "segmentation": [inst["segmentation"]] if inst["segmentation"] else [],
            "iscrowd": 0,
            "z_depth": inst["z_depth"],
            "defocus_sigma": inst["defocus_sigma"],
            "truncated": inst["truncated"],
            "site_id": inst["site_id"],
            "layer": inst["layer"],
        })
    return {
        "images": [{"id": 1, "file_name": f"{output_prefix}.png",
                    "width": canvas.shape[1], "height": canvas.shape[0]}],
        "categories": categories,
        "annotations": annotations,
    }


def _normalize_8bit(canvas, invert_contrast=False):
    lo, hi = np.percentile(canvas, [0.5, 99.5])
    img = np.clip((canvas - lo) / (hi - lo + 1e-8), 0, 1)
    if invert_contrast:
        # Bright-field TEM: denser/thicker regions absorb more and read dark
        # against a bright unscattered-beam background (mass-thickness contrast).
        img = 1.0 - img
    return (img * 255).astype(np.uint8)


def _save_outputs(canvas, instances, coco, output_prefix, invert_contrast=False):
    img8 = _normalize_8bit(canvas, invert_contrast)
    plt.imsave(f"{output_prefix}.png", img8, cmap='gray')
    np.save(f"{output_prefix}.npy", canvas)
    with open(f"{output_prefix}_coco.json", "w") as f:
        json.dump(coco, f, indent=2)

    fig, ax = plt.subplots(figsize=(8, 8))
    ax.imshow(img8, cmap='gray')
    colors = plt.cm.tab10(np.linspace(0, 1, 10))
    cat_color = {}
    for inst in instances:
        cat_color.setdefault(inst["category"], colors[len(cat_color) % 10])
        color = cat_color[inst["category"]]
        x, y, w, h = inst["bbox"]
        ax.add_patch(Rectangle((x, y), w, h, fill=False, edgecolor=color, linewidth=1.2))
        ax.text(x, max(y - 3, 0), inst["category"], color=color, fontsize=6,
                clip_on=True)
    ax.set_title(f"{len(instances)} particles | {len(cat_color)} categories")
    ax.axis('off')
    fig.tight_layout()
    fig.savefig(f"{output_prefix}_overlay.png", dpi=150)
    plt.close(fig)

    print(f"  Saved: {output_prefix}.png, {output_prefix}.npy, "
          f"{output_prefix}_coco.json, {output_prefix}_overlay.png")


# ============================================================
# CLI
# ============================================================

def main():
    p = argparse.ArgumentParser(description="Simulate a multi-particle TEM scene.")
    p.add_argument('--shapes', type=str, default='trunc_octahedron',
                    help="Comma-separated phantom names (categories), e.g. "
                         "sphere,dumbbell,trunc_octahedron")
    p.add_argument('--canvas-size', type=int, default=512)
    p.add_argument('--n-particles', type=int, default=40)
    p.add_argument('--size-range', type=str, default="24,56",
                    help="min,max particle diameter in pixels")
    p.add_argument('--phantom-voxels', type=int, default=64)
    p.add_argument('--shape-variation', type=float, default=0.15)
    p.add_argument('--max-tilt-deg', type=float, default=180.0,
                    help="180 = free 3D tumbling; smaller (e.g. 20) keeps "
                         "particles mostly face-on, as if resting flat on "
                         "the grid, with only a small random tilt")
    p.add_argument('--overlap-ratio', type=float, default=0.2)
    p.add_argument('--vertical-density', type=float, default=1.0,
                    help="mean particles stacked in Z per XY site "
                         "(1.0 = monolayer on the grid, all in focus)")
    p.add_argument('--layer-spacing', type=float, default=0.6,
                    help="z-distance between stacked layers")
    p.add_argument('--focus-jitter', type=float, default=0.05,
                    help="small random z jitter within a layer")
    p.add_argument('--defocus-strength', type=float, default=3.0)
    p.add_argument('--snr-db', type=float, default=18.0)
    p.add_argument('--pollution-strength', type=float, default=0.0)
    p.add_argument('--invert-contrast', action='store_true',
                    help="bright-field TEM look: dark particles on a light "
                         "background (mass-thickness contrast)")
    p.add_argument('--seed', type=int, default=42)
    p.add_argument('--output-prefix', type=str, default="sim_tem_scene")
    p.add_argument('--list-phantoms', action='store_true')
    args = p.parse_args()

    if args.list_phantoms:
        list_phantoms()
        return

    size_min, size_max = (int(x) for x in args.size_range.split(','))

    simulate_scene(
        shapes=[s.strip() for s in args.shapes.split(',')],
        canvas_size=args.canvas_size,
        n_particles=args.n_particles,
        size_range=(size_min, size_max),
        phantom_voxels=args.phantom_voxels,
        shape_variation=args.shape_variation,
        max_tilt_deg=args.max_tilt_deg,
        overlap_ratio=args.overlap_ratio,
        vertical_density=args.vertical_density,
        layer_spacing=args.layer_spacing,
        focus_jitter=args.focus_jitter,
        defocus_strength=args.defocus_strength,
        snr_db=args.snr_db,
        pollution_strength=args.pollution_strength,
        invert_contrast=args.invert_contrast,
        seed=args.seed,
        output_prefix=args.output_prefix,
    )


if __name__ == "__main__":
    main()
