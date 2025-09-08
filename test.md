# I8PAY API 对接文档（含完整示例代码）

## 1）概览

- 基础域名：`https://api.inpark.online`
- 认证方式：`Authorization: Basic <base64(mid:signature)>`
- 时间戳：`Request-Time`（13 位毫秒时间戳），**必须**与签名中使用的一致
- 货币：`INR`
- 支付方式（`pm`）：
  - `NATIVE`
  - `INVOKE`
  - `QR`
  - `WALLET`
  - `BANK`

---

## 2）签名规则

### 2.1 POST 请求签名
- 签名字符串：`signatureString = Request-Time + "." + body`
  - `body` 为 **JSON 字符串**，**与实际请求体一字不差**（包含字段顺序、分隔符、空格等）
- 计算方式：
  ```
  signature = hex(hmac-sha256(signatureString, secret))
  ```
- 认证头：
  ```
  Authorization: Basic base64(mid:signature)
  ```

### 2.2 GET 请求签名
- 将查询参数 **按 key 升序**排序，拼接成：`key=value`，以 `&` 连接，得到 `queryParams`
- 签名字符串：`signatureString = Request-Time + "." + queryParams`
- 计算方式与 Authorization 同上

> **实现要点**  
> - `Request-Time` 使用 13 位毫秒时间戳  
> - Python 序列化 JSON 时，建议使用 `json.dumps(obj, separators=(',', ':'), ensure_ascii=False)`，确保与实际请求体完全一致  
> - 任一差异（空格、字段顺序）都会导致签名校验失败

---

## 3）代收（入金）/ Pay-in

### 3.1 接口
**POST** `/api/mcht/payment/create`  
完整 URL：`https://api.inpark.online/api/mcht/payment/create`

**Headers**
```
Content-Type: application/json
Authorization: Basic <base64(mid:signature)>
Request-Time: <13位毫秒时间戳>
```

**Body 参数**
| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| amount | number | 是 | 金额（两位小数） |
| pm | string | 是 | 支付方式（NATIVE / INVOKE / QR / WALLET / BANK） |
| ref | string | 是 | 商户订单号，**唯一** |
| redirect | string | 否 | 支付完成后跳转地址 |

### 3.2 Python 示例（含签名）
```python
import time
import hmac
import hashlib
import base64
import json
import requests

# === 商户配置 ===
mid = "c70f1719017e290354017d1c101d0cc288d06ceb"
secret = "ME2VRe6tWH6weK/NAUJA5lhmewHkB23rA6CdWlrHrAs+/E/E3j3eG3io/GCHbQKqMMurfTNrBj/R4Yy84UziM5YJheiKFKbsWQc5xRoE46E3/0EYy4ZjbK9jhwGyHS+C"

url = "https://api.inpark.online/api/mcht/payment/create"

body = {
    "amount": 100.00,
    "pm": "QR",                          # NATIVE/INVOKE/QR/WALLET/BANK
    "ref": "ORDER_TEST_001",             # 唯一单号
    "redirect": "https://example.com"
}

# 1) 时间戳
request_time = str(int(time.time() * 1000))

# 2) 严格序列化（与实际请求一字不差）
body_str = json.dumps(body, ensure_ascii=False, separators=(',', ':'))

# 3) 签名字符串 = Request-Time + "." + body
signature_str = f"{request_time}.{body_str}"

# 4) HMAC-SHA256
signature_hex = hmac.new(
    secret.encode("utf-8"),
    signature_str.encode("utf-8"),
    hashlib.sha256
).hexdigest()

# 5) Authorization
auth_header = "Basic " + base64.b64encode(f"{mid}:{signature_hex}".encode()).decode()

headers = {
    "Content-Type": "application/json",
    "Authorization": auth_header,
    "Request-Time": request_time
}

resp = requests.post(url, headers=headers, data=body_str, timeout=30)
print("HTTP Status:", resp.status_code)
print("Response:", resp.text)
```

### 3.3 响应示例
```json
{
  "success": true,
  "code": 200,
  "data": {
    "amount": "100",
    "pm": "QR",
    "ref": "ORDER_TEST_001",
    "type": "REDIRECT",
    "currency": "INR",
    "txid": "202509041748A6DIV3G4",
    "paymentUrl": "/x9qn3v3b",
    "createTime": 1756979326312
  }
}
```

---

## 4）查询余额 / Wallet Balance

### 4.1 接口
**GET** `/api/mcht/wallet?currency=INR`  
完整 URL：`https://api.inpark.online/api/mcht/wallet?currency=INR`

**Headers**
```
Authorization: Basic <base64(mid:signature)>
Request-Time: <13位毫秒时间戳>
```

