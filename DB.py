import sqlite3
from datetime import datetime
from typing import List, Optional
import matplotlib.pyplot as plt
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from io import BytesIO
import base64
import uvicorn
import socket
from contextlib import closing
import logging
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SmartHomeAPI")

app = FastAPI(
    title="智能家居系统 API",
    description="提供智能家居设备管理、使用记录、安防事件和用户反馈的API接口",
    version="1.0.0",
    openapi_tags=[
        {"name": "用户管理", "description": "用户账户管理操作"},
        {"name": "房屋管理", "description": "房屋信息管理操作"},
        {"name": "设备管理", "description": "智能设备管理操作"},
        {"name": "设备使用记录", "description": "设备使用记录管理"},
        {"name": "安防事件", "description": "安全事件记录管理"},
        {"name": "用户反馈", "description": "用户反馈管理"},
        {"name": "分析功能", "description": "数据分析接口"},
        {"name": "可视化", "description": "数据可视化接口"},
        {"name": "系统管理", "description": "系统维护接口"},
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境需限制，调试时用 * 快速验证
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



app.mount("/static", StaticFiles(directory="static"), name="static")




@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
    )




@app.get("/", tags=["系统管理"])
def home():
    """系统根端点"""
    return {
        "message": "Smart Home API is running!",
        "docs": "/docs",
        "redoc": "/redoc",
        "health_check": "/health"
    }


@app.get("/test", tags=["系统管理"])
def test_endpoint():
    """测试端点"""
    return {
        "status": "success",
        "message": "API is working!",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "health_check": "/health",
            "reset_db": "/reset-db"
        }
    }


def find_free_port(start_port=8000, end_port=9000):
    """查找可用端口"""
    for port in range(start_port, end_port):
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
            try:
                s.bind(('', port))
                return port
            except OSError:
                continue
    raise RuntimeError("No free port available")


