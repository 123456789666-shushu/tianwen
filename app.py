"""
CosmoLearn - 宇宙天文科普学习平台
====================================

依赖安装：
pip install streamlit pandas requests python-dotenv altair

运行方式：
streamlit run app.py

环境变量配置（在项目根目录创建.env文件）：
NASA_API_KEY=你的NASA密钥
DEEPSEEK_API_KEY=你的DeepSeek API密钥
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
"""

# 导入依赖
import streamlit as st
import pandas as pd
import requests
import os
import json
import altair as alt
import random
from datetime import datetime, timedelta
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ==================== 环境变量配置 ====================
NASA_API_KEY = os.getenv("NASA_API_KEY", "DEMO_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")
LLM_API_URL = f"{LLM_BASE_URL}/v1/chat/completions"

# ==================== 文件路径配置 ====================
QUESTIONS_CSV = "questions.csv"
USER_HISTORY_CSV = "user_history.csv"
USERS_JSON = "users.json"
IPGEOLOCATION_API_KEY = "bd4c9d9bbb874aea966c2942ee69c974"

# ==================== 用户系统 ====================

def init_users():
    """初始化用户JSON文件"""
    if not os.path.exists(USERS_JSON):
        with open(USERS_JSON, 'w', encoding='utf-8') as f:
            json.dump({}, f)

def register_user(username, password):
    init_users()
    with open(USERS_JSON, 'r', encoding='utf-8') as f:
        users = json.load(f)
    if username in users:
        return False, "用户名已存在"
    if len(username) < 2:
        return False, "用户名至少2个字符"
    if len(password) < 3:
        return False, "密码至少3个字符"
    users[username] = password
    with open(USERS_JSON, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False)
    return True, "注册成功"

def login_user(username, password):
    init_users()
    with open(USERS_JSON, 'r', encoding='utf-8') as f:
        users = json.load(f)
    if username not in users:
        return False, "用户名不存在"
    if users[username] != password:
        return False, "密码错误"
    return True, "登录成功"

# ==================== 初始化函数 ====================

