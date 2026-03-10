import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from functools import lru_cache


def set_axes_equal(ax):
    x_limits = ax.get_xlim3d()
    y_limits = ax.get_ylim3d()
    z_limits = ax.get_zlim3d()

    x_range = abs(x_limits[1] - x_limits[0])
    y_range = abs(y_limits[1] - y_limits[0])
    z_range = abs(z_limits[1] - z_limits[0])

    x_middle = np.mean(x_limits)
    y_middle = np.mean(y_limits)
    z_middle = np.mean(z_limits)

    plot_radius = 0.5 * max(x_range, y_range, z_range)

    ax.set_xlim3d([x_middle - plot_radius, x_middle + plot_radius])
    ax.set_ylim3d([y_middle - plot_radius, y_middle + plot_radius])
    ax.set_zlim3d([z_middle - plot_radius, z_middle + plot_radius])


def rotate90_ccw(v):
    return np.array([-v[1], v[0]], dtype=float)


def compute_fractal(delta_scale, zeta_scale, max_depth=10, cull_ratio=0.02):
    """
    Compute a Pythagoras tree in 2D.
    Returns square corners plus the outward unit normal for each square.
    """
    a = 4.0 * delta_scale
    b = 3.0 * zeta_scale
    c = np.sqrt(a ** 2 + b ** 2)

    p1_current = np.array([[-c / 2.0, 0.0]])
    p2_current = np.array([[c / 2.0, 0.0]])

    all_p1 = []
    all_p2 = []
    all_p3 = []
    all_p4 = []
    all_normals = []
    all_lengths = []

    for depth in range(max_depth + 1):
        if len(p1_current) == 0:
            break

        u = p2_current - p1_current
        lengths = np.linalg.norm(u, axis=1)
        u_unit = u / lengths[:, None]

        v_unit = np.column_stack([-u_unit[:, 1], u_unit[:, 0]])
        v = v_unit * lengths[:, None]

        p4_current = p1_current + v
        p3_current = p2_current + v

        all_p1.append(p1_current)
        all_p2.append(p2_current)
        all_p3.append(p3_current)
        all_p4.append(p4_current)
        all_normals.append(v_unit)
        all_lengths.append(lengths)

        if depth < max_depth:
            c_vertex = p4_current + (b ** 2 / c ** 2) * u + (a * b / c ** 2) * v

            p1_next = np.vstack([p4_current, c_vertex])
            p2_next = np.vstack([c_vertex, p3_current])

            lengths_next = np.linalg.norm(p2_next - p1_next, axis=1)
            mask = lengths_next > (c * cull_ratio)

            p1_current = p1_next[mask]
            p2_current = p2_next[mask]

    p1 = np.concatenate(all_p1)
    p2 = np.concatenate(all_p2)
    p3 = np.concatenate(all_p3)
    p4 = np.concatenate(all_p4)
    normals = np.concatenate(all_normals)
    lengths = np.concatenate(all_lengths)

    return p1, p2, p3, p4, normals, lengths, a, b, c


@lru_cache(maxsize=128)
def get_fractal_cached(delta_scale, zeta_scale):
    return compute_fractal(delta_scale, zeta_scale, max_depth=10, cull_ratio=0.02)


def cylinder_volume(radius, height):
    return np.pi * radius * radius * height


def draw_square_lines(ax, p1, p2, p3, p4):
    n = len(p1)
    if n == 0:
        return

    nan_arr = np.full(n, np.nan)

    x_sq = np.column_stack([p1[:, 0], p2[:, 0], p3[:, 0], p4[:, 0], p1[:, 0], nan_arr]).ravel()
    y_sq = np.column_stack([p1[:, 1], p2[:, 1], p3[:, 1], p4[:, 1], p1[:, 1], nan_arr]).ravel()
    z_sq = np.zeros_like(x_sq)

    ax.plot(x_sq, y_sq, z_sq, color="black", linewidth=0.8, alpha=0.5)


