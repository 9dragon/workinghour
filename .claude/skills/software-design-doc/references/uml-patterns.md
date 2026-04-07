# UML 图模板参考

本文件提供数字工厂 / 项目管理系统中最常用的 Mermaid 图模板，按需选用。

---

## 1. 设备实时数据采集 — 时序图

```mermaid
sequenceDiagram
    participant D as 设备/PLC
    participant E as EMQX Broker
    participant S as Spring Boot 服务
    participant R as Redis
    participant DB as MongoDB
    participant WS as WebSocket 客户端

    D->>E: MQTT Publish (topic: device/{id}/metrics)
    E->>S: 消息推送（规则引擎转发）
    S->>S: 数据解析 & 阈值判断
    alt 触发告警
        S->>R: 写入告警状态（防重）
        S->>DB: 异步落库告警记录
        S->>WS: 推送告警通知
    else 正常数据
        S->>R: 更新设备最新状态
        S->>DB: 批量写入时序数据
    end
```

---

## 2. 工单多级审批 — 泳道图

```mermaid
flowchart LR
    subgraph 操作员
        A([提交工单]) --> B[填写工单信息]
        B --> C[提交审批]
    end
    subgraph 班组长
        D{审核} -->|拒绝| E[退回修改]
        D -->|通过| F[转生产主管]
    end
    subgraph 生产主管
        G{审核} -->|拒绝| E
        G -->|通过| H[工单下达]
    end
    subgraph 系统
        C --> D
        F --> G
        H --> I([执行中])
    end
    E --> C
```

---

## 3. 工单状态机 — stateDiagram

```mermaid
stateDiagram-v2
    [*] --> 草稿 : 创建
    草稿 --> 待审批 : 提交
    待审批 --> 草稿 : 退回
    待审批 --> 执行中 : 审批通过
    执行中 --> 暂停 : 异常暂停
    暂停 --> 执行中 : 恢复
    执行中 --> 待验收 : 完工上报
    待验收 --> 执行中 : 验收不通过
    待验收 --> 已完成 : 验收通过
    草稿 --> 已取消 : 取消
    执行中 --> 已取消 : 强制关闭
    已完成 --> [*]
    已取消 --> [*]
```

---

## 4. 报表异步生成 — 时序图

```mermaid
sequenceDiagram
    participant U as 用户
    participant API as API 服务
    participant MQ as RabbitMQ
    participant W as 报表 Worker
    participant OSS as 对象存储
    participant DB as MySQL

    U->>API: 请求生成报表（参数）
    API->>DB: 创建任务记录（状态：待处理）
    API->>MQ: 发布报表任务消息
    API-->>U: 返回任务 ID（立即响应）

    MQ->>W: 消费任务消息
    W->>DB: 更新状态（处理中）
    W->>DB: 查询数据
    W->>W: 生成 Excel/PDF
    W->>OSS: 上传文件
    W->>DB: 更新状态（完成）+ 存储下载链接
    W->>U: WebSocket 推送下载通知

    U->>API: 查询任务状态 / 下载
```

---

## 5. 系统上下文 — C4 Context 风格

```mermaid
graph TB
    subgraph 外部系统
        ERP[ERP 系统\nSAP/金蝶]
        PLC[PLC/传感器]
        SMS[短信平台]
        OSS_EXT[对象存储\nOSS/MinIO]
    end

    subgraph 数字工厂管理系统
        GW[API 网关]
        subgraph 应用层
            SVC1[生产服务]
            SVC2[设备服务]
            SVC3[项目服务]
        end
        subgraph 中间件
            EMQX[EMQX]
            MQ[RabbitMQ]
            Cache[Redis]
        end
        subgraph 存储层
            MySQL[(MySQL)]
            Mongo[(MongoDB)]
        end
    end

    subgraph 客户端
        WebApp[Web 端]
        MobileApp[手机端 App]
    end

    PLC -->|MQTT| EMQX --> SVC2
    ERP -->|REST 定时同步| GW
    GW --> SVC1 & SVC2 & SVC3
    SVC1 & SVC2 & SVC3 --> Cache & MQ
    SVC1 & SVC2 & SVC3 --> MySQL & Mongo
    SVC1 -->|告警短信| SMS
    WebApp & MobileApp --> GW
```

---

## 6. 移动端离线同步 — 时序图

```mermaid
sequenceDiagram
    participant App as 手机端 App
    participant Local as 本地 SQLite
    participant API as 同步 API

    Note over App: 离线状态
    App->>Local: 写入本地操作记录（带 localId）

    Note over App: 网络恢复
    App->>API: 上传本地变更（带 lastSyncTime）
    API->>API: 冲突检测（服务端版本 vs 客户端版本）
    alt 无冲突
        API->>App: 返回确认 + 新数据
        App->>Local: 更新本地状态
    else 有冲突
        API->>App: 返回冲突详情
        App->>App: 展示冲突给用户选择
        App->>API: 提交最终选择
    end
```

---

## 7. 多租户数据隔离 — 流程图

```mermaid
flowchart TD
    REQ[HTTP 请求] --> AUTH{JWT 验证}
    AUTH -->|失败| REJECT[401 Unauthorized]
    AUTH -->|成功| EXTRACT[提取 tenantId + userId]
    EXTRACT --> INJECT[注入 ThreadLocal / MDC]
    INJECT --> FILTER[MyBatis 拦截器\n自动追加 WHERE tenant_id=?]
    FILTER --> QUERY[执行查询]
    QUERY --> CLEAR[清理 ThreadLocal]
    CLEAR --> RESP[返回响应]
```