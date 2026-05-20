"""
OpenHuman Swarm — delegate_task 非阻塞模式补丁

通过 monkey-patch 给 delegate_task 添加 wait=False 参数。
后台任务通过 cronjob 推送结果，不阻塞主会话。

安装方式（已自动注入）：
  此文件通过 ~/.local/lib/python3.11/site-packages/usercustomize.py 自动加载，
  无需手动操作。
"""

import json
import logging
import os
import threading
import time
import uuid

logger = logging.getLogger("swarm_patch")

# 后台任务注册表
_background_tasks: dict = {}
_lock = threading.Lock()


def apply():
    """应用补丁到 delegate_task 函数"""
    try:
        import tools.delegate_tool as dt

        original = dt.delegate_task

        def patched_delegate(
            goal=None,
            context=None,
            toolsets=None,
            tasks=None,
            max_iterations=None,
            acp_command=None,
            acp_args=None,
            role=None,
            parent_agent=None,
            wait=True,  # ← 新增参数
        ):
            if wait:
                # 阻塞模式：原样调用
                return original(
                    goal=goal,
                    context=context,
                    toolsets=toolsets,
                    tasks=tasks,
                    max_iterations=max_iterations,
                    acp_command=acp_command,
                    acp_args=acp_args,
                    role=role,
                    parent_agent=parent_agent,
                )

            # 非阻塞模式：后台线程执行，立即返回 task_id
            task_id = f"swarm-{uuid.uuid4().hex[:12]}"
            swarm_dir = os.path.expanduser("~/.hermes/swarm")
            state_path = os.path.join(swarm_dir, "state.json")

            # 注册后台任务
            entry = {
                "task_id": task_id,
                "goal": (goal or "")[:60],
                "status": "running",
                "started_at": time.time(),
                "completed_at": None,
                "result": None,
                "error": None,
            }
            with _lock:
                _background_tasks[task_id] = entry

            def _run():
                try:
                    result = original(
                        goal=goal,
                        context=context,
                        toolsets=toolsets,
                        tasks=tasks,
                        max_iterations=max_iterations,
                        acp_command=acp_command,
                        acp_args=acp_args,
                        role=role,
                        parent_agent=parent_agent,
                    )
                    parsed = json.loads(result) if isinstance(result, str) else result
                    with _lock:
                        _background_tasks[task_id].update(
                            {"status": "completed", "completed_at": time.time(), "result": parsed}
                        )
                except Exception as exc:
                    logger.error("Background task %s failed: %s", task_id, exc)
                    with _lock:
                        _background_tasks[task_id].update(
                            {"status": "failed", "completed_at": time.time(), "error": str(exc)}
                        )
                finally:
                    # 更新 state.json
                    _flush_state(state_path)

            thread = threading.Thread(target=_run, daemon=True)
            thread.start()

            # 初始化 state.json
            _flush_state(state_path)

            return json.dumps(
                {
                    "status": "spawned",
                    "task_id": task_id,
                    "message": (
                        f"🚀 任务已后台启动（{task_id}）\n"
                        f"你的聊天不会被阻塞，完成后自动通知你。\n"
                        f"可用命令：\n"
                        f"  swarm_status({task_id!r}) — 查看进度\n"
                        f"  swarm_cancel({task_id!r}) — 取消任务"
                    ),
                },
                ensure_ascii=False,
            )

        # 应用补丁
        dt.delegate_task = patched_delegate
        logger.info("swarm_patch: delegate_task monkey-patch applied (wait=False mode)")
        return True

    except ImportError:
        logger.warning("swarm_patch: could not import tools.delegate_tool — Hermes not loaded yet")
        return False
    except Exception as exc:
        logger.error("swarm_patch: patch failed: %s", exc)
        return False


def _flush_state(state_path: str):
    """将当前后台任务状态写入 state.json"""
    try:
        with _lock:
            state = {
                "background_tasks": dict(_background_tasks),
                "updated_at": time.time(),
            }
        os.makedirs(os.path.dirname(state_path), exist_ok=True)
        with open(state_path, "w") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception as exc:
        logger.debug("swarm_patch: flush_state failed: %s", exc)


def get_status(task_id: str) -> dict:
    """获取后台任务状态"""
    with _lock:
        return dict(_background_tasks.get(task_id, {"status": "not_found"}))


def list_tasks() -> list:
    """列出所有后台任务"""
    with _lock:
        return [dict(v) for v in _background_tasks.values()]


def cancel_task(task_id: str) -> bool:
    """取消后台任务（标记取消，不强制终止线程）"""
    with _lock:
        if task_id in _background_tasks and _background_tasks[task_id]["status"] == "running":
            _background_tasks[task_id]["status"] = "cancelled"
            _background_tasks[task_id]["completed_at"] = time.time()
            return True
    return False


# 模块导入时自动应用补丁
_auto_applied = apply()