def init_questions_csv():
    """初始化题库CSV文件（多维度，100题）"""
    if not os.path.exists(QUESTIONS_CSV):
        questions_data = [
            # ===== 太阳系 =====
            {"id": 1, "question": "太阳的核心温度大约是多少？", "option_a": "100万度", "option_b": "1500万度", "option_c": "1亿度", "option_d": "5000度", "correct_answer": "B", "explanation": "太阳核心温度约为1500万摄氏度，在如此高温高压下发生核聚变反应，将氢转化为氦并释放巨大能量。", "topic": "太阳系"},
            {"id": 2, "question": "地球围绕太阳公转一周需要多长时间？", "option_a": "一天", "option_b": "一个月", "option_c": "一年", "option_d": "一百年", "correct_answer": "C", "explanation": "地球绕太阳公转一周需要约365.25天，即一个回归年。这就是为什么每四年有一个闰年。", "topic": "太阳系"},
            {"id": 3, "question": "木星是太阳系中最大的行星，它是什么类型的行星？", "option_a": "岩石行星", "option_b": "气态巨行星", "option_c": "冰巨星", "option_d": "矮行星", "correct_answer": "B", "explanation": "木星是气态巨行星，主要由氢和氦组成，没有固体表面，质量是地球的318倍。", "topic": "太阳系"},
            {"id": 11, "question": "太阳系中离太阳最近的行星是哪颗？", "option_a": "金星", "option_b": "水星", "option_c": "地球", "option_d": "火星", "correct_answer": "B", "explanation": "水星是离太阳最近的行星，距离太阳约5790万公里，表面温度可高达427℃。", "topic": "太阳系"},
            {"id": 12, "question": "太阳系的疆界最远可以到达哪里？", "option_a": "冥王星轨道", "option_b": "柯伊伯带", "option_c": "奥尔特云", "option_d": "海王星轨道", "correct_answer": "C", "explanation": "奥尔特云是包裹太阳系的球形云团，被认为是太阳系的最外层边界，距离太阳约1光年。", "topic": "太阳系"},
            {"id": 10, "question": "太阳系中哪颗行星有美丽的光环？", "option_a": "火星", "option_b": "木星", "option_c": "土星", "option_d": "海王星", "correct_answer": "C", "explanation": "土星拥有太阳系中最壮观的光环系统，由冰块和岩石碎片组成，直径可达数十万公里。", "topic": "太阳系"},
            # ===== 银河系 =====
            {"id": 4, "question": "银河系的形状是什么？", "option_a": "椭圆形", "option_b": "螺旋形", "option_c": "不规则形", "option_d": "球形", "correct_answer": "B", "explanation": "银河系是一个棒旋星系，具有明显的螺旋结构，太阳系位于其中一条旋臂上。", "topic": "银河系"},
            {"id": 13, "question": "银河系大约有多少颗恒星？", "option_a": "1亿颗", "option_b": "100亿颗", "option_c": "1000亿到4000亿颗", "option_d": "1万亿颗", "correct_answer": "C", "explanation": "银河系拥有约1000亿到4000亿颗恒星，直径约10万光年。", "topic": "银河系"},
            {"id": 14, "question": "太阳系在银河系的什么位置？", "option_a": "银河系中心", "option_b": "猎户座旋臂", "option_c": "银河系边缘", "option_d": "银盘上方", "correct_answer": "B", "explanation": "太阳系位于银河系猎户座旋臂的内侧，距离银河系中心约2.6万光年。", "topic": "银河系"},
            # ===== 恒星 =====
            {"id": 5, "question": "离地球最近的恒星是哪一颗？", "option_a": "太阳", "option_b": "比邻星", "option_c": "天狼星", "option_d": "北极星", "correct_answer": "A", "explanation": "太阳是离地球最近的恒星，距离约1.5亿公里。比邻星是离太阳系最近的恒星，距离约4.2光年。", "topic": "恒星"},
            {"id": 9, "question": "什么是超新星？", "option_a": "新诞生的恒星", "option_b": "恒星死亡时的剧烈爆炸", "option_c": "行星形成的过程", "option_d": "星系碰撞", "correct_answer": "B", "explanation": "超新星是大质量恒星在生命末期发生的剧烈爆炸，亮度会瞬间增加数十亿倍，是宇宙中最壮观的现象之一。", "topic": "恒星"},
            {"id": 15, "question": "恒星的颜色与什么有关？", "option_a": "距离", "option_b": "表面温度", "option_c": "大小", "option_d": "年龄", "correct_answer": "B", "explanation": "恒星的颜色取决于其表面温度：蓝色恒星最热（>30000K），红色恒星较冷（<3000K），太阳呈黄色（约5778K）。", "topic": "恒星"},
            {"id": 16, "question": "中子星是如何形成的？", "option_a": "恒星缓慢演化而来", "option_b": "大质量恒星超新星爆发后的遗迹", "option_c": "两颗恒星碰撞而成", "option_d": "黑洞蒸发残留", "correct_answer": "B", "explanation": "中子星是大质量恒星在超新星爆发后，核心坍缩形成的致密天体，直径仅20公里左右，但质量可达太阳的1.4倍。", "topic": "恒星"},
            # ===== 黑洞与天体物理 =====
            {"id": 6, "question": "黑洞是什么？", "option_a": "一个巨大的黑色行星", "option_b": "引力极强、光无法逃逸的天体", "option_c": "宇宙中的空洞区域", "option_d": "暗物质聚集区", "correct_answer": "B", "explanation": "黑洞是引力坍缩形成的天体，其引力强大到连光都无法逃脱。事件视界是黑洞的边界。", "topic": "黑洞与天体物理"},
            {"id": 17, "question": "黑洞的边界称为什么？", "option_a": "奇点", "option_b": "事件视界", "option_c": "吸积盘", "option_d": "光子球", "correct_answer": "B", "explanation": "事件视界是黑洞的边界，一旦越过这个边界，任何物质（包括光）都无法逃脱黑洞的引力。", "topic": "黑洞与天体物理"},
            {"id": 18, "question": "人类拍摄到的第一张黑洞照片是哪个黑洞？", "option_a": "银河系中心黑洞Sgr A*", "option_b": "M87星系中心黑洞", "option_c": "天鹅座X-1", "option_d": "室女座超黑洞", "correct_answer": "B", "explanation": "2019年事件视界望远镜（EHT）拍摄了M87星系中心黑洞的首张照片，距离地球约5500万光年。", "topic": "黑洞与天体物理"},
            # ===== 天文探索 =====
            {"id": 7, "question": "哈勃太空望远镜是以谁的名字命名的？", "option_a": "伽利略", "option_b": "埃德温·哈勃", "option_c": "牛顿", "option_d": "爱因斯坦", "correct_answer": "B", "explanation": "哈勃太空望远镜以美国天文学家埃德温·哈勃命名，他发现了宇宙膨胀的证据。", "topic": "天文探索"},
            {"id": 19, "question": "中国天眼FAST位于哪个省份？", "option_a": "四川", "option_b": "贵州", "option_c": "云南", "option_d": "甘肃", "correct_answer": "B", "explanation": "FAST（500米口径球面射电望远镜）位于贵州省黔南布依族苗族自治州，是世界上最大的单口径射电望远镜。", "topic": "天文探索"},
            {"id": 20, "question": "詹姆斯·韦伯太空望远镜主要观测什么波段？", "option_a": "可见光", "option_b": "红外线", "option_c": "紫外线", "option_d": "X射线", "correct_answer": "B", "explanation": "韦伯望远镜主要观测红外波段，这使它能够看到宇宙早期星系和隐藏在尘埃中的天体。", "topic": "天文探索"},
            # ===== 月球 =====
            {"id": 8, "question": "月球上的环形山主要是如何形成的？", "option_a": "火山喷发", "option_b": "小行星和彗星撞击", "option_c": "地震活动", "option_d": "月球板块运动", "correct_answer": "B", "explanation": "月球表面的环形山主要是由小行星和彗星撞击形成的。由于月球没有大气层保护，撞击更加频繁。", "topic": "月球"},
            {"id": 21, "question": "月球大约多长时间绕地球公转一圈？", "option_a": "7天", "option_b": "15天", "option_c": "27.3天", "option_d": "365天", "correct_answer": "C", "explanation": "月球绕地球公转一周约27.3天（恒星月），这也是月球自转一周的时间，所以月球总是同一面朝向地球。", "topic": "月球"},
            {"id": 22, "question": "人类首次登月是在哪一年？", "option_a": "1965年", "option_b": "1969年", "option_c": "1972年", "option_d": "1981年", "correct_answer": "B", "explanation": "1969年7月20日，阿波罗11号的尼尔·阿姆斯特朗和巴兹·奥尔德林成为首次踏上月球的人类。", "topic": "月球"},
            # ===== 宇宙学 =====
            {"id": 23, "question": "宇宙大爆炸理论认为宇宙起源于多少年前？", "option_a": "46亿年", "option_b": "100亿年", "option_c": "138亿年", "option_d": "500亿年", "correct_answer": "C", "explanation": "宇宙大爆炸发生在约138亿年前，此后宇宙一直在膨胀和冷却。", "topic": "宇宙学"},
            {"id": 24, "question": "暗物质在天文学中的主要证据是什么？", "option_a": "望远镜直接观测到", "option_b": "星系旋转曲线异常", "option_c": "宇宙射线检测", "option_d": "引力波信号", "correct_answer": "B", "explanation": "星系的旋转曲线显示星系外围恒星的旋转速度远超预期，说明存在大量不可见的暗物质提供额外引力。", "topic": "宇宙学"},
            {"id": 25, "question": "宇宙微波背景辐射的发现有什么重要意义？", "option_a": "证明黑洞存在", "option_b": "支持大爆炸理论", "option_c": "发现暗能量", "option_d": "找到外星生命", "correct_answer": "B", "explanation": "1965年发现的宇宙微波背景辐射是大爆炸理论的关键证据，它是大爆炸后约38万年的宇宙遗存辐射。", "topic": "宇宙学"},
            # ===== 航天技术 =====
            {"id": 26, "question": "第一颗人造地球卫星是哪个国家发射的？", "option_a": "美国", "option_b": "苏联", "option_c": "中国", "option_d": "英国", "correct_answer": "B", "explanation": "1957年10月4日，苏联发射了世界上第一颗人造地球卫星斯普特尼克1号。", "topic": "航天技术"},
            {"id": 27, "question": "中国空间站的核心舱叫什么名字？", "option_a": "问天", "option_b": "梦天", "option_c": "天和", "option_d": "天宫", "correct_answer": "C", "explanation": "天和核心舱是中国空间站的主控舱段，2021年4月29日成功发射。", "topic": "航天技术"},
            {"id": 28, "question": "火箭发射时为什么会有大量白色烟雾？", "option_a": "燃料燃烧产生的烟", "option_b": "水蒸气凝结形成的雾", "option_c": "排放的化学气体", "option_d": "大气污染", "correct_answer": "B", "explanation": "白色烟雾主要是火箭发射时喷水系统产生的水蒸气凝结形成的，目的是降噪和隔热。", "topic": "航天技术"},
            # ===== 星座 =====
            {"id": 29, "question": "北极星位于哪个星座？", "option_a": "大熊座", "option_b": "小熊座", "option_c": "仙后座", "option_d": "天龙座", "correct_answer": "B", "explanation": "北极星（勾陈一）位于小熊座，距离地球约430光年，由于靠近北天极而被用作导航星。", "topic": "星座"},
            {"id": 30, "question": "黄道十二星座中，哪个星座的亮星最多？", "option_a": "白羊座", "option_b": "狮子座", "option_c": "天蝎座", "option_d": "双子座", "correct_answer": "C", "explanation": "天蝎座拥有众多亮星，包括红色超巨星心宿二（大火），是黄道星座中星等最明亮的星座之一。", "topic": "星座"},
            # ===== 太阳系（新增6题）=====
            {"id": 31, "question": "金星的表面温度大约是多少？", "option_a": "100℃", "option_b": "约460℃", "option_c": "50℃", "option_d": "1000℃", "correct_answer": "B", "explanation": "金星表面温度约460℃，是太阳系中最热的行星，这主要归因于其浓厚的二氧化碳大气层产生的强烈温室效应。", "topic": "太阳系"},
            {"id": 32, "question": "太阳系中哪颗行星的自转方向与其他行星相反？", "option_a": "火星", "option_b": "金星", "option_c": "木星", "option_d": "海王星", "correct_answer": "B", "explanation": "金星是太阳系中唯一逆向自转的行星，即自转方向与公转方向相反，这意味着在金星上太阳从西方升起。", "topic": "太阳系"},
            {"id": 33, "question": "火星的卫星有几颗？", "option_a": "0颗", "option_b": "1颗", "option_c": "2颗", "option_d": "3颗", "correct_answer": "C", "explanation": "火星有两颗天然卫星：火卫一（福波斯）和火卫二（德摩斯），它们形状不规则，可能是被引力捕获的小行星。", "topic": "太阳系"},
            {"id": 34, "question": "小行星带位于哪两颗行星之间？", "option_a": "地球和火星", "option_b": "火星和木星", "option_c": "木星和土星", "option_d": "土星和天王星", "correct_answer": "B", "explanation": "小行星带位于火星和木星轨道之间，包含数百万颗大小不等的小行星，是太阳系形成时留下的原始物质。", "topic": "太阳系"},
            {"id": 35, "question": "太阳系中最大的火山在哪颗行星上？", "option_a": "地球", "option_b": "金星", "option_c": "火星", "option_d": "木星", "correct_answer": "C", "explanation": "火星上的奥林匹斯山是太阳系中最大的火山，高约21.9公里，底部直径约600公里，是一座巨大的盾状火山。", "topic": "太阳系"},
            {"id": 36, "question": "天王星和海王星属于哪类行星？", "option_a": "岩石行星", "option_b": "气态巨行星", "option_c": "冰巨星", "option_d": "矮行星", "correct_answer": "C", "explanation": "天王星和海王星被称为冰巨星，主要由水、甲烷和氨的冰构成，不同于木星和土星那样的气态巨行星。", "topic": "太阳系"},
            # ===== 银河系（新增8题）=====
            {"id": 37, "question": "银河系的中心位于哪个星座方向？", "option_a": "猎户座", "option_b": "射手座", "option_c": "大熊座", "option_d": "仙后座", "correct_answer": "B", "explanation": "银河系的中心位于人马座（射手座）方向，距离地球约2.6万光年，那里有一个超大质量黑洞——人马座A*。", "topic": "银河系"},
            {"id": 38, "question": "银河系的直径大约是多少？", "option_a": "1万光年", "option_b": "10万光年", "option_c": "100万光年", "option_d": "1000万光年", "correct_answer": "B", "explanation": "银河系的直径约为10万光年，包含1000亿到4000亿颗恒星。", "topic": "银河系"},
            {"id": 39, "question": "银河系的卫星星系有哪些？", "option_a": "仙女座星系", "option_b": "大小麦哲伦云", "option_c": "三角座星系", "option_d": "漩涡星系", "correct_answer": "B", "explanation": "大麦哲伦云和小麦哲伦云是银河系最大的两个卫星星系，在南半球肉眼可见，距离地球约16万光年。", "topic": "银河系"},
            {"id": 40, "question": "银河系属于哪个星系群？", "option_a": "室女座星系团", "option_b": "本星系群", "option_c": "后发座星系团", "option_d": "武仙座超星系团", "correct_answer": "B", "explanation": "银河系属于本星系群，该星系群包含约80个星系，其中最大的成员是仙女座星系和银河系。", "topic": "银河系"},
            {"id": 41, "question": "银河系中恒星的主要诞生区域在哪里？", "option_a": "银晕", "option_b": "银心", "option_c": "旋臂", "option_d": "银盘边缘", "correct_answer": "C", "explanation": "银河系的旋臂是恒星形成的主要区域，那里有大量的星际气体和尘埃，为恒星诞生提供了原料。", "topic": "银河系"},
            {"id": 42, "question": "银河系中大约有多少个球状星团？", "option_a": "约50个", "option_b": "约150个", "option_c": "约500个", "option_d": "约2000个", "correct_answer": "B", "explanation": "银河系中已知约有150个球状星团，它们由数十万颗老年恒星组成，分布在银晕中。", "topic": "银河系"},
            {"id": 43, "question": "太阳绕银河系中心公转一周大约需要多久？", "option_a": "1亿年", "option_b": "2.5亿年", "option_c": "10亿年", "option_d": "1000万年", "correct_answer": "B", "explanation": "太阳以约220公里/秒的速度绕银河系中心运动，完成一次公转大约需要2.5亿年，这被称为一个银河年。", "topic": "银河系"},
            {"id": 44, "question": "银河系中星际介质的密度大约是多少？", "option_a": "每立方厘米1个原子", "option_b": "每立方厘米100个原子", "option_c": "每立方厘米1000个原子", "option_d": "与地球大气相同", "correct_answer": "A", "explanation": "银河系中的星际介质极其稀薄，平均密度约为每立方厘米1个氢原子，远低于地球上能达到的最高真空度。", "topic": "银河系"},
            # ===== 恒星（新增7题）=====
            {"id": 45, "question": "恒星演化末期可能形成的天体有哪些？", "option_a": "白矮星", "option_b": "中子星", "option_c": "黑洞", "option_d": "以上都是", "correct_answer": "D", "explanation": "恒星演化的最终产物取决于其初始质量：小质量恒星→白矮星，中等质量→中子星，大质量→黑洞。", "topic": "恒星"},
            {"id": 46, "question": "赫罗图（H-R图）的横轴和纵轴分别代表什么？", "option_a": "质量和半径", "option_b": "光谱型和光度", "option_c": "温度和密度", "option_d": "距离和速度", "correct_answer": "B", "explanation": "赫罗图以恒星的光谱型（或表面温度）为横轴、光度（或绝对星等）为纵轴，是研究恒星演化的重要工具。", "topic": "恒星"},
            {"id": 47, "question": "变星中最著名的一颗是哪个？", "option_a": "天狼星", "option_b": "造父一（仙王座δ）", "option_c": "天津四", "option_d": "织女星", "correct_answer": "B", "explanation": "造父一（仙王座δ）是最著名的造父变星，其亮度周期性变化，被视为测量遥远星系距离的\"标准烛光\"。", "topic": "恒星"},
            {"id": 48, "question": "太阳属于哪种光谱型恒星？", "option_a": "O型", "option_b": "B型", "option_c": "G型", "option_d": "M型", "correct_answer": "C", "explanation": "太阳属于G2V型恒星（黄矮星），表面温度约5778K，处于主序星阶段，预计总寿命约100亿年。", "topic": "恒星"},
            {"id": 49, "question": "红矮星的主要特征是什么？", "option_a": "温度高、质量大", "option_b": "温度低、质量小、寿命长", "option_c": "温度高、光度大", "option_d": "寿命短、快速演化", "correct_answer": "B", "explanation": "红矮星是质量最小的主序星（0.08-0.5太阳质量），表面温度低、呈红色，但寿命极长可达数千亿年。", "topic": "恒星"},
            {"id": 50, "question": "比邻星距离地球多远？", "option_a": "1光年", "option_b": "约4.2光年", "option_c": "10光年", "option_d": "100光年", "correct_answer": "B", "explanation": "比邻星是距太阳最近的恒星，距离约4.2光年，它是半人马座α三星系统中的一员。", "topic": "恒星"},
            {"id": 51, "question": "恒星在何时达到生命周期中最稳定的阶段？", "option_a": "红巨星阶段", "option_b": "主序星阶段", "option_c": "原恒星阶段", "option_d": "白矮星阶段", "correct_answer": "B", "explanation": "主序星阶段是恒星生命周期中最长、最稳定的时期，恒星通过氢核聚变产生能量，内部处于流体静力学平衡。", "topic": "恒星"},
            # ===== 黑洞与天体物理（新增8题）=====
            {"id": 52, "question": "黑洞\"事件视界\"的含义是什么？", "option_a": "黑洞的物理表面", "option_b": "光无法逃逸的边界", "option_c": "黑洞的自转轴", "option_d": "黑洞的吸积盘外缘", "correct_answer": "B", "explanation": "事件视界是黑洞的边界，任何物质（包括光）一旦越过此边界就无法逃脱黑洞的引力束缚。", "topic": "黑洞与天体物理"},
            {"id": 53, "question": "史瓦西半径与什么有关？", "option_a": "黑洞的自转速度", "option_b": "黑洞的质量", "option_c": "黑洞的电荷", "option_d": "黑洞的温度", "correct_answer": "B", "explanation": "史瓦西半径与黑洞质量成正比，它定义了非旋转黑洞的事件视界半径，一个太阳质量的黑洞史瓦西半径约3公里。", "topic": "黑洞与天体物理"},
            {"id": 54, "question": "引力波是由谁首先预言存在的？", "option_a": "牛顿", "option_b": "爱因斯坦", "option_c": "霍金", "option_d": "伽利略", "correct_answer": "B", "explanation": "爱因斯坦在1916年基于广义相对论预言了引力波的存在。2015年LIGO首次直接探测到引力波信号。", "topic": "黑洞与天体物理"},
            {"id": 55, "question": "霍金辐射理论认为黑洞最终会怎样？", "option_a": "永远存在", "option_b": "逐渐蒸发消失", "option_c": "变成白矮星", "option_d": "分裂成两个黑洞", "correct_answer": "B", "explanation": "霍金辐射理论认为黑洞会因量子效应而缓慢辐射能量，最终完全蒸发消失，但这一过程对恒星质量黑洞极其漫长。", "topic": "黑洞与天体物理"},
            {"id": 56, "question": "LIGO探测到的首个引力波信号来自什么？", "option_a": "超新星爆发", "option_b": "两个黑洞的合并", "option_c": "两颗中子星合并", "option_d": "宇宙大爆炸", "correct_answer": "B", "explanation": "2015年LIGO探测到的首个引力波信号GW150914来自约13亿光年外两个恒星质量黑洞的合并事件。", "topic": "黑洞与天体物理"},
            {"id": 57, "question": "银河系中心的超大质量黑洞叫什么？", "option_a": "M87*", "option_b": "人马座A*", "option_c": "天鹅座X-1", "option_d": "GRO J1655-40", "correct_answer": "B", "explanation": "银河系中心的超大质量黑洞被称为人马座A*（Sagittarius A*），质量约为太阳的430万倍。", "topic": "黑洞与天体物理"},
            {"id": 58, "question": "什么是白洞？", "option_a": "白色黑洞", "option_b": "理论上物质只能喷出不能进入的天体", "option_c": "恒星演化末期", "option_d": "星系中心的明亮区域", "correct_answer": "B", "explanation": "白洞是广义相对论中预言的一种理论天体，物质只能从其中喷出而不能进入，与黑洞的性质完全相反，目前尚未被观测证实。", "topic": "黑洞与天体物理"},
            {"id": 59, "question": "吸积盘在黑洞系统中有什么作用？", "option_a": "保护黑洞不受撞击", "option_b": "物质螺旋落入黑洞时释放能量", "option_c": "阻挡X射线", "option_d": "产生暗物质", "correct_answer": "B", "explanation": "吸积盘是围绕黑洞旋转的气体和尘埃盘，物质在螺旋落向黑洞的过程中因摩擦而剧烈加热，释放出大量X射线和可见光。", "topic": "黑洞与天体物理"},
            # ===== 天文探索（新增8题）=====
            {"id": 60, "question": "人类历史上首次进入太空的宇航员是谁？", "option_a": "阿姆斯特朗", "option_b": "加加林", "option_c": "列昂诺夫", "option_d": "季托夫", "correct_answer": "B", "explanation": "1961年4月12日，苏联宇航员尤里·加加林乘坐东方一号飞船进入太空，成为人类历史上第一个进入太空的人。", "topic": "天文探索"},
            {"id": 61, "question": "中国首次火星探测任务叫什么？", "option_a": "嫦娥", "option_b": "天问一号", "option_c": "神舟", "option_d": "北斗", "correct_answer": "B", "explanation": "天问一号是中国首次火星探测任务，2021年成功着陆火星表面，一次性完成了绕、着、巡三大目标。", "topic": "天文探索"},
            {"id": 62, "question": "旅行者1号探测器目前在哪里？", "option_a": "火星轨道", "option_b": "木星附近", "option_c": "进入星际空间", "option_d": "已坠毁", "correct_answer": "C", "explanation": "旅行者1号于1977年发射，2012年穿越日球层顶进入星际空间，是目前离地球最远的人造探测器。", "topic": "天文探索"},
            {"id": 63, "question": "开普勒太空望远镜的主要科学目标是什么？", "option_a": "观测黑洞", "option_b": "搜寻系外行星", "option_c": "研究太阳活动", "option_d": "绘制银河系地图", "correct_answer": "B", "explanation": "开普勒太空望远镜的主要任务是搜寻系外行星，通过观测恒星的亮度变化来发现凌星现象，已确认数千颗系外行星。", "topic": "天文探索"},
            {"id": 64, "question": "世界上最大的光学望远镜位于哪里？", "option_a": "夏威夷", "option_b": "智利", "option_c": "加那利群岛", "option_d": "西藏", "correct_answer": "B", "explanation": "欧洲极大望远镜（E-ELT）和大型综合巡天望远镜（LSST）均位于智利，智利阿塔卡马沙漠是世界顶级天文观测地。", "topic": "天文探索"},
            {"id": 65, "question": "钱德拉X射线天文台主要观测什么？", "option_a": "可见光", "option_b": "X射线", "option_c": "红外线", "option_d": "射电波", "correct_answer": "B", "explanation": "钱德拉X射线天文台专门观测宇宙中的X射线源，如黑洞、超新星遗迹、星系团中的高温气体等极端天体。", "topic": "天文探索"},
            {"id": 66, "question": "中国嫦娥五号任务的主要成就是什么？", "option_a": "首次载人登月", "option_b": "月球背面软着陆", "option_c": "月面采样返回", "option_d": "月球车巡视", "correct_answer": "C", "explanation": "2020年嫦娥五号成功从月球表面采集约1.73公斤月壤样品并返回地球，是中国首次地外天体采样返回任务。", "topic": "天文探索"},
            {"id": 67, "question": "首次系外行星是在哪一年被发现的？", "option_a": "1985年", "option_b": "1995年", "option_c": "2005年", "option_d": "2010年", "correct_answer": "B", "explanation": "1995年，天文学家发现飞马座51b，这是人类发现的第一颗围绕主序星运行的系外行星，开辟了系外行星研究新时代。", "topic": "天文探索"},
            # ===== 月球（新增8题）=====
            {"id": 68, "question": "月球表面的最高温度能达到多少？", "option_a": "约50℃", "option_b": "约127℃", "option_c": "约300℃", "option_d": "约500℃", "correct_answer": "B", "explanation": "月球表面白天温度可升至约127℃，夜间则降至零下173℃，昼夜温差高达300℃，这是由于月球没有大气层保温。", "topic": "月球"},
            {"id": 69, "question": "月球上为什么有很多陨石坑？", "option_a": "月球引力更强", "option_b": "没有大气层保护", "option_c": "月球更靠近小行星带", "option_d": "月球年龄更大", "correct_answer": "B", "explanation": "月球没有大气层，流星体可以直接撞击月面形成陨石坑，不像地球大气层能烧毁大部分小天体。", "topic": "月球"},
            {"id": 70, "question": "月球正在以多快的速度远离地球？", "option_a": "每年约1厘米", "option_b": "每年约3.8厘米", "option_c": "每年约1米", "option_d": "每年约10米", "correct_answer": "B", "explanation": "由于潮汐相互作用，月球正以约每年3.8厘米的速度远离地球，同时地球的自转速度也在逐渐减慢。", "topic": "月球"},
            {"id": 71, "question": "月球表面最显著的地形特征是什么？", "option_a": "高山", "option_b": "月海", "option_c": "峡谷", "option_d": "火山口", "correct_answer": "B", "explanation": "月海是月球表面大片暗色玄武岩平原，最早的天文学家误以为是海洋，因此取名\"月海\"，实际没有任何水体。", "topic": "月球"},
            {"id": 72, "question": "月球轨道偏离黄道面的角度是多少？", "option_a": "约5度", "option_b": "约10度", "option_c": "约15度", "option_d": "约23.5度", "correct_answer": "A", "explanation": "月球轨道与黄道面（地球公转轨道面）的夹角约为5度，这个倾角使得日食和月食并不每个月都发生。", "topic": "月球"},
            {"id": 73, "question": "月壤（月尘）的主要成分是什么？", "option_a": "铁和镍", "option_b": "硅酸盐矿物", "option_c": "纯硅", "option_d": "水冰", "correct_answer": "B", "explanation": "月壤主要由硅酸盐矿物颗粒组成，含有丰富的氧、硅、铝、铁等元素，经过数十亿年的微陨石轰击形成细粉状。", "topic": "月球"},
            {"id": 74, "question": "人类最后一次登月是在哪一年？", "option_a": "1970年", "option_b": "1972年", "option_c": "1975年", "option_d": "1980年", "correct_answer": "B", "explanation": "阿波罗17号于1972年12月完成人类迄今为止最后一次登月任务，指令长尤金·塞尔南是最后一个踏上月球的人。", "topic": "月球"},
            {"id": 75, "question": "月球上是否发现过水冰？", "option_a": "从未发现", "option_b": "在极地阴影区发现", "option_c": "在月海发现大量水", "option_d": "只在月球背面发现", "correct_answer": "B", "explanation": "多项探测任务在月球极地永久阴影区的陨石坑中发现了水冰存在的证据，这些水冰可能是未来月球探测的重要资源。", "topic": "月球"},
            # ===== 宇宙学（新增8题）=====
            {"id": 76, "question": "宇宙大爆炸后大约多久形成了第一批恒星？", "option_a": "1万年", "option_b": "约1亿年", "option_c": "10亿年", "option_d": "100亿年", "correct_answer": "B", "explanation": "宇宙大爆炸后约1亿年，原始气体云在引力作用下坍缩，形成了宇宙中第一批恒星（族III恒星）。", "topic": "宇宙学"},
            {"id": 77, "question": "宇宙的膨胀是由什么现象发现的？", "option_a": "恒星运动", "option_b": "星系红移", "option_c": "行星轨道", "option_d": "彗星轨迹", "correct_answer": "B", "explanation": "埃德温·哈勃观测到遥远星系的谱线出现红移，且红移量与星系距离成正比，证明宇宙正在膨胀。", "topic": "宇宙学"},
            {"id": 78, "question": "暗能量在宇宙中占多少比例？", "option_a": "约5%", "option_b": "约25%", "option_c": "约68%", "option_d": "约95%", "correct_answer": "C", "explanation": "根据普朗克卫星数据，宇宙中暗能量约占68%，暗物质约占27%，普通物质仅占约5%。", "topic": "宇宙学"},
            {"id": 79, "question": "什么是宇宙学原理？", "option_a": "宇宙以地球为中心", "option_b": "宇宙在大尺度上是均匀且各向同性的", "option_c": "宇宙是静止不变的", "option_d": "宇宙是无限大的", "correct_answer": "B", "explanation": "宇宙学原理认为在足够大的尺度上（>1亿光年），宇宙是均匀且各向同性的，这是现代宇宙学的基本假设。", "topic": "宇宙学"},
            {"id": 80, "question": "可观测宇宙的直径大约是多少？", "option_a": "约100亿光年", "option_b": "约930亿光年", "option_c": "约1万亿光年", "option_d": "约10万亿光年", "correct_answer": "B", "explanation": "可观测宇宙的直径约930亿光年，这是从地球到宇宙可见边界的距离，由于宇宙膨胀，实际范围比宇宙年龄对应的大。", "topic": "宇宙学"},
            {"id": 81, "question": "星系红移的宇宙学含义是什么？", "option_a": "星系在远离我们", "option_b": "星系在靠近我们", "option_c": "星系在自转", "option_d": "星系在变暗", "correct_answer": "A", "explanation": "星系红移意味着星系正在远离我们，这是宇宙膨胀的直接证据，红移量越大说明星系远离速度越快。", "topic": "宇宙学"},
            {"id": 82, "question": "宇宙微波背景辐射的温度是多少？", "option_a": "约零下100℃", "option_b": "约2.7K", "option_c": "约零度", "option_d": "约100K", "correct_answer": "B", "explanation": "宇宙微波背景辐射的温度约为2.725开尔文（约零下270.4℃），是宇宙大爆炸的余晖，均匀分布在宇宙各处。", "topic": "宇宙学"},
            {"id": 83, "question": "什么是费米悖论？", "option_a": "宇宙是有限的", "option_b": "外星文明存在的概率与观测缺失的矛盾", "option_c": "光速无法超越", "option_d": "量子纠缠的不确定性", "correct_answer": "B", "explanation": "费米悖论指出：考虑到宇宙的年龄和星系数量，外星文明应该普遍存在，但人类至今没有发现任何地外文明的证据，这一矛盾令人深思。", "topic": "宇宙学"},
            # ===== 航天技术（新增8题）=====
            {"id": 84, "question": "中国第一位进入太空的航天员是谁？", "option_a": "杨利伟", "option_b": "费俊龙", "option_c": "聂海胜", "option_d": "翟志刚", "correct_answer": "A", "explanation": "2003年10月15日，杨利伟乘坐神舟五号飞船进入太空，使中国成为继苏美之后第三个独立将人送入太空的国家。", "topic": "航天技术"},
            {"id": 85, "question": "国际空间站的轨道高度大约是多少？", "option_a": "约200公里", "option_b": "约400公里", "option_c": "约1000公里", "option_d": "约36000公里", "correct_answer": "B", "explanation": "国际空间站运行在距地面约400公里的近地轨道上，轨道倾角51.6度，以约7.66公里/秒的速度绕地球飞行。", "topic": "航天技术"},
            {"id": 86, "question": "火箭推进的基本物理原理是什么？", "option_a": "伯努利定律", "option_b": "牛顿第三定律（作用与反作用）", "option_c": "热力学第二定律", "option_d": "万有引力定律", "correct_answer": "B", "explanation": "火箭发动机通过向后高速喷射燃料燃烧产生的高速气流，根据牛顿第三定律获得向前的推力，从而在真空中也能航行。", "topic": "航天技术"},
            {"id": 87, "question": "地球同步轨道卫星的高度是多少？", "option_a": "约400公里", "option_b": "约2000公里", "option_c": "约35786公里", "option_d": "约10万公里", "correct_answer": "C", "explanation": "地球同步轨道距地面约35786公里，卫星在此轨道上运行周期等于地球自转周期（约24小时），相对地面保持静止。", "topic": "航天技术"},
            {"id": 88, "question": "中国北斗卫星导航系统属于什么类型的轨道？", "option_a": "仅地球静止轨道", "option_b": "混合轨道（GEO+IGSO+MEO）", "option_c": "仅中地球轨道", "option_d": "仅低地球轨道", "correct_answer": "B", "explanation": "北斗系统采用混合星座设计，包括地球静止轨道（GEO）、倾斜地球同步轨道（IGSO）和中地球轨道（MEO）三种轨道卫星。", "topic": "航天技术"},
            {"id": 89, "question": "航天员在太空中为什么会失重？", "option_a": "没有地球引力", "option_b": "处于自由落体状态", "option_c": "离地球太远", "option_d": "太空没有空气", "correct_answer": "B", "explanation": "航天员处于失重状态是因为飞船和航天员一起绕地球做自由落体运动，并非因为没有引力（轨道上的引力仍有地球表面的约90%）。", "topic": "航天技术"},
            {"id": 90, "question": "可重复使用火箭技术的主要优势是什么？", "option_a": "飞得更快", "option_b": "降低发射成本", "option_c": "载重更大", "option_d": "飞行更安全", "correct_answer": "B", "explanation": "可重复使用火箭通过回收和复用一级火箭，大幅降低航天发射成本，SpaceX的猎鹰9号火箭已实现多次成功回收。", "topic": "航天技术"},
            {"id": 91, "question": "深空探测中\"引力弹弓\"效应利用的是什么原理？", "option_a": "电磁加速", "option_b": "行星引力转移轨道能量", "option_c": "太阳风推进", "option_d": "激光推进", "correct_answer": "B", "explanation": "引力弹弓效应利用飞越行星时的引力转移能量，给探测器加速或减速，旅行者号就是利用木星和土星的引力弹弓飞向外太阳系。", "topic": "航天技术"},
            # ===== 星座（新增9题）=====
            {"id": 92, "question": "全天共有多少个星座？", "option_a": "48个", "option_b": "66个", "option_c": "88个", "option_d": "108个", "correct_answer": "C", "explanation": "国际天文学联合会将全天划分为88个星座，覆盖整个天球，每个星座有明确的边界。", "topic": "星座"},
            {"id": 93, "question": "夏季大三角由哪三颗星组成？", "option_a": "织女星、牛郎星、天津四", "option_b": "天狼星、参宿四、南河三", "option_c": "北极星、织女星、心宿二", "option_d": "大角星、角宿一、五帝座一", "correct_answer": "A", "explanation": "夏季大三角由天琴座的织女星、天鹰座的牛郎星和天鹅座的天津四组成，是夏季夜空中最显著的星群。", "topic": "星座"},
            {"id": 94, "question": "北斗七星属于哪个星座？", "option_a": "小熊座", "option_b": "大熊座", "option_c": "猎户座", "option_d": "仙后座", "correct_answer": "B", "explanation": "北斗七星是大熊座的一部分，由七颗亮星组成勺状结构，常被用作寻找北极星的导航标志。", "topic": "星座"},
            {"id": 95, "question": "全天最亮的恒星是哪颗？", "option_a": "北极星", "option_b": "天狼星", "option_c": "织女星", "option_d": "参宿四", "correct_answer": "B", "explanation": "天狼星（大犬座α）是全天最亮的恒星，视星等约-1.46，距离地球约8.6光年，实际上是一个双星系统。", "topic": "星座"},
            {"id": 96, "question": "冬季夜空中最容易辨认的星座是哪个？", "option_a": "大熊座", "option_b": "猎户座", "option_c": "天鹰座", "option_d": "天蝎座", "correct_answer": "B", "explanation": "猎户座是冬季夜空最耀眼的星座，其\"腰带\"三星排列整齐，周围有参宿四（红色）和参宿七（蓝色）等亮星。", "topic": "星座"},
            {"id": 97, "question": "黄道星座共有多少个？", "option_a": "10个", "option_b": "12个", "option_c": "13个", "option_d": "14个", "correct_answer": "B", "explanation": "黄道星座传统上有12个，但太阳实际在天球上经过13个星座（包括蛇夫座），不过占星学仍沿用12星座体系。", "topic": "星座"},
            {"id": 98, "question": "南半球最著名的星座是哪个？", "option_a": "猎户座", "option_b": "南十字座", "option_c": "大熊座", "option_d": "仙后座", "correct_answer": "B", "explanation": "南十字座是南半球夜空最具代表性的星座，虽然是最小的星座之一，但其中的南十字星是南半球导航的重要标志。", "topic": "星座"},
            {"id": 99, "question": "仙后座在北半球夜空中是什么形状？", "option_a": "勺状", "option_b": "W或M状", "option_c": "十字形", "option_d": "三角形", "correct_answer": "B", "explanation": "仙后座由五颗亮星组成W（或M）形状，与北斗七星分别位于北极星两侧，是北半球全年可见的拱极星座。", "topic": "星座"},
            {"id": 100, "question": "星座中星星的命名规则是什么？", "option_a": "按距离排序", "option_b": "一般按亮度用希腊字母排序", "option_c": "按发现的先后顺序", "option_d": "随机编号", "correct_answer": "B", "explanation": "星座中的恒星通常按亮度由亮到暗用希腊字母命名，如α星最亮、β星次之，后面再跟所属星座的属格名称。", "topic": "星座"},
        ]
        df = pd.DataFrame(questions_data)
        df.to_csv(QUESTIONS_CSV, index=False, encoding='utf-8-sig')

