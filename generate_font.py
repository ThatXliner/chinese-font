#!/usr/bin/env python3
"""Generate a Chinese literal-meaning font where characters are replaced by English glosses."""

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont
import math

# Character to English gloss mapping (~1000 common characters)
CHAR_GLOSSES = {
    # Basic radicals and elements
    "人": "person", "山": "mountain", "火": "fire", "水": "water", "日": "sun",
    "月": "moon", "木": "tree", "口": "mouth", "手": "hand", "心": "heart",
    "一": "one", "二": "two", "三": "three", "四": "four", "五": "five",
    "六": "six", "七": "seven", "八": "eight", "九": "nine", "十": "ten",
    "百": "hundred", "千": "thousand", "万": "ten thousand", "亿": "hundred million",
    # Nature
    "天": "sky", "地": "earth", "风": "wind", "雨": "rain", "云": "cloud",
    "雪": "snow", "石": "stone", "金": "gold", "土": "soil", "草": "grass",
    "花": "flower", "树": "tree", "林": "forest", "森": "woods", "河": "river",
    "江": "river", "湖": "lake", "海": "sea", "洋": "ocean", "岛": "island",
    "星": "star", "阳": "sun", "阴": "shade", "光": "light", "暗": "dark",
    "热": "hot", "冷": "cold", "温": "warm", "凉": "cool", "冰": "ice",
    "沙": "sand", "泥": "mud", "岩": "rock", "峰": "peak", "谷": "valley",
    "田": "field", "野": "wild", "园": "garden", "池": "pond", "泉": "spring",
    "雷": "thunder", "电": "lightning", "虹": "rainbow", "霜": "frost", "露": "dew",
    "雾": "fog", "霞": "rosy clouds", "晴": "clear", "阵": "burst",
    # Body parts
    "目": "eye", "耳": "ear", "鼻": "nose", "足": "foot", "头": "head",
    "身": "body", "骨": "bone", "血": "blood", "肉": "flesh", "皮": "skin",
    "脸": "face", "眼": "eye", "嘴": "mouth", "唇": "lip", "舌": "tongue",
    "牙": "tooth", "齿": "teeth", "发": "hair", "毛": "fur", "指": "finger",
    "腿": "leg", "臂": "arm", "肩": "shoulder", "背": "back", "腰": "waist",
    "胸": "chest", "腹": "belly", "脑": "brain", "肝": "liver", "肺": "lung",
    "胃": "stomach", "肠": "intestine", "脾": "spleen", "肾": "kidney", "胆": "gallbladder",
    "筋": "tendon", "脉": "vein", "膀": "bladder", "颈": "neck", "喉": "throat",
    # Animals
    "鸟": "bird", "鱼": "fish", "马": "horse", "牛": "cow", "羊": "sheep",
    "虫": "insect", "狗": "dog", "猫": "cat", "龙": "dragon", "虎": "tiger",
    "蛇": "snake", "兔": "rabbit", "鼠": "rat", "猪": "pig", "鸡": "chicken",
    "鸭": "duck", "鹅": "goose", "狼": "wolf", "熊": "bear", "狮": "lion",
    "象": "elephant", "猴": "monkey", "蜂": "bee", "蝶": "butterfly", "蚁": "ant",
    "蚊": "mosquito", "蝇": "fly", "蜘": "spider", "蛛": "spider", "蟹": "crab",
    "虾": "shrimp", "贝": "shell", "蛙": "frog", "龟": "turtle", "鹰": "eagle",
    "雀": "sparrow", "燕": "swallow", "鸽": "pigeon", "鹤": "crane", "凤": "phoenix",
    "麟": "unicorn", "驴": "donkey", "骡": "mule", "骆": "camel", "驼": "camel",
    "豹": "leopard", "鹿": "deer", "兽": "beast", "禽": "fowl", "畜": "livestock",
    # Actions/Verbs
    "走": "walk", "跑": "run", "看": "look", "听": "listen", "说": "speak",
    "写": "write", "读": "read", "吃": "eat", "喝": "drink", "睡": "sleep",
    "坐": "sit", "站": "stand", "躺": "lie down", "跳": "jump", "飞": "fly",
    "游": "swim", "爬": "climb", "打": "hit", "拿": "take", "放": "put",
    "给": "give", "送": "send", "买": "buy", "卖": "sell", "找": "find",
    "用": "use", "做": "do", "作": "make", "造": "create", "建": "build",
    "开": "open", "关": "close", "进": "enter", "出": "exit", "来": "come",
    "去": "go", "回": "return", "过": "pass", "起": "rise", "落": "fall",
    "升": "ascend", "降": "descend", "停": "stop", "动": "move", "静": "still",
    "变": "change", "换": "exchange", "转": "turn", "摇": "shake", "推": "push",
    "拉": "pull", "扔": "throw", "接": "catch", "抱": "hug", "握": "grasp",
    "抓": "grab", "捉": "capture", "挖": "dig", "切": "cut", "割": "slice",
    "砍": "chop", "杀": "kill", "死": "die", "活": "live", "救": "save",
    "帮": "help", "助": "assist", "教": "teach", "学": "learn", "练": "practice",
    "试": "try", "考": "test", "答": "answer", "问": "ask", "想": "think",
    "知": "know", "懂": "understand", "记": "remember", "忘": "forget", "感": "feel",
    "爱": "love", "恨": "hate", "怕": "fear", "喜": "like", "乐": "joy",
    "哭": "cry", "笑": "laugh", "怒": "anger", "惊": "surprise", "悲": "sorrow",
    "忧": "worry", "愁": "melancholy", "烦": "annoyed", "急": "urgent", "慌": "panic",
    "洗": "wash", "擦": "wipe", "扫": "sweep", "刷": "brush", "涂": "smear",
    "画": "draw", "唱": "sing", "跳": "dance", "玩": "play", "演": "perform",
    "穿": "wear", "脱": "remove", "戴": "wear", "系": "tie", "解": "untie",
    "修": "repair", "补": "mend", "装": "install", "拆": "dismantle", "组": "assemble",
    "收": "collect", "发": "send", "寄": "mail", "传": "transmit", "递": "deliver",
    "借": "borrow", "还": "return", "租": "rent", "存": "store", "取": "withdraw",
    "数": "count", "算": "calculate", "量": "measure", "称": "weigh", "比": "compare",
    # Objects
    "门": "door", "窗": "window", "车": "vehicle", "船": "boat", "书": "book",
    "笔": "pen", "刀": "knife", "衣": "clothes", "食": "food", "酒": "wine",
    "桌": "table", "椅": "chair", "床": "bed", "柜": "cabinet", "架": "shelf",
    "灯": "lamp", "钟": "clock", "表": "watch", "镜": "mirror", "画": "painting",
    "碗": "bowl", "盘": "plate", "杯": "cup", "壶": "pot", "瓶": "bottle",
    "锅": "pan", "勺": "spoon", "筷": "chopstick", "叉": "fork", "盆": "basin",
    "桶": "bucket", "袋": "bag", "箱": "box", "盒": "case", "包": "package",
    "伞": "umbrella", "扇": "fan", "帽": "hat", "鞋": "shoe", "袜": "sock",
    "裤": "pants", "裙": "skirt", "衫": "shirt", "褂": "jacket", "袍": "robe",
    "被": "quilt", "枕": "pillow", "毯": "blanket", "席": "mat", "帘": "curtain",
    "绳": "rope", "线": "thread", "针": "needle", "布": "cloth", "纸": "paper",
    "墨": "ink", "砚": "inkstone", "尺": "ruler", "剪": "scissors", "梳": "comb",
    "钥": "key", "锁": "lock", "链": "chain", "环": "ring", "钉": "nail",
    "锤": "hammer", "斧": "axe", "锯": "saw", "钻": "drill", "铲": "shovel",
    "犁": "plow", "耙": "rake", "镰": "sickle", "锄": "hoe", "网": "net",
    "枪": "gun", "炮": "cannon", "弓": "bow", "箭": "arrow", "盾": "shield",
    "剑": "sword", "矛": "spear", "戟": "halberd", "鞭": "whip", "棍": "stick",
    "琴": "zither", "棋": "chess", "鼓": "drum", "笛": "flute", "钢": "steel",
    "铁": "iron", "铜": "copper", "银": "silver", "玉": "jade", "珠": "pearl",
    "宝": "treasure", "币": "coin", "钱": "money", "票": "ticket", "证": "certificate",
    # Abstract concepts
    "大": "big", "小": "small", "上": "up", "下": "down", "左": "left",
    "右": "right", "中": "middle", "内": "inside", "外": "outside", "前": "front",
    "后": "back", "高": "high", "低": "low", "长": "long", "短": "short",
    "宽": "wide", "窄": "narrow", "厚": "thick", "薄": "thin", "深": "deep",
    "浅": "shallow", "远": "far", "近": "near", "快": "fast", "慢": "slow",
    "早": "early", "晚": "late", "新": "new", "旧": "old", "老": "aged",
    "少": "few", "多": "many", "全": "all", "半": "half", "双": "pair",
    "单": "single", "空": "empty", "满": "full", "轻": "light", "重": "heavy",
    "软": "soft", "硬": "hard", "干": "dry", "湿": "wet", "脏": "dirty",
    "净": "clean", "美": "beautiful", "丑": "ugly", "真": "true", "假": "false",
    "对": "correct", "错": "wrong", "好": "good", "坏": "bad", "善": "kind",
    "恶": "evil", "正": "upright", "邪": "crooked", "明": "bright", "黑": "black",
    "白": "white", "红": "red", "黄": "yellow", "蓝": "blue", "绿": "green",
    "紫": "purple", "橙": "orange", "粉": "pink", "灰": "gray", "棕": "brown",
    "色": "color", "彩": "colorful", "形": "shape", "状": "state", "态": "manner",
    "度": "degree", "量": "amount", "质": "quality", "性": "nature", "理": "reason",
    "道": "way", "法": "law", "术": "technique", "艺": "art", "能": "ability",
    "力": "power", "气": "air", "神": "spirit", "魂": "soul", "意": "meaning",
    "志": "will", "情": "emotion", "欲": "desire", "念": "thought", "智": "wisdom",
    "慧": "intelligence", "勇": "brave", "仁": "benevolence", "义": "righteousness", "礼": "courtesy",
    "信": "trust", "忠": "loyalty", "孝": "filial", "悌": "fraternal", "廉": "integrity",
    "耻": "shame", "德": "virtue", "才": "talent", "命": "fate", "运": "luck",
    "福": "blessing", "祸": "disaster", "吉": "auspicious", "凶": "ominous", "安": "peace",
    "危": "danger", "难": "difficult", "易": "easy", "苦": "bitter", "甜": "sweet",
    "酸": "sour", "辣": "spicy", "咸": "salty", "淡": "bland", "香": "fragrant",
    "臭": "stinky", "声": "sound", "音": "tone", "响": "loud", "静": "quiet",
    # Time
    "年": "year", "月": "month", "日": "day", "时": "hour", "分": "minute",
    "秒": "second", "春": "spring", "夏": "summer", "秋": "autumn", "冬": "winter",
    "今": "now", "古": "ancient", "昔": "past", "未": "not yet", "已": "already",
    "曾": "once", "将": "will", "永": "forever", "久": "long time", "暂": "temporary",
    "常": "often", "偶": "occasionally", "初": "first", "末": "end", "始": "begin",
    "终": "final", "继": "continue", "续": "continue", "断": "break", "连": "connect",
    "周": "week", "旬": "ten days", "季": "season", "岁": "age", "代": "generation",
    "纪": "era", "世": "world", "期": "period", "段": "section", "际": "boundary",
    # Places
    "话": "speech", "图": "picture", "馆": "hall", "本": "origin", "文": "writing",
    "北": "north", "南": "south", "东": "east", "西": "west", "京": "capital",
    "国": "country", "省": "province", "市": "city", "县": "county", "村": "village",
    "镇": "town", "区": "district", "街": "street", "路": "road", "巷": "alley",
    "桥": "bridge", "塔": "tower", "楼": "building", "房": "room", "厅": "hall",
    "院": "courtyard", "宫": "palace", "庙": "temple", "寺": "monastery", "堂": "hall",
    "店": "shop", "厂": "factory", "场": "field", "站": "station", "港": "harbor",
    "机": "machine", "所": "place", "处": "location", "址": "address", "境": "border",
    "域": "domain", "界": "boundary", "洲": "continent", "州": "state", "邦": "nation",
    # People and relationships
    "男": "male", "女": "female", "子": "child", "父": "father", "母": "mother",
    "家": "home", "朋": "friend", "友": "companion", "兄": "elder brother", "弟": "younger brother",
    "姐": "elder sister", "妹": "younger sister", "夫": "husband", "妻": "wife", "婚": "marriage",
    "亲": "relative", "戚": "kin", "祖": "ancestor", "孙": "grandchild", "侄": "nephew",
    "叔": "uncle", "姑": "aunt", "舅": "uncle", "姨": "aunt", "婆": "grandmother",
    "公": "grandfather", "翁": "old man", "媳": "daughter-in-law", "婿": "son-in-law", "嫂": "sister-in-law",
    "王": "king", "皇": "emperor", "帝": "emperor", "后": "queen", "臣": "minister",
    "官": "official", "吏": "clerk", "将": "general", "兵": "soldier", "士": "scholar",
    "民": "people", "众": "crowd", "群": "group", "族": "clan", "党": "party",
    "师": "teacher", "徒": "apprentice", "生": "student", "童": "child", "婴": "infant",
    "幼": "young", "少": "youth", "青": "green/youth", "壮": "robust", "老": "old",
    "翁": "elderly", "妇": "woman", "媪": "old woman", "奴": "slave", "仆": "servant",
    "主": "master", "客": "guest", "宾": "visitor", "邻": "neighbor", "伴": "companion",
    "侣": "mate", "敌": "enemy", "仇": "foe", "友": "friend", "盟": "ally",
    # Food and drink
    "米": "rice", "麦": "wheat", "豆": "bean", "菜": "vegetable", "果": "fruit",
    "瓜": "melon", "茶": "tea", "糖": "sugar", "盐": "salt", "酱": "sauce",
    "醋": "vinegar", "油": "oil", "蛋": "egg", "奶": "milk", "肉": "meat",
    "饭": "meal", "面": "noodle", "粥": "porridge", "饼": "cake", "糕": "pastry",
    "汤": "soup", "羹": "thick soup", "馒": "bun", "饺": "dumpling", "包": "bun",
    "酒": "wine", "啤": "beer", "烟": "smoke", "药": "medicine", "毒": "poison",
    # Buildings and structures
    "墙": "wall", "顶": "roof", "底": "bottom", "角": "corner", "边": "side",
    "梯": "ladder", "阶": "stairs", "坛": "altar", "台": "platform", "亭": "pavilion",
    "廊": "corridor", "厦": "mansion", "府": "mansion", "宅": "residence", "舍": "house",
    "室": "room", "屋": "house", "棚": "shed", "仓": "warehouse", "库": "storehouse",
    "井": "well", "坑": "pit", "沟": "ditch", "渠": "canal", "堤": "dam",
    "坝": "dam", "塘": "pond", "窖": "cellar", "洞": "cave", "穴": "hole",
    # Education and knowledge
    "校": "school", "班": "class", "课": "lesson", "题": "topic", "卷": "scroll",
    "章": "chapter", "节": "section", "篇": "article", "句": "sentence", "词": "word",
    "字": "character", "语": "language", "言": "speech", "论": "theory", "说": "explain",
    "讲": "lecture", "谈": "talk", "议": "discuss", "辩": "debate", "释": "explain",
    "注": "annotate", "评": "comment", "批": "criticize", "审": "examine", "验": "verify",
    "究": "research", "探": "explore", "索": "search", "查": "check", "搜": "search",
    "寻": "seek", "觅": "look for", "察": "observe", "视": "view", "望": "gaze",
    "瞧": "look", "瞪": "stare", "眺": "overlook", "窥": "peek", "监": "supervise",
    # Work and occupation
    "工": "work", "农": "farmer", "商": "merchant", "医": "doctor", "护": "nurse",
    "警": "police", "军": "army", "政": "politics", "经": "economy", "贸": "trade",
    "业": "industry", "企": "enterprise", "司": "company", "行": "profession", "职": "job",
    "务": "affair", "任": "duty", "责": "responsibility", "权": "authority", "利": "profit",
    "益": "benefit", "损": "loss", "亏": "deficit", "盈": "surplus", "赚": "earn",
    "赔": "compensate", "欠": "owe", "债": "debt", "贷": "loan", "税": "tax",
    "费": "fee", "价": "price", "值": "value", "廉": "cheap", "贵": "expensive",
    # Communication
    "报": "newspaper", "刊": "publication", "杂": "magazine", "志": "magazine", "稿": "manuscript",
    "版": "edition", "印": "print", "刻": "engrave", "摄": "photograph", "影": "shadow",
    "像": "image", "照": "photo", "拍": "shoot", "录": "record", "播": "broadcast",
    "映": "reflect", "显": "display", "示": "show", "告": "tell", "知": "inform",
    "晓": "dawn", "悉": "know", "闻": "hear", "睹": "witness", "见": "see",
    # Technology
    "科": "science", "技": "skill", "术": "art", "算": "calculate", "计": "count",
    "程": "procedure", "码": "code", "网": "net", "络": "connect", "联": "unite",
    "互": "mutual", "通": "through", "讯": "message", "息": "news", "据": "data",
    "库": "storage", "存": "save", "档": "file", "件": "piece", "软": "soft",
    "硬": "hard", "盘": "disk", "屏": "screen", "键": "key", "鼠": "mouse",
    # More verbs
    "带": "bring", "领": "lead", "引": "guide", "导": "direct", "率": "lead",
    "管": "manage", "控": "control", "制": "control", "限": "limit", "禁": "forbid",
    "许": "permit", "准": "allow", "批": "approve", "赞": "praise", "反": "oppose",
    "抗": "resist", "争": "fight", "战": "battle", "攻": "attack", "守": "defend",
    "退": "retreat", "追": "chase", "逃": "flee", "藏": "hide", "躲": "dodge",
    "避": "avoid", "挡": "block", "护": "protect", "卫": "guard", "保": "preserve",
    "持": "hold", "维": "maintain", "养": "nourish", "育": "nurture", "培": "cultivate",
    "植": "plant", "种": "plant", "播": "sow", "收": "harvest", "割": "reap",
    "采": "pick", "摘": "pluck", "捡": "pick up", "拾": "collect", "聚": "gather",
    "散": "scatter", "分": "divide", "合": "combine", "并": "merge", "混": "mix",
    "融": "melt", "溶": "dissolve", "化": "transform", "成": "become", "为": "be",
    "是": "is", "非": "not", "有": "have", "无": "none", "在": "at",
    "存": "exist", "亡": "perish", "灭": "extinguish", "消": "disappear", "失": "lose",
    "得": "get", "获": "obtain", "赢": "win", "败": "lose", "胜": "victory",
    # Particles and common words
    "的": "of", "了": "(past)", "和": "and", "与": "with", "或": "or",
    "而": "and", "但": "but", "却": "yet", "则": "then", "若": "if",
    "如": "like", "虽": "although", "因": "because", "所": "that which", "以": "by",
    "于": "at", "从": "from", "向": "toward", "到": "arrive", "往": "go",
    "由": "from", "经": "through", "过": "pass", "被": "by", "把": "hold",
    "将": "will", "会": "can", "能": "able", "可": "may", "要": "want",
    "需": "need", "必": "must", "应": "should", "该": "ought", "须": "must",
    "很": "very", "太": "too", "最": "most", "更": "more", "越": "exceed",
    "极": "extreme", "甚": "very", "颇": "quite", "稍": "slightly", "略": "brief",
    "这": "this", "那": "that", "哪": "which", "什": "what", "么": "(suffix)",
    "谁": "who", "何": "what", "怎": "how", "为": "why", "几": "how many",
    "每": "every", "各": "each", "某": "certain", "另": "another", "别": "other",
    "自": "self", "己": "self", "我": "I", "你": "you", "他": "he",
    "她": "she", "它": "it", "们": "(plural)", "咱": "we", "您": "you(polite)",
    # Additional common characters
    "事": "matter", "物": "thing", "品": "product", "具": "tool", "器": "utensil",
    "材": "material", "料": "material", "源": "source", "根": "root", "本": "origin",
    "基": "foundation", "础": "base", "端": "end", "首": "head", "尾": "tail",
    "始": "begin", "末": "end", "点": "point", "线": "line", "面": "surface",
    "体": "body", "块": "piece", "片": "slice", "条": "strip", "根": "root",
    "只": "only", "个": "piece", "位": "position", "名": "name", "号": "number",
    "级": "level", "等": "class", "类": "type", "种": "kind", "样": "manner",
    "式": "style", "型": "model", "版": "version", "期": "issue", "届": "session",
    "次": "time", "回": "time", "遍": "time", "番": "time", "场": "occasion",
    "阵": "period", "顿": "meal", "套": "set", "副": "pair", "批": "batch",
    "层": "layer", "排": "row", "列": "column", "组": "group", "队": "team",
    "伙": "group", "帮": "gang", "班": "class", "团": "group", "社": "society",
    "会": "meeting", "盟": "league", "派": "faction", "系": "system", "门": "school",
    "派": "school", "宗": "sect", "教": "religion", "道": "way", "佛": "Buddha",
    "神": "god", "鬼": "ghost", "仙": "immortal", "妖": "demon", "魔": "devil",
    "灵": "spirit", "怪": "strange", "异": "different", "奇": "odd", "特": "special",
    "殊": "special", "独": "alone", "唯": "only", "仅": "merely", "只": "just",
    "但": "only", "不": "not", "没": "not have", "无": "without", "非": "not",
    "未": "not yet", "勿": "don't", "莫": "don't", "别": "don't", "休": "cease",
    "罢": "stop", "了": "finish", "完": "complete", "毕": "finish", "终": "end",
    "尽": "exhaust", "竭": "exhaust", "穷": "poor", "富": "rich", "贫": "poor",
    "财": "wealth", "产": "property", "资": "capital", "金": "money", "银": "silver",
}

