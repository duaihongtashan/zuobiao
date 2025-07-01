# 快捷键自定义功能使用指南

## 🎯 功能概述

截图工具现在支持完全自定义快捷键，用户可以根据个人喜好和系统环境设置专属的快捷键组合。

## ⌨️ 快捷键格式规范

### 基本格式
```
修饰键+主键
```

### 修饰键 (至少选择一个)
- `ctrl` - Ctrl键
- `shift` - Shift键  
- `alt` - Alt键
- `win` - Windows键

### 主键 (选择一个)
- **字母**: a-z
- **数字**: 0-9
- **功能键**: f1-f12
- **特殊键**: space, enter, tab, esc, backspace, delete
- **方向键**: up, down, left, right
- **其他**: home, end, page_up, page_down

## ✅ 正确示例

```bash
ctrl+shift+s     # 标准三键组合
alt+f4           # Alt + F4
ctrl+alt+delete  # 经典组合
win+r            # Windows + R
shift+f10        # Shift + F10
ctrl+space       # Ctrl + 空格
alt+tab          # Alt + Tab
```

## ❌ 错误示例

```bash
s                    # ❌ 缺少修饰键
ctrl+                # ❌ 缺少主键
ctrl+shift+ctrl      # ❌ 重复修饰键
invalid+key          # ❌ 无效键名
ctrl shift s         # ❌ 缺少+号分隔符
CTRL+SHIFT+S         # ❌ 大写字母（请使用小写）
```

## 🖥️ GUI界面操作

### 1. 打开快捷键设置
在主界面中找到"快捷键设置 (可自定义)"区域。

### 2. 编辑快捷键
- **单次截图**: 默认 `ctrl+shift+s`
- **连续截图**: 默认 `ctrl+shift+c`
- **停止截图**: 默认 `ctrl+shift+x`

### 3. 验证快捷键
点击"验证快捷键"按钮，系统会检查：
- ✅ 格式是否正确
- ✅ 是否存在冲突
- ✅ 键名是否有效

### 4. 应用设置
点击"应用快捷键"按钮：
- 停止当前快捷键监听
- 注册新的快捷键
- 重启快捷键服务
- 保存配置到文件

### 5. 重置默认
点击"重置默认"恢复到出厂设置。

## 🔧 命令行测试

### 运行快捷键测试程序
```bash
uv run python hotkey_test.py
```

### 测试功能
1. **验证快捷键格式** - 检查快捷键是否符合规范
2. **启动快捷键监听** - 实时测试快捷键响应
3. **停止快捷键监听** - 停止监听服务
4. **显示当前配置** - 查看已保存的快捷键
5. **测试自定义快捷键** - 交互式设置新快捷键

## 📋 配置文件格式

快捷键保存在 `config.json` 文件中：

```json
{
  "hotkeys": {
    "single_capture": "ctrl+shift+s",
    "start_continuous": "ctrl+shift+c",
    "stop_continuous": "ctrl+shift+x"
  }
}
```

## 🚨 常见问题与解决方案

### 问题1: 快捷键不响应
**可能原因**:
- 被其他程序占用
- 权限不足
- 快捷键服务未启动

**解决方案**:
```bash
# 1. 检查快捷键服务状态
uv run python hotkey_test.py

# 2. 选择选项2启动监听测试
# 3. 尝试不同的快捷键组合
```

### 问题2: 格式验证失败
**可能原因**:
- 修饰键拼写错误
- 缺少+号分隔符
- 使用了无效的主键

**解决方案**:
```bash
# 检查格式是否正确
ctrl+shift+s  ✅ 正确
ctlr+shift+s  ❌ ctrl拼写错误
ctrl shift s  ❌ 缺少+号
ctrl+invalid  ❌ invalid不是有效主键
```

### 问题3: 快捷键冲突
**可能原因**:
- 三个快捷键设置相同
- 与系统快捷键冲突

**解决方案**:
- 确保三个快捷键都不相同
- 避免使用系统预留快捷键如 `ctrl+alt+delete`
- 选择不常用的组合如 `ctrl+shift+f1`

## 💡 推荐快捷键组合

### 适合办公环境
```bash
ctrl+shift+s    # 单次截图
ctrl+shift+d    # 连续截图  
ctrl+shift+q    # 停止截图
```

### 适合游戏环境
```bash
alt+f1          # 单次截图
alt+f2          # 连续截图
alt+f3          # 停止截图
```

### 适合设计师
```bash
ctrl+shift+1    # 单次截图
ctrl+shift+2    # 连续截图
ctrl+shift+3    # 停止截图
```

## 🔐 安全注意事项

1. **避免系统快捷键**: 不要使用 `ctrl+alt+delete`、`win+l` 等系统保留快捷键
2. **检查软件冲突**: 确保快捷键不与其他软件冲突
3. **权限问题**: 在某些企业环境中可能需要管理员权限
4. **备份配置**: 建议备份 `config.json` 文件

## 🎉 高级技巧

### 1. 批量设置快捷键
编辑 `config.json` 文件直接设置：
```json
{
  "hotkeys": {
    "single_capture": "ctrl+shift+f1",
    "start_continuous": "ctrl+shift+f2", 
    "stop_continuous": "ctrl+shift+f3"
  }
}
```

### 2. 导入导出配置
```bash
# 备份当前配置
cp config.json config_backup.json

# 恢复配置
cp config_backup.json config.json
```

### 3. 快速验证
```bash
# 使用命令行快速验证快捷键
uv run python -c "
from core.hotkey import hotkey_manager
result = hotkey_manager.validate_hotkey_with_details('ctrl+shift+s')
print('验证结果:', result)
"
```

---

🎯 **现在你可以完全自定义快捷键，让截图工具更符合你的使用习惯！** 