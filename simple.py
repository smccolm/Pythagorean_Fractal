import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider


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


def square_from_segment(p1, p2, outward_hint):
    edge = p2 - p1
    length = np.linalg.norm(edge)
    unit = edge / length

    n1 = rotate90_ccw(unit)
    n2 = -n1

    center = (p1 + p2) / 2.0

    test1 = center + n1 * 0.25 * length
    test2 = center + n2 * 0.25 * length

    if np.dot(test1 - center, outward_hint) >= np.dot(test2 - center, outward_hint):
        n = n1
    else:
        n = n2

    p3 = p2 + n * length
    p4 = p1 + n * length

    return [p1, p2, p3, p4], n, length


def cylinder_volume_from_side(side_length):
    return np.pi * (side_length / 2.0) ** 2 * side_length


def draw_square(ax, corners, shared_color="blue", edge_color="black", lw=2):
    p1, p2, p3, p4 = corners

    ax.plot([p1[0], p2[0]], [p1[1], p2[1]], [0, 0], color=shared_color, linewidth=lw)

    for a, b in [(p2, p3), (p3, p4), (p4, p1)]:
        ax.plot([a[0], b[0]], [a[1], b[1]], [0, 0], color=edge_color, linewidth=lw)


def draw_vertical_circle(ax, p1, p2, center, label_text, label_angle_deg, label_offset, color="red", lw=3):
    segment = p2 - p1
    radius = np.linalg.norm(p2 - p1) / 2.0
    u = segment / np.linalg.norm(segment)

    t = np.linspace(0.0, 2.0 * np.pi, 400)

    x = center[0] + radius * np.cos(t) * u[0]
    y = center[1] + radius * np.cos(t) * u[1]
    z = radius * np.sin(t)

    ax.plot(x, y, z, color=color, linewidth=lw)

    angle = np.deg2rad(label_angle_deg)
    label_x = center[0] + radius * np.cos(angle) * u[0] + label_offset[0]
    label_y = center[1] + radius * np.cos(angle) * u[1] + label_offset[1]
    label_z = radius * np.sin(angle) + label_offset[2]

    ax.text(label_x, label_y, label_z, label_text, color=color, fontsize=16)


def draw_cylinder_from_circle_face(ax, face_center, axis_direction, radius, height, label_text, label_offset):
    axis_direction = np.array(axis_direction, dtype=float)
    axis_direction = axis_direction / np.linalg.norm(axis_direction)

    face_u = np.array([0.0, 0.0, 1.0], dtype=float)

    face_v = np.cross(axis_direction, face_u)
    face_v_norm = np.linalg.norm(face_v)
    if face_v_norm == 0:
        raise ValueError("Cylinder axis cannot be parallel to Z for this construction.")
    face_v = face_v / face_v_norm

    theta = np.linspace(0.0, 2.0 * np.pi, 80)
    s = np.linspace(0.0, height, 28)
    theta_grid, s_grid = np.meshgrid(theta, s)

    x = (
        face_center[0]
        + s_grid * axis_direction[0]
        + radius * np.cos(theta_grid) * face_u[0]
        + radius * np.sin(theta_grid) * face_v[0]
    )
    y = (
        face_center[1]
        + s_grid * axis_direction[1]
        + radius * np.cos(theta_grid) * face_u[1]
        + radius * np.sin(theta_grid) * face_v[1]
    )
    z = (
        face_center[2]
        + s_grid * axis_direction[2]
        + radius * np.cos(theta_grid) * face_u[2]
        + radius * np.sin(theta_grid) * face_v[2]
    )

    ax.plot_surface(
        x,
        y,
        z,
        color="pink",
        alpha=0.22,
        linewidth=0,
        shade=False
    )

    rim_theta = np.linspace(0.0, 2.0 * np.pi, 240)
    for s_val in [0.0, height]:
        rim_x = (
            face_center[0]
            + s_val * axis_direction[0]
            + radius * np.cos(rim_theta) * face_u[0]
            + radius * np.sin(rim_theta) * face_v[0]
        )
        rim_y = (
            face_center[1]
            + s_val * axis_direction[1]
            + radius * np.cos(rim_theta) * face_u[1]
            + radius * np.sin(rim_theta) * face_v[1]
        )
        rim_z = (
            face_center[2]
            + s_val * axis_direction[2]
            + radius * np.cos(rim_theta) * face_u[2]
            + radius * np.sin(rim_theta) * face_v[2]
        )
        ax.plot(rim_x, rim_y, rim_z, color="lightcoral", linewidth=1.0)

    label_point = face_center + 0.72 * height * axis_direction + label_offset
    ax.text(label_point[0], label_point[1], label_point[2], label_text, color="purple", fontsize=16)


