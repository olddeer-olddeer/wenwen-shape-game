# -*- coding: utf-8 -*-
"""
========================================================
   文文开心每一天 - 手机图形拖动小游戏（优化版）
========================================================
功能特性：
1. 空心/实心图形，两两匹配消除
2. 每关同一种图形不会重复（5 种图形随机抽取）
3. 每关随机冰淇淋背景（冰淇淋1.jpeg / 2 / 3）
4. 图形随机游动
5. 红色醒目标题：第 N 关 ★ 文文开心每一天 ★
6. 全部消除后自动进入下一关，难度递增（最多 5 对）

运行方式：
    python main.py

依赖：
    pip install kivy
========================================================
"""

import os
import random
import math

from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.core.image import Image as CoreImage
from kivy.resources import resource_find
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.vector import Vector


# 图形类型：0=圆形, 1=方形, 2=三角形, 3=菱形, 4=六边形
SHAPE_TYPES = 5


class GameWidget(Widget):
    """游戏主控件：负责图形生成、绘制、触摸交互、随机游动"""

    SHAPE_SIZE = 60          # 图形尺寸
    TOUCH_RADIUS = 60        # 触摸选中半径
    MATCH_THRESHOLD = 80     # 匹配判定距离
    MAX_PAIRS = SHAPE_TYPES  # 最大对数（等于图形类型数，保证不重复）

    MOVE_SPEED = 40          # 游动速度
    TURN_PROBABILITY = 0.02  # 转向概率
    FPS = 20                 # 游动刷新率

    BACKGROUND_IMAGES = [
        "bg1.jpg",
        "bg2.jpg",
        "bg3.jpg",
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.level = 0
        self.shapes = []
        self.selected_shape = None
        self.bg_texture = None
        self._initialized = False

        Clock.schedule_interval(self._update_shapes, 1.0 / self.FPS)
        self.bind(size=self._on_size)

    def _on_size(self, *args):
        if not self._initialized and self.width > 0 and self.height > 0:
            self._initialized = True
            self.next_level()

    def load_random_background(self):
        """随机加载冰淇淋背景"""
        self.bg_texture = None
        image_name = random.choice(self.BACKGROUND_IMAGES)
        try:
            image_path = resource_find(image_name)
            if image_path:
                self.bg_texture = CoreImage(image_path).texture
            else:
                print(f"警告：找不到背景图片 {image_name}，使用默认背景")
        except Exception as e:
            print(f"警告：背景图片加载失败 {image_name}，错误：{e}")
            self.bg_texture = None

    # ---------- 关卡初始化 ----------
    def next_level(self):
        """进入下一关：随机抽取不重复的图形类型"""
        self.level += 1
        pairs = min(self.level, self.MAX_PAIRS)  # 第1关1对，第2关2对...

        self.load_random_background()

        self.shapes.clear()
        self.selected_shape = None

        # 从所有类型中随机抽取 pairs 个不重复的类型
        chosen_types = random.sample(range(SHAPE_TYPES), pairs)

        for shape_type in chosen_types:
            for solid in (True, False):
                angle = random.uniform(0, 2 * math.pi)
                shape = {
                    'type': shape_type,
                    'solid': solid,
                    'pos': [0, 0],
                    'initial': [0, 0],
                    'active': True,
                    'dir': [math.cos(angle), math.sin(angle)],
                }
                self.shapes.append(shape)

        self._place_shapes()
        self.draw()

        app = App.get_running_app()
        if app is not None and hasattr(app, 'update_level_label'):
            app.update_level_label(self.level)

    def _place_shapes(self):
        """随机放置图形，避免重叠"""
        margin = self.SHAPE_SIZE
        x_min = margin
        x_max = self.width - margin
        y_min = margin
        y_max = self.height - margin

        for shape in self.shapes:
            for _ in range(100):
                x = random.uniform(x_min, x_max)
                y = random.uniform(y_min, y_max)
                if not self._is_overlapping(x, y):
                    shape['initial'] = [x, y]
                    shape['pos'] = [x, y]
                    break

    def _is_overlapping(self, x, y):
        min_dist = self.SHAPE_SIZE + 10
        for s in self.shapes:
            if s['initial'][0] != 0 or s['initial'][1] != 0:
                if Vector(x, y).distance(s['initial']) < min_dist:
                    return True
        return False

    # ---------- 绘制辅助 ----------
    @staticmethod
    def get_vertices(shape_type, cx, cy, size):
        """返回图形顶点坐标列表（用于绘制空心多边形）"""
        half = size / 2
        if shape_type == 0:      # 圆形
            return None
        elif shape_type == 1:    # 方形
            return [
                (cx - half, cy - half),
                (cx + half, cy - half),
                (cx + half, cy + half),
                (cx - half, cy + half),
            ]
        elif shape_type == 2:    # 三角形
            return [
                (cx, cy + half),
                (cx - half * 0.87, cy - half * 0.5),
                (cx + half * 0.87, cy - half * 0.5),
            ]
        elif shape_type == 3:    # 菱形
            return [
                (cx, cy + half),
                (cx + half * 0.8, cy),
                (cx, cy - half),
                (cx - half * 0.8, cy),
            ]
        else:                    # 六边形
            pts = []
            for i in range(6):
                angle = math.radians(60 * i - 30)
                pts.append((cx + half * math.cos(angle), cy + half * math.sin(angle)))
            return pts

    def draw_shape(self, shape):
        """根据图形类型绘制实心或空心图形"""
        x, y = shape['pos']
        r = self.SHAPE_SIZE / 2

        with self.canvas:
            if shape['type'] == 0:  # 圆形
                if shape['solid']:
                    Color(0.2, 0.5, 1, 1)          # 实心蓝色
                    Ellipse(pos=(x - r, y - r), size=(self.SHAPE_SIZE, self.SHAPE_SIZE))
                else:
                    Color(1, 0.6, 0.2, 1)          # 空心橙色
                    Line(circle=(x, y, r), width=3)

            else:  # 多边形（方形、三角形、菱形、六边形）
                vertices = self.get_vertices(shape['type'], x, y, self.SHAPE_SIZE)
                if shape['solid']:
                    Color(0.2, 0.5, 1, 1)
                    # 使用多边形最近似圆的填充方式：用多个三角形/四边形拼接
                    if shape['type'] == 1:     # 方形用Rectangle
                        half = r
                        Rectangle(pos=(x - half, y - half), size=(self.SHAPE_SIZE, self.SHAPE_SIZE))
                    else:
                        # 将凸多边形拆分为三角形绘制填充
                        self._draw_convex_polygon(vertices)
                else:
                    Color(1, 0.6, 0.2, 1)
                    flat = [coord for v in vertices for coord in v]
                    Line(points=flat, close=True, width=3)

    def _draw_convex_polygon(self, vertices):
        """用三角形扇面填充凸多边形"""
        v0 = vertices[0]
        for i in range(1, len(vertices) - 1):
            v1 = vertices[i]
            v2 = vertices[i + 1]
            # 使用 Triangle 指令绘制三角形（三点坐标）
            from kivy.graphics import Triangle
            Triangle(points=[v0[0], v0[1], v1[0], v1[1], v2[0], v2[1]])

    # ---------- 绘制 ----------
    def draw(self):
        self.canvas.clear()

        # 背景
        with self.canvas:
            if self.bg_texture:
                Rectangle(texture=self.bg_texture, pos=self.pos, size=self.size)
            else:
                Color(0.97, 0.97, 0.97, 1)
                Rectangle(pos=self.pos, size=self.size)

        # 图形
        for shape in self.shapes:
            if not shape['active']:
                continue
            self.draw_shape(shape)

    # ---------- 随机游动 ----------
    def _update_shapes(self, dt):
        if not self.shapes or not self._initialized:
            return

        half = self.SHAPE_SIZE / 2
        x_min, x_max = half, self.width - half
        y_min, y_max = half, self.height - half

        for shape in self.shapes:
            if not shape['active'] or shape is self.selected_shape:
                continue

            speed = self.MOVE_SPEED * dt
            shape['pos'][0] += shape['dir'][0] * speed
            shape['pos'][1] += shape['dir'][1] * speed

            if shape['pos'][0] < x_min:
                shape['pos'][0] = x_min
                shape['dir'][0] = abs(shape['dir'][0])
            elif shape['pos'][0] > x_max:
                shape['pos'][0] = x_max
                shape['dir'][0] = -abs(shape['dir'][0])

            if shape['pos'][1] < y_min:
                shape['pos'][1] = y_min
                shape['dir'][1] = abs(shape['dir'][1])
            elif shape['pos'][1] > y_max:
                shape['pos'][1] = y_max
                shape['dir'][1] = -abs(shape['dir'][1])

            if random.random() < self.TURN_PROBABILITY:
                angle = random.uniform(-0.5, 0.5)
                cos_a, sin_a = math.cos(angle), math.sin(angle)
                dx, dy = shape['dir'][0], shape['dir'][1]
                shape['dir'][0] = dx * cos_a - dy * sin_a
                shape['dir'][1] = dx * sin_a + dy * cos_a
                norm = math.hypot(*shape['dir'])
                if norm > 0:
                    shape['dir'][0] /= norm
                    shape['dir'][1] /= norm

        self.draw()

    # ---------- 匹配 ----------
    def attempt_match(self, shape):
        for s in self.shapes:
            if s['active'] and not s['solid'] and s['type'] == shape['type']:
                if Vector(shape['pos']).distance(s['pos']) <= self.MATCH_THRESHOLD:
                    shape['active'] = False
                    s['active'] = False
                    return True
        return False

    # ---------- 触摸 ----------
    def on_touch_down(self, touch):
        for shape in reversed(self.shapes):
            if shape['active'] and shape['solid']:
                if Vector(touch.pos).distance(shape['pos']) <= self.TOUCH_RADIUS:
                    self.selected_shape = shape
                    shape['pos'] = list(touch.pos)
                    self.draw()
                    return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.selected_shape and self.selected_shape['active']:
            self.selected_shape['pos'] = list(touch.pos)
            self.draw()
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self.selected_shape:
            selected = self.selected_shape
            self.selected_shape = None

            matched = self.attempt_match(selected)

            if not matched:
                selected['pos'] = selected['initial'][:]
                angle = random.uniform(0, 2 * math.pi)
                selected['dir'] = [math.cos(angle), math.sin(angle)]

            self.draw()
            self._check_level_complete()
            return True
        return super().on_touch_up(touch)

    def _check_level_complete(self):
        for shape in self.shapes:
            if shape['solid'] and shape['active']:
                return
        Clock.schedule_once(lambda dt: self.next_level(), 0.5)


class ShapedDragApp(App):
    """Kivy 应用入口"""

    def build(self):
        layout = BoxLayout(orientation='vertical', spacing=5, padding=5)

        self.info_label = Label(
            text='文文开心每一天',
            size_hint=(1, 0.12),
            font_size='36sp',
            bold=True,
            color=(0.9, 0.1, 0.1, 1),
            halign='center',
            valign='middle'
        )

        self.game = GameWidget(size_hint=(1, 0.88))

        layout.add_widget(self.info_label)
        layout.add_widget(self.game)
        return layout

    def update_level_label(self, level):
        self.info_label.text = f"第 {level} 关  ★ 文文开心每一天 ★"


if __name__ == '__main__':
    ShapedDragApp().run()
