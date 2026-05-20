"""
usercustomize.py — Python 启动时自动加载

让 Hermes 启动时自动加载 swarm_patch（不修改框架代码）。
此文件放在 user site-packages 目录下，Python 会在所有解释器启动时自动导入。
仅在检测到 Hermes 环境时激活补丁。
"""

import importlib
import os
import sys


def _try_load_swarm_patch():
    """尝试加载 swarm_patch（仅在 Hermes 环境中）"""
    # 判断是否在 Hermes 环境中
    # 检测是否在 Hermes 环境中：命令行包含 hermes 关键词，或环境变量
    hermes_keywords = ["hermes", "gateway", "delegate_tool"]
    is_hermes = any(
        kw in (arg or "").lower() for arg in sys.argv for kw in hermes_keywords
    ) or "HERMES_HOME" in os.environ

    if not is_hermes:
        return  # 非 Hermes 环境，跳过

    swarm_dir = os.path.expanduser("~/.hermes/swarm")
    if not os.path.isdir(swarm_dir):
        return  # swarm 目录不存在，跳过

    # 将 swarm 目录加入 sys.path
    if swarm_dir not in sys.path:
        sys.path.insert(0, swarm_dir)

    try:
        import swarm_patch
        if hasattr(swarm_patch, "apply"):
            applied = swarm_patch.apply()
            if applied:
                print("[swarm] delegate_task patch applied", file=sys.stderr)
    except Exception:
        pass  # 静默失败，不影响 Hermes 启动


_try_load_swarm_patch()