def compute_geometry(delta_scale, epsilon_slider_value, zeta_scale):
    ab_len = 4.0 * delta_scale
    ag_len = 3.0 * zeta_scale
    bg_len = np.sqrt(ab_len ** 2 + ag_len ** 2)

    alpha = np.array([0.0, 0.0], dtype=float)
    beta = np.array([ab_len, 0.0], dtype=float)
    gamma = np.array([0.0, ag_len], dtype=float)

    delta = (alpha + beta) / 2.0
    epsilon = (beta + gamma) / 2.0
    zeta = (gamma + alpha) / 2.0

    derived_epsilon_scale = bg_len / 5.0

    return {
        "alpha": alpha,
        "beta": beta,
        "gamma": gamma,
        "delta": delta,
        "epsilon": epsilon,
        "zeta": zeta,
        "ab_len": ab_len,
        "bg_len": bg_len,
        "ag_len": ag_len,
        "derived_epsilon_scale": derived_epsilon_scale
    }


def draw_scene(ax, fig, title_text, formula_text, stats_text, delta_scale, epsilon_slider_value, zeta_scale):
    geom = compute_geometry(delta_scale, epsilon_slider_value, zeta_scale)

    alpha = geom["alpha"]
    beta = geom["beta"]
    gamma = geom["gamma"]
    delta = geom["delta"]
    epsilon = geom["epsilon"]
    zeta = geom["zeta"]

    ab_len = geom["ab_len"]
    bg_len = geom["bg_len"]
    ag_len = geom["ag_len"]
    derived_epsilon_scale = geom["derived_epsilon_scale"]

    delta3 = np.array([delta[0], delta[1], 0.0], dtype=float)
    epsilon3 = np.array([epsilon[0], epsilon[1], 0.0], dtype=float)
    zeta3 = np.array([zeta[0], zeta[1], 0.0], dtype=float)

    triangle_center = (alpha + beta + gamma) / 3.0

    square_ab, n_ab, len_ab = square_from_segment(
        alpha, beta, ((alpha + beta) / 2.0) - triangle_center
    )
    square_bg, n_bg, len_bg = square_from_segment(
        beta, gamma, ((beta + gamma) / 2.0) - triangle_center
    )
    square_ga, n_ga, len_ga = square_from_segment(
        gamma, alpha, ((gamma + alpha) / 2.0) - triangle_center
    )

    delta_end = delta + n_ab * len_ab
    epsilon_end = epsilon + n_bg * len_bg
    zeta_end = zeta + n_ga * len_ga

    ax.cla()

    plane_size = max(8.0, ab_len, ag_len, bg_len) * 1.3
    xx, yy = np.meshgrid(
        np.linspace(-plane_size, plane_size, 2),
        np.linspace(-plane_size, plane_size, 2)
    )
    zz = np.zeros_like(xx)
    ax.plot_surface(xx, yy, zz, alpha=0.08, edgecolor="none")

    triangle_points = [alpha, beta, gamma, alpha]
    ax.plot(
        [p[0] for p in triangle_points],
        [p[1] for p in triangle_points],
        [0, 0, 0, 0],
        color="blue",
        linewidth=3
    )

    ax.scatter(
        [alpha[0], beta[0], gamma[0]],
        [alpha[1], beta[1], gamma[1]],
        [0, 0, 0],
        color="blue",
        s=35
    )
    label_pad = max(ab_len, ag_len, bg_len) * 0.025 + 0.08
    ax.text(alpha[0] - label_pad, alpha[1] - label_pad, 0.12, "α", fontsize=16)
    ax.text(beta[0] + label_pad * 0.4, beta[1] - label_pad, 0.12, "β", fontsize=16)
    ax.text(gamma[0] - label_pad, gamma[1] + label_pad * 0.4, 0.12, "γ", fontsize=16)

    ax.scatter(
        [delta[0], epsilon[0], zeta[0]],
        [delta[1], epsilon[1], zeta[1]],
        [0, 0, 0],
        color="black",
        s=25
    )
    ax.text(delta[0], delta[1] - label_pad, 0.12, "δ", fontsize=14)
    ax.text(epsilon[0] + label_pad * 0.35, epsilon[1] + label_pad * 0.1, 0.12, "ε", fontsize=14)
    ax.text(zeta[0] - label_pad, zeta[1], 0.12, "ζ", fontsize=14)

    draw_square(ax, square_ab, shared_color="blue", edge_color="black", lw=2)
    draw_square(ax, square_bg, shared_color="blue", edge_color="black", lw=2)
    draw_square(ax, square_ga, shared_color="blue", edge_color="black", lw=2)

    for start, end in [
        (delta, delta_end),
        (epsilon, epsilon_end),
        (zeta, zeta_end)
    ]:
        ax.plot(
            [start[0], end[0]],
            [start[1], end[1]],
            [0, 0],
            color="green",
            linewidth=3
        )

    draw_vertical_circle(
        ax=ax,
        p1=alpha,
        p2=beta,
        center=delta,
        label_text="η",
        label_angle_deg=58.0,
        label_offset=np.array([0.10, -0.15, 0.30]),
        color="red",
        lw=3
    )

    draw_vertical_circle(
        ax=ax,
        p1=beta,
        p2=gamma,
        center=epsilon,
        label_text="θ",
        label_angle_deg=122.0,
        label_offset=np.array([0.18, 0.10, 0.30]),
        color="red",
        lw=3
    )

    draw_vertical_circle(
        ax=ax,
        p1=alpha,
        p2=gamma,
        center=zeta,
        label_text="ι",
        label_angle_deg=128.0,
        label_offset=np.array([-0.22, 0.05, 0.32]),
        color="red",
        lw=3
    )

    delta_axis_direction = np.array([n_ab[0], n_ab[1], 0.0], dtype=float)
    epsilon_axis_direction = np.array([n_bg[0], n_bg[1], 0.0], dtype=float)
    zeta_axis_direction = np.array([n_ga[0], n_ga[1], 0.0], dtype=float)

    draw_cylinder_from_circle_face(
        ax=ax,
        face_center=delta3,
        axis_direction=delta_axis_direction,
        radius=0.5 * len_ab,
        height=len_ab,
        label_text="Κ",
        label_offset=np.array([0.18, -0.08, 0.22])
    )

    draw_cylinder_from_circle_face(
        ax=ax,
        face_center=epsilon3,
        axis_direction=epsilon_axis_direction,
        radius=0.5 * len_bg,
        height=len_bg,
        label_text="Λ",
        label_offset=np.array([0.20, 0.08, 0.25])
    )

    draw_cylinder_from_circle_face(
        ax=ax,
        face_center=zeta3,
        axis_direction=zeta_axis_direction,
        radius=0.5 * len_ga,
        height=len_ga,
        label_text="Μ",
        label_offset=np.array([-0.18, 0.06, 0.22])
    )

    vol_kappa = cylinder_volume_from_side(len_ab)
    vol_lambda = cylinder_volume_from_side(len_bg)
    vol_mu = cylinder_volume_from_side(len_ga)

    title_text.set_text("Geometric Relationship Between the Volumes of a Pythagorean Triplet of Cylinders")
    formula_text.set_text(r"$V_{\mathrm{K}}^{2/3} + V_{\Lambda}^{2/3} = V_{\mathrm{M}}^{2/3}$")
    stats_text.set_text(
        f"V_Κ = {vol_kappa:.3f}      "
        f"V_Λ = {vol_lambda:.3f}      "
        f"V_Μ = {vol_mu:.3f}      "
        f"derived ε scale = {derived_epsilon_scale:.3f}"
    )

    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")

    extent = max(6.0, ab_len, ag_len, bg_len) * 1.6
    ax.set_xlim(-extent * 0.6, extent * 1.1)
    ax.set_ylim(-extent * 0.6, extent * 1.1)
    ax.set_zlim(-extent * 0.8, extent * 0.8)

    ax.grid(True)
    set_axes_equal(ax)
    ax.view_init(elev=24, azim=-58)


