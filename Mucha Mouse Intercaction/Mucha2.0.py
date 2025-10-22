import pygame
import random
import math
from datetime import datetime
import pygame.gfxdraw  # 用于抗锯齿绘制（增强流畅度）

# 初始化Pygame
pygame.init()

# --------------------------
# 1. 风格与参数配置（增强写实感）
# --------------------------
# 穆夏色调+写实花卉配色（增加过渡色）
MUCHA_COLORS = {
    "bg": [(255, 248, 230), (240, 230, 250), (230, 245, 240)],
    "vine": [
        (60, 100, 50, 255), (80, 120, 60, 255),  # 深绿基底
        (100, 140, 80, 255), (120, 160, 100, 255)  # 浅绿过渡
    ],
    "petal": {
        "base": [(255, 190, 210, 255), (220, 170, 255, 255), (180, 230, 255, 255)],  # 花瓣底色
        "edge": [(255, 210, 220, 255), (230, 190, 255, 255), (200, 240, 255, 255)]   # 花瓣边缘色（更浅，增强层次）
    },
    "center": [(255, 220, 100, 255), (250, 180, 50, 255), (240, 160, 30, 255)],  # 花心多色过渡
    "stamen": [(255, 240, 180, 255)]  # 花蕊色（新增，增强写实）
}

# 窗口与性能配置
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("穆夏写实藤蔓 - 滑动生成，S保存")
clock = pygame.time.Clock()
FPS = 60
current_bg = 0
max_trail = 300  # 更多轨迹点，确保贝塞尔曲线流畅并保留更久
# 将退化速度拆分为轨迹与花朵两类，便于单独调节保留时间
TRAIL_FADE_SPEED = 1   # 轨迹衰减更慢（更长时间保留）
FLOWER_FADE_SPEED = 0.6 # 花朵衰减更慢（浮点允许更细腻）


