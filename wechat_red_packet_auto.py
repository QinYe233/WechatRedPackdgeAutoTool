#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信红包自动识别点击程序
功能：自动识别并点击红包 -> 打开按钮 -> 关闭按钮
仅支持桌面微信 (Windows/macOS/Linux)
"""

import cv2
import numpy as np
import pyautogui
import time
import sys
import os
from typing import Optional, Tuple


class RedPacketBot:
    """红包机器人 - 三步循环：找红包 -> 点打开 -> 点关闭"""
    
    def __init__(self, red_packet_path: str, open_button_path: str, back_button_path: str,
                 threshold: float = 0.8, interval: float = 0.02, 
                 post_click_delay: float = 0.05, open_button_timeout: float = 0.5,
                 back_button_delay: float = 0.5, 
                 back_button_search_region: Optional[Tuple[int, int, int, int]] = None,
                 back_button_threshold: Optional[float] = None):
        """
        初始化配置
        
        参数说明：
            红包和打开按钮：
                threshold: 匹配度 0.8 = 80%
                interval: 每 0.02 秒检测一次
                post_click_delay: 点击后等待 0.05 秒
                open_button_timeout: 打开按钮超时 0.5 秒
            
            关闭按钮（防误识别）：
                back_button_delay: 等待 0.5 秒再查找
                back_button_threshold: 独立匹配度，1.0 = 100%完全匹配
                back_button_search_region: 限制搜索区域 (x, y, 宽, 高)
        """
        # 基础配置
        self.threshold = threshold
        self.interval = interval
        self.post_click_delay = post_click_delay
        self.open_button_timeout = open_button_timeout
        
        # 关闭按钮特殊配置
        self.back_button_delay = back_button_delay
        self.back_button_search_region = back_button_search_region
        self.back_button_threshold = back_button_threshold if back_button_threshold is not None else threshold
        
        # 加载模板图片
        self.templates = {}
        self._load_templates({
            'red_packet': red_packet_path,
            'open_button': open_button_path,
            'back_button': back_button_path
        })
        
        # 统计数据
        self.stats = {'red_packets_found': 0, 'red_packets_opened': 0, 'cycles_completed': 0}
        self.running = False
        
    def _load_templates(self, template_paths: dict):
        """加载模板图片"""
        for name, path in template_paths.items():
            if not os.path.exists(path):
                raise FileNotFoundError(f"找不到文件: {path}")
            
            template = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
            if template is None:
                raise ValueError(f"无法读取图片: {path}")
            
            self.templates[name] = template
            print(f"✓ {name}: {template.shape[1]}x{template.shape[0]}px")
    
    def _find_image(self, template_name: str, 
                    search_region: Optional[Tuple[int, int, int, int]] = None, 
                    custom_threshold: Optional[float] = None) -> Optional[Tuple[int, int, float]]:
        """
        在屏幕中查找图片
        返回: (x坐标, y坐标, 匹配度) 或 None
        """
        threshold = custom_threshold if custom_threshold is not None else self.threshold
        
        # 截屏
        if search_region:
            x, y, w, h = search_region
            screenshot = pyautogui.screenshot(region=(x, y, w, h))
            offset_x, offset_y = x, y
        else:
            screenshot = pyautogui.screenshot()
            offset_x, offset_y = 0, 0
        
        # 转灰度图
        screenshot_gray = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)
        template = self.templates[template_name]
        
        # 模板匹配
        result = cv2.matchTemplate(screenshot_gray, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        # 匹配成功
        if max_val >= threshold:
            h, w = template.shape
            center_x = max_loc[0] + w // 2 + offset_x
            center_y = max_loc[1] + h // 2 + offset_y
            return center_x, center_y, max_val
        
        return None
    
    def _wait_and_click(self, template_name: str, 
                        timeout: Optional[float] = None, 
                        description: str = "", 
                        pre_delay: float = 0.0,
                        search_region: Optional[Tuple[int, int, int, int]] = None,
                        custom_threshold: Optional[float] = None) -> bool:
        """等待图像出现并点击"""
        threshold = custom_threshold if custom_threshold is not None else self.threshold
        
        # 延迟等待
        if pre_delay > 0:
            print(f"等待 {pre_delay:.1f}秒...", end='', flush=True)
            time.sleep(pre_delay)
        
        # 显示搜索信息
        desc = description or template_name
        threshold_tag = f" [{threshold:.0%}]" if custom_threshold else ""
        print(f"查找{desc}{threshold_tag}", end='', flush=True)
        
        start_time = time.time()
        dots = 0
        
        while self.running:
            # 超时检查
            if timeout and (time.time() - start_time > timeout):
                print(f" ⏱超时")
                return False
            
            # 查找并点击
            result = self._find_image(template_name, search_region, custom_threshold)
            if result:
                x, y, confidence = result
                print(f" ✓ ({x},{y}) {confidence:.0%}")
                pyautogui.click(x, y)
                time.sleep(self.post_click_delay)
                return True
            
            # 等待动画
            if int((time.time() - start_time) * 10) > dots:
                print('.', end='', flush=True)
                dots += 1
            
            time.sleep(self.interval)
        
        return False
    
    def run(self):
        """启动机器人"""
        self.running = True
        
        # 显示配置
        print("\n" + "="*60)
        print("🧧 微信红包自动抢夺")
        print("="*60)
        print(f"红包/打开按钮: {self.threshold:.0%} 匹配度")
        print(f"关闭按钮: {self.back_button_threshold:.0%} 匹配度" + 
              (" 🎯完全匹配" if self.back_button_threshold >= 0.99 else ""))
        print(f"搜索间隔: {self.interval*1000:.0f}ms | 点击延迟: {self.post_click_delay*1000:.0f}ms")
        if self.back_button_search_region:
            x, y, w, h = self.back_button_search_region
            print(f"关闭按钮区域: ({x},{y}) {w}x{h}px")
        print("按 Ctrl+C 停止")
        print("="*60 + "\n")
        
        try:
            while self.running:
                round_num = self.stats['cycles_completed'] + 1
                print(f"\n━━━ 第 {round_num} 轮 ━━━")
                
                # 步骤1: 找红包
                if not self._wait_and_click('red_packet', description="红包"):
                    continue
                self.stats['red_packets_found'] += 1
                
                # 步骤2: 点打开（有超时）
                if self._wait_and_click('open_button', timeout=self.open_button_timeout, description="打开"):
                    self.stats['red_packets_opened'] += 1
                
                # 步骤3: 点关闭（延迟+区域+高阈值）
                self._wait_and_click('back_button', 
                                    description="关闭",
                                    pre_delay=self.back_button_delay,
                                    search_region=self.back_button_search_region,
                                    custom_threshold=self.back_button_threshold)
                
                self.stats['cycles_completed'] += 1
                print(f"✓ 完成")
                
        except KeyboardInterrupt:
            print("\n\n收到停止信号")
        finally:
            self.stop()
    
    def stop(self):
        """停止并显示统计"""
        self.running = False
        print("\n" + "="*60)
        print("📊 统计")
        print("="*60)
        print(f"发现: {self.stats['red_packets_found']} 个")
        print(f"打开: {self.stats['red_packets_opened']} 个")
        print(f"轮数: {self.stats['cycles_completed']} 轮")
        if self.stats['red_packets_found'] > 0:
            rate = self.stats['red_packets_opened'] / self.stats['red_packets_found'] * 100
            print(f"成功率: {rate:.1f}%")
        print("="*60)


def main():
    """主程序"""
    
    # ==================== 配置区 ====================
    config = {
        # 图片路径（一般不需要改，已打包在 PNG 文件夹）
        'red_packet_path': r"PNG\red_packet_icon.png",
        'open_button_path': r"PNG\open_button.png",
        'back_button_path': r"PNG\back_icon.png",
        
        # 基础设置
        'threshold': 0.8,              # 红包和打开按钮：80% 匹配
        'interval': 0.02,              # 20ms 检测一次
        'post_click_delay': 0.05,      # 点击后等 50ms
        'open_button_timeout': 0.5,    # 打开按钮 0.5 秒超时
        
        # 关闭按钮防误触（重要！）
        'back_button_delay': 0.5,      # 等 0.5 秒再查找
        'back_button_threshold': 1.0,  # 100% 匹配（推荐）
        'back_button_search_region': None,  # 限制区域 (x, y, 宽, 高)，运行 select_region.py 获取
        
        # 提示：
        # 1. 运行 select_region.py 可视化选择关闭按钮区域
        # 2. 设置 back_button_threshold=1.0 要求完全匹配
        # 3. 如果误识别其他程序，缩小 back_button_search_region
    }
    # ==============================================
    
    try:
        bot = RedPacketBot(**config)
        bot.run()
    except FileNotFoundError as e:
        print(f"\n❌ {e}")
        print("请检查图片路径")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
