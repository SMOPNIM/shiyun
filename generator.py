"""
诗云 - 究极吟诗程序
枚举所有UTF-8可打印字符的排列组合
"""

import gzip
import json
import os
import threading
from datetime import datetime
from typing import Dict, Generator, Optional

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


def generate_combinations(chars: str, max_length: int) -> Generator[str, None, None]:
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


# In-memory session state
# session_id -> {"generated": int, "start_time": datetime, "running": bool}
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
            "total": total,
            "elapsed": round(elapsed, 2),
            "running": running,
            "chars_len": len(state["chars"]),
            "max_length": state["max_length"],
            "rate": round(rate, 2),
        }


def increment_generated(session_id: str):
    with _session_lock:
        if session_id in _session_state:
            _session_state[session_id]["generated"] += 1


def mark_complete(session_id: str):
    with _session_lock:
        if session_id in _session_state:
            state = _session_state[session_id]
            state["running"] = False
            state["end_time"] = datetime.now()


def stream_combinations(session_id: str, chars: str, max_length: int):
    create_session(session_id, chars, max_length)
    count = 0
    try:
        for combo in generate_combinations(chars, max_length):
            if is_stopped(session_id):
                break
            count += 1
            yield f"data: {combo}\n\n"
            if count % 500 == 0:
                with _session_lock:
                    if session_id in _session_state:
                        _session_state[session_id]["generated"] = count
    finally:
        with _session_lock:
            if session_id in _session_state:
                state = _session_state[session_id]
                state["generated"] = count
                state["running"] = False
                state["end_time"] = datetime.now()


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
