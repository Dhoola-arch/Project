# 数据库课程学习记录
# 第一周
课堂学习：

1.了解了数据库的概念，原理，应用场景等

2.了解了数据库语言的作用和数据库系统的架构

课后完成：

1.下载并安装了postgresql


收获：

1.postgresql的安装完成后，自己使用的admin和密码需要好好记住

2.确保SQL的默认接口不会被拦截而导致问题


# 第二周
课堂学习：

1.关系数据库的结构

2.关系，元组，属性的概念

3.码的类型：超码，候选码，主码，外码，

课后完成：

1.尝试创建一个关系表

```
CREATE TABLE students (
    student_id SERIAL PRIMARY KEY,          -- 学生ID 
    name VARCHAR(50) NOT NULL,              -- 姓名
    gender CHAR(1) CHECK (gender IN ('M', 'F', 'O')), -- 性别 
    birth_date DATE,                        -- 出生日期
    enrollment_date DATE DEFAULT CURRENT_DATE, -- 入学日期
);
```

收获：

1.主码的非空性和唯一性

2.外码的精确引用要求

3.属性是否允许为空


# 第三周
课堂学习：

1.关系代数和SELECT的使用，以及结合where和and

2.常见的数据类型和使用

课后完成：

1.尝试使用SELECT选择来查询数据

```
-- 查询所有学生信息
SELECT * FROM students;

-- 查询特定列（姓名和邮箱）
SELECT name, email FROM students;

-- 限制返回行数（前5名学生）
SELECT * FROM students LIMIT 5;

```

收获：

1.不同数据类型对应的正确写法

2.varchar的长度设置考量



# 第四周
课堂学习：

1.Datagrip的下载和安装

2.SQL的配置和链接

3.模糊查询和转义字符

课后完成：

1.实操Datagrip完成模糊查询等操作

2.转义字符的使用

```
SELECT * FROM students 
WHERE name LIKE '张%';

SELECT * FROM students 
WHERE name LIKE '%三%';

SELECT * FROM students 
WHERE name LIKE '_四%';

SELECT * FROM students 
WHERE name LIKE '%\_%' ESCAPE '\';  -- 查找包含 _ 的名字

SELECT * FROM students 
WHERE name LIKE '%\%%' ESCAPE '\';  -- 查找包含 % 的名字

SELECT * FROM students 
WHERE name LIKE '%#_%' ESCAPE '#';  -- 使用 # 作为转义符

```

收获：

1.LIKE查询内容的大小写敏感

2.集合操作对所选内容的列数和类型要求

# 第五周
课堂学习：

1.空值的算术运算和比较

2.distinct消除重复值

3.聚集函数和嵌套子查询

课后完成：

1.嵌套子查询结合聚合函数的代码编写

```
-- 找出每个班级中分数最高的学生
SELECT 
    student_id,
    name,
    class_id,
    score
FROM students s1
WHERE score = (
    SELECT MAX(score)
    FROM students s2
    WHERE s2.class_id = s1.class_id
);

```

收获：

1.unknown和null的关系

2.聚合函数的使用逻辑

# 第六周
课堂学习：

1.数据库的增删改

2.使用rank进行排序

课后完成：

1.尝试对已有数据进行增删改的操作

```
-- 插入单个学生
INSERT INTO students (name, gender, birth_date, class_id, email)
VALUES ('赵六', 'M', '2004-05-20', 1, 'zhaoliu@edu.cn');

-- 更新单个学生信息
UPDATE students
SET phone = '13912345678', updated_at = NOW()
WHERE name = '赵六';

-- 删除单个学生
DELETE FROM students
WHERE name = '孙八';
```



收获：

1.ORDER BY 务必明确指定 ASC/DESC，否则默认为 ASC。

2.NULL 会被视为最小值：在升序排名中排在最前，在降序排名中排在最后。

3.where子句中不能直接引用rank，正确做法应该使用子查询


# 第七周
课堂学习：

1.多种不同的连接类型和不同的连接条件使用



2.视图的构建和使用

课后完成：

1.试用连接操作替换WHERE

```
SELECT s.name, c.class_name
FROM students s, classes c
WHERE s.class_id = c.class_id
  AND c.department = '计算机学院';

SELECT s.name, c.class_name
FROM students s
INNER JOIN classes c ON s.class_id = c.class_id
WHERE c.department = '计算机学院';

```


2.创建视图

