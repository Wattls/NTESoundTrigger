# NTESoundTrigger

基于波形识别的异环（NTE）游戏音效自动触发工具，支持闪避和承轨反击自动操作。

## 功能特点

- 🔊 **自动闪避触发**：识别闪避音效波形，自动执行闪避操作
- ⚔️ **承轨反击自动触发**：识别反击音效波形，自动执行反击操作
- 🎛️ **可配置参数**：阈值、波形文件、触发间隔等参数可自定义
- 📊 **实时波形监控**：内置监控模块，实时追踪匹配分数
- 🎯 **高通滤波**：Butterworth 高通滤波器，去除低频噪音，提高准确率

## 快速开始

### 环境要求

- Python 3.8+
- Windows 系统（使用 soundcard 的 mediafoundation）

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行程序

**注意：需要以管理员身份运行**

```bash
python Main.py
```

## 配置说明

修改 `Main.py` 中的参数来自定义行为：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `SAMPLE_PATH` | 闪避特征波形文件位置 | `./闪避波形.wav` |
| `COUNTER_ATTACK_SAMPLE_PATH` | 反击特征波形文件位置 | `./承轨反击波形.wav` |
| `THRESHOLD` | 闪避触发阈值（越小越灵敏） | `0.13` |
| `COUNTER_ATTACK_THRESHOLD` | 反击触发阈值（越小越灵敏） | `0.12` |
| `EXPANSION_RATIO` | 最大归一化交叉相关倍数 | `1.0` |
| `IS_ALLOW_SUCCESSIVE_TRIGGER` | 是否允许连续触发（防误触默认关闭） | `False` |
| `MONITOR_TIME` | 监控时间窗口（秒） | `5` |

## 工作原理

1. **音频采集**：通过系统 loopback 设备实时捕获游戏音效
2. **波形匹配**：使用归一化交叉相关算法（NCC）进行精确匹配
3. **高通滤波**：Butterworth 高通滤波器，去除背景低频噪音
4. **动作执行**：匹配分数超过阈值时，通过 PyDirectInput 执行键鼠操作

## 自定义波形文件

如需使用自己的波形文件：

1. 录制游戏中的闪避/反击音效（保存为 WAV 格式）
2. 裁剪到只包含特征波形片段（建议 0.5-2 秒）
3. 替换默认的波形文件，或修改 `Main.py` 中的文件路径
4. 根据匹配情况调整 `THRESHOLD` 阈值

## 项目结构

```
NTESoundTrigger/
├── Main.py              # 主程序入口
├── Trigger.py           # 触发器与键鼠操作模块
├── Listener.py          # 音频监听与处理
├── Monitor.py           # 波形监控与分数计算
├── 闪避波形.wav         # 闪避特征波形
├── 承轨反击波形.wav     # 反击特征波形
├── requirements.txt     # 依赖包列表
└── LICENSE              # GPLv3 许可证
```

## 常见问题

**Q: 没有触发？**
A: 尝试降低 `THRESHOLD` 阈值。

**Q: 误触发太频繁？**
A: 提高 `THRESHOLD` 阈值，或修改 `IS_ALLOW_SUCCESSIVE_TRIGGER` 为 `True`。

**Q: 需要管理员权限？**
A: 是的，键鼠操作需要管理员权限才能在全屏游戏中生效。

## 许可证

本项目基于 [GPLv3](LICENSE) 许可证开源。

## 致谢

本项目基于 [ImLaoBJie/ZZZSoundTrigger](https://github.com/ImLaoBJie/ZZZSoundTrigger) 改编而来，感谢原作者的开源分享。

## 免责声明

- 使用本项目产生的所有问题与本项目及开发者无关。
- 若您遇到商家使用本软件进行代练、演示、贩卖或收费，产生的任何问题及后果与本项目无关。