# Compound ligatures (~200 common words and phrases)
LIGATURES = {
    # Places
    ("火", "山"): "volcano", ("日", "本"): "Japan", ("北", "京"): "Beijing",
    ("上", "海"): "Shanghai", ("中", "国"): "China", ("美", "国"): "America",
    ("英", "国"): "Britain", ("法", "国"): "France", ("德", "国"): "Germany",
    ("韩", "国"): "Korea", ("台", "湾"): "Taiwan", ("香", "港"): "Hong Kong",
    ("澳", "门"): "Macau", ("新", "加", "坡"): "Singapore", ("东", "京"): "Tokyo",
    ("纽", "约"): "New York", ("伦", "敦"): "London", ("巴", "黎"): "Paris",
    ("广", "州"): "Guangzhou", ("深", "圳"): "Shenzhen", ("天", "津"): "Tianjin",
    ("南", "京"): "Nanjing", ("西", "安"): "Xi'an", ("成", "都"): "Chengdu",
    ("重", "庆"): "Chongqing", ("武", "汉"): "Wuhan", ("杭", "州"): "Hangzhou",
    ("苏", "州"): "Suzhou", ("长", "城"): "Great Wall",
    # Common words
    ("人", "口"): "population", ("电", "话"): "telephone", ("手", "机"): "cellphone",
    ("电", "脑"): "computer", ("电", "视"): "television", ("电", "影"): "movie",
    ("图", "书", "馆"): "library", ("博", "物", "馆"): "museum", ("医", "院"): "hospital",
    ("学", "校"): "school", ("大", "学"): "university", ("小", "学"): "elementary school",
    ("中", "学"): "middle school", ("高", "中"): "high school", ("幼", "儿", "园"): "kindergarten",
    ("学", "生"): "student", ("老", "师"): "teacher", ("教", "授"): "professor",
    ("中", "文"): "Chinese", ("英", "文"): "English", ("日", "文"): "Japanese",
    ("语", "言"): "language", ("文", "化"): "culture", ("历", "史"): "history",
    ("科", "学"): "science", ("数", "学"): "mathematics", ("物", "理"): "physics",
    ("化", "学"): "chemistry", ("生", "物"): "biology", ("地", "理"): "geography",
    ("音", "乐"): "music", ("美", "术"): "fine arts", ("体", "育"): "physical education",
    # Relationships
    ("朋", "友"): "friend", ("父", "母"): "parents", ("兄", "弟"): "brothers",
    ("姐", "妹"): "sisters", ("夫", "妻"): "husband and wife", ("男", "女"): "man and woman",
    ("老", "人"): "elderly", ("小", "孩"): "child", ("家", "人"): "family",
    ("同", "学"): "classmate", ("同", "事"): "colleague", ("朋", "友"): "friend",
    # Nature
    ("山", "水"): "landscape", ("天", "地"): "heaven and earth", ("日", "月"): "sun and moon",
    ("风", "雨"): "wind and rain", ("春", "天"): "spring", ("夏", "天"): "summer",
    ("秋", "天"): "autumn", ("冬", "天"): "winter", ("太", "阳"): "sun",
    ("月", "亮"): "moon", ("星", "星"): "stars", ("云", "彩"): "clouds",
    ("地", "球"): "Earth", ("宇", "宙"): "universe", ("世", "界"): "world",
    ("大", "海"): "ocean", ("河", "流"): "river", ("森", "林"): "forest",
    # Food
    ("早", "餐"): "breakfast", ("午", "餐"): "lunch", ("晚", "餐"): "dinner",
    ("米", "饭"): "rice", ("面", "条"): "noodles", ("饺", "子"): "dumplings",
    ("包", "子"): "buns", ("馒", "头"): "steamed buns", ("面", "包"): "bread",
    ("牛", "奶"): "milk", ("咖", "啡"): "coffee", ("果", "汁"): "juice",
    ("可", "乐"): "cola", ("啤", "酒"): "beer", ("白", "酒"): "liquor",
    ("水", "果"): "fruit", ("蔬", "菜"): "vegetables", ("牛", "肉"): "beef",
    ("猪", "肉"): "pork", ("鸡", "肉"): "chicken", ("鱼", "肉"): "fish",
    ("豆", "腐"): "tofu", ("鸡", "蛋"): "egg", ("海", "鲜"): "seafood",
    # Time
    ("今", "天"): "today", ("明", "天"): "tomorrow", ("昨", "天"): "yesterday",
    ("上", "午"): "morning", ("下", "午"): "afternoon", ("晚", "上"): "evening",
    ("现", "在"): "now", ("以", "前"): "before", ("以", "后"): "after",
    ("时", "间"): "time", ("日", "期"): "date", ("星", "期"): "week",
    ("周", "末"): "weekend", ("假", "期"): "vacation", ("节", "日"): "holiday",
    ("春", "节"): "Spring Festival", ("中", "秋"): "Mid-Autumn", ("国", "庆"): "National Day",
    ("新", "年"): "New Year", ("生", "日"): "birthday", ("纪", "念"): "anniversary",
    # Objects
    ("手", "心"): "palm", ("手", "表"): "wristwatch", ("眼", "镜"): "glasses",
    ("太", "阳", "镜"): "sunglasses", ("雨", "伞"): "umbrella", ("钥", "匙"): "key",
    ("钱", "包"): "wallet", ("背", "包"): "backpack", ("手", "套"): "gloves",
    ("帽", "子"): "hat", ("鞋", "子"): "shoes", ("袜", "子"): "socks",
    ("衣", "服"): "clothes", ("裤", "子"): "pants", ("裙", "子"): "skirt",
    # Transportation
    ("汽", "车"): "car", ("火", "车"): "train", ("飞", "机"): "airplane",
    ("地", "铁"): "subway", ("公", "交"): "bus", ("出", "租", "车"): "taxi",
    ("自", "行", "车"): "bicycle", ("摩", "托", "车"): "motorcycle", ("船", "只"): "ship",
    ("机", "场"): "airport", ("火", "车", "站"): "train station", ("汽", "车", "站"): "bus station",
    # Body
    ("身", "体"): "body", ("心", "脏"): "heart", ("大", "脑"): "brain",
    ("眼", "睛"): "eyes", ("耳", "朵"): "ears", ("嘴", "巴"): "mouth",
    ("鼻", "子"): "nose", ("头", "发"): "hair", ("手", "指"): "fingers",
    ("脚", "趾"): "toes", ("皮", "肤"): "skin", ("骨", "头"): "bones",
    # Actions
    ("工", "作"): "work", ("学", "习"): "study", ("休", "息"): "rest",
    ("运", "动"): "exercise", ("旅", "行"): "travel", ("购", "物"): "shopping",
    ("吃", "饭"): "eat", ("睡", "觉"): "sleep", ("看", "书"): "read",
    ("看", "电", "视"): "watch TV", ("听", "音", "乐"): "listen to music", ("玩", "游", "戏"): "play games",
    ("上", "班"): "go to work", ("下", "班"): "get off work", ("上", "学"): "go to school",
    ("回", "家"): "go home", ("出", "门"): "go out", ("进", "来"): "come in",
    # Abstract
    ("生", "活"): "life", ("生", "命"): "life", ("健", "康"): "health",
    ("幸", "福"): "happiness", ("快", "乐"): "joy", ("悲", "伤"): "sadness",
    ("爱", "情"): "love", ("友", "情"): "friendship", ("亲", "情"): "family love",
    ("希", "望"): "hope", ("梦", "想"): "dream", ("理", "想"): "ideal",
    ("成", "功"): "success", ("失", "败"): "failure", ("经", "验"): "experience",
    ("知", "识"): "knowledge", ("智", "慧"): "wisdom", ("能", "力"): "ability",
    ("问", "题"): "problem", ("答", "案"): "answer", ("方", "法"): "method",
    ("原", "因"): "reason", ("结", "果"): "result", ("目", "的"): "purpose",
    ("意", "思"): "meaning", ("感", "觉"): "feeling", ("想", "法"): "idea",
    # Technology
    ("网", "络"): "internet", ("软", "件"): "software", ("硬", "件"): "hardware",
    ("程", "序"): "program", ("数", "据"): "data", ("信", "息"): "information",
    ("视", "频"): "video", ("音", "频"): "audio", ("图", "片"): "image",
    ("文", "件"): "file", ("邮", "件"): "email", ("短", "信"): "text message",
    ("密", "码"): "password", ("用", "户"): "user", ("账", "号"): "account",
    # Society
    ("政", "府"): "government", ("国", "家"): "nation", ("社", "会"): "society",
    ("经", "济"): "economy", ("政", "治"): "politics", ("法", "律"): "law",
    ("公", "司"): "company", ("银", "行"): "bank", ("市", "场"): "market",
    ("新", "闻"): "news", ("报", "纸"): "newspaper", ("杂", "志"): "magazine",
    ("广", "告"): "advertisement", ("电", "台"): "radio station", ("电", "视", "台"): "TV station",
    # More compounds
    ("安", "全"): "safety", ("危", "险"): "danger", ("重", "要"): "important",
    ("必", "要"): "necessary", ("可", "能"): "possible", ("应", "该"): "should",
    ("需", "要"): "need", ("喜", "欢"): "like", ("讨", "厌"): "dislike",
    ("相", "信"): "believe", ("怀", "疑"): "doubt", ("同", "意"): "agree",
    ("反", "对"): "oppose", ("支", "持"): "support", ("帮", "助"): "help",
    ("感", "谢"): "thank", ("对", "不", "起"): "sorry", ("没", "关", "系"): "no problem",
    ("再", "见"): "goodbye", ("你", "好"): "hello", ("谢", "谢"): "thanks",
    ("欢", "迎"): "welcome", ("恭", "喜"): "congratulations", ("祝", "福"): "blessing",
}

