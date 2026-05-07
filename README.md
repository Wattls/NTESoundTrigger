# NTESoundTrigger

基于音频匹配的游戏自动闪避 / 自动反击工具。通过实时监听系统音频输出，用 FFT 交叉相关匹配预设波形，检测到游戏内攻击音效时自动模拟键鼠操作完成闪避或反击。

## 功能

- **音频匹配检测**：高通滤波 + FFT 交叉相关，匹配预设的闪避 / 反击音频波形
- **自动闪避**：检测到闪避音效时，自动执行 `右键 → Shift` 闪避操作
- **自动反击**：检测到反击音效时，自动执行数字键 `1-4` + 鼠标左键反击操作
- **实时监控窗口**：独立进程运行，显示闪避 / 反击匹配得分的实时波形图和触发日志
- **设备重连**：音频设备断开后自动重连，不影响程序运行

## 安装

```bash
git clone https://github.com/Wattls/NTESoundTrigger.git
cd NTESoundTrigger
pip install -r requirements.txt
```

## 依赖

```
soundcard       # 系统音频回路采集
numpy           # 数值计算
scipy           # 滤波器 + FFT
librosa         # 音频加载与重采样
matplotlib      # 监控窗口绘图
PyDirectInput   # 键鼠模拟
```

## 配置

配置项均在 `Config.py` 的 `Config` 类中，运行前按需修改：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `SR` | 32000 | 音频采样率 |
| `CHANNELS` | 2 | 音频通道数 |
| `CHUNK` | 1600 | 每次采集的帧数 |
| `FRAME` | 0.2 | 每次处理的音频长度（秒） |
| `HP_ORDER` | 4 | 高通滤波器阶数 |
| `HP_CUT` | 1000 | 高通滤波器截止频率（Hz） |
| `DODGE_WAV` | `./闪避波形.wav` | 闪避音频样本文件 |
| `DODGE_THRESH` | 0.13 | 闪避匹配阈值 |
| `COUNTER_WAV` | `./承轨反击波形.wav` | 反击音频样本文件 |
| `COUNTER_THRESH` | 0.12 | 反击匹配阈值 |
| `RATIO` | 1.0 | 匹配灵敏度倍率 |
| `ALLOW_REPEAT` | False | 是否允许连续触发 |
| `DODGE_WIN` | None | 闪避匹配窗口时长（秒），None 为自动 |
| `COUNTER_WIN` | None | 反击匹配窗口时长（秒），None 为自动 |
| `MONITOR_SEC` | 5 | 监控窗口显示的历史时长（秒） |

## 使用

1. 将游戏内的闪避 / 反击音效录制成 `.wav` 文件，放置到项目根目录
2. 修改 `Config.py` 中的 `DODGE_WAV` 和 `COUNTER_WAV` 路径
3. 运行：

```bash
python Main.py
```

4. 程序会自动打开监控窗口，显示实时匹配得分波形
5. `Ctrl+C` 或关闭监控窗口退出程序

首次运行会自动从 `.wav` 生成 `.npy` 缓存文件，后续启动直接加载缓存。

## 工作原理

```
系统音频 → SoundCard 回路采集 → 高通滤波 → 环形缓冲区
                                              ↓
                               FFT 交叉相关 ← RMS 归一化
                                              ↓
                               得分 ≥ 阈值 → 触发键鼠操作
                                              ↓
                                    监控窗口 / 日志
```

- **高通滤波**：过滤低频背景噪音，提取攻击音效的高频特征
- **环形缓冲区**：O(1) 写入，多数情况下零拷贝读取
- **FFT 交叉相关**：频域卷积实现，比时域相关快一个数量级
- **RMS 归一化**：消除音量波动对匹配结果的影响
- **线程池**：单线程执行器处理动作触发，避免重复按键

## 项目结构

```
NTESoundTrigger/
├── Main.py       # 入口，组装各模块并启动主循环
├── Config.py     # 配置类 / 滤波器 / 音频引擎 / 样本加载
├── Listener.py   # 匹配器，环形缓冲区 + FFT 匹配 + 触发逻辑
├── Monitor.py    # 监控窗口，matplotlib 波形图 + 日志面板
├── Trigger.py    # 键盘鼠标模拟（PyDirectInput）
├── Logger.py     # 日志配置
└── requirements.txt
```

## 注意

- 仅支持 Windows（键鼠模拟使用 PyDirectInput）
- 需要启用系统立体声混音或使用 SoundCard 支持的回路设备
- 管理员权限非必需，但部分游戏可能需要以管理员身份运行才能正常发送键鼠输入

## 许可证

本项目基于 [GPLv3](LICENSE) 许可证开源。

## 致谢

本项目基于 [ImLaoBJie/ZZZSoundTrigger](https://github.com/ImLaoBJie/ZZZSoundTrigger) 改编而来，感谢原作者的开源分享。

## 免责声明

- 使用本项目产生的所有问题与本项目及开发者无关。
- 若您遇到商家使用本软件进行代练、演示、贩卖或收费，产生的任何问题及后果与本项目无关。