### 4.2 Python 示例（含签名）
```python
import time
import hmac
import hashlib
import base64
import requests

mid = "c70f1719017e290354017d1c101d0cc288d06ceb"
secret = "ME2VRe6tWH6weK/NAUJA5lhmewHkB23rA6CdWlrHrAs+/E/E3j3eG3io/GCHbQKqMMurfTNrBj/R4Yy84UziM5YJheiKFKbsWQc5xRoE46E3/0EYy4ZjbK9jhwGyHS+C"

base_url = "https://api.inpark.online/api/mcht/wallet"
params = {"currency": "INR"}

# 1) 时间戳
request_time = str(int(time.time() * 1000))

# 2) queryParams 升序拼接
query_str = "&".join([f"{k}={v}" for k, v in sorted(params.items())])

# 3) 签名字符串
signature_str = f"{request_time}.{query_str}"

# 4) HMAC-SHA256
signature_hex = hmac.new(
    secret.encode("utf-8"),
    signature_str.encode("utf-8"),
    hashlib.sha256
).hexdigest()

# 5) Authorization
auth_header = "Basic " + base64.b64encode(f"{mid}:{signature_hex}".encode()).decode()

headers = {
    "Authorization": auth_header,
    "Request-Time": request_time
}

resp = requests.get(base_url, headers=headers, params=params, timeout=30)
print("HTTP Status:", resp.status_code)
print("Response:", resp.text)
```

### 4.3 响应示例
```json
{
  "success": true,
  "code": 200,
  "data": [
    {
      "currency": "INR",
      "balance": "1000",
      "freeze": "0",
      "total": "1000"
    }
  ]
}
```

---

## 5）代付（出金）/ Disbursement

### 5.1 接口
**POST** `/api/mcht/disbursement/create`  
完整 URL：`https://api.inpark.online/api/mcht/disbursement/create`

**Headers**
```
Content-Type: application/json
Authorization: Basic <base64(mid:signature)>
Request-Time: <13位毫秒时间戳>
```

**Body 参数**
| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| amount | number | 是 | 金额（两位小数） |
| bankAccountName | string | 是 | 收款人姓名 |
| bankAccountNumber | string | 是 | 收款人账号 |
| bankCode | string | 是 | 收款银行代码（IFSC） |
| ref | string | 是 | 商户订单号，**唯一** |

### 5.2 Python 示例（含签名）
```python
import time
import hmac
import hashlib
import base64
import json
import requests

mid = "c70f1719017e290354017d1c101d0cc288d06ceb"
secret = "ME2VRe6tWH6weK/NAUJA5lhmewHkB23rA6CdWlrHrAs+/E/E3j3eG3io/GCHbQKqMMurfTNrBj/R4Yy84UziM5YJheiKFKbsWQc5xRoE46E3/0EYy4ZjbK9jhwGyHS+C"

url = "https://api.inpark.online/api/mcht/disbursement/create"

body = {
    "amount": 100.00,
    "bankAccountName": "PATANGRAO",
    "bankAccountNumber": "33672747179",
    "bankCode": "SBIN0011132",
    "ref": "WITHDRAW_TEST_001"
}

request_time = str(int(time.time() * 1000))
body_str = json.dumps(body, ensure_ascii=False, separators=(',', ':'))
signature_str = f"{request_time}.{body_str}"

signature_hex = hmac.new(
    secret.encode("utf-8"),
    signature_str.encode("utf-8"),
    hashlib.sha256
).hexdigest()

auth_header = "Basic " + base64.b64encode(f"{mid}:{signature_hex}".encode()).decode()

headers = {
    "Content-Type": "application/json",
    "Authorization": auth_header,
    "Request-Time": request_time
}

resp = requests.post(url, headers=headers, data=body_str, timeout=30)
print("HTTP Status:", resp.status_code)
print("Response:", resp.text)
```

### 5.3 响应示例
```json
{
  "success": true,
  "code": 200,
  "data": {
    "amount": "100",
    "bankAccountName": "PATANGRAO",
    "bankAccountNumber": "33672747179",
    "bankCode": "SBIN0011132",
    "ref": "WITHDRAW_TEST_001",
    "currency": "INR",
    "txid": "PO202509041758A6DIVNRK",
    "netAmount": "100",
    "fee": "0",
    "createTime": 1756979890084
  }
}
```

---

## 6）常见问题与建议

1. **幂等性**：`ref` 请务必保持唯一（可用毫秒时间戳或业务单号前缀）。  
2. **JSON 序列化**：签名用的 JSON 必须与请求体完全一致，推荐 `separators=(',', ':')`。  
3. **时间戳**：使用 13 位毫秒时间戳，且与签名一致。  
4. **网络与重试**：生产环境建议增加超时、重试机制与失败告警，并在 4xx/5xx 时记录签名串与响应体以便排查。  
5. **安全**：请妥善保管 `secret`，避免泄露到客户端或前端代码中。  
