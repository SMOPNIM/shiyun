"""
诗云 - 究极吟诗程序
枚举所有UTF-8可打印字符的排列组合
"""

import gzip
import json
import os
import threading
import unicodedata
from datetime import datetime
from typing import Dict, Generator, List, Optional

CJK_THOUSAND = (
    "天地玄黄宇宙洪荒日月盈昃辰宿列张寒来暑往秋收冬藏闰余成岁律吕调阳"
    "云腾致雨露结为霜金生丽水玉出昆冈剑号巨阙珠称夜光果珍李柰菜重芥姜"
    "海咸河淡鳞潜羽翔龙师火帝鸟官人皇始制文字乃服衣裳推位让国有虞陶唐"
    "吊民伐罪周发殷汤坐朝问道垂拱平章爱育黎首臣伏戎羌遐迩一体率宾归王"
    "鸣凤在树白驹食场化被草木赖及万方盖此身发四大五常恭惟鞠养岂敢毁伤"
    "女慕贞洁男效才良知过必改得能莫忘罔谈彼短靡恃己长信使可覆器欲难量"
    "墨悲丝染诗赞羔羊景行维贤克念作圣德建名立形端表正空谷传声虚堂习听"
    "祸因恶积福缘善庆尺璧非宝寸阴是竞资父事君曰严与敬孝当竭力忠则尽命"
    "临深履薄夙兴温凊似兰斯馨如松之盛川流不息渊澄取映容止若思言辞安定"
    "笃初诚美慎终宜令荣业所基籍甚无竟学优登仕摄职从政存以甘棠去而益咏"
    "乐殊贵贱礼别尊卑上和下睦夫唱妇随外受傅训入奉母仪诸姑伯仲犹子比儿"
    "孔怀兄弟同气连枝交友投分切磨箴规仁慈隐恻造次弗离节义廉退颠沛匪亏"
    "性静情逸心动神疲守真志满逐物意移坚持雅操好爵自縻都邑华夏东西二京"
    "背邙面洛浮渭据泾宫殿盘楼观飞惊图写禽兽画彩仙灵丙舍旁启甲帐对楹"
    "肆筵设席鼓瑟吹笙升阶纳陛弁转疑星右通广内左达承明既集坟典亦聚群英"
    "杜稿钟隶漆书壁经府罗将相路侠槐卿户封八县家给千兵高冠陪辇驱毂振缨"
    "世禄侈富车驾肥轻策功茂绩勒碑刻铭盘溪伊尹佐时阿衡奄宅曲阜微旦孰营"
    "桓公匡合济弱扶倾绮回汉惠说感武丁俊义密勿多士宁晋楚更霸赵魏困横"
    "假途灭虢践土会盟何遵约法韩弊烦刑起剪颇牧用军最精宣威沙漠驰誉丹青"
    "九州禹迹百郡秦并岳宗恒岱禅主云亭雁门紫塞鸡田赤城昆池碣石巨野洞庭"
    "旷远绵邈岩岫杳冥治本于农务兹稼穑载南亩我艺黍稷税熟贡新劝赏黜陟"
    "孟轲敦素史鱼秉直庶几中庸劳谦谨敕聆音察理鉴貌辨色贻厥嘉猷勉其祗植"
    "省躬讥诫宠增抗极殆辱近耻林皋幸即两疏见机解组谁逼索居闲处沉默寂寥"
    "求古寻论散虑逍遥欣奏累遣戚谢欢招渠荷的历园莽抽条枇杷晚翠梧桐蚤凋"
    "陈根委翳落叶飘摇游鵾独运凌摩绛霄耽读玩市寓目囊箱易攸畏属耳墙"
    "具膳餐饭适口充肠饱饫烹饥厌糟糠亲戚故旧老少异粮妾御绩纺侍巾帷房"
    "纨扇圆絜银烛炜煌昼眠夕寐蓝笋象床弦歌酒宴接杯举觞矫手顿足悦豫且康"
    "嫡后嗣续祭祀蒸尝稽颡再拜悚惧恐惶笺牒简要顾答审详骸垢想浴执热愿凉"
    "驴骡犊特骇跃超骡诛斩贼盗捕获叛亡布射僚丸嵇琴阮箫恬笔伦纸钧巧任钓"
    "释纷利俗并皆佳妙毛施淑姿工嚬妍笑年矢每催曦晖朗曜璇玑悬斡晦魄环照"
    "指薪修祜永绥吉劭矩步引领俯仰廊庙束带矜庄徘徊瞻眺孤陋寡闻愚蒙等诮"
    "谓语助者焉哉乎也"
)


def build_utf8_charset() -> str:
    chars = []
    for cp in range(0x20, 0x110000):
        try:
            ch = chr(cp)
            cat = unicodedata.category(ch)
            if cat and cat[0] in "LMNPS":
                chars.append(ch)
        except (ValueError, UnicodeEncodeError):
            pass
    return "".join(chars)


UTF8_ALL = build_utf8_charset()

