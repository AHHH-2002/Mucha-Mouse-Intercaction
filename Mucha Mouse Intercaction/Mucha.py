import pygame
import random
import math
from datetime import datetime  # 用于生成带时间戳的文件名

# 初始化Pygame
pygame.init()

# --------------------------
# 1. 配置参数（穆夏风格+功能扩展）
# --------------------------
MUCHA_COLORS = {
    "bg": [(255, 248, 230), (240, 230, 250), (230, 245, 240)],  # 背景色
    "vine": [(80, 120, 60, 255), (100, 140, 80, 255), (60, 100, 70, 255)],  # 藤蔓色（新增alpha通道）
    "petal": [(255, 180, 200, 255), (220, 160, 255, 255), (180, 220, 255, 255)],  # 花瓣色（含alpha）
    "center": [(255, 220, 100, 255), (250, 180, 50, 255)]  # 花心色（含alpha）
}

# 窗口设置
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("穆夏藤蔓繁花 - 滑动生成，S保存，点击换背景")

# 游戏参数（新增渐变消失相关）
clock = pygame.time.Clock()
FPS = 60
current_bg = 0
max_trail = 80  # 最大轨迹点数量（比之前多，适配渐变效果）
fade_speed = 3  # 透明度衰减速度（值越大消失越快）


# --------------------------
# 2. 核心类与函数（新增渐变逻辑）
# --------------------------
class TrailPoint:
    """轨迹点类（存储位置与透明度，支持渐变消失）"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.alpha = 255  # 初始透明度（完全不透明）
        # 每个轨迹点固定一种藤蔓颜色，避免每次绘制时颜色抖动
        self.vine_color = random.choice(MUCHA_COLORS["vine"])
    
    def fade(self):
        """降低透明度，返回是否已完全透明"""
        self.alpha = max(0, self.alpha - fade_speed)
        return self.alpha == 0


def draw_mucha_flower(surf, x, y, size, alpha):
    """绘制带透明度的穆夏风格花卉。
    现在接受颜色参数以保证同一花朵颜色稳定（避免闪烁）。
    如果传入的是 (r,g,b,a) 元组，会按其 alpha 与传入 alpha 做最小值处理。
    """
    # 选择稳定的颜色（如果外部传入 None，则在内部选择一次）
    # 支持 petal_color, center_color 作为参数 tuple 的情形通过包装在调用端处理。
    
    # 如果调用方未传入具体颜色，则在内部随机选择（保持原行为）
    global _tmp_petal_color, _tmp_center_color
    try:
        petal_color
        center_color
    except NameError:
        _tmp_petal_color = list(random.choice(MUCHA_COLORS["petal"]))
        _tmp_center_color = list(random.choice(MUCHA_COLORS["center"]))
        petal_color = _tmp_petal_color
        center_color = _tmp_center_color
    # 传入的颜色已是带 alpha 的 tuple/list
    petal_color = list(petal_color)
    center_color = list(center_color)
    # 应用当前 alpha（取两者的最小值以避免透明度溢出）
    petal_color[3] = min(petal_color[3], alpha)
    center_color[3] = min(center_color[3], alpha)

    # 绘制花瓣（5片旋转排列）
    for i in range(5):
        angle = math.radians(i * 72)
        petal_x = x + math.cos(angle) * size
        petal_y = y + math.sin(angle) * size
        petal_rect = pygame.Rect(petal_x - size//2, petal_y - size//4, size, size//2)
        pygame.draw.ellipse(surf, tuple(petal_color), petal_rect)

    # 绘制花心
    center_radius = size // 4
    pygame.draw.circle(surf, tuple(center_color), (x, y), center_radius)


def draw_mucha_vine(surf, trail_points):
    """绘制带渐变消失效果的藤蔓"""
    if len(trail_points) < 2:
        return
    
    # 遍历轨迹点绘制藤蔓段
    for i in range(1, len(trail_points)):
        p1 = trail_points[i-1]
        p2 = trail_points[i]

        # 计算两点距离（控制藤蔓粗细）
        distance = math.hypot(p2.x - p1.x, p2.y - p1.y)
        vine_width = max(2, 8 - int(distance // 5))

        # 使用两点预先固定的颜色，按透明度平均值混合
        avg_alpha = (p1.alpha + p2.alpha) // 2
        c1 = p1.vine_color
        c2 = p2.vine_color
        # 简单混色：按两点颜色加权平均
        vine_color = [
            (c1[0] + c2[0]) // 2,
            (c1[1] + c2[1]) // 2,
            (c1[2] + c2[2]) // 2,
            avg_alpha,
        ]

        # 绘制抗锯齿藤蔓（在带 alpha 的 surface 上绘制）
        pygame.draw.line(surf, tuple(vine_color), (p1.x, p1.y), (p2.x, p2.y), vine_width)

        # 在移动缓慢且间距较近时按概率生成一朵花，花朵颜色固定（避免每帧变色）
        if distance < 15 and random.random() < 0.18:
            flower_size = random.randint(8, 15)
            petal_color = list(random.choice(MUCHA_COLORS["petal"]))
            center_color = list(random.choice(MUCHA_COLORS["center"]))
            # 花朵的初始 alpha 跟藤蔓段保持一致
            petal_color[3] = avg_alpha
            center_color[3] = avg_alpha
            # 创建一个固定颜色的花朵对象并附加到全局 flowers 列表
            flowers.append(Flower(p2.x, p2.y, flower_size, petal_color, center_color))


class Flower:
    """表示一朵花的类，保存颜色/大小/位置/透明度并负责自我衰减"""
    def __init__(self, x, y, size, petal_color, center_color):
        self.x = x
        self.y = y
        self.size = size
        self.petal_color = list(petal_color)
        self.center_color = list(center_color)
        self.alpha = min(self.petal_color[3], self.center_color[3])

    def fade(self):
        self.alpha = max(0, self.alpha - fade_speed)
        return self.alpha == 0

    def draw(self, surf):
        # 在绘制时应用当前 alpha
        pc = list(self.petal_color)
        cc = list(self.center_color)
        pc[3] = min(pc[3], self.alpha)
        cc[3] = min(cc[3], self.alpha)
        draw_mucha_flower(surf, int(self.x), int(self.y), self.size, self.alpha)


# 全局花朵列表
flowers = []

# 创建一个带 alpha 的临时 surface，用于一次性绘制藤蔓+花朵以减少闪烁
alpha_surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), flags=pygame.SRCALPHA)


def save_drawing(surf):
    """保存当前画面为PNG（带时间戳，避免重名）"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"mucha_art_{timestamp}.png"
    pygame.image.save(surf, filename)
    print(f"画作已保存：{filename}")  # 控制台提示保存成功