# 数据库初始化（添加索引）
def init_db():
    conn = sqlite3.connect('smart_home.db', detect_types=sqlite3.PARSE_DECLTYPES)
    cursor = conn.cursor()

    # 创建用户表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        age INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')

    # 创建房屋表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS houses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        address TEXT NOT NULL,
        area REAL NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_houses_user ON houses(user_id)')

    # 创建设备表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS devices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        house_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (house_id) REFERENCES houses (id) ON DELETE CASCADE
    )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_devices_house ON devices(house_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_devices_type ON devices(type)')

    # 创建设备使用记录表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS device_usage (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id INTEGER NOT NULL,
        start_time TIMESTAMP NOT NULL,
        end_time TIMESTAMP NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (device_id) REFERENCES devices (id) ON DELETE CASCADE
    )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_usage_device ON device_usage(device_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_usage_time ON device_usage(start_time)')

    # 创建安防事件表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS security_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id INTEGER NOT NULL,
        event_type TEXT NOT NULL,
        event_time TIMESTAMP NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (device_id) REFERENCES devices (id) ON DELETE CASCADE
    )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_device ON security_events(device_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_time ON security_events(event_time)')

    # 创建用户反馈表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        rating INTEGER CHECK (rating BETWEEN 1 AND 5),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_feedback_user ON feedback(user_id)')

    conn.commit()
    conn.close()

# 调用初始化函数
init_db()





# Pydantic 模型定义
class UserCreate(BaseModel):
    name: str
    email: str
    age: Optional[int] = None


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    age: Optional[int] = None
    created_at: datetime


class HouseCreate(BaseModel):
    user_id: int
    address: str
    area: float


class HouseResponse(BaseModel):
    id: int
    user_id: int
    address: str
    area: float
    created_at: datetime


class DeviceCreate(BaseModel):
    house_id: int
    name: str
    type: str


class DeviceResponse(BaseModel):
    id: int
    house_id: int
    name: str
    type: str
    created_at: datetime


class DeviceUsageCreate(BaseModel):
    device_id: int
    start_time: datetime
    end_time: datetime


class DeviceUsageResponse(BaseModel):
    id: int
    device_id: int
    start_time: datetime
    end_time: datetime
    created_at: datetime


class SecurityEventCreate(BaseModel):
    device_id: int
    event_type: str
    event_time: datetime
    description: Optional[str] = None


class SecurityEventResponse(BaseModel):
    id: int
    device_id: int
    event_type: str
    event_time: datetime
    description: Optional[str] = None
    created_at: datetime


class FeedbackCreate(BaseModel):
    user_id: int
    content: str
    rating: int


class FeedbackResponse(BaseModel):
    id: int
    user_id: int
    content: str
    rating: int
    created_at: datetime


class DeviceUsageFrequency(BaseModel):
    device_id: int
    device_name: str
    frequency: int
    time_slot: str


class ConcurrentDevices(BaseModel):
    device1_id: int
    device1_name: str
    device2_id: int
    device2_name: str
    concurrent_count: int


class AreaUsageImpact(BaseModel):
    area_range: str
    device_type: str
    avg_duration: float
    usage_count: int


class SecurityEventStats(BaseModel):
    event_type: str
    count: int
    percentage: float


class VisualizationResponse(BaseModel):
    plot_base64: str
    description: str


# 安全的数据库连接函数
def get_db_connection():
    conn = sqlite3.connect('smart_home.db', detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    return conn


def execute_query(query: str, params: tuple = (), fetch_one: bool = False, commit: bool = False):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        if commit:
            conn.commit()

        if fetch_one:
            result = cursor.fetchone()
        else:
            result = cursor.fetchall()
        return result
    except sqlite3.Error as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database operation failed")
    finally:
        conn.close()


'''def populate_sample_data():
    """填充更全面的示例数据，支持多样化的可视化演示"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 检查是否已有数据
        if cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0] > 0:
            logger.info("数据库已有数据，跳过示例数据填充")
            return

        logger.info("开始填充更全面的示例数据...")

        # 创建更多示例用户（10个用户，覆盖不同年龄段和使用习惯）
        users = [
            ("张三", "zhangsan@example.com", 35),  # 中年用户，家庭稳定
            ("李四", "lisi@example.com", 28),  # 青年用户，科技爱好者
            ("王五", "wangwu@example.com", 42),  # 中老年用户，注重节能
            ("赵六", "zhaoliu@example.com", 31),  # 职场人士，使用时间规律
            ("钱七", "qianqi@example.com", 26),  # 年轻用户，夜间活动频繁
            ("孙八", "sunba@example.com", 55),  # 老年用户，使用较少
            ("周九", "zhoujiu@example.com", 22),  # 学生，使用不规律
            ("吴十", "wushi@example.com", 38),  # 家庭主妇，日间使用多
            ("郑十一", "zhengshiyi@example.com", 45),  # 企业主，安全意识强
            ("陈十二", "chenshier@example.com", 30),  # 自由职业者，全天候使用
        ]
        user_ids = []
        for user in users:
            cursor.execute(
                "INSERT INTO users (name, email, age) VALUES (?, ?, ?)",
                user
            )
            user_ids.append(cursor.lastrowid)

        # 创建多样化的房屋（不同面积、位置、装修风格）
        houses = [
            (user_ids[0], "北京市海淀区中关村大街1号", 120.5),  # 城市中心大户型
            (user_ids[1], "上海市浦东新区张江高科技园区", 89.3),  # 青年公寓
            (user_ids[2], "广州市天河区珠江新城", 150.2),  # 豪华住宅
            (user_ids[3], "深圳市南山区科技园", 75.8),  # 小户型
            (user_ids[4], "杭州市西湖区文三路", 110.0),  # 中等户型
            (user_ids[5], "成都市锦江区春熙路", 90.7),  # 退休公寓
            (user_ids[6], "南京市鼓楼区", 65.2),  # 学生公寓
            (user_ids[7], "武汉市武昌区", 130.4),  # 家庭住宅
            (user_ids[8], "重庆市渝中区", 140.9),  # 安全要求高的住宅
            (user_ids[9], "天津市和平区", 100.3),  # 现代风格住宅
        ]
        house_ids = []
        for house in houses:
            cursor.execute(
                "INSERT INTO houses (user_id, address, area) VALUES (?, ?, ?)",
                house
            )
            house_ids.append(cursor.lastrowid)

        # 创建设备类型映射（增加更多设备种类和细分类型）
        device_types = {
            "照明": ["客厅主灯", "卧室灯", "走廊灯", "厨房灯", "书房灯", "浴室灯"],
            "安防": ["大门摄像头", "客厅监控", "车库传感器", "门窗传感器", "烟雾报警器", "水浸传感器"],
            "环境": ["空调", "加湿器", "空气净化器", "除湿机", "新风系统", "智能窗帘"],
            "娱乐": ["智能电视", "音响系统", "投影仪", "游戏机", "家庭影院"],
            "厨房": ["智能冰箱", "烤箱", "咖啡机", "洗碗机", "微波炉", "电饭煲"],
            "家电": ["洗衣机", "烘干机", "扫地机器人", "吸尘器", "热水器", "智能门锁"]
        }

        # 创建设备（为每个房屋分配不同数量和类型的设备，模拟真实场景）
        device_ids = []
        device_type_map = {}  # 设备ID到类型的映射
        device_house_map = {}  # 设备ID到房屋ID的映射

        for i, house_id in enumerate(house_ids):
            # 根据房屋面积和用户类型分配不同设备
            if i < 3:  # 大户型房屋
                for device_type, names in device_types.items():
                    for name in names[:3]:  # 每种类型选3个设备
                        cursor.execute(
                            "INSERT INTO devices (house_id, name, type) VALUES (?, ?, ?)",
                            (house_id, f"{name}_{house_id}", device_type)
                        )
                        device_id = cursor.lastrowid
                        device_ids.append(device_id)
                        device_type_map[device_id] = device_type
                        device_house_map[device_id] = house_id
            elif i < 6:  # 中等户型
                for device_type, names in device_types.items():
                    for name in names[:2]:  # 每种类型选2个设备
                        cursor.execute(
                            "INSERT INTO devices (house_id, name, type) VALUES (?, ?, ?)",
                            (house_id, f"{name}_{house_id}", device_type)
                        )
                        device_id = cursor.lastrowid
                        device_ids.append(device_id)
                        device_type_map[device_id] = device_type
                        device_house_map[device_id] = house_id
            else:  # 小户型
                for device_type, names in device_types.items():
                    if device_type in ["照明", "安防", "环境"]:  # 小户型更关注基础设备
                        for name in names[:1]:  # 每种类型选1个设备
                            cursor.execute(
                                "INSERT INTO devices (house_id, name, type) VALUES (?, ?, ?)",
                                (house_id, f"{name}_{house_id}", device_type)
                            )
                            device_id = cursor.lastrowid
                            device_ids.append(device_id)
                            device_type_map[device_id] = device_type
                            device_house_map[device_id] = house_id

        # 创建设备使用记录（更复杂的时间模式，模拟真实使用场景）
        import random
        from datetime import datetime, timedelta, time

        # 定义不同设备类型的使用模式
        device_usage_patterns = {
            "照明": {
                "morning": (6, 10, 0.3),  # 早上使用概率30%
                "afternoon": (12, 18, 0.1),  # 下午使用概率10%
                "evening": (18, 23, 0.8),  # 晚上使用概率80%
                "night": (23, 6, 0.2),  # 夜间使用概率20%
                "duration": (0.5, 4)  # 使用时长0.5-4小时
            },
            "安防": {
                "morning": (6, 10, 0.1),
                "afternoon": (12, 18, 0.1),
                "evening": (18, 23, 0.1),
                "night": (23, 6, 0.9),  # 夜间安防设备高概率工作
                "duration": (8, 12)  # 安防设备持续工作时间长
            },
            "环境": {
                "morning": (6, 10, 0.6),
                "afternoon": (12, 18, 0.7),  # 下午环境设备使用频繁
                "evening": (18, 23, 0.6),
                "night": (23, 6, 0.3),
                "duration": (2, 6)
            },
            "娱乐": {
                "morning": (6, 10, 0.1),
                "afternoon": (12, 18, 0.2),
                "evening": (18, 23, 0.7),  # 晚上娱乐设备使用频繁
                "night": (23, 6, 0.3),
                "duration": (1, 5)
            },
            "厨房": {
                "morning": (6, 10, 0.7),  # 早餐时间
                "afternoon": (12, 14, 0.8),  # 午餐时间
                "evening": (18, 20, 0.8),  # 晚餐时间
                "night": (23, 6, 0.05),
                "duration": (0.5, 2)
            },
            "家电": {
                "morning": (6, 10, 0.4),
                "afternoon": (12, 18, 0.6),  # 下午做家务
                "evening": (18, 23, 0.4),
                "night": (23, 6, 0.05),
                "duration": (1, 4)
            }
        }

        # 为每个设备创建使用记录
        for device_id in device_ids:
            if device_id not in device_type_map:
                logger.warning(f"设备ID {device_id} 类型信息缺失，跳过使用记录生成")
                continue

            device_type = device_type_map[device_id]
            house_id = device_house_map[device_id]  # 使用预存的房屋ID

            # 基于房屋所属用户类型调整使用频率
            user_type = house_id % 3  # 将用户分为3类（0,1,2）
            base_usage_days = 60 if user_type == 0 else 45 if user_type == 1 else 30  # 不同用户使用天数不同

            # 为每个设备创建30-60天的使用记录
            for day_offset in range(random.randint(20, base_usage_days)):
                day = datetime.now() - timedelta(days=day_offset)

                # 获取当前设备类型的使用模式
                usage_pattern = device_usage_patterns[device_type]

                # 根据时间段决定是否使用设备
                for slot_name, slot_info in [
                    ("morning", usage_pattern["morning"]),
                    ("afternoon", usage_pattern["afternoon"]),
                    ("evening", usage_pattern["evening"]),
                    ("night", usage_pattern["night"])
                ]:
                    start_hour, end_hour, probability = slot_info

                    # 处理跨天的时间范围（如23点到次日6点）
                    if start_hour > end_hour:
                        # 跨天情况：拆分为两段时间
                        # 第一段：start_hour 到 23点59分
                        if random.random() < probability:
                            start_h = random.randint(start_hour, 23)
                            start_m = random.randint(0, 59)
                            start_time = day.replace(hour=start_h, minute=start_m)

                            min_dur, max_dur = usage_pattern["duration"]
                            duration = random.uniform(min_dur, max_dur)
                            end_time = start_time + timedelta(hours=duration)

                            # 确保结束时间不超过当天23:59
                            if end_time.day > start_time.day:
                                end_time = start_time.replace(hour=23, minute=59)

                            cursor.execute(
                                "INSERT INTO device_usage (device_id, start_time, end_time) VALUES (?, ?, ?)",
                                (device_id, start_time, end_time)
                            )

                        # 第二段：0点到 end_hour
                        if random.random() < probability:
                            start_h = random.randint(0, end_hour - 1)
                            start_m = random.randint(0, 59)
                            # 注意这里是次日，需要加一天
                            start_time = (day + timedelta(days=1)).replace(hour=start_h, minute=start_m)

                            min_dur, max_dur = usage_pattern["duration"]
                            duration = random.uniform(min_dur, max_dur)
                            end_time = start_time + timedelta(hours=duration)

                            cursor.execute(
                                "INSERT INTO device_usage (device_id, start_time, end_time) VALUES (?, ?, ?)",
                                (device_id, start_time, end_time)
                            )

                    else:
                        # 普通情况：直接使用给定的时间范围
                        if random.random() < probability:
                            start_h = random.randint(start_hour, end_hour - 1)
                            start_m = random.randint(0, 59)
                            start_time = day.replace(hour=start_h, minute=start_m)

                            min_dur, max_dur = usage_pattern["duration"]
                            duration = random.uniform(min_dur, max_dur)
                            end_time = start_time + timedelta(hours=duration)

                            # 避免结束时间跨天
                            if end_time.day != start_time.day:
                                end_time = start_time + timedelta(hours=min_dur)

                            cursor.execute(
                                "INSERT INTO device_usage (device_id, start_time, end_time) VALUES (?, ?, ?)",
                                (device_id, start_time, end_time)
                            )
        # 创建安防事件（更丰富的事件类型和时间分布）
        event_types = [
            "门禁异常", "移动检测", "火灾警报", "水浸检测", "闯入警报",
            "设备离线", "温度异常", "烟雾报警", "玻璃破碎", "非法访问"
        ]

        # 为不同设备类型设置不同的事件概率
        device_event_probability = {
            "安防": 0.6,  # 安防设备更容易触发事件
            "环境": 0.3,
            "照明": 0.1,
            "娱乐": 0.1,
            "厨房": 0.4,  # 厨房设备可能触发火灾、水浸等
            "家电": 0.2
        }

        for day_offset in range(90):  # 过去90天的事件
            day = datetime.now() - timedelta(days=day_offset)

            # 每天随机选择一些设备触发事件（确保只选择有效的设备ID）
            valid_device_ids = [id for id in device_ids if id in device_type_map]
            if not valid_device_ids:
                continue

            for device_id in random.sample(valid_device_ids, random.randint(1, min(5, len(valid_device_ids)))):
                device_type = device_type_map[device_id]

                # 根据设备类型决定事件概率
                if random.random() < device_event_probability.get(device_type, 0.2):
                    # 事件时间（集中在夜间和无人时段）
                    if random.random() < 0.7:  # 70%的事件发生在夜间或无人时段
                        event_hour = random.randint(0, 6) or random.randint(12, 14)  # 夜间或午休时间
                    else:
                        event_hour = random.randint(7, 23)

                    event_minute = random.randint(0, 59)
                    event_time = day.replace(hour=event_hour, minute=event_minute)

                    event_type = random.choice(event_types)

                    # 根据事件类型生成不同的描述
                    descriptions = {
                        "门禁异常": ["未授权尝试开门", "密码连续输入错误", "门未正常关闭"],
                        "移动检测": ["检测到异常移动", "夜间有人活动", "触发区域移动警报"],
                        "火灾警报": ["烟雾浓度过高", "温度异常升高", "检测到明火"],
                        "水浸检测": ["厨房漏水", "浴室积水", "水管破裂"],
                        "闯入警报": ["窗户被撬动", "检测到非法入侵", "安防系统触发"],
                        "设备离线": ["设备信号丢失", "网络连接中断", "电池电量过低"],
                        "温度异常": ["室内温度过高", "空调故障导致温度异常", "温控器失灵"],
                        "烟雾报警": ["烹饪产生大量烟雾", "吸烟触发警报", "电器冒烟"],
                        "玻璃破碎": ["检测到玻璃破碎声音", "窗户安全系统触发", "疑似暴力闯入"],
                        "非法访问": ["非授权设备尝试连接", "密码被破解", "系统检测到异常登录"]
                    }

                    description = random.choice(descriptions.get(event_type, ["系统自动报警"]))

                    cursor.execute(
                        "INSERT INTO security_events (device_id, event_type, event_time, description) VALUES (?, ?, ?, ?)",
                        (device_id, event_type, event_time, description)
                    )

        # 创建用户反馈（更丰富的反馈内容和评分分布）
        feedback_contents = [
            "系统非常好用，推荐！",
            "设备偶尔会掉线，希望优化连接稳定性",
            "界面设计很直观，但某些功能位置不太好找",
            "希望能增加更多设备支持，尤其是厨房电器",
            "报警系统很灵敏，给我带来了安全感",
            "手机APP需要优化，偶尔会卡顿",
            "客服响应迅速，问题解决很及时",
            "安装过程很顺利，技术人员很专业",
            "希望增加自动化场景，比如离家模式一键启动",
            "能耗统计功能很有用，但数据展示可以更直观",
            "安防摄像头画质清晰，但夜视效果一般",
            "智能门锁指纹识别速度有待提高",
            "环境监测数据不准确，希望校准算法",
            "语音控制功能很好用，但识别率需要提升",
            "价格偏高，希望推出更多套餐优惠"
        ]

        # 为每个用户创建1-5条反馈，评分更分散
        for user_id in user_ids:
            for _ in range(random.randint(1, 5)):
                # 评分分布：30%概率给5分，20%概率给4分，30%概率给3分，10%概率给2分，10%概率给1分
                weights = [0.3, 0.2, 0.3, 0.1, 0.1]
                rating = random.choices([5, 4, 3, 2, 1], weights=weights)[0]
                content = random.choice(feedback_contents)

                # 根据评分调整反馈内容的情感倾向
                if rating >= 4:
                    positive_comments = ["非常满意", "超出预期", "推荐购买", "很实用", "值得投资"]
                    content = f"{random.choice(positive_comments)}，{content}"
                elif rating <= 2:
                    negative_comments = ["不太满意", "体验较差", "存在问题", "需要改进", "不推荐"]
                    content = f"{random.choice(negative_comments)}，{content}"

                cursor.execute(
                    "INSERT INTO feedback (user_id, content, rating) VALUES (?, ?, ?)",
                    (user_id, content, rating)
                )

        conn.commit()
        logger.info("全面示例数据填充完成！")

    except sqlite3.Error as e:
        logger.error(f"填充示例数据失败: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

populate_sample_data()'''

# 用户管理 API
@app.post("/users/", response_model=UserResponse, tags=["用户管理"])
def create_user(user: UserCreate):
    try:
        result = execute_query(
            "INSERT INTO users (name, email, age) VALUES (?, ?, ?) RETURNING id, name, email, age, created_at",
            (user.name, user.email, user.age),
            fetch_one=True,
            commit=True
        )
        return dict(result)
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Email already exists")


@app.get("/users/{user_id}", response_model=UserResponse, tags=["用户管理"])
def get_user(user_id: int):
    result = execute_query(
        "SELECT id, name, email, age, created_at FROM users WHERE id = ?",
        (user_id,),
        fetch_one=True
    )
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    return dict(result)


@app.delete("/users/{user_id}", tags=["用户管理"])
def delete_user(user_id: int):
    execute_query(
        "DELETE FROM users WHERE id = ?",
        (user_id,),
        commit=True
    )
    return {"message": "User deleted successfully"}


# 房屋管理 API
@app.post("/houses/", response_model=HouseResponse, tags=["房屋管理"])
def create_house(house: HouseCreate):
    # 验证用户存在
    user_exists = execute_query(
        "SELECT 1 FROM users WHERE id = ?",
        (house.user_id,),
        fetch_one=True
    )
    if not user_exists:
        raise HTTPException(status_code=404, detail="User not found")

    result = execute_query(
        "INSERT INTO houses (user_id, address, area) VALUES (?, ?, ?) RETURNING id, user_id, address, area, created_at",
        (house.user_id, house.address, house.area),
        fetch_one=True,
        commit=True
    )
    return dict(result)


@app.get("/houses/{house_id}", response_model=HouseResponse, tags=["房屋管理"])
def get_house(house_id: int):
    result = execute_query(
        "SELECT id, user_id, address, area, created_at FROM houses WHERE id = ?",
        (house_id,),
        fetch_one=True
    )
    if not result:
        raise HTTPException(status_code=404, detail="House not found")
    return dict(result)


# 设备管理 API
@app.post("/devices/", response_model=DeviceResponse, tags=["设备管理"])
def create_device(device: DeviceCreate):
    # 验证房屋存在
    house_exists = execute_query(
        "SELECT 1 FROM houses WHERE id = ?",
        (device.house_id,),
        fetch_one=True
    )
    if not house_exists:
        raise HTTPException(status_code=404, detail="House not found")

    result = execute_query(
        "INSERT INTO devices (house_id, name, type) VALUES (?, ?, ?) RETURNING id, house_id, name, type, created_at",
        (device.house_id, device.name, device.type),
        fetch_one=True,
        commit=True
    )
    return dict(result)


@app.get("/devices/{device_id}", response_model=DeviceResponse, tags=["设备管理"])
def get_device(device_id: int):
    result = execute_query(
        "SELECT id, house_id, name, type, created_at FROM devices WHERE id = ?",
        (device_id,),
        fetch_one=True
    )
    if not result:
        raise HTTPException(status_code=404, detail="Device not found")
    return dict(result)


# 设备使用记录 API
@app.post("/device-usage/", response_model=DeviceUsageResponse, tags=["设备使用记录"])
def create_device_usage(usage: DeviceUsageCreate):
    if usage.end_time <= usage.start_time:
        raise HTTPException(status_code=400, detail="End time must be after start time")

    # 验证设备存在
    device_exists = execute_query(
        "SELECT 1 FROM devices WHERE id = ?",
        (usage.device_id,),
        fetch_one=True
    )
    if not device_exists:
        raise HTTPException(status_code=404, detail="Device not found")

    result = execute_query(
        "INSERT INTO device_usage (device_id, start_time, end_time) VALUES (?, ?, ?) RETURNING id, device_id, start_time, end_time, created_at",
        (usage.device_id, usage.start_time, usage.end_time),
        fetch_one=True,
        commit=True
    )
    return dict(result)


# 安防事件 API
@app.post("/security-events/", response_model=SecurityEventResponse, tags=["安防事件"])
def create_security_event(event: SecurityEventCreate):
    # 验证设备存在
    device_exists = execute_query(
        "SELECT 1 FROM devices WHERE id = ?",
        (event.device_id,),
        fetch_one=True
    )
    if not device_exists:
        raise HTTPException(status_code=404, detail="Device not found")

    result = execute_query(
        "INSERT INTO security_events (device_id, event_type, event_time, description) VALUES (?, ?, ?, ?) RETURNING id, device_id, event_type, event_time, description, created_at",
        (event.device_id, event.event_type, event.event_time, event.description),
        fetch_one=True,
        commit=True
    )
    return dict(result)


# 用户反馈 API
@app.post("/feedback/", response_model=FeedbackResponse, tags=["用户反馈"])
def create_feedback(feedback: FeedbackCreate):
    if feedback.rating < 1 or feedback.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    # 验证用户存在
    user_exists = execute_query(
        "SELECT 1 FROM users WHERE id = ?",
        (feedback.user_id,),
        fetch_one=True
    )
    if not user_exists:
        raise HTTPException(status_code=404, detail="User not found")

    result = execute_query(
        "INSERT INTO feedback (user_id, content, rating) VALUES (?, ?, ?) RETURNING id, user_id, content, rating, created_at",
        (feedback.user_id, feedback.content, feedback.rating),
        fetch_one=True,
        commit=True
    )
    return dict(result)


# 分析功能 API
@app.get("/analysis/device-usage-frequency/", response_model=List[DeviceUsageFrequency], tags=["分析功能"])
def get_device_usage_frequency():
    """分析不同设备的使用频率和使用时间段"""
    query = """
    SELECT 
        d.id AS device_id,
        d.name AS device_name,
        COUNT(*) AS frequency,
        CASE 
            WHEN CAST(strftime('%H', start_time) AS INTEGER) BETWEEN 6 AND 12 THEN 'Morning (6-12)'
            WHEN CAST(strftime('%H', start_time) AS INTEGER) BETWEEN 12 AND 18 THEN 'Afternoon (12-18)'
            WHEN CAST(strftime('%H', start_time) AS INTEGER) BETWEEN 18 AND 24 THEN 'Evening (18-24)'
            ELSE 'Night (0-6)'
        END AS time_slot
    FROM device_usage du
    JOIN devices d ON du.device_id = d.id
    GROUP BY d.id, time_slot
    ORDER BY frequency DESC
    """
    results = execute_query(query)
    return [dict(row) for row in results] if results else []


@app.get("/analysis/concurrent-devices/", response_model=List[ConcurrentDevices], tags=["分析功能"])
def get_concurrent_devices():
    """找出经常同时使用的设备"""
    query = """
    SELECT 
        d1.id AS device1_id,
        d1.name AS device1_name,
        d2.id AS device2_id,
        d2.name AS device2_name,
        COUNT(*) AS concurrent_count
    FROM device_usage du1
    JOIN device_usage du2 
        ON du1.device_id < du2.device_id
        AND du1.start_time <= du2.end_time
        AND du1.end_time >= du2.start_time
    JOIN devices d1 ON du1.device_id = d1.id
    JOIN devices d2 ON du2.device_id = d2.id
    GROUP BY d1.id, d2.id
    HAVING concurrent_count > 2
    ORDER BY concurrent_count DESC
    LIMIT 10
    """
    results = execute_query(query)
    return [dict(row) for row in results] if results else []


@app.get("/analysis/area-usage-impact/", response_model=List[AreaUsageImpact], tags=["分析功能"])
def get_area_usage_impact():
    """分析房屋面积对设备使用行为的影响"""
    query = """
    SELECT 
        CASE 
            WHEN h.area < 50 THEN '0-50'
            WHEN h.area BETWEEN 50 AND 100 THEN '50-100'
            WHEN h.area BETWEEN 100 AND 150 THEN '100-150'
            ELSE '150+'
        END AS area_range,
        d.type AS device_type,
        AVG((JULIANDAY(du.end_time) - JULIANDAY(du.start_time)) * 1440 AS avg_duration,
        COUNT(*) AS usage_count
    FROM device_usage du
    JOIN devices d ON du.device_id = d.id
    JOIN houses h ON d.house_id = h.id
    GROUP BY area_range, device_type
    ORDER BY area_range, usage_count DESC
    """
    results = execute_query(query)
    return [dict(row) for row in results] if results else []


@app.get("/analysis/security-event-stats/", response_model=List[SecurityEventStats], tags=["分析功能"])
def get_security_event_stats():
    """分析安防事件类型分布"""
    query = """
    SELECT 
        event_type,
        COUNT(*) AS count,
        ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM security_events), 2) AS percentage
    FROM security_events
    GROUP BY event_type
    ORDER BY count DESC
    """
    results = execute_query(query)
    return [dict(row) for row in results] if results else []


# 可视化 API
@app.get("/visualization/device-usage-frequency/", response_model=VisualizationResponse, tags=["可视化"])
def visualize_device_usage_frequency():
    """可视化设备使用频率"""
    data = get_device_usage_frequency()
    if not data:
        raise HTTPException(status_code=404, detail="No data available for visualization")

    df = pd.DataFrame(data)
    pivot_df = df.pivot_table(index='device_name', columns='time_slot', values='frequency', fill_value=0)

    plt.figure(figsize=(12, 8))
    pivot_df.plot(kind='bar', stacked=True)
    plt.title('设备使用频率按时间段分布')
    plt.ylabel('使用次数')
    plt.xlabel('设备名称')
    plt.xticks(rotation=45)
    plt.legend(title='时间段')
    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    buf.seek(0)
    plot_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()

    return {
        "plot_base64": plot_base64,
        "description": "各设备在不同时间段的使用频率分布"
    }


@app.get("/visualization/area-usage-impact/", response_model=VisualizationResponse, tags=["可视化"])
def visualize_area_usage_impact():
    """可视化房屋面积对设备使用行为的影响"""
    data = get_area_usage_impact()
    if not data:
        raise HTTPException(status_code=404, detail="No data available for visualization")

    df = pd.DataFrame(data)

    plt.figure(figsize=(14, 8))
    for device_type in df['device_type'].unique():
        subset = df[df['device_type'] == device_type]
        plt.plot(subset['area_range'], subset['avg_duration'], marker='o', label=device_type)

    plt.title('不同房屋面积下各类设备的平均使用时长')
    plt.ylabel('平均使用时长 (分钟)')
    plt.xlabel('房屋面积范围 (平方米)')
    plt.legend(title='设备类型')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    buf.seek(0)
    plot_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()

    return {
        "plot_base64": plot_base64,
        "description": "不同房屋面积下各类设备的平均使用时长"
    }


@app.get("/visualization/security-event-stats/", response_model=VisualizationResponse, tags=["可视化"])
def visualize_security_event_stats():
    """可视化安防事件类型分布"""
    data = get_security_event_stats()
    if not data:
        raise HTTPException(status_code=404, detail="No data available for visualization")

    df = pd.DataFrame(data)

    plt.figure(figsize=(10, 8))
    plt.pie(df['count'], labels=df['event_type'], autopct='%1.1f%%',
            startangle=90, shadow=True, explode=[0.05] * len(df))
    plt.title('安防事件类型分布')
    plt.axis('equal')
    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    buf.seek(0)
    plot_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()

    return {
        "plot_base64": plot_base64,
        "description": "安防事件类型分布饼图"
    }


@app.get("/visualization/concurrent-devices/", response_model=VisualizationResponse, tags=["可视化"])
def visualize_concurrent_devices():
    """可视化经常同时使用的设备"""
    data = get_concurrent_devices()
    if not data:
        raise HTTPException(status_code=404, detail="No data available for visualization")

    df = pd.DataFrame(data)
    df['device_pair'] = df['device1_name'] + ' & ' + df['device2_name']

    plt.figure(figsize=(12, 8))
    plt.barh(df['device_pair'], df['concurrent_count'], color='skyblue')
    plt.title('经常同时使用的设备组合')
    plt.xlabel('同时使用次数')
    plt.ylabel('设备组合')
    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    buf.seek(0)
    plot_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()

    return {
        "plot_base64": plot_base64,
        "description": "经常同时使用的设备组合及其同时使用次数"
    }


# 重置数据库 API
@app.post("/reset-db/", tags=["系统管理"])
def reset_database():
    """重置数据库，删除所有数据并重新创建表结构"""
    try:
        import os
        db_file = 'smart_home.db'
        if os.path.exists(db_file):
            os.remove(db_file)
            logger.info("Database file removed")

        init_db()
        return {"message": "Database reset successfully"}
    except Exception as e:
        logger.error(f"Reset DB failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/test-static", tags=["系统管理"])
def test_static():
    try:
        with open("static/swagger-ui-bundle.js", "r", encoding="utf-8") as f:
            content = f.read(100)  # 读取前100个字符
        return {"status": "success", "content_sample": content}
    except FileNotFoundError:
        return {"status": "error", "message": "Static file not found"}




# 健康检查端点
@app.get("/health", tags=["系统管理"])
def health_check():
    """服务健康检查"""
    try:
        # 检查数据库连接和基本查询
        execute_query("SELECT 1")
        return {"status": "ok", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {"status": "error", "error": str(e)}, 500


if __name__ == "__main__":
    PORT = 9999
    try:
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
            s.bind(('', PORT))
        logger.info(f"Port {PORT} is available")
    except OSError:
        PORT = find_free_port()
        logger.warning(f"Port 9999 occupied, using free port: {PORT}")

    logger.info(f"Starting Smart Home API server on port {PORT}")

    uvicorn.run(
        "DB:app",
        host="127.0.0.1",
        port=PORT,
        reload=True,
        log_level="info"
    )