PRESETS = {
    "ascii": {
        "label": "ASCII可打印字符",
        "chars": "".join(chr(i) for i in range(0x21, 0x7F)),
        "description": "95个可打印ASCII字符",
    },
    "digits": {
        "label": "数字",
        "chars": "0123456789",
        "description": "10个数字 (0-9)",
    },
    "letters": {
        "label": "英文字母",
        "chars": "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
        "description": "52个英文字母 (大小写)",
    },
    "alphanum": {
        "label": "数字+字母",
        "chars": "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
        "description": "62个字母数字",
    },
    "cjk_sample": {
        "label": "千字文精选",
        "chars": CJK_THOUSAND,
        "description": "《千字文》1000个不重复汉字",
    },
    "emoji": {
        "label": "基础表情符号",
        "chars": "😀😂🤣😃😄😅😆😉😊😋😎😍😘🥰😗😙😚🙂🤗🤩🤔🤨😐😑😶🙄😏😣😥😮🤐😯😪😫😴😌😛😜😝🤤😒😓😔😕🙃🤑😲☹️🙁😖😞😟😤😢😭😦😧😨😩🤯😬😰😱🥵🥶😳🤪😵😡😠🤬",
        "description": "48个常用表情符号",
    },
    "utf8_all": {
        "label": "全部UTF-8可打印字符",
        "chars": UTF8_ALL,
        "description": f"所有Unicode可打印字符，共{len(UTF8_ALL)}个",
    },
}


def estimate_total(chars_len: int, max_length: int) -> int:
    total = 0
    term = 1
    for _ in range(max_length):
        term *= chars_len
        total += term
        if total > 10 ** 18:
            break
    return total


# ============================================================
# StreamState – stateful combination generator
# ============================================================

class StreamState:
    def __init__(self, chars: str, max_length: int,
                 current_length: int = 1, indices: Optional[List[int]] = None,
                 generated: int = 0):
        self.chars = chars
        self.max_length = max_length
        self.current_length = current_length
        self.indices = indices or [0]
        self.generated = generated

    def _advance(self) -> bool:
        n = len(self.chars)
        pos = self.current_length - 1
        while pos >= 0 and self.indices[pos] == n - 1:
            self.indices[pos] = 0
            pos -= 1
        if pos < 0:
            self.current_length += 1
            if self.current_length > self.max_length:
                return False
            self.indices = [0] * self.current_length
        else:
            self.indices[pos] += 1
        return True

    def peek(self) -> str:
        return "".join(self.chars[i] for i in self.indices)

    def next(self) -> Optional[str]:
        if self.current_length > self.max_length:
            return None
        result = self.peek()
        self.generated += 1
        if not self._advance():
            self.current_length = self.max_length + 1
        return result

    def serialize(self) -> Dict:
        return {
            "chars": self.chars,
            "max_length": self.max_length,
            "current_length": self.current_length,
            "indices": list(self.indices),
            "generated": self.generated,
        }

    @classmethod
    def deserialize(cls, data: Dict) -> "StreamState":
        return cls(
            chars=data["chars"],
            max_length=data["max_length"],
            current_length=data["current_length"],
            indices=data["indices"],
            generated=data["generated"],
        )


# ============================================================
# Session management
# ============================================================

_session_state: Dict[str, Dict] = {}
_session_lock = threading.RLock()
_stop_events: Dict[str, threading.Event] = {}


def create_session(session_id: str, chars: str, max_length: int) -> Dict:
    with _session_lock:
        _session_state[session_id] = {
            "chars": chars,
            "max_length": max_length,
            "generated": 0,
            "start_time": datetime.now(),
            "end_time": None,
            "running": True,
        }
        _stop_events[session_id] = threading.Event()
    return get_session_stats(session_id)


def stop_session(session_id: str):
    with _session_lock:
        if session_id in _stop_events:
            _stop_events[session_id].set()
        if session_id in _session_state:
            state = _session_state[session_id]
            state["running"] = False
            if state["end_time"] is None:
                state["end_time"] = datetime.now()


def is_stopped(session_id: str) -> bool:
    with _session_lock:
        ev = _stop_events.get(session_id)
        return ev is not None and ev.is_set()


def clear_stop(session_id: str):
    with _session_lock:
        if session_id in _stop_events:
            _stop_events[session_id].clear()


def get_session_stats(session_id: str) -> Dict:
    with _session_lock:
        state = _session_state.get(session_id)
        if not state:
            return {"generated": 0, "total": 0, "running": False, "elapsed": 0, "rate": 0}
        end = state["end_time"] or datetime.now()
        elapsed = (end - state["start_time"]).total_seconds()
        total = estimate_total(len(state["chars"]), state["max_length"])
        running = not is_stopped(session_id) and state["running"]
        rate = state["generated"] / elapsed if elapsed > 0 else 0
        return {
            "generated": state["generated"],
            "total": str(total),
            "elapsed": round(elapsed, 2),
            "running": running,
            "chars_len": len(state["chars"]),
            "max_length": state["max_length"],
            "rate": round(rate, 2),
        }


# ============================================================
# Streaming with pause / resume support
# ============================================================