def draw_scene(ax, title_text, formula_text, stats_text, delta_scale, epsilon_slider_value, zeta_scale):
    height_scale = epsilon_slider_value

    p1, p2, p3, p4, normals, side_lengths, a, b, c = get_fractal_cached(delta_scale, zeta_scale)

    ax.cla()
    draw_square_lines(ax, p1, p2, p3, p4)

    centers = (p1 + p2) / 2.0
    radii = side_lengths / 2.0
    heights = side_lengths * height_scale

    render_mask = side_lengths > (c * 0.035)
    centers = centers[render_mask]
    radii = radii[render_mask]
    heights = heights[render_mask]
    normals = normals[render_mask]
    side_lengths = side_lengths[render_mask]

    n_cylinders = len(centers)
    max_z = c * height_scale

    if n_cylinders > 0:
        n_theta = 20

        c_x = centers[:, 0:1]
        c_y = centers[:, 1:2]
        c_z = np.zeros((n_cylinders, 1))

        n_x = normals[:, 0:1]
        n_y = normals[:, 1:2]

        r = radii[:, None]
        h = heights[:, None]

        theta = np.linspace(0.0, 2.0 * np.pi, n_theta)

        x_b = c_x + r * np.sin(theta) * n_y
        y_b = c_y - r * np.sin(theta) * n_x
        z_b = c_z + r * np.cos(theta)

        x_t = x_b + h * n_x
        y_t = y_b + h * n_y
        z_t = z_b

        max_z = np.max(z_t)

        nan_col = np.full((n_cylinders, 1), np.nan)
        x_rims = np.hstack([x_b, nan_col, x_t, nan_col]).ravel()
        y_rims = np.hstack([y_b, nan_col, y_t, nan_col]).ravel()
        z_rims = np.hstack([z_b, nan_col, z_t, nan_col]).ravel()

        ax.plot(x_rims, y_rims, z_rims, color="lightcoral", linewidth=0.6, alpha=0.8)

        p_b = np.stack([x_b, y_b, z_b], axis=-1)
        p_t = np.stack([x_t, y_t, z_t], axis=-1)

        q1 = p_b[:, :-1, :]
        q2 = p_b[:, 1:, :]
        q3 = p_t[:, 1:, :]
        q4 = p_t[:, :-1, :]

        quads = np.stack([q1, q2, q3, q4], axis=-2).reshape(-1, 4, 3)
        collection = Poly3DCollection(quads, color="pink", alpha=0.18, linewidths=0)
        ax.add_collection3d(collection)

        caps = np.concatenate([p_b[:, :-1, :], p_t[:, :-1, :]], axis=0)
        cap_collection = Poly3DCollection(caps, color="pink", alpha=0.18, linewidths=0)
        ax.add_collection3d(cap_collection)

    vols = cylinder_volume(radii, heights)
    total_vol = np.sum(vols)
    trunk_vol = cylinder_volume(c / 2.0, c * height_scale)

    title_text.set_text("3D Pythagorean Fractal Tree of Cylinders")
    formula_text.set_text(r"$V_{\mathrm{total}} = \sum \pi r^2 h$")
    stats_text.set_text(
        f"Total Vol = {total_vol:,.2f}    |    Trunk Vol = {trunk_vol:,.2f}    |    Rendered Cylinders = {n_cylinders:,}"
    )

    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")

    extent = c * 1.9
    ax.set_xlim(-extent * 1.05, extent * 0.95)
    ax.set_ylim(-extent * 0.15, extent * 2.15)
    ax.set_zlim(-extent * 0.45, max(extent * 1.35, max_z * 1.08))

    ax.grid(True)
    ax.set_box_aspect((1.2, 1.7, 0.9))
    set_axes_equal(ax)
    ax.view_init(elev=22, azim=-62)


def plot_geometry_app():
    fig = plt.figure(figsize=(12, 10))

    # Narrower and slightly more left-shifted 3D area so the right side does not clip.
    ax = fig.add_axes([0.10, 0.25, 0.60, 0.50], projection="3d")

    title_text = fig.text(
        0.5, 0.972, "",
        ha="center", va="top", fontsize=19
    )

    formula_text = fig.text(
        0.5, 0.910, "",
        ha="center", va="top", fontsize=20
    )

    stats_text = fig.text(
        0.5, 0.855, "",
        ha="center", va="top", fontsize=13, fontweight="bold", color="darkgreen"
    )

    # Moved farther right so labels are not cut off.
    ax_delta = fig.add_axes([0.28, 0.14, 0.57, 0.03])
    ax_epsilon = fig.add_axes([0.28, 0.095, 0.57, 0.03])
    ax_zeta = fig.add_axes([0.28, 0.05, 0.57, 0.03])

    s_delta = Slider(ax_delta, "Right Leg Base (δ)", 1.0, 10.0, valinit=1.0, valstep=0.1)
    s_epsilon = Slider(ax_epsilon, "Cylinder Height Scale (ε)", 1.0, 10.0, valinit=1.0, valstep=0.1)
    s_zeta = Slider(ax_zeta, "Left Leg Base (ζ)", 1.0, 10.0, valinit=1.0, valstep=0.1)

    draw_scene(
        ax=ax,
        title_text=title_text,
        formula_text=formula_text,
        stats_text=stats_text,
        delta_scale=s_delta.val,
        epsilon_slider_value=s_epsilon.val,
        zeta_scale=s_zeta.val
    )

    def update(_):
        draw_scene(
            ax=ax,
            title_text=title_text,
            formula_text=formula_text,
            stats_text=stats_text,
            delta_scale=s_delta.val,
            epsilon_slider_value=s_epsilon.val,
            zeta_scale=s_zeta.val
        )
        fig.canvas.draw_idle()

    s_delta.on_changed(update)
    s_epsilon.on_changed(update)
    s_zeta.on_changed(update)

    plt.show()


if __name__ == "__main__":
    plot_geometry_app()