def init_user_history_csv():
    """初始化用户答题历史CSV文件（迁移旧格式）"""
    if not os.path.exists(USER_HISTORY_CSV):
        df = pd.DataFrame(columns=["username", "timestamp", "question", "user_answer", "is_correct", "topic"])
        df.to_csv(USER_HISTORY_CSV, index=False, encoding='utf-8-sig')
    else:
        df = pd.read_csv(USER_HISTORY_CSV, encoding='utf-8-sig')
        if 'username' not in df.columns:
            df.insert(0, 'username', '')
            df.to_csv(USER_HISTORY_CSV, index=False, encoding='utf-8-sig')

def load_questions():
    """加载题库"""
    init_questions_csv()
    return pd.read_csv(QUESTIONS_CSV, encoding='utf-8-sig')

def load_user_history():
    """加载当前用户的答题历史"""
    init_user_history_csv()
    df = pd.read_csv(USER_HISTORY_CSV, encoding='utf-8-sig')
    if 'username' not in df.columns:
        df['username'] = ''
    user = st.session_state.get('user', '')
    if user:
        df = df[df['username'] == user]
    return df

def save_user_answer(question, user_answer, is_correct, topic):
    """保存答题记录到CSV"""
    init_user_history_csv()
    user = st.session_state.get('user', '')
    new_record = pd.DataFrame({
        "username": [user],
        "timestamp": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        "question": [question],
        "user_answer": [user_answer],
        "is_correct": [is_correct],
        "topic": [topic]
    })
    new_record.to_csv(USER_HISTORY_CSV, mode='a', header=False, index=False, encoding='utf-8-sig')