UNITS_PER_EM = 1000
ASCENDER = 800
DESCENDER = -200
CAP_HEIGHT = 700


def text_to_outline(text: str, font_size: int = 60) -> tuple[list, int]:
    """Convert text to outline paths using PIL and return contours and width."""
    try:
        pil_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except OSError:
        try:
            pil_font = ImageFont.truetype(
                "/System/Library/Fonts/SFNSMono.ttf", font_size
            )
        except OSError:
            pil_font = ImageFont.load_default()

    bbox = pil_font.getbbox(text)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    padding = 10
    img_width = text_width + padding * 2
    img_height = text_height + padding * 2

    img = Image.new("L", (img_width, img_height), 0)
    draw = ImageDraw.Draw(img)
    draw.text((padding - bbox[0], padding - bbox[1]), text, font=pil_font, fill=255)

    return img, img_width, img_height


def image_to_charstring(
    img: Image.Image, img_width: int, img_height: int, target_height: int = 600
) -> tuple[bytes, int]:
    """Convert a PIL image to a CFF CharString with proper scaling."""
    scale = target_height / img_height
    scaled_width = int(img_width * scale)

    threshold = 128
    contours = []

    for y in range(img.height):
        row_start = None
        for x in range(img.width + 1):
            pixel = img.getpixel((x, y)) if x < img.width else 0
            if pixel >= threshold and row_start is None:
                row_start = x
            elif pixel < threshold and row_start is not None:
                x1 = int(row_start * scale)
                x2 = int(x * scale)
                y1 = int((img.height - y - 1) * scale) + 100
                y2 = int((img.height - y) * scale) + 100
                contours.append((x1, y1, x2, y2))
                row_start = None

    pen = T2CharStringPen(scaled_width, None)

    for x1, y1, x2, y2 in contours:
        pen.moveTo((x1, y1))
        pen.lineTo((x2, y1))
        pen.lineTo((x2, y2))
        pen.lineTo((x1, y2))
        pen.closePath()

    charstring = pen.getCharString()
    return charstring, scaled_width