# --------------------------
# 3. 主游戏循环（整合新功能）
# --------------------------
running = True
trail_points = []  # 存储TrailPoint对象（替代原坐标列表）

while running:
    # 事件处理
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        # 点击切换背景色
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            current_bg = (current_bg + 1) % len(MUCHA_COLORS["bg"])
        # 按S键保存画作
        if event.type == pygame.KEYDOWN and event.key == pygame.K_s:
            save_drawing(screen)
    
    # 鼠标轨迹更新（只在移动时添加新点）
    mouse_x, mouse_y = pygame.mouse.get_pos()
    if not trail_points or (mouse_x != trail_points[-1].x or mouse_y != trail_points[-1].y):
        trail_points.append(TrailPoint(mouse_x, mouse_y))
        # 限制轨迹点数量
        if len(trail_points) > max_trail:
            trail_points.pop(0)
    
    # 轨迹点渐变消失（更新透明度，移除完全透明的点）
    trail_points = [p for p in trail_points if not p.fade()]
    
    # 绘制画面
    screen.fill(MUCHA_COLORS["bg"][current_bg])  # 填充背景
    # 清空 alpha_surf
    alpha_surf.fill((0, 0, 0, 0))
    # 在 alpha_surf 上绘制藤蔓和新增的花朵
    draw_mucha_vine(alpha_surf, trail_points)
    # 绘制并更新花朵：移除已完全透明的花朵
    new_flowers = []
    for f in flowers:
        if not f.fade():
            f.draw(alpha_surf)
            new_flowers.append(f)
    flowers = new_flowers
    # 将 alpha_surf 一次性 blit 到屏幕，减少因多次 draw 引起的闪烁
    screen.blit(alpha_surf, (0, 0))
    
    # 更新显示
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()