# ==================== 天文数据查询 ====================

def get_astronomy_data(location=None, lat=None, long=None):
    """从ipgeolocation.io获取天文数据"""
    base_url = "https://api.ipgeolocation.io/astronomy"
    params = {"apiKey": IPGEOLOCATION_API_KEY}
    if location:
        params["location"] = location
    elif lat is not None and long is not None:
        params["lat"] = lat
        params["long"] = long
    else:
        return None
    try:
        resp = requests.get(base_url, params=params, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        st.error(f"API 请求失败 (HTTP {resp.status_code})")
        return None
    except requests.exceptions.Timeout:
        st.error("请求超时，请检查网络连接")
        return None
    except requests.exceptions.ConnectionError:
        st.error("网络连接失败，请检查网络")
        return None
    except Exception as e:
        st.error(f"请求出错：{e}")
        return None

def parse_time(t_str):
    """解析时间字符串 → time 对象（支持 12h/24h 格式）"""
    for fmt in ("%H:%M:%S", "%H:%M", "%I:%M:%S %p", "%I:%M %p"):
        try:
            return datetime.strptime(t_str.strip(), fmt).time()
        except:
            pass
    return None

def add_min(t, mins):
    """time 对象加减分钟"""
    dt = datetime.combine(datetime.today(), t) + timedelta(minutes=mins)
    return dt.time()

def fmt_t(t):
    return t.strftime("%H:%M")

# ==================== 全局CSS样式 ====================

def apply_global_css():
    """应用深空科幻风格的全局CSS"""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Poppins:wght@500;600;700;800&display=swap');
    
    /* ==================== 1. BG: 星空图片 ==================== */
    .stApp {
        background: #050514;
        background-image: url('https://images.unsplash.com/photo-1462331940025-496dfbfc7564?w=1920&q=80');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        background-repeat: no-repeat;
        min-height: 100vh;
        position: relative;
    }
    .stApp::before {
        content: '';
        position: fixed;
        inset: 0;
        background: rgba(5, 5, 20, 0.55);
        pointer-events: none;
        z-index: 0;
    }
    
    /* ==================== 2. LAYOUT compact ==================== */
    .block-container {
        padding: 1.5rem 2rem !important;
        max-width: 1050px !important;
        margin: 0 auto !important;
        position: relative;
        z-index: 1;
    }
    section.main > div:has(> .block-container) {
        padding-top: 0 !important;
    }
    
    /* ==================== 3. TYPOGRAPHY: 白色加粗 ==================== */
    h1, h2, h3, h4, h5, h6,
    body, p, span, div, label, .stMarkdown, .stText {
        font-family: 'Inter', sans-serif !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        line-height: 1.6 !important;
    }
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Poppins', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: -0.01em;
    }
    /* 页面主标题亮蓝渐变 */
    .cosmo-page-title {
        font-family: 'Poppins', sans-serif !important;
        font-weight: 800 !important;
        font-size: 2rem !important;
        background: linear-gradient(135deg, #60a5fa, #a78bfa) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        margin-bottom: 0.15rem !important;
        text-shadow: 0 0 40px rgba(96,165,250,0.3);
    }
    .cosmo-page-subtitle {
        color: rgba(255,255,255,0.7) !important;
        font-weight: 500 !important;
        font-size: 0.95rem !important;
        margin-bottom: 1rem !important;
    }
    .cosmo-subtitle {
        color: rgba(255,255,255,0.55) !important;
        font-size: 0.85em !important;
        font-weight: 500 !important;
    }
    
    /* ==================== 4. GLASS CARD: 透明发光 ==================== */
    .cosmo-card {
        background: rgba(10, 10, 30, 0.3) !important;
        backdrop-filter: blur(18px) !important;
        -webkit-backdrop-filter: blur(18px) !important;
        border-radius: 14px !important;
        padding: 18px 22px !important;
        margin-bottom: 14px !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        box-shadow: 0 8px 32px rgba(0,0,0,0.35), 0 0 24px rgba(74,108,247,0.08) !important;
        color: #ffffff !important;
        transition: all 0.3s ease !important;
    }
    .cosmo-card:hover {
        border-color: rgba(255,255,255,0.15) !important;
        box-shadow: 0 8px 32px rgba(0,0,0,0.35), 0 0 40px rgba(74,108,247,0.15) !important;
    }
    .cosmo-card h1, .cosmo-card h2, .cosmo-card h3,
    .cosmo-card h4, .cosmo-card h5, .cosmo-card h6,
    .cosmo-card p, .cosmo-card span, .cosmo-card div {
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    
    /* ==================== 5. BUTTONS: 透明发光 ==================== */
    .stButton>button, .stFormSubmitButton > button {
        background: rgba(74,108,247,0.25) !important;
        backdrop-filter: blur(8px) !important;
        color: white !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        border-radius: 10px !important;
        padding: 0.5rem 1.4rem !important;
        font-weight: 700 !important;
        font-size: 0.9rem !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 20px rgba(74,108,247,0.2) !important;
    }
    .stButton>button:hover, .stFormSubmitButton > button:hover {
        background: rgba(74,108,247,0.4) !important;
        border-color: rgba(255,255,255,0.25) !important;
        box-shadow: 0 6px 30px rgba(74,108,247,0.35) !important;
        transform: translateY(-1px) !important;
    }
    .stDownloadButton>button {
        background: rgba(16,185,129,0.25) !important;
        box-shadow: 0 4px 20px rgba(16,185,129,0.15) !important;
    }
    .stDownloadButton>button:hover {
        background: rgba(16,185,129,0.4) !important;
        box-shadow: 0 6px 30px rgba(16,185,129,0.3) !important;
    }
    
    /* ==================== 6. SIDEBAR: 透明玻璃 ==================== */
    section[data-testid="stSidebar"] {
        background: rgba(5, 5, 20, 0.5) !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
        border-right: 1px solid rgba(255,255,255,0.06) !important;
        max-width: 280px !important;
        min-width: 200px !important;
    }
    section[data-testid="stSidebar"] > div {
        padding: 1rem 0.8rem !important;
    }
    /* 窄版伸缩按钮 */
    button[data-testid="collapsedControl"] {
        background: transparent !important;
        border: none !important;
        color: rgba(255,255,255,0.35) !important;
        box-shadow: none !important;
        backdrop-filter: none !important;
        padding: 2px 4px !important;
        border-radius: 4px !important;
        font-size: 0.75rem !important;
        line-height: 1 !important;
        min-width: unset !important;
        width: auto !important;
    }
    button[data-testid="collapsedControl"]:hover {
        background: rgba(255,255,255,0.06) !important;
        color: rgba(255,255,255,0.7) !important;
    }
    .sidebar-divider {
        border: none !important;
        height: 1px !important;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent) !important;
        margin: 0.6rem 0 !important;
    }
    .sidebar-stats {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 10px;
        padding: 0.7rem 1rem;
        margin-top: 0.5rem;
    }
    .sidebar-stats p {
        margin: 0.2rem 0;
        font-size: 0.85rem;
        font-weight: 500;
    }
    .sidebar-stats strong {
        color: #60a5fa;
        font-weight: 700;
    }
    /* 导航 radio 透明 */
    section[data-testid="stSidebar"] .stRadio > div label {
        padding: 0.55rem 0.8rem !important;
        border-radius: 8px !important;
        margin-bottom: 1px !important;
        background: rgba(255,255,255,0.03) !important;
        border: 1px solid rgba(255,255,255,0.04) !important;
        color: rgba(255,255,255,0.8) !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
    }
    section[data-testid="stSidebar"] .stRadio > div label:hover {
        background: rgba(74,108,247,0.15) !important;
        border-color: rgba(74,108,247,0.25) !important;
        color: #ffffff !important;
    }
    section[data-testid="stSidebar"] .stRadio > div label:has(input:checked) {
        background: rgba(74,108,247,0.2) !important;
        border-color: rgba(74,108,247,0.35) !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        box-shadow: 0 0 16px rgba(74,108,247,0.15);
    }
    
    /* ==================== 7. METRICS: 透明 ==================== */
    .stMetric {
        background: rgba(255,255,255,0.05) !important;
        backdrop-filter: blur(8px) !important;
        border-radius: 12px !important;
        padding: 0.8rem 1.2rem !important;
        border: 1px solid rgba(255,255,255,0.06) !important;
        box-shadow: 0 4px 20px rgba(0,0,0,0.2) !important;
    }
    .stMetric label {
        color: rgba(255,255,255,0.6) !important;
        font-weight: 600 !important;
        font-size: 0.8rem !important;
    }
    .stMetric [data-testid="stMetricValue"] {
        font-family: 'Poppins', sans-serif !important;
        font-weight: 800 !important;
        font-size: 1.6rem !important;
        color: #ffffff !important;
    }
    
    /* ==================== 8. SUBHEADER ==================== */
    .stSubheader {
        font-family: 'Poppins', sans-serif !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        margin-top: 1.2rem !important;
        margin-bottom: 0.5rem !important;
        padding-bottom: 0.3rem !important;
        border-bottom: 1px solid rgba(255,255,255,0.08) !important;
    }
    
    /* ==================== 9. QUIZ RADIO: compact + 透明 ==================== */
    .stRadio > div[role="radiogroup"] {
        gap: 6px !important;
    }
    .stRadio > div label {
        display: flex !important;
        align-items: center !important;
        width: 100% !important;
        padding: 0.65rem 1rem !important;
        border-radius: 10px !important;
        margin-bottom: 0 !important;
        background: rgba(20, 20, 45, 0.25) !important;
        backdrop-filter: blur(6px) !important;
        border: 1px solid rgba(255,255,255,0.06) !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        line-height: 1.4 !important;
        transition: all 0.2s ease !important;
        cursor: pointer !important;
    }
    .stRadio > div label:hover {
        background: rgba(74,108,247,0.2) !important;
        border-color: rgba(74,108,247,0.3) !important;
        box-shadow: 0 0 16px rgba(74,108,247,0.1);
    }
    
    /* ==================== 10. CHAT: DeepSeek 风格对话气泡 ==================== */
    .chat-scroll-area {
        max-height: 55vh;
        overflow-y: auto;
        padding-right: 4px;
        display: flex;
        flex-direction: column;
        gap: 6px;
    }
    .chat-scroll-area > div {
        animation: fadeInUp 0.3s ease both;
    }
    .user-row {
        display: flex;
        justify-content: flex-end;
        margin-bottom: 10px;
    }
    .user-bubble {
        background: rgba(74,108,247,0.25) !important;
        backdrop-filter: blur(8px) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 18px 18px 4px 18px !important;
        padding: 10px 16px !important;
        max-width: 75% !important;
        color: #ffffff !important;
        box-shadow: 0 4px 16px rgba(74,108,247,0.15) !important;
        line-height: 1.5 !important;
        font-size: 0.9rem !important;
        font-weight: 500 !important;
    }
    .ai-row {
        display: flex;
        align-items: flex-start;
        gap: 10px;
        margin-bottom: 10px;
    }
    .ai-avatar {
        width: 36px;
        min-width: 36px;
        height: 36px;
        border-radius: 50%;
        background: rgba(74,108,247,0.2);
        backdrop-filter: blur(8px);
        border: 1px solid rgba(255,255,255,0.12);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
        box-shadow: 0 0 16px rgba(74,108,247,0.1);
        flex-shrink: 0;
    }
    .ai-bubble {
        background: rgba(20,20,40,0.3) !important;
        backdrop-filter: blur(8px) !important;
        border: 1px solid rgba(255,255,255,0.06) !important;
        border-radius: 18px 18px 18px 4px !important;
        padding: 10px 16px !important;
        max-width: 75% !important;
        color: #ffffff !important;
        box-shadow: 0 4px 16px rgba(0,0,0,0.2) !important;
        line-height: 1.5 !important;
        font-size: 0.9rem !important;
        font-weight: 500 !important;
    }
    .welcome-card {
        text-align: center;
        padding: 2rem 1rem;
        background: rgba(10,10,30,0.2) !important;
        backdrop-filter: blur(12px) !important;
        border-radius: 16px !important;
        border: 1px solid rgba(255,255,255,0.06) !important;
        margin: 1rem 0;
    }
    .welcome-card .icon {
        font-size: 3rem;
        margin-bottom: 0.5rem;
    }
    .welcome-card h3 {
        font-size: 1.2rem !important;
        margin-bottom: 0.3rem !important;
    }
    .welcome-card p {
        color: rgba(255,255,255,0.6) !important;
        font-size: 0.9rem !important;
    }
    .chat-divider {
        border: none !important;
        height: 1px !important;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.08), transparent) !important;
        margin: 0.5rem 0 !important;
    }
    .persona-label {
        color: rgba(255,255,255,0.6) !important;
        font-size: 0.8rem !important;
        font-weight: 500 !important;
        margin-bottom: 0.2rem !important;
    }
    
    /* ==================== 11. MISC glow ==================== */
    .success-card {
        border: 1.5px solid rgba(16,185,129,0.5) !important;
        background: rgba(16,185,129,0.08) !important;
        box-shadow: 0 0 24px rgba(16,185,129,0.12) !important;
    }
    .error-card {
        border: 1.5px solid rgba(239,68,68,0.5) !important;
        background: rgba(239,68,68,0.08) !important;
        box-shadow: 0 0 24px rgba(239,68,68,0.12) !important;
    }
    .stProgress > div > div {
        background: rgba(255,255,255,0.1) !important;
        border-radius: 6px !important;
    }
    .stProgress > div > div > div {
        background: linear-gradient(90deg, rgba(74,108,247,0.6), rgba(124,77,255,0.6)) !important;
        border-radius: 6px !important;
        box-shadow: 0 0 12px rgba(74,108,247,0.2);
    }
    .stTextInput input {
        background: rgba(20,20,40,0.3) !important;
        backdrop-filter: blur(8px) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 10px !important;
        padding: 0.6rem 1rem !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.9rem !important;
    }
    .stTextInput input:focus {
        border-color: rgba(74,108,247,0.5) !important;
        box-shadow: 0 0 0 3px rgba(74,108,247,0.15) !important;
    }
    .stTextInput input::placeholder {
        color: rgba(255,255,255,0.3) !important;
        font-weight: 500 !important;
    }
    .stTable table {
        background: rgba(10,10,30,0.3) !important;
        border-radius: 10px !important;
        overflow: hidden !important;
    }
    .stTable thead tr th {
        background: rgba(74,108,247,0.2) !important;
        color: white !important;
        font-weight: 700 !important;
        font-size: 0.8rem !important;
        padding: 0.5rem 0.8rem !important;
        border: none !important;
    }
    .stTable tbody tr td {
        padding: 0.4rem 0.8rem !important;
        border: none !important;
        border-bottom: 1px solid rgba(255,255,255,0.04) !important;
        color: rgba(255,255,255,0.85) !important;
        font-weight: 500 !important;
    }
    .stTable tbody tr:hover td {
        background: rgba(74,108,247,0.06) !important;
    }
    hr {
        border: none !important;
        height: 1px !important;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent) !important;
        margin: 1rem 0 !important;
    }
    .stWarning, .stInfo, .stError {
        background: rgba(10,10,30,0.4) !important;
        backdrop-filter: blur(8px) !important;
        border-radius: 10px !important;
        border: 1px solid rgba(255,255,255,0.06) !important;
        color: #ffffff !important;
    }
    .stSelectSlider > div {
        color: #ffffff !important;
    }
    .stSelectSlider > div > div {
        background: rgba(255,255,255,0.1) !important;
    }
    .stSelectSlider > div > div > div {
        background: rgba(74,108,247,0.6) !important;
    }
    .stSpinner > div {
        color: rgba(255,255,255,0.8) !important;
    }
    div[data-testid="stToast"] {
        background: rgba(10,10,30,0.8) !important;
        backdrop-filter: blur(12px) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
    }
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: rgba(74,108,247,0.25); border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(74,108,247,0.4); }
    
    /* Selectbox: 按钮同款玻璃蓝风格 */
    div[data-baseweb="select"] {
        background: rgba(74,108,247,0.25) !important;
        backdrop-filter: blur(8px) !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 20px rgba(74,108,247,0.2) !important;
        transition: all 0.3s ease !important;
    }
    div[data-baseweb="select"]:hover {
        background: rgba(74,108,247,0.4) !important;
        border-color: rgba(255,255,255,0.25) !important;
        box-shadow: 0 6px 30px rgba(74,108,247,0.35) !important;
    }
    div[data-baseweb="select"] > div {
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 0.9rem !important;
    }
    div[data-baseweb="select"] * {
        color: #ffffff !important;
    }
    div[data-baseweb="select"] span {
        color: #ffffff !important;
    }
    div[data-baseweb="popover"] ul {
        background: rgba(15,15,35,0.95) !important;
        backdrop-filter: blur(16px) !important;
        border-radius: 10px !important;
        box-shadow: 0 8px 32px rgba(0,0,0,0.5), 0 0 24px rgba(74,108,247,0.08) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        padding: 4px !important;
    }
    div[data-baseweb="popover"] li {
        color: #ffffff !important;
        background: transparent !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        border-radius: 6px !important;
    }
    div[data-baseweb="popover"] li[aria-selected="true"] {
        background: rgba(74,108,247,0.25) !important;
        color: #ffffff !important;
    }
    div[data-baseweb="popover"] li:hover {
        background: rgba(74,108,247,0.15) !important;
    }
    
    /* 侧边栏伸缩按钮：经典默认款 */
    button[data-testid="collapsedControl"] {
        background: transparent !important;
        border: none !important;
        color: rgba(255,255,255,0.4) !important;
        box-shadow: none !important;
        backdrop-filter: none !important;
        padding: 4px !important;
        border-radius: 6px !important;
        transition: all 0.2s ease !important;
    }
    button[data-testid="collapsedControl"]:hover {
        background: rgba(255,255,255,0.08) !important;
        color: rgba(255,255,255,0.8) !important;
        transform: none !important;
        box-shadow: none !important;
    }
    
    /* Logo 美化 */
    .sidebar-logo {
        text-align: center;
        padding: 0.8rem 0 1rem !important;
        position: relative;
    }
    .logo-icon-wrap {
        display: inline-block;
        position: relative;
        margin-bottom: 0.3rem;
    }
    .logo-icon-wrap .glow-ring {
        position: absolute;
        inset: -10px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(74,108,247,0.15), transparent 70%);
        border: 1px solid rgba(74,108,247,0.15);
        box-shadow: 0 0 30px rgba(74,108,247,0.1), inset 0 0 30px rgba(74,108,247,0.05);
        animation: logoPulse 3s ease-in-out infinite;
        pointer-events: none;
    }
    .logo-icon-wrap .icon {
        font-size: 2.2rem;
        display: block;
        position: relative;
        z-index: 1;
    }
    @keyframes logoPulse {
        0%, 100% { transform: scale(1); opacity: 0.6; }
        50% { transform: scale(1.12); opacity: 1; }
    }
    .sidebar-logo h1 {
        font-size: 1.3rem !important;
        margin-bottom: 0.1rem !important;
        background: linear-gradient(135deg, #60a5fa, #a78bfa) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        letter-spacing: 0.05em !important;
    }
    .sidebar-logo .sub {
        color: rgba(255,255,255,0.45) !important;
        font-size: 0.7rem !important;
        font-weight: 500 !important;
        letter-spacing: 0.15em !important;
        margin-top: 0.1rem !important;
    }
    .sidebar-logo .deco-stars {
        color: rgba(255,255,255,0.15) !important;
        font-size: 0.6rem !important;
        letter-spacing: 0.6em !important;
        margin-top: 0.3rem !important;
    }
    
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .cosmo-card {
        animation: fadeInUp 0.35s ease both;
    }
    </style>
    """, unsafe_allow_html=True)

# ==================== 页面模块 ====================

def daily_apod():
    """每日天文模块 - DeepSeek生成 + Unsplash星空图"""
    st.markdown('<h1 class="cosmo-page-title">🌌 每日天文</h1>', unsafe_allow_html=True)
    st.markdown('<p class="cosmo-page-subtitle">探索宇宙的奇妙瞬间</p>', unsafe_allow_html=True)

    today_str = datetime.now().strftime("%Y-%m-%d")

    # 每日 Unsplash 星空图（按日期取模保证每日一致）
    space_images = [
        "https://images.unsplash.com/photo-1419242902214-272b3f66ee7a?w=1000",
        "https://images.unsplash.com/photo-1462331940025-496dfbfc7564?w=1000",
        "https://images.unsplash.com/photo-1444703686981-a3abbc4d4fe3?w=1000",
        "https://images.unsplash.com/photo-1504333638930-c8787321eee0?w=1000",
        "https://images.unsplash.com/photo-1543722530-d2c3201371e7?w=1000",
        "https://images.unsplash.com/photo-1445905595283-21f8ae8a33d2?w=1000",
        "https://images.unsplash.com/photo-1534469628714-1c27e8a420e4?w=1000",
    ]
    img_url = random.choice(space_images)

    # 缓存每日知识
    cache_key = f"daily_knowledge_{today_str}"
    if cache_key not in st.session_state:
        st.session_state[cache_key] = None

    if st.session_state[cache_key] is None:
        prompt = f"""你是天文科普专家。请为今天（{today_str}）生成一条有趣的天文知识。
以JSON格式返回，严格按以下结构，不要加额外文字：
{{"title": "简短标题（10字内）", "explanation": "300-500字的科普说明，通俗易懂，内容准确"}}"""
        with st.spinner("🧠 AI 正在生成今日天文知识..."):
            try:
                raw = call_llm_api([], prompt)
                import json as _json
                resp = _json.loads(raw.strip())
                title = resp.get("title", "今日天文")
                explanation = resp.get("explanation", "暂无内容")
            except:
                title = "🌠 今日天文"
                explanation = "宇宙浩瀚无垠，每一天都有新的发现等待我们去探索。从恒星诞生到星系演化，天文学不断揭示着宇宙的奥秘。"
            st.session_state[cache_key] = {"title": title, "explanation": explanation}

    data = st.session_state[cache_key]

    # 展示
    st.markdown(f"""
    <div class="cosmo-card">
        <h3>💡 今日天文知识 — <span style="font-weight:600;">{data['title']}</span></h3>
        <p class="cosmo-subtitle">📅 {today_str}</p>
        <p style="font-size:1.1rem;line-height:1.8;">{data['explanation']}</p>
    </div>
    """, unsafe_allow_html=True)

    st.image(img_url, use_container_width=True, caption="✨ 深邃星空")

def quiz_challenge():
    """答题挑战馆模块"""
    st.markdown('<h1 class="cosmo-page-title">🚀 答题挑战馆</h1>', unsafe_allow_html=True)
    st.markdown('<p class="cosmo-page-subtitle">测试你的天文知识</p>', unsafe_allow_html=True)
    
    # 初始化会话状态
    if 'questions' not in st.session_state:
        st.session_state['questions'] = load_questions()
    
    if 'current_question' not in st.session_state:
        st.session_state['current_question'] = None
    
    if 'answer_history' not in st.session_state:
        st.session_state['answer_history'] = pd.DataFrame(columns=["timestamp", "question", "user_answer", "is_correct", "topic"])
    
    if 'last_question_id' not in st.session_state:
        st.session_state['last_question_id'] = -1
    if 'set_count' not in st.session_state:
        st.session_state['set_count'] = 0
    if 'set_complete' not in st.session_state:
        st.session_state['set_complete'] = False
    if 'topics_used_in_set' not in st.session_state:
        st.session_state['topics_used_in_set'] = []
    
    # 获取下一题（多维度均衡出题）
    def get_next_question():
        all_q = st.session_state['questions']
        all_topics = list(all_q['topic'].unique())
        used = st.session_state.get('topics_used_in_set', [])
        remaining = [t for t in all_topics if t not in used]
        target = random.choice(remaining) if remaining else random.choice(all_topics)
        pool = all_q[(all_q['topic'] == target) & (all_q['id'] != st.session_state['last_question_id'])]
        if pool.empty:
            pool = all_q[all_q['id'] != st.session_state['last_question_id']]
        q = pool.sample(n=1).iloc[0]
        used.append(target)
        st.session_state['topics_used_in_set'] = list(set(used))
        return q
    
    # 重置答题记录
    def reset_history():
        st.session_state['answer_history'] = pd.DataFrame(columns=["timestamp", "question", "user_answer", "is_correct", "topic"])
        st.session_state['last_question_id'] = -1
        st.session_state['current_question'] = None
        st.session_state['user_answer'] = None
        st.session_state['show_result'] = False
        st.session_state['set_count'] = 0
        st.session_state['set_complete'] = False
        st.session_state['topics_used_in_set'] = []
    
    # 如果已完成一组，显示总结
    if st.session_state['set_complete']:
        total = len(st.session_state['answer_history'])
        correct = st.session_state['answer_history']['is_correct'].sum()
        pct = correct / total * 100 if total > 0 else 0
        
        st.markdown(f"""
        <div class="cosmo-card" style="text-align:center;padding:2rem;">
            <div style="font-size:3rem;margin-bottom:0.5rem;">🏆</div>
            <h2>答题完成！</h2>
            <p style="font-size:1.1rem;margin:0.5rem 0;">
                共 <strong>{total}</strong> 题 · 正确 <strong>{correct}</strong> 题 · 正确率 <strong>{pct:.1f}%</strong>
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔄 开始新一组"):
            reset_history()
            st.rerun()
        return
    
    # 显示进度
    st.markdown(f'<div style="text-align:center;margin-bottom:0.5rem;color:rgba(255,255,255,0.6);font-size:0.85rem;">第 {st.session_state["set_count"] + 1}/10 题</div>', unsafe_allow_html=True)
    
    # 获取当前题目
    if st.session_state['current_question'] is None:
        st.session_state['current_question'] = get_next_question()
        st.session_state['show_result'] = False
        st.session_state['user_answer'] = None
    
    question = st.session_state['current_question']
    
    # 显示题目卡片
    card_class = "cosmo-card"
    if 'show_result' in st.session_state and st.session_state['show_result']:
        if st.session_state['is_correct']:
            card_class = "cosmo-card success-card"
        else:
            card_class = "cosmo-card error-card"
    
    st.markdown(f"""
    <div class="{card_class}">
        <h3>📝 问题：{question['question']}</h3>
        <p class="cosmo-subtitle">🏷️ 知识点：{question['topic']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 选项
    options = [
        f"A. {question['option_a']}",
        f"B. {question['option_b']}",
        f"C. {question['option_c']}",
        f"D. {question['option_d']}"
    ]
    
    user_answer = st.radio("选择你的答案：", options, index=None, key='quiz_answer')
    
    # 提交答案
    if st.button("✅ 提交答案"):
        if user_answer is None:
            st.warning("请先选择一个答案！")
        else:
            selected_option = user_answer[0]  # 获取A/B/C/D
            is_correct = selected_option == question['correct_answer']
            
            st.session_state['is_correct'] = is_correct
            st.session_state['show_result'] = True
            
            # 显示Toast提示
            if is_correct:
                st.toast("🎉 回答正确！", icon="✅")
            else:
                st.toast("😢 回答错误", icon="❌")
            
            # 记录答题历史
            new_record = pd.DataFrame({
                "timestamp": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                "question": [question['question']],
                "user_answer": [selected_option],
                "is_correct": [is_correct],
                "topic": [question['topic']]
            })
            st.session_state['answer_history'] = pd.concat([st.session_state['answer_history'], new_record], ignore_index=True)
            
            # 保存到CSV
            save_user_answer(question['question'], selected_option, is_correct, question['topic'])
            
            st.session_state['set_count'] += 1
    
    # 显示结果和解析
    if 'show_result' in st.session_state and st.session_state['show_result']:
        correct_answer_text = {
            'A': question['option_a'],
            'B': question['option_b'],
            'C': question['option_c'],
            'D': question['option_d']
        }
        
        st.markdown(f"""
        <div class="cosmo-card {'success-card' if st.session_state['is_correct'] else 'error-card'}">
            <h4>{"✅ 正确！" if st.session_state['is_correct'] else "❌ 错误！"}</h4>
            <p><strong>正确答案：</strong>{question['correct_answer']}. {correct_answer_text[question['correct_answer']]}</p>
            <p><strong>你的答案：</strong>{user_answer}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="cosmo-card">
            <h4>📚 解析</h4>
            <p>{question['explanation']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 下一题 / 完成按钮
        if st.button("🏁 完成答题" if st.session_state['set_count'] >= 10 else "➡️ 下一题"):
            if st.session_state['set_count'] >= 10:
                st.session_state['set_complete'] = True
            else:
                st.session_state['last_question_id'] = question['id']
                st.session_state['current_question'] = get_next_question()
                st.session_state['show_result'] = False
                st.session_state['user_answer'] = None
            st.rerun()

def data_analysis():
    """学习数据分析室模块"""
    st.markdown('<h1 class="cosmo-page-title">📊 学习数据分析室</h1>', unsafe_allow_html=True)
    st.markdown('<p class="cosmo-page-subtitle">分析你的学习进度和知识掌握情况</p>', unsafe_allow_html=True)
    
    # 加载历史数据
    history_df = load_user_history()
    
    if history_df.empty:
        st.markdown("""
        <div class="cosmo-card">
            <h3>📭 暂无答题记录</h3>
            <p>请先去「答题挑战馆」完成一些题目，回来查看分析结果！</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # 更新session_state
    st.session_state['answer_history'] = history_df
    
    # 统计数据
    total_answered = len(history_df)
    correct_count = history_df['is_correct'].sum()
    accuracy = (correct_count / total_answered * 100)
    
    # 大号数字卡片
    set_count = total_answered // 10
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📖 答题组数", set_count)
    with col2:
        st.metric("✏️ 累计答题数", total_answered)
    with col3:
        st.metric("🎯 总正确率", f"{accuracy:.1f}%")
    
    # 近10次答题正确率折线图（加粗线条+高饱和节点）
    st.subheader("📈 近10次答题趋势")
    recent_df = history_df.tail(10).copy().reset_index(drop=True)
    recent_df['quiz_num'] = recent_df.index + 1
    recent_df['correct_rate'] = recent_df['is_correct'].cumsum() / recent_df['quiz_num'] * 100
    recent_df['is_correct_str'] = recent_df['is_correct'].astype(str)
    recent_df['color_label'] = recent_df['is_correct_str'].map({'True': '正确', 'False': '错误'})
    
    base_line = alt.Chart(recent_df).encode(
        x=alt.X('quiz_num:Q', title='答题次数', axis=alt.Axis(labelFontSize=12, labelColor='rgba(255,255,255,0.7)', titleColor='rgba(255,255,255,0.9)', grid=False, domainColor='rgba(255,255,255,0.1)', tickColor='rgba(255,255,255,0.1)'))
    )
    line = base_line.mark_line(strokeWidth=4, color='#4A6CF7', smooth=False).encode(
        y=alt.Y('correct_rate:Q', title='正确率 (%)', scale=alt.Scale(domain=[0, 100]), axis=alt.Axis(labelFontSize=12, labelColor='rgba(255,255,255,0.7)', titleColor='rgba(255,255,255,0.9)', gridColor='rgba(255,255,255,0.06)', domainColor='rgba(255,255,255,0.1)', tickColor='rgba(255,255,255,0.1)'))
    )
    points = base_line.mark_point(size=160, filled=True, stroke='rgba(255,255,255,0.6)', strokeWidth=2.5).encode(
        y='correct_rate:Q',
        color=alt.Color('color_label:N',
            scale=alt.Scale(domain=['正确', '错误'], range=['#00E676', '#FF1744']),
            legend=alt.Legend(title='答题结果', orient='top-right', labelColor='rgba(255,255,255,0.7)', titleColor='rgba(255,255,255,0.9)')
        ),
        tooltip=['quiz_num', alt.Tooltip('correct_rate:Q', format='.1f'), 'color_label']
    )
    line_chart = (line + points).properties(
        height=400,
        background='transparent'
    ).configure_axis(
        grid=True, gridColor='rgba(255,255,255,0.06)'
    ).configure_view(strokeWidth=0)
    st.altair_chart(line_chart, use_container_width=True)
    
    # 各知识点正确率横向柱状图（多彩高饱和）
    st.subheader("📈 知识点掌握情况")
    all_topics = ["太阳系", "银河系", "恒星", "黑洞与天体物理", "天文探索", "月球", "宇宙学", "航天技术", "星座"]
    topic_stats = history_df.groupby('topic')['is_correct'].agg(['sum', 'count'])
    topic_stats['accuracy'] = (topic_stats['sum'] / topic_stats['count']) * 100
    topic_stats = topic_stats.reset_index()
    topic_df = pd.DataFrame({'topic': all_topics})
    topic_stats = topic_df.merge(topic_stats, on='topic', how='left')
    topic_stats[['sum', 'count']] = topic_stats[['sum', 'count']].fillna(0).astype(int)
    topic_stats['accuracy'] = topic_stats['accuracy'].fillna(0)
    topic_stats = topic_stats.sort_values('accuracy', ascending=True).reset_index(drop=True)
    
    space_colors = ['#FF6B6B', '#FF9F43', '#FECA57', '#48DBFB', '#0ABDE3',
                    '#A29BFE', '#FD79A8', '#00D2D3', '#6C5CE7', '#FDCB6E']
    colors = space_colors[:len(topic_stats)]
    
    bars = alt.Chart(topic_stats).mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4).encode(
        x=alt.X('accuracy:Q', title='正确率 (%)', scale=alt.Scale(domain=[0, 100]), axis=alt.Axis(labelFontSize=12, labelColor='rgba(255,255,255,0.7)', titleColor='rgba(255,255,255,0.9)', gridColor='rgba(255,255,255,0.06)', domainColor='rgba(255,255,255,0.1)', tickColor='rgba(255,255,255,0.1)')),
        y=alt.Y('topic:N', title=None, sort='-x', axis=alt.Axis(labelFontSize=13, labelColor='rgba(255,255,255,0.8)', grid=False, domainColor='rgba(255,255,255,0.1)', tickColor='rgba(255,255,255,0.1)')),
        color=alt.Color('topic:N', scale=alt.Scale(range=colors), legend=None),
        tooltip=['topic', alt.Tooltip('accuracy:Q', format='.1f')]
    )
    text = bars.mark_text(align='left', dx=5, fontSize=13, color='rgba(255,255,255,0.8)').encode(
        text=alt.Text('accuracy:Q', format='.1f')
    )
    bar_chart = (bars + text).properties(height=300, background='transparent').configure_axis(
        grid=True, gridColor='rgba(255,255,255,0.06)'
    ).configure_view(strokeWidth=0)
    st.altair_chart(bar_chart, use_container_width=True)
    
    # 所有知识点错题分布
    st.subheader("⚠️ 薄弱知识点（错题分布）")
    all_topics = ["太阳系", "银河系", "恒星", "黑洞与天体物理", "天文探索", "月球", "宇宙学", "航天技术", "星座"]
    wrong_counts = history_df[history_df['is_correct'] == False]['topic'].value_counts().reset_index()
    wrong_counts.columns = ['topic', '错题数']
    weak_topic_df = pd.DataFrame({'topic': all_topics})
    weak_topic_df = weak_topic_df.merge(wrong_counts, on='topic', how='left')
    weak_topic_df['错题数'] = weak_topic_df['错题数'].fillna(0).astype(int)
    weak_topic_df.columns = ['知识点', '错题数']
    weak_topic_df.index = range(1, len(weak_topic_df) + 1)
    st.table(weak_topic_df)
    
    # 答题时间分布（多彩柱状图）
    st.subheader("🕐 答题时间分布")
    history_df['hour'] = pd.to_datetime(history_df['timestamp']).dt.hour
    hour_df = history_df['hour'].value_counts().sort_index().reset_index()
    hour_df.columns = ['hour', 'count']
    
    hour_chart = alt.Chart(hour_df).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
        x=alt.X('hour:Q', title='小时', axis=alt.Axis(labelAngle=0, format='d', labelColor='rgba(255,255,255,0.7)', titleColor='rgba(255,255,255,0.9)', grid=False, domainColor='rgba(255,255,255,0.1)', tickColor='rgba(255,255,255,0.1)')),
        y=alt.Y('count:Q', title='答题数', axis=alt.Axis(labelColor='rgba(255,255,255,0.7)', titleColor='rgba(255,255,255,0.9)', gridColor='rgba(255,255,255,0.06)', domainColor='rgba(255,255,255,0.1)', tickColor='rgba(255,255,255,0.1)')),
        color=alt.Color('hour:Q', scale=alt.Scale(scheme='viridis'), legend=None),
        tooltip=['hour', 'count']
    ).properties(height=300, background='transparent').configure_axis(
        grid=True, gridColor='rgba(255,255,255,0.06)'
    ).configure_view(strokeWidth=0)
    st.altair_chart(hour_chart, use_container_width=True)

def ai_assistant():
    """天文AI助手模块 - DeepSeek风格对话"""
    st.markdown('<h1 class="cosmo-page-title">🤖 天文AI助手</h1>', unsafe_allow_html=True)

    # ===== 角色设定 =====
    personas = {
        "🔬 科学老师": {
            "prompt": "你是一名耐心且富有热情的天文科学老师。用通俗易懂的方式讲解天文知识，善用类比和生活中的例子，多鼓励提问。回答应当准确、结构清晰。",
            "greeting": "同学你好！我是你的天文科学老师 🌟\n有什么关于宇宙的好奇问题，尽管问我吧！"
        },
        "🔭 天文学家": {
            "prompt": "你是一名严谨专业的天文学家，擅长用数据和科学事实回答问题。回答要基于已有的天文研究成果，适当引用观测数据或理论，语言专业但不失亲切。",
            "greeting": "您好，我是专业天文学家 🔭\n很高兴与您探讨宇宙的奥秘，有什么科学问题吗？"
        },
        "🌠 天文科普家": {
            "prompt": "你是一名充满热情的天文科普作家，擅长用生动有趣的方式传播天文知识。回答要引人入胜，穿插有趣的天文事实和冷知识，让每个人都能感受到宇宙的魅力。",
            "greeting": "嗨！我是你的宇宙导游 🌠\n准备好探索奇妙的宇宙了吗？让我们一起出发！"
        },
        "🏛️ 古代占星师": {
            "prompt": "你是一名来自古代的占星师，用诗意和哲思的语言解读星象。将现代天文学知识与古代占星术的神秘感结合，回答时多用比喻、典故和富有韵律的语言。",
            "greeting": "星垂平野，月涌大江 🌙\n吾乃观星之人，愿与君共话苍穹之秘。"
        },
        "🚀 科幻作家": {
            "prompt": "你是一名脑洞大开的科幻作家，擅长将天文知识与科幻想象结合。回答要有创意和画面感，可以适当畅想未来的太空文明、星际旅行等，但要在科学事实基础上展开想象。",
            "greeting": "准备好开启星际穿越了吗？🚀\n我是你的科幻向导，一起畅想宇宙的无限可能！"
        }
    }

    # ===== 初始化 =====
    if 'chat_history' not in st.session_state:
        st.session_state['chat_history'] = []
    if 'ai_persona' not in st.session_state:
        st.session_state['ai_persona'] = "🔬 科学老师"
    if 'chat_df' not in st.session_state:
        st.session_state['chat_df'] = pd.DataFrame(columns=['timestamp', 'user_message', 'ai_response'])

    # ===== 风格选择 + 操作按钮 =====
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown('<p style="font-size:0.8rem;color:rgba(255,255,255,0.55);margin-bottom:0.2rem;">🎭 AI 人格</p>', unsafe_allow_html=True)
        selected_persona = st.selectbox(
            "", list(personas.keys()),
            index=list(personas.keys()).index(st.session_state['ai_persona']),
            key='persona_select',
            label_visibility="collapsed"
        )
        if selected_persona != st.session_state['ai_persona']:
            st.session_state['ai_persona'] = selected_persona
    with col2:
        st.markdown('<div style="margin-top:1.5rem;">', unsafe_allow_html=True)
        if st.button("🗑️ 新对话", use_container_width=True):
            st.session_state['chat_history'] = []
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # ===== 聊天区域 =====
    chat_container = st.container()
    with chat_container:
        if not st.session_state['chat_history']:
            st.markdown(f"""
            <div class="welcome-card">
                <div class="icon">{selected_persona.split()[0]}</div>
                <h3>{selected_persona} 已上线</h3>
                <p>{personas[selected_persona]['greeting']}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown('<div class="chat-scroll-area">', unsafe_allow_html=True)
            for msg in st.session_state['chat_history']:
                if msg['role'] == 'user':
                    st.markdown(f"""
                    <div class="user-row">
                        <div class="user-bubble">{msg['content']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="ai-row">
                        <div class="ai-avatar">{selected_persona.split()[0]}</div>
                        <div class="ai-bubble">{msg['content']}</div>
                    </div>
                    """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    # ===== 输入区域 =====
    st.markdown('<hr class="chat-divider">', unsafe_allow_html=True)
    col_inp, col_btn = st.columns([5, 1])
    with col_inp:
        user_input = st.text_input("", placeholder=f"输入你的天文问题...", label_visibility="collapsed", key='ai_input')
    with col_btn:
        send_clicked = st.button("📤 发送", use_container_width=True, type="primary")

    if send_clicked and user_input.strip():
        st.session_state['chat_history'].append({'role': 'user', 'content': user_input.strip()})

        # 获取AI回复（传入完整对话历史 + 人格设定）
        with st.spinner(f"{selected_persona.split()[0]} 思考中..."):
            system_prompt = personas[selected_persona]['prompt']
            ai_response = call_llm_api(st.session_state['chat_history'], system_prompt)

        st.session_state['chat_history'].append({'role': 'assistant', 'content': ai_response})

        # 记录到DataFrame
        new_record = pd.DataFrame({
            'timestamp': [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            'user_message': [user_input],
            'ai_response': [ai_response]
        })
        st.session_state['chat_df'] = pd.concat([st.session_state['chat_df'], new_record], ignore_index=True)
        st.rerun()

    # ===== 导出聊天记录 =====
    if not st.session_state['chat_df'].empty:
        csv_data = st.session_state['chat_df'].to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 导出聊天记录",
            data=csv_data,
            file_name='cosmolearn_chat_history.csv',
            mime='text/csv'
        )


def call_llm_api(chat_history, system_prompt):
    """调用DeepSeek API（支持完整对话上下文）"""
    if not DEEPSEEK_API_KEY:
        return "抱歉，AI服务暂时不可用，请稍后再试。建议查阅NASA官网。"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }

    messages = [{"role": "system", "content": system_prompt}]
    for msg in chat_history:
        messages.append({"role": msg['role'], "content": msg['content']})

    data = {
        "model": LLM_MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 2048
    }

    try:
        response = requests.post(LLM_API_URL, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        return f"抱歉，AI服务暂时不可用。错误信息: {str(e)}"

# ==================== 登录注册页 ====================

def show_auth_page():
    """显示登录/注册页面"""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="text-align:center;margin:2rem 0 1.5rem;">
            <div style="font-size:4rem;margin-bottom:0.5rem;">🌌</div>
            <h1 style="font-size:2rem;text-align:center;background:linear-gradient(135deg,#60a5fa,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">星空学堂</h1>
            <p style="color:rgba(255,255,255,0.5);font-size:0.9rem;text-align:center;">探索宇宙的奥秘</p>
        </div>
        """, unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["🔑 登录", "📝 注册"])
        
        with tab1:
            with st.form("login_form"):
                u = st.text_input("用户名", key="login_user")
                p = st.text_input("密码", type="password", key="login_pass")
                if st.form_submit_button("🔑 登录", use_container_width=True):
                    ok, msg = login_user(u, p)
                    if ok:
                        st.session_state['user'] = u
                        st.rerun()
                    else:
                        st.error(msg)
        
        with tab2:
            with st.form("register_form"):
                u = st.text_input("用户名", key="reg_user")
                p = st.text_input("密码", type="password", key="reg_pass")
                p2 = st.text_input("确认密码", type="password", key="reg_pass2")
                if st.form_submit_button("📝 注册", use_container_width=True):
                    if p != p2:
                        st.error("两次输入的密码不一致")
                    else:
                        ok, msg = register_user(u, p)
                        if ok:
                            st.success("注册成功！请切换到登录页登录")
                        else:
                            st.error(msg)

def astronomy_query():
    """天文数据查询页面"""
    st.markdown('<h1 class="cosmo-page-title">🌤️ 天文数据查询</h1>', unsafe_allow_html=True)
    st.markdown('<p class="cosmo-page-subtitle">查询任意地点的日出日落、月相月照、金色与蓝色时刻</p>', unsafe_allow_html=True)

    loc_mode = st.radio("查询方式", ["城市名称", "经纬度"], label_visibility="collapsed", key="astro_mode", horizontal=True)
    loc_val = None; lat_val = None; lon_val = None
    if loc_mode == "城市名称":
        loc_val = st.text_input("输入城市名（如 Beijing、Tokyo）", placeholder="城市英文名", label_visibility="collapsed", key="astro_city")
    else:
        c1, c2 = st.columns(2)
        with c1: lat_val = st.text_input("纬度", placeholder="39.9042", label_visibility="collapsed", key="astro_lat")
        with c2: lon_val = st.text_input("经度", placeholder="116.4074", label_visibility="collapsed", key="astro_lon")

    if st.button("🔍 查询天文数据", use_container_width=True, key="astro_btn"):
        if loc_val:
            data = get_astronomy_data(location=loc_val)
        elif lat_val and lon_val:
            try:
                data = get_astronomy_data(lat=float(lat_val), long=float(lon_val))
            except:
                st.error("经纬度格式有误，请输入数字")
                data = None
        else:
            st.info("请输入城市名称或经纬度")
            data = None

        if data:
            sunrise = parse_time(data.get("sunrise", ""))
            sunset = parse_time(data.get("sunset", ""))
            civ_begin = parse_time(data.get("civil_twilight_begin", ""))
            civ_end = parse_time(data.get("civil_twilight_end", ""))
            if not civ_begin and sunrise:
                civ_begin = add_min(sunrise, -30)
            if not civ_end and sunset:
                civ_end = add_min(sunset, 30)
            day_len = data.get("day_length", "")
            moon_phase = data.get("moon_phase", "")
            moon_ill = data.get("moon_illumination_percentage", "")
            loc_name = data.get("location", {}).get("city", loc_val or f"{lat_val},{lon_val}")

            gh_m_start = add_min(sunrise, -25) if sunrise else None
            gh_m_end = add_min(sunrise, 35) if sunrise else None
            gh_e_start = add_min(sunset, -35) if sunset else None
            gh_e_end = add_min(sunset, 25) if sunset else None
            bh_m_start = civ_begin
            bh_m_end = sunrise
            bh_e_start = sunset
            bh_e_end = civ_end

            st.markdown(f"""
            <div style="background:rgba(74,108,247,0.15);backdrop-filter:blur(8px);border-radius:14px;border:1px solid rgba(255,255,255,0.08);padding:1.2rem 1.5rem;margin-top:0.6rem;">
                <div style="font-size:0.95rem;color:rgba(255,255,255,0.9);line-height:2;">
                    <div style="font-size:1.2rem;font-weight:700;margin-bottom:0.5rem;">📍 {loc_name}</div>
                    <div>🌅 日出：<strong>{fmt_t(sunrise) if sunrise else '--'}</strong></div>
                    <div>🌇 日落：<strong>{fmt_t(sunset) if sunset else '--'}</strong></div>
                    <div>⏳ 昼长：<strong>{day_len}</strong></div>
                    <hr style="border-color:rgba(255,255,255,0.08);margin:0.3rem 0;">
                    <div>🌙 月相：<strong>{moon_phase}</strong>（{moon_ill}%）</div>
                    <hr style="border-color:rgba(255,255,255,0.08);margin:0.3rem 0;">
                    <div>🌆 民用晨光始：<strong>{fmt_t(civ_begin) if civ_begin else '--'}</strong></div>
                    <div>🌆 民用昏影终：<strong>{fmt_t(civ_end) if civ_end else '--'}</strong></div>
                    <hr style="border-color:rgba(255,255,255,0.08);margin:0.3rem 0;">
                    <div>✨ 金色时刻（晨）：<strong>{fmt_t(gh_m_start) if gh_m_start else '--'} ~ {fmt_t(gh_m_end) if gh_m_end else '--'}</strong></div>
                    <div>✨ 金色时刻（昏）：<strong>{fmt_t(gh_e_start) if gh_e_start else '--'} ~ {fmt_t(gh_e_end) if gh_e_end else '--'}</strong></div>
                    <div>🔵 蓝色时刻（晨）：<strong>{fmt_t(bh_m_start) if bh_m_start else '--'} ~ {fmt_t(bh_m_end) if bh_m_end else '--'}</strong></div>
                    <div>🔵 蓝色时刻（昏）：<strong>{fmt_t(bh_e_start) if bh_e_start else '--'} ~ {fmt_t(bh_e_end) if bh_e_end else '--'}</strong></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ==================== 主函数 ====================

def main():
    # 应用配置
    st.set_page_config(
        page_title="星空学堂 - 宇宙天文科普",
        page_icon="🌌",
        layout="wide"
    )
    
    # 应用全局CSS
    apply_global_css()
    
    # 未登录 → 显示登录页
    if 'user' not in st.session_state:
        show_auth_page()
        return
    
    # 侧边栏
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-logo">
            <div class="logo-icon-wrap">
                <div class="glow-ring"></div>
                <span class="icon">🌌</span>
            </div>
            <h1>星空学堂</h1>
            <p class="sub">✦ 探索宇宙的奥秘 ✦</p>
            <p class="deco-stars">· · · · ·</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 用户信息
        st.markdown(f'<div style="font-size:1.1rem;font-weight:700;margin-bottom:0.4rem;padding-left:0.2rem;">👤 {st.session_state["user"]}</div>', unsafe_allow_html=True)
        
        # 菜单选项
        menu_options = ["每日天文", "天文数据查询", "答题挑战", "学习数据分析", "天文AI助手"]
        selected_page = st.radio("导航", menu_options, label_visibility="collapsed")
        
        # 退出按钮
        if st.button("🚪 退出登录", use_container_width=True):
            del st.session_state['user']
            for k in ['chat_history', 'answer_history', 'apod_fetch_done', 'apod_cache']:
                st.session_state.pop(k, None)
            st.rerun()
        
        # 实时统计
        st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)
        st.markdown("### 📈 实时统计")
        
        # 读取历史数据用于统计
        history_df = load_user_history()
        total_answered = len(history_df)
        correct_count = history_df['is_correct'].sum() if not history_df.empty else 0
        accuracy = (correct_count / total_answered * 100) if total_answered > 0 else 0
        
        st.markdown(f"""
        <div class="sidebar-stats">
            <p>✏️ 总答题数: <strong>{total_answered}</strong></p>
            <p>✅ 正确数: <strong>{correct_count}</strong></p>
            <p>🎯 正确率: <strong>{accuracy:.1f}%</strong></p>
        </div>
        """, unsafe_allow_html=True)
    
    # 根据选择显示不同页面
    if selected_page == "每日天文":
        daily_apod()
    elif selected_page == "天文数据查询":
        astronomy_query()
    elif selected_page == "答题挑战":
        quiz_challenge()
    elif selected_page == "学习数据分析":
        data_analysis()
    elif selected_page == "天文AI助手":
        ai_assistant()

if __name__ == "__main__":
    main()