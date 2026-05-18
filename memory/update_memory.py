#!/usr/bin/env python3
"""
记忆自动更新脚本 v2
- 每1小时由 cronjob 调用
- 指纹去重：无变化秒跳过，0 token消耗
- 按 ID 逐项比对，只更新变动项
- 记忆 ≤4000 token，超额自动淘汰
"""

import json, os, datetime, subprocess, hashlib

HERMES_HOME = os.path.expanduser("~/.hermes")
OH_PATH = f"{HERMES_HOME}/node/bin"
ARCHIVE_DIR = f"{HERMES_HOME}/archive/daily"
FINGERPRINT_FILE = f"{HERMES_HOME}/archive/.fingerprint"
SCRIPT_DIR = f"{HERMES_HOME}/scripts"
TODAY = datetime.date.today().isoformat()
NOW = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

os.makedirs(ARCHIVE_DIR, exist_ok=True)

def lark_cmd(cmd):
    try:
        full_cmd = f"env -i HOME='{os.path.expanduser('~')}' PATH='{OH_PATH}:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin' {cmd}"
        r = subprocess.run(full_cmd, capture_output=True, text=True, timeout=30, shell=True)
        if r.returncode == 0 and r.stdout.strip():
            return json.loads(r.stdout)
        return {"ok": False, "error": r.stderr[:200] if r.stderr else "empty response"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def sha256_fingerprint(obj):
    """计算任意对象的 SHA256 指纹"""
    raw = json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def load_prev_fingerprint():
    """加载上次的指纹"""
    if os.path.exists(FINGERPRINT_FILE):
        with open(FINGERPRINT_FILE) as f:
            return json.load(f)
    return {}

def save_fingerprint(fp):
    with open(FINGERPRINT_FILE, "w") as f:
        json.dump(fp, f)

def extract_items(data, item_key="items"):
    """从飞书API响应中提取条目列表"""
    if not data.get("ok"):
        return []
    body = data.get("data", {})
    if isinstance(body, dict):
        return body.get(item_key, [])
    return []

def count_tokens(text):
    return int(len(text) * 0.7)

# ════════════════════════════════════════
# 第一步：拉数据
# ════════════════════════════════════════
print("📡 拉取飞书数据...")
cal_data = lark_cmd("lark-cli calendar +agenda")
tasks_data = lark_cmd("lark-cli task +get-my-tasks")
docs_data = lark_cmd("lark-cli docs +search")

if not cal_data.get("ok"):
    print("❌ 飞书CLI调用失败，跳过")
    # 仍然退出0，不让cron报警
    exit(0)

# ════════════════════════════════════════
# 第二步：指纹比对（快速跳过）
# ════════════════════════════════════════

# 计算本次的各类指纹
cal_events = cal_data.get("data", [])
task_items = extract_items(tasks_data)
doc_items = extract_items(docs_data, item_key="results")

fingerprints = {
    "cal": sha256_fingerprint([e.get("event_id", e.get("summary", "")) for e in cal_events]),
    "tasks": sha256_fingerprint([{"id": t.get("id", ""), "status": t.get("status", ""), "summary": t.get("summary", "")} for t in task_items]),
    "docs": sha256_fingerprint([{"token": d.get("result_meta", {}).get("token", ""), "update_time": d.get("result_meta", {}).get("update_time", "")} for d in doc_items]),
}
fingerprints["global"] = sha256_fingerprint(fingerprints)

prev = load_prev_fingerprint()

if prev.get("global") == fingerprints.get("global"):
    print(f"⏭️ 无变化，跳过 (指纹相同)")
    exit(0)

changed = []
for k in ["cal", "tasks", "docs"]:
    if prev.get(k) != fingerprints.get(k):
        changed.append(k)
print(f"🔄 变动项: {', '.join(changed)}")

# ════════════════════════════════════════
# 第三步：写入归档
# ════════════════════════════════════════
today_file = f"{ARCHIVE_DIR}/{TODAY}.json"
existing_archive = {}
if os.path.exists(today_file):
    with open(today_file) as f:
        existing_archive = json.load(f)

archive = {
    "time": NOW,
    "date": TODAY,
}

# 只更新有变动的部分
for k in ["cal", "tasks", "docs"]:
    if k in changed or not existing_archive:
        if k == "cal":
            archive["calendar"] = cal_events
        elif k == "tasks":
            archive["tasks"] = task_items
        elif k == "docs":
            archive["docs"] = doc_items
    else:
        archive[k] = existing_archive.get(k, [])

with open(today_file, "w") as f:
    json.dump(archive, f, ensure_ascii=False, indent=2)
print(f"✅ 归档已更新: {TODAY}.json")

# ════════════════════════════════════════
# 第四步：更新记忆（直接覆盖，不追加）
# ════════════════════════════════════════
mem_path = f"{HERMES_HOME}/memories/MEMORY.md"
with open(mem_path) as f:
    memory = f.read()

# 生成新的概览行
cal_str = "无"
if cal_events:
    cal_str = " / ".join([e.get("summary", "?") for e in cal_events[:3]])

tasks_active = [t for t in task_items if t.get("status", "") != "completed"][:3]
tasks_str = "无"
if tasks_active:
    tasks_str = " / ".join([t.get("summary", "?") for t in tasks_active])

docs_str = "无"
if doc_items:
    docs_str = " / ".join([d.get("title_highlighted", "?") for d in doc_items[:3]])

new_section = f"📅 日程: {cal_str}\n📋 任务: {tasks_str}\n📄 文档: {docs_str}\n§\n\n(last updated: {TODAY} {NOW})"

# 找到并替换记忆中的飞书概览段
lines = memory.split("\n")
new_lines = []
in_feishu_section = False
replaced = False

for line in lines:
    if line.strip().startswith("📅 ") or line.strip().startswith("📋 ") or line.strip().startswith("📄 "):
        # 这是旧飞书概览行，跳过
        in_feishu_section = True
        continue
    if in_feishu_section and line.strip() == "§":
        in_feishu_section = False
        # 插入新内容
        new_lines.append(new_section)
        replaced = True
        continue
    if not in_feishu_section:
        new_lines.append(line)

# 如果记忆里原来没有飞书概览段，追加到最后
if not replaced:
    new_lines.append("")
    new_lines.extend(new_section.split("\n"))

new_memory = "\n".join(new_lines)

# ════════════════════════════════════════
# 第五步：token 预算检查
# ════════════════════════════════════════
total_tokens = count_tokens(new_memory)
max_tokens = 4000
if total_tokens > max_tokens:
    print(f"⚠️ 超预算 ({total_tokens} > {max_tokens}), 清理冗余行...")
    # 删除文件头部15行之后超过4000tok的部分
    head_len = 15
    head_lines = new_lines[:head_len]
    tail_lines = new_lines[head_len:]
    while tail_lines and count_tokens("\n".join(head_lines + tail_lines)) > max_tokens:
        tail_lines.pop(0)
    new_memory = "\n".join(head_lines + tail_lines)
    total_tokens = count_tokens(new_memory)
    print(f"  清理后: {total_tokens} tokens")

with open(mem_path, "w") as f:
    f.write(new_memory)

# ════════════════════════════════════════
# 第六步：保存指纹
# ════════════════════════════════════════
save_fingerprint(fingerprints)

print(f"✅ 记忆已更新 ({total_tokens} tokens)")
print("🎉 完成")