#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
区域选择工具
用于可视化选择关闭按钮的搜索区域
"""

import pyautogui
import tkinter as tk
from tkinter import messagebox


class RegionSelector:
    """可视化区域选择器"""
    
    def __init__(self):
        # 创建全屏半透明窗口
        self.root = tk.Tk()
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-alpha', 0.3)  # 30% 透明度
        self.root.configure(bg='black')
        
        # 创建画布
        self.canvas = tk.Canvas(self.root, cursor="cross", bg='black', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # 初始化变量
        self.start_x = None
        self.start_y = None
        self.rect = None
        self.region = None
        
        # 绑定鼠标事件
        self.canvas.bind('<ButtonPress-1>', self.on_press)
        self.canvas.bind('<B1-Motion>', self.on_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_release)
        self.root.bind('<Escape>', lambda e: self.cancel())
        
        # 显示操作提示
        self.canvas.create_text(
            self.root.winfo_screenwidth() // 2, 50,
            text="拖动鼠标选择区域\nESC 取消 | 松开鼠标确认",
            font=('Arial', 20, 'bold'),
            fill='yellow',
            justify=tk.CENTER
        )
    
    def on_press(self, event):
        """鼠标按下 - 开始选择"""
        self.start_x = event.x
        self.start_y = event.y
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline='red', width=3, dash=(5, 5)
        )
    
    def on_drag(self, event):
        """鼠标拖动 - 更新选择框"""
        if self.rect:
            self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)
    
    def on_release(self, event):
        """鼠标释放 - 确认选择"""
        x = min(self.start_x, event.x)
        y = min(self.start_y, event.y)
        width = abs(event.x - self.start_x)
        height = abs(event.y - self.start_y)
        
        # 验证区域大小
        if width < 10 or height < 10:
            messagebox.showwarning("区域太小", "请重新选择更大的区域")
            if self.rect:
                self.canvas.delete(self.rect)
            return
        
        self.region = (x, y, width, height)
        self.root.quit()
    
    def cancel(self):
        """取消选择"""
        self.region = None
        self.root.quit()
    
    def select(self):
        """启动选择界面"""
        self.root.mainloop()
        self.root.destroy()
        return self.region


def main():
    """主程序"""
    print("="*60)
    print("关闭按钮区域选择工具")
    print("="*60)
    print("\n操作步骤:")
    print("1. 打开微信红包详情页（显示关闭按钮）")
    print("2. 按 Enter 启动选择工具")
    print("3. 鼠标拖动选择包含关闭按钮的区域")
    print("4. 松开鼠标确认")
    print("5. 复制生成的配置参数")
    print("\n提示:")
    print("- 区域应略大于关闭按钮")
    print("- 避免区域过大（可能包含其他程序的按钮）")
    print("- 按 ESC 取消")
    print("="*60)
    
    input("\n按 Enter 开始...")
    
    # 启动选择器
    selector = RegionSelector()
    region = selector.select()
    
    if region:
        x, y, width, height = region
        print("\n✓ 选择成功！")
        print("="*60)
        print("配置参数:")
        print("-"*60)
        print(f"'back_button_search_region': ({x}, {y}, {width}, {height}),")
        print("-"*60)
        print("\n复制上面的参数到主程序 config 字典中")
        print(f"\n区域: ({x},{y}) 大小: {width}x{height}px")
        print("="*60)
    else:
        print("\n已取消")


if __name__ == "__main__":
    main()