def plot_geometry_app():
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection="3d")
    plt.subplots_adjust(left=0.08, right=0.95, bottom=0.20, top=0.72)

    title_text = fig.text(
        0.5,
        0.972,
        "Geometric Relationship Between the Volumes of a Pythagorean Triplet of Cylinders",
        ha="center",
        va="top",
        fontsize=19
    )

    formula_text = fig.text(
        0.5,
        0.915,
        r"$V_{\mathrm{K}}^{2/3} + V_{\Lambda}^{2/3} = V_{\mathrm{M}}^{2/3}$",
        ha="center",
        va="top",
        fontsize=22
    )

    stats_text = fig.text(
        0.5,
        0.875,
        "",
        ha="center",
        va="top",
        fontsize=11
    )

    ax_delta = fig.add_axes([0.12, 0.11, 0.72, 0.025])
    ax_epsilon = fig.add_axes([0.12, 0.075, 0.72, 0.025])
    ax_zeta = fig.add_axes([0.12, 0.04, 0.72, 0.025])

    s_delta = Slider(ax_delta, "δ", 1.0, 10.0, valinit=1.0, valstep=0.1)
    s_epsilon = Slider(ax_epsilon, "ε", 1.0, 10.0, valinit=1.0, valstep=0.1)
    s_zeta = Slider(ax_zeta, "ζ", 1.0, 10.0, valinit=1.0, valstep=0.1)

    draw_scene(
        ax=ax,
        fig=fig,
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
            fig=fig,
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


plot_geometry_app()
