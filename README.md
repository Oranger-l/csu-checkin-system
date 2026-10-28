# CSU 平安打卡

基于 [IAMNAVY/fuck-csu-checkin](https://github.com/IAMNAVY/fuck-csu-checkin) 的 Python 3.12 项目。当前 Fork 已关闭定时打卡和邮件通知；GitHub Actions 仅保留手动只查询验证。

## 复用与部署

### 1. Fork 并启用 Actions

Fork 到自己的 GitHub 账号，在自己的仓库打开 **Actions**，按页面提示启用工作流。配置在自己的仓库完成，无需修改 Python 源码。

Fork 不会复制原仓库的 Secrets；学校凭据需自行配置，不能复用其他人的认证信息。

### 2. 配置 Secrets 和 Variables

进入自己仓库的 **Settings → Secrets and variables → Actions**，按表格分别添加：

| 名称 | 添加位置 | 内容 |
| --- | --- | --- |
| `CHECKIN_AUTH_JSON` | **Secrets → New repository secret** | 自己的学校认证与实际位置 JSON，格式见下文 |

旧版的 `CHECKIN_ENABLED` 变量及邮件 Secrets 即使仍保留，当前工作流也不会读取它们。

### 3. 配置自己的学校认证

将下面 JSON 修改后，整体粘贴到 `CHECKIN_AUTH_JSON` 的值中。示例账号、密码和坐标均为占位内容；`110.0, 30.0` 是虚构坐标，必须替换为自己的实际位置。

```json
{
  "credentials": {
    "username": "your-student-id",
    "password": "your-school-password"
  },
  "cookies": [],
  "business": {},
  "settings": {
    "lng": 110.0,
    "lat": 30.0,
    "coord": "gcj02",
    "dklb": "PA"
  }
}
```

- `credentials`：自己的统一认证学号和密码。
- `settings`：`lng` 是经度，`lat` 是纬度；`coord` 与坐标来源一致，支持 `gcj02`（高德）、`wgs84`、`bd09`（百度）；`dklb: PA` 表示平安打卡。位置变化时需更新，云端不会读取手机实时 GPS。
- `business`：可先保持 `{}`，脚本会尝试正常登录获取业务凭据；已有自己的有效配置时，可填 `{"token": "自己的业务token", "casual": "与其配套的casual"}`。凭据失效会尝试重新登录，并不代表到期后永久无法使用。
- `cookies`：无可用记录时可先用 `[]`。如果学校要求二次认证，需本人先在学校官方页面完成认证，再更新自己的登录记录；只有账号密码不保证每次都能通过二次认证。

已有本机认证文件时，对应关系为：`.local-credentials.json` → `credentials`，`.cas-session.json` → `cookies`，`checkin_config.json` → `business`；实际位置填入 `settings`。这些文件包含敏感信息，只能存入自己的 Secret，不应上传仓库。

Cookie 使用对象数组，每项保留 `name`、`value`、`domain`、`path`。只加载 `ca.csu.edu.cn` 和 `zhxg.csu.edu.cn` 的记录；同名 Cookie 也要保留各自域名和路径，不能合并。认证摘要或显示“已配置”的核对报告不能替代这些真实配置。

### 4. 手动只查询验证

进入 **Actions → 平安打卡 → Run workflow**，选择默认分支运行。`verify_login` 默认开启，用于验证云端重新登录。此工作流只查询学校状态，不提交打卡，也不发送邮件。

## 当前运行方式

- GitHub Actions 没有定时触发器；只有用户手动运行时才会执行只查询验证。
- 工作流没有邮件步骤，不会读取已保存的 QQ SMTP Secrets。
- 本地 `local_runner.py --scheduled` 和 `--submit` 仍是手动可调用的真实打卡命令，请勿误用。
- 学校要求重新二次认证时，需本人完成并更新 `CHECKIN_AUTH_JSON`，之后重新进行只查询验证。

## 本地检查

使用 Python 3.12 安装依赖并运行离线测试：

```sh
python -m pip install -r requirements.txt
python -m unittest discover -v
```

已有自己的本机认证和位置配置后，可只查询验证：

```sh
python local_runner.py --dry-run
```

云端认证文件仅在临时 runner 中使用，执行结束时清理，不上传为产物。不要把账号密码、Cookie、token、SMTP 授权码或真实位置提交进源码、Issue 或公开日志。