def create_notdef_charstring(width: int = 500) -> bytes:
    """Create a .notdef glyph (empty rectangle)."""
    pen = T2CharStringPen(width, None)
    pen.moveTo((50, 0))
    pen.lineTo((width - 50, 0))
    pen.lineTo((width - 50, 700))
    pen.lineTo((50, 700))
    pen.closePath()
    pen.moveTo((100, 50))
    pen.lineTo((100, 650))
    pen.lineTo((width - 100, 650))
    pen.lineTo((width - 100, 50))
    pen.closePath()
    return pen.getCharString()


def create_space_charstring(width: int = 250) -> bytes:
    """Create a space glyph."""
    pen = T2CharStringPen(width, None)
    return pen.getCharString()


def build_font():
    """Build the literal Chinese font."""
    print("Building literal_chinese.ttf...")

    glyph_names = [".notdef", "space"]
    char_strings = {}
    widths = {".notdef": 500, "space": 250}
    cmap = {32: "space"}

    char_strings[".notdef"] = create_notdef_charstring()
    char_strings["space"] = create_space_charstring()

    ligature_glyph_map = {}

    for chars, gloss in LIGATURES.items():
        glyph_name = "lig_" + "_".join(f"u{ord(c):04X}" for c in chars)
        glyph_names.append(glyph_name)

        img, img_w, img_h = text_to_outline(gloss)
        charstring, width = image_to_charstring(img, img_w, img_h)
        char_strings[glyph_name] = charstring
        widths[glyph_name] = width
        ligature_glyph_map[chars] = glyph_name

    for char, gloss in CHAR_GLOSSES.items():
        codepoint = ord(char)
        glyph_name = f"u{codepoint:04X}"
        glyph_names.append(glyph_name)

        img, img_w, img_h = text_to_outline(gloss)
        charstring, width = image_to_charstring(img, img_w, img_h)
        char_strings[glyph_name] = charstring
        widths[glyph_name] = width
        cmap[codepoint] = glyph_name

    fb = FontBuilder(UNITS_PER_EM, isTTF=False)
    fb.setupGlyphOrder(glyph_names)
    fb.setupCharacterMap(cmap)

    fb.setupCFF(
        psName="LiteralChinese-Regular",
        fontInfo={"FamilyName": "Literal Chinese", "FullName": "Literal Chinese Regular"},
        charStringsDict=char_strings,
        privateDict={},
    )

    advance_widths = {name: (widths.get(name, 500), 0) for name in glyph_names}
    fb.setupHorizontalMetrics(advance_widths)

    fb.setupHorizontalHeader(ascent=ASCENDER, descent=DESCENDER)
    fb.setupOS2(
        sTypoAscender=ASCENDER,
        sTypoDescender=DESCENDER,
        sCapHeight=CAP_HEIGHT,
        sxHeight=500,
    )
    fb.setupPost()
    fb.setupNameTable(
        {
            "familyName": "Literal Chinese",
            "styleName": "Regular",
            "uniqueFontIdentifier": "LiteralChinese-Regular",
            "fullName": "Literal Chinese Regular",
            "version": "Version 1.0",
            "psName": "LiteralChinese-Regular",
        }
    )

    font = fb.font

    from fontTools.ttLib import newTable
    gsub = font["GSUB"] = newTable("GSUB")
    gsub.table = build_gsub_table(cmap, ligature_glyph_map)

    font.save("literal_chinese.ttf")
    print(f"Created literal_chinese.ttf with {len(CHAR_GLOSSES)} characters and {len(LIGATURES)} ligatures")