```
-- 创建学生详情视图
CREATE VIEW student_details AS
SELECT 
    s.student_id,
    s.name AS student_name,
    s.gender,
    s.birth_date,
    c.class_name,
    c.department,
    t.name AS advisor_name
FROM students s
JOIN classes c ON s.class_id = c.class_id
LEFT JOIN teachers t ON c.advisor_id = t.teacher_id;

-- 使用视图查询
SELECT * FROM student_details 
WHERE department = '计算机学院';

```

收获：

1.简单视图封装常用连接来完成

2.连接类型的声明很重要

3.复杂查询避免通过视图二次连接

# 第八周
课堂学习：

1.高级数据类型

2.时间和日期相关函数

3.类型转换

课后完成：

1.日期数据处理

```
-- 获取当前日期和时间
SELECT CURRENT_DATE AS today, CURRENT_TIME AS now, NOW() AS timestamp_now;

-- 提取日期部分
SELECT 
    event_name,
    EXTRACT(YEAR FROM start_date) AS event_year,
    EXTRACT(MONTH FROM event_timestamp) AS event_month,
    DATE_PART('dow', start_date) AS day_of_week -- 0=周日, 6=周六
FROM events;

-- 格式化日期
SELECT 
    event_name,
    TO_CHAR(start_date, 'YYYY年MM月DD日') AS date_cn,
    TO_CHAR(event_timestamp, 'HH24:MI "on" Dy, DD Mon YYYY') AS formatted_timestamp
FROM events;
```

2.计算时间间隔

```
-- 计算两个日期之间的天数
SELECT 
    event_name,
    start_date,
    CURRENT_DATE - start_date AS days_since_start
FROM events;

-- 精确时间差
SELECT 
    event_name,
    event_timestamp,
    NOW() - event_timestamp AS time_elapsed,
    AGE(NOW(), event_timestamp) AS precise_interval
FROM events;

```

收获：

1.储存和查询时的时区转换为所在时区，建议统一为UTC

2.服务器、数据库、应用层、客户端浏览器可能处于不同时区，务必在存储和传输时明确标注时区信息

3.在where子句里使用日期函数会导致性能变差，需要避免这个问题

# 第九周
课堂学习：

1.函数的自定义

2.触发器

3.SQL注入攻击原理

课后完成：

1.创建一个简单的计算折扣价格的函数

```
-- 创建折扣计算函数
CREATE OR REPLACE FUNCTION calculate_discount_price(
    base_price NUMERIC, 
    discount_rate NUMERIC
) RETURNS NUMERIC AS $$
DECLARE
    discount_amount NUMERIC;
    final_price NUMERIC;
BEGIN
    -- 计算折扣金额
    discount_amount := base_price * (discount_rate / 100);
    
    -- 确保折扣后价格不低于0
    final_price := GREATEST(base_price - discount_amount, 0);
    
    RETURN ROUND(final_price, 2);
END;

```

2.设置一个触发器，当任何记录被修改时，更新为当前时间戳

```
CREATE TRIGGER update_student_timestamp
BEFORE UPDATE ON students
FOR EACH ROW
EXECUTE FUNCTION update_last_modified();
```

收获：

1.将 SQL 语句与用户输入分离，输入内容始终被视为数据而非代码，可避免SQL注入攻击

2，简单转义不完全可靠


# 第十周
课堂学习：

1.ER图组成和绘制

2.实体，属性和关系的配置

课后完成：

1.非关系型数据库的配置，Mongodb

收获：

1.注意多对多关系的拆解

2.ER图设计：宁可多拆表，不要少拆表

# 第十一周
课堂学习：

1.第一范式

2.第二范式

3.函数依赖

课后完成：

1.第二范式的规范化

```
CREATE TABLE orders (
    order_id INT,
    customer_id INT,
    customer_name VARCHAR(50),
    product_id INT,
    product_name VARCHAR(50),
    category VARCHAR(30),
    quantity INT,
    price DECIMAL(10,2),
    order_date DATE,
    PRIMARY KEY (order_id, product_id) -- 复合主键
);

-- 1. 客户表 (消除客户信息部分依赖)
CREATE TABLE customers (
    customer_id INT PRIMARY KEY,
    customer_name VARCHAR(50) NOT NULL
);

-- 2. 产品表 (消除产品信息部分依赖)
CREATE TABLE products (
    product_id INT PRIMARY KEY,
    product_name VARCHAR(50) NOT NULL,
    category VARCHAR(30) NOT NULL,
    price DECIMAL(10,2) NOT NULL
);

-- 3. 订单主表
CREATE TABLE orders (
    order_id INT PRIMARY KEY,
    customer_id INT NOT NULL,
    order_date DATE NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- 4. 订单明细表 
CREATE TABLE order_details (
    order_id INT,
    product_id INT,
    quantity INT NOT NULL CHECK (quantity > 0),
    PRIMARY KEY (order_id, product_id),
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);
```