_paused_states: Dict[str, Dict] = {}
_active_generators: Dict[str, StreamState] = {}
_pause_requested: set = set()


def pause_session(session_id: str):
    with _session_lock:
        _pause_requested.add(session_id)
        if session_id in _stop_events:
            _stop_events[session_id].set()
        gen = _active_generators.get(session_id)
        if gen:
            _paused_states[session_id] = gen.serialize()
        if session_id in _session_state:
            state = _session_state[session_id]
            state["running"] = False
            if state["end_time"] is None:
                state["end_time"] = datetime.now()


def get_paused_state(session_id: str) -> Optional[Dict]:
    with _session_lock:
        return _paused_states.get(session_id)


def clear_paused_state(session_id: str):
    with _session_lock:
        _paused_states.pop(session_id, None)


def stream_combinations(session_id: str, chars: str, max_length: int,
                        resume_state: Optional[Dict] = None):
    if resume_state:
        state = StreamState.deserialize(resume_state)
        create_session(session_id, chars, max_length)
        with _session_lock:
            if session_id in _session_state:
                _session_state[session_id]["generated"] = state.generated
        clear_stop(session_id)
    else:
        create_session(session_id, chars, max_length)
        state = StreamState(chars, max_length)

    with _session_lock:
        _active_generators[session_id] = state

    try:
        while True:
            if is_stopped(session_id):
                break
            combo = state.next()
            if combo is None:
                break
            yield f"data: {combo}\n\n"
            if state.generated % 500 == 0:
                with _session_lock:
                    if session_id in _session_state:
                        _session_state[session_id]["generated"] = state.generated
    finally:
        with _session_lock:
            _active_generators.pop(session_id, None)
            if session_id in _session_state:
                ss = _session_state[session_id]
                ss["generated"] = state.generated
                ss["running"] = False
                if ss["end_time"] is None:
                    ss["end_time"] = datetime.now()
            if session_id in _pause_requested:
                _pause_requested.discard(session_id)
                _paused_states[session_id] = state.serialize()


# ============================================================
# External state save / load (to disk)
# ============================================================

def save_state_to_file(state: Dict, output_dir: str = "output") -> str:
    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(output_dir, f"session_{ts}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    return path


def list_saved_states(output_dir: str = "output") -> List[Dict]:
    os.makedirs(output_dir, exist_ok=True)
    files = []
    for fname in sorted(os.listdir(output_dir), reverse=True):
        if fname.startswith("session_") and fname.endswith(".json"):
            fpath = os.path.join(output_dir, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                chars_len = len(data.get("chars", ""))
                max_length = data.get("max_length", 0)
                generated = data.get("generated", 0)
                files.append({
                    "filename": fname,
                    "path": fpath,
                    "chars_len": chars_len,
                    "max_length": max_length,
                    "generated": generated,
                    "total": str(estimate_total(chars_len, max_length)),
                    "timestamp": datetime.fromtimestamp(os.path.getmtime(fpath)).isoformat(),
                })
            except Exception:
                pass
    return files


def load_state_from_file(filename: str, output_dir: str = "output") -> Optional[Dict]:
    fpath = os.path.join(output_dir, filename)
    if not os.path.exists(fpath):
        return None
    try:
        with open(fpath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


# ============================================================
# Save combination results to file (original, unchanged)
# ============================================================

def save_combinations(
    chars: str, max_length: int, filepath: str, compress: bool = True,
    cancel_event: Optional[threading.Event] = None,
) -> Dict:
    total = estimate_total(len(chars), max_length)
    count = 0

    metadata = {
        "chars": chars,
        "chars_len": len(chars),
        "max_length": max_length,
        "timestamp": datetime.now().isoformat(),
        "program": "诗云 - 究极吟诗程序",
    }
    meta_json = json.dumps(metadata, ensure_ascii=False)

    if compress:
        path = filepath + ".gz"
        f = gzip.open(path, "wt", encoding="utf-8")
    else:
        path = filepath
        f = open(path, "w", encoding="utf-8")

    try:
        f.write(f"// {meta_json}\n")
        for combo in generate_combinations(chars, max_length):
            if cancel_event and cancel_event.is_set():
                break
            f.write(combo + "\n")
            count += 1
    finally:
        f.close()

    return {"path": path, "count": count, "compress": compress}


# kept for backward compatibility with save_combinations
def generate_combinations(chars: str, max_length: int,
                          start_state: Optional[Dict] = None) -> Generator[str, None, None]:
    if start_state:
        ss = StreamState.deserialize(start_state)
        while True:
            combo = ss.next()
            if combo is None:
                break
            yield combo
    else:
        for combo in _generate_from_scratch(chars, max_length):
            yield combo


def _generate_from_scratch(chars: str, max_length: int) -> Generator[str, None, None]:
    n = len(chars)
    if n == 0:
        return
    for length in range(1, max_length + 1):
        indices = [0] * length
        while True:
            yield "".join(chars[i] for i in indices)
            pos = length - 1
            while pos >= 0 and indices[pos] == n - 1:
                indices[pos] = 0
                pos -= 1
            if pos < 0:
                break
            indices[pos] += 1