# --------------------------
# 2. 核心类与工具函数（增强细节）
# --------------------------
class TrailPoint:
    """轨迹点（新增曲率参数，辅助藤蔓平滑）"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.alpha = 255
        self.curve_factor = random.uniform(-0.5, 0.5)  # 曲率因子，影响藤蔓弯曲
        # 每个轨迹点固定一种藤蔓颜色，避免每帧变色闪烁
        self.vine_color = random.choice(MUCHA_COLORS["vine"])[:]

    def fade(self):
        self.alpha = max(0, self.alpha - TRAIL_FADE_SPEED)
        return self.alpha == 0


def bezier_curve(points, num_segments=10):
    """贝塞尔曲线计算（让藤蔓更流畅）"""
    if len(points) < 3:
        return []  # 点太少时返回空列表

    curve = []
    n = len(points) - 1
    # 现在同时计算位置、对应的透明度（alpha）和颜色（r,g,b），以便后续绘制使用
    for t in [i/num_segments for i in range(num_segments+1)]:
        x, y, a = 0.0, 0.0, 0.0
        r, g, b = 0.0, 0.0, 0.0
        for i in range(n+1):
            # 贝塞尔公式：加权平均控制点
            binom = math.comb(n, i) * (t**i) * ((1-t)**(n-i))
            pt = points[i]
            x += binom * pt.x
            y += binom * pt.y
            a += binom * pt.alpha
            # 混合颜色
            vc = pt.vine_color
            r += binom * vc[0]
            g += binom * vc[1]
            b += binom * vc[2]
        curve.append((x, y, a, r, g, b))
    return curve


def draw_realistic_flower(surf, x, y, size, alpha):
    """写实花卉绘制（使用传入的已缓存花瓣多边形与颜色，避免每帧随机）
    如果调用方传入 petal_layers（每层是 list of polygon points）和 colors，则直接绘制。
    """
    # 支持两种调用方式：1) 传入 cached_layers/colors；2) 没有传入则回退到随机绘制（兼容性）
    try:
        petal_layers
        petal_colors
    except NameError:
        # 兼容旧调用：随机一次性生成颜色和形状
        petal_colors = [list(random.choice(MUCHA_COLORS["petal"]["base"])) for _ in range(3)]
        for pc in petal_colors:
            pc[3] = alpha
        petal_layers = []
        for layer in [1.0, 0.85, 0.7]:
            layer_polys = []
            for i in range(5):
                angle = math.radians(i * 72)
                petal_size = size * layer
                p1 = (int(x + math.cos(angle) * petal_size), int(y + math.sin(angle) * petal_size * 0.8))
                p2 = (int(x + math.cos(angle + math.radians(30)) * petal_size * 0.6), int(y + math.sin(angle + math.radians(30)) * petal_size * 1.2))
                p3 = (int(x + math.cos(angle - math.radians(30)) * petal_size * 0.6), int(y + math.sin(angle - math.radians(30)) * petal_size * 1.2))
                layer_polys.append([p1, p2, (int(x), int(y)), p3])
            petal_layers.append(layer_polys)

    # 绘制分层花瓣（从大到小），petal_layers: list(layer -> list(polygons))
    for layer_idx, layer in enumerate(petal_layers):
        color = petal_colors[min(layer_idx, len(petal_colors)-1)]
        for poly in layer:
            pygame.gfxdraw.filled_polygon(surf, poly, color)
            pygame.gfxdraw.aapolygon(surf, poly, color)

    # 绘制花心和花蕊
    center_radius = int(size // 3)
    center_color = random.choice(MUCHA_COLORS["center"])[:]
    pygame.gfxdraw.filled_circle(surf, int(x), int(y), center_radius, center_color)
    stamen_color = list(MUCHA_COLORS["stamen"][0])
    stamen_color[3] = alpha
    for i in range(12):
        angle = math.radians(i * 30)
        stamen_length = center_radius * 1.2
        sx = int(x + math.cos(angle) * stamen_length)
        sy = int(y + math.sin(angle) * stamen_length)
        pygame.gfxdraw.line(surf, int(x), int(y), sx, sy, stamen_color)


# Flower 类：缓存花瓣多边形与颜色以确保每朵花稳定不闪烁
class Flower:
    def __init__(self, x, y, size):
        self.x = x
        self.y = y
        self.size = size
        self.alpha = 255
        # 生成稳定的颜色与角度偏移
        self.base_color = list(random.choice(MUCHA_COLORS["petal"]["base"]))
        self.edge_color = list(random.choice(MUCHA_COLORS["petal"]["edge"]))
        # 计算3层花瓣的多边形（缓存）
        self.layers = []
        jitter = random.uniform(-6, 6)
        for layer in [1.0, 0.88, 0.76]:
            layer_polys = []
            for i in range(5):
                angle = math.radians(i * 72 + jitter)
                petal_size = int(size * layer)
                p1 = (int(self.x + math.cos(angle) * petal_size), int(self.y + math.sin(angle) * petal_size * 0.85))
                p2 = (int(self.x + math.cos(angle + math.radians(28)) * petal_size * 0.62), int(self.y + math.sin(angle + math.radians(28)) * petal_size * 1.1))
                p3 = (int(self.x + math.cos(angle - math.radians(28)) * petal_size * 0.62), int(self.y + math.sin(angle - math.radians(28)) * petal_size * 1.1))
                layer_polys.append([p1, p2, (int(self.x), int(self.y)), p3])
            self.layers.append(layer_polys)

    def fade(self):
        self.alpha = max(0, self.alpha - FLOWER_FADE_SPEED)
        return self.alpha == 0

    def draw(self, surf):
        # 应用当前 alpha 到颜色并绘制
        base = self.base_color[:]
        edge = self.edge_color[:]
        base[3] = self.alpha
        edge[3] = self.alpha
        # 轻微混合边缘色以制造柔和效果
        for li, layer in enumerate(self.layers):
            col = base
            for poly in layer:
                pygame.gfxdraw.filled_polygon(surf, poly, col)
                pygame.gfxdraw.aapolygon(surf, poly, edge)

# 全局花朵列表与 alpha surface
flowers = []
alpha_surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), flags=pygame.SRCALPHA)


def draw_smooth_vine(surf, trail_points):
    """流畅藤蔓绘制（贝塞尔曲线+自然粗细变化）"""
    if len(trail_points) < 3:
        return []

    # 用贝塞尔曲线平滑轨迹（同时得到对应 alpha）
    curve_points = bezier_curve(trail_points)

    # 绘制藤蔓主线（随曲线动态调整粗细）
    for i in range(1, len(curve_points)):
        x1, y1, a1, r1, g1, b1 = curve_points[i-1]
        x2, y2, a2, r2, g2, b2 = curve_points[i]
        # 计算两点距离，动态调整粗细（加入随机波动，更自然）
        distance = math.hypot(x2 - x1, y2 - y1)
        base_width = max(2, 7 - int(distance // 8))
        vine_width = base_width + random.uniform(-0.5, 0.5)  # 细微波动

        # 使用曲线上点的 alpha 作为颜色透明度
        alpha = int((a1 + a2) / 2)
        # 使用贝塞尔混合得到的颜色（更稳定，不随机）
        vine_color = [int((r1 + r2) / 2), int((g1 + g2) / 2), int((b1 + b2) / 2), alpha]

        # 抗锯齿线条绘制（增强流畅感）
        pygame.gfxdraw.line(surf, int(x1), int(y1), int(x2), int(y2), vine_color)
        # 藤蔓边缘柔和处理（叠加细线条）
        if vine_width > 3:
            light_color = list(vine_color)
            light_color[1] = min(255, light_color[1] + 20)  # 稍亮的边缘色
            pygame.gfxdraw.line(surf, int(x1)+1, int(y1), int(x2)+1, int(y2), light_color)

    return curve_points


def save_drawing(surf):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"mucha_realistic_art_{timestamp}.png"
    pygame.image.save(surf, filename)
    print(f"写实画作已保存：{filename}")


# --------------------------
# 3. 主游戏循环
# --------------------------
running = True
trail_points = []

while running:
    # 事件处理
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            current_bg = (current_bg + 1) % len(MUCHA_COLORS["bg"])
        if event.type == pygame.KEYDOWN and event.key == pygame.K_s:
            save_drawing(screen)
    
    # 鼠标轨迹更新
    mouse_x, mouse_y = pygame.mouse.get_pos()
    if not trail_points or (abs(mouse_x - trail_points[-1].x) > 2 or abs(mouse_y - trail_points[-1].y) > 2):
        trail_points.append(TrailPoint(mouse_x, mouse_y))
        if len(trail_points) > max_trail:
            trail_points.pop(0)
    
    # 轨迹渐变消失
    trail_points = [p for p in trail_points if not p.fade()]
    
    # 绘制画面（先背景）
    screen.fill(MUCHA_COLORS["bg"][current_bg])
    # 清空 alpha_surf
    alpha_surf.fill((0, 0, 0, 0))
    # 在 alpha_surf 上绘制流畅藤蔓并获取曲线点
    curve_points = draw_smooth_vine(alpha_surf, trail_points)
    # 在曲线顶点生成固定的 Flower 对象（避免每帧变形/变色）
    if len(curve_points) > 5 and random.random() < 0.12:
        peak_idx = random.choice(range(3, len(curve_points)-3))
        px, py, pa, pr, pg, pb = curve_points[peak_idx]
        flower_size = random.randint(12, 20)
        f = Flower(int(px), int(py), flower_size)
        f.alpha = int(pa)
        flowers.append(f)

    # 绘制并更新花朵（移除已消失的）
    new_flowers = []
    for f in flowers:
        if not f.fade():
            f.draw(alpha_surf)
            new_flowers.append(f)
    flowers = new_flowers

    # 把 alpha_surf 一次性 blit 到屏幕上
    screen.blit(alpha_surf, (0, 0))
    
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()