收获：

1.1NF 是规范化的基础，确保属性的原子性，不可再分；2NF 在此基础上解决部分依赖问题，使非主属性完全依赖于主键。


# 第十二周
课堂学习：

1.第三范式

2.BCNF范式

课后完成：

1.BCNF范式的规范化
```
-- 违反BCNF的示例
CREATE TABLE course_enrollment (
    student_id INT,
    course_id INT,
    instructor_id INT,
    PRIMARY KEY (student_id, course_id)
);

-- 假设：
-- 每个课程只有一个教师 (course_id → instructor_id)
-- 每个教师只教一门课程 (instructor_id → course_id)

-- BCNF规范化方案：
CREATE TABLE course_instructor (
    course_id INT PRIMARY KEY,
    instructor_id INT UNIQUE NOT NULL
);

CREATE TABLE enrollments (
    student_id INT,
    course_id INT REFERENCES course_instructor(course_id),
    PRIMARY KEY (student_id, course_id)
);
```

收获：

1.3NF：重点消除非主属性对主键的传递依赖，确保非主属性直接依赖主键。

2.BCNF：在 3NF 基础上，消除主属性之间的依赖关系，要求所有依赖的左侧为超键，是更严格的规范化标准。

3.实际设计中，BCNF 主要用于复杂依赖场景（如多候选键表），而 3NF 已能满足大多数业务需求。规范化的核心是在数据一致性和查询效率之间找到平衡，避免过度设计或忽视依赖异常。



# 第十三周
课堂学习：

1.python与数据库的连接


课后完成：

1.postgresql和python的连接

```import psycopg2
from psycopg2 import sql

# 创建连接
conn = psycopg2.connect(
    host="localhost",
    dbname="your_db",
    user="your_username",
    password="your_password",
    port=5432
)

try:
    # 创建游标
    with conn.cursor() as cursor:
        # 安全SQL拼接（防注入）
        query = sql.SQL("SELECT * FROM products WHERE category = {}").format(
            sql.Literal('electronics')
        )
        cursor.execute(query)
        
        # 获取所有结果
        products = cursor.fetchall()
        for product in products:
            print(product)
            
        # 批量插入
        data = [('phone', 599), ('laptop', 1299)]
        insert_query = sql.SQL("INSERT INTO products (name, price) VALUES {}").format(
            sql.SQL(',').join(map(sql.Literal, data))
        )
        cursor.execute(insert_query)
        
    conn.commit()
    
except psycopg2.Error as e:
    print(f"PostgreSQL error: {e}")
    conn.rollback()
    
finally:
    if conn:
        conn.close()
```



收获：

1.直接使用相关的包即可关联数据库

2.注意防SQL注入






# 第十四周
课堂学习：

1.储存结构和索引

2.查询的优化

3.索引

课后完成：

1.创建索引加速查询
```
CREATE INDEX idx_department ON employees(department);
CREATE INDEX idx_salary ON employees(salary);
CREATE INDEX idx_department_salary ON employees(department, salary);
```

2.使用EXPLAIN函数分析查询计划
```
EXPLAIN 
SELECT * FROM employees 
WHERE department = 'Engineering' 
  AND salary > 100000;
```


收获：

1.索引的写性能下降可使读性能提升，需平衡读写比例

2.EXPLAIN起到重要的导航作用，优化前必看执行计划，避免盲目调优

# 第十五周
课堂学习：

1.事务的四个属性

2.事务的分隔等级

课后完成：

1.空闲事务的检测
```

SELECT 
    pid,
    usename,
    state,
    query,
    age(now(), state_change) AS idle_duration
FROM pg_stat_activity 
WHERE state = 'idle in transaction' 
  AND now() - state_change > interval '2 minutes'
ORDER BY idle_duration DESC;

```

收获：

  隔离级别	         脏读       不可重复读      幻读	        	
READ UNCOMMITTED	 ❌可能	    ❌可能	     ❌可能
READ COMMITTED	    ✅避免	    ❌可能	     ❌可能	
REPEATABLE READ	    ✅避免	    ✅避免	     ❌可能
SERIALIZABLE	     ✅避免	    ✅避免	     ✅避免

# 第十六周
了解DUCKdb和一些其他数据库的基本信息和使用方式

问题总结：
1.很多时候需要AI辅助学习和完成作业