def build_gsub_table(cmap, ligature_glyph_map):
    """Build GSUB table for ligature substitutions."""
    from fontTools.ttLib.tables import otTables

    gsub = otTables.GSUB()
    gsub.Version = 0x00010000

    script_list = otTables.ScriptList()
    script_record = otTables.ScriptRecord()
    script_record.ScriptTag = "DFLT"
    script = otTables.Script()
    script.DefaultLangSys = otTables.DefaultLangSys()
    script.DefaultLangSys.ReqFeatureIndex = 0xFFFF
    script.DefaultLangSys.FeatureIndex = [0]
    script.DefaultLangSys.LookupOrder = None
    script.LangSysRecord = []
    script_record.Script = script
    script_list.ScriptRecord = [script_record]

    feature_list = otTables.FeatureList()
    feature_record = otTables.FeatureRecord()
    feature_record.FeatureTag = "liga"
    feature = otTables.Feature()
    feature.FeatureParams = None
    feature.LookupListIndex = [0]
    feature_record.Feature = feature
    feature_list.FeatureRecord = [feature_record]

    lookup_list = otTables.LookupList()
    lookup = otTables.Lookup()
    lookup.LookupType = 4
    lookup.LookupFlag = 0

    ligature_subst = otTables.LigatureSubst()
    ligature_subst.Format = 1
    ligature_subst.ligatures = {}

    for chars, lig_glyph in ligature_glyph_map.items():
        first_char = chars[0]
        rest_chars = chars[1:]

        first_glyph = cmap.get(ord(first_char))
        if not first_glyph:
            continue

        rest_glyphs = []
        valid = True
        for c in rest_chars:
            g = cmap.get(ord(c))
            if not g:
                valid = False
                break
            rest_glyphs.append(g)

        if not valid:
            continue

        if first_glyph not in ligature_subst.ligatures:
            ligature_subst.ligatures[first_glyph] = []

        lig = otTables.Ligature()
        lig.LigGlyph = lig_glyph
        lig.Component = rest_glyphs
        ligature_subst.ligatures[first_glyph].append(lig)

    lookup.SubTable = [ligature_subst]
    lookup_list.Lookup = [lookup]

    gsub.ScriptList = script_list
    gsub.FeatureList = feature_list
    gsub.LookupList = lookup_list

    return gsub


if __name__ == "__main__":
    build_font()
