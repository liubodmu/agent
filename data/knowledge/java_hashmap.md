# Java HashMap 面试知识点

## HashMap 基本原理

HashMap 是基于哈希表实现的 Map 接口，存储键值对（Key-Value）。

核心特点：
- 允许 null key 和 null value
- 非线程安全
- 不保证顺序
- 默认初始容量 16，负载因子 0.75

## HashMap 底层数据结构

JDK 1.8 之前：数组 + 链表
JDK 1.8 之后：数组 + 链表 + 红黑树

当链表长度超过 8 且数组长度超过 64 时，链表转为红黑树，提高查找效率。

## HashMap 的 put 流程

1. 计算 key 的 hash 值：`(h = key.hashCode()) ^ (h >>> 16)`
2. 计算数组下标：`(n - 1) & hash`
3. 如果该位置为空，直接放入
4. 如果不为空（哈希冲突）：
   - key 相同则覆盖 value
   - key 不同则追加到链表/红黑树
5. 判断是否需要扩容

## HashMap 扩容机制

- 当元素数量超过 容量 × 负载因子 时触发扩容
- 每次扩容为原来的 2 倍
- 扩容后需要重新计算所有元素的位置（rehash）
- JDK 1.8 优化：扩容时元素要么在原位置，要么在原位置+旧容量的位置

## HashMap 线程安全问题

- JDK 1.7 中并发 put 可能导致死循环（链表成环）
- JDK 1.8 中不会死循环，但会导致数据丢失
- 解决方案：ConcurrentHashMap、Collections.synchronizedMap()

## ConcurrentHashMap 原理

JDK 1.7：分段锁（Segment），每个 Segment 是一个小 HashMap
JDK 1.8：CAS + synchronized，锁粒度更细（锁单个 Node）

## 面试常见追问

Q: HashMap 的 key 可以是自定义对象吗？
A: 可以，但必须重写 hashCode() 和 equals() 方法。

Q: 为什么容量必须是 2 的幂次方？
A: 为了用位运算 (n-1)&hash 代替取模运算，效率更高。

Q: 为什么负载因子是 0.75？
A: 时间和空间的折中。太大导致冲突多，太小浪费空间。
