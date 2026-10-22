# CSU 平安打卡

基于 https://github.com/IAMNAVY/fuck-csu-checkin 的 Python 3.12 命令行项目，适配 GitHub Actions。

## 云端运行

- 手动运行工作流只进行登录、查询和校验，不提交打卡。
- 仓库变量 `CHECKIN_ENABLED=true` 后，定时任务才会提交。
- 定时任务每天北京时间 20:13 启动，在当天 20:13–20:23 内随机执行一次。
- 使用配置的实际坐标；已打卡、时段不允许或位置校验失败时跳过提交。
- 密码、token、Cookie 和坐标统一放入 Actions Secret `CHECKIN_AUTH_JSON`，不能提交进仓库。
- 初次迁移应手动验证云端登录。学校要求二次认证时需本人完成并更新认证记录。
- GitHub 调度可能延迟；私有仓库等待随机时间会占用 Actions 分钟额度，随机等待平均约每月 150 分钟，另加安装和测试时间。此项目不会开启付费预算。
- 云端首次验证成功后停用其他设备的定时任务，避免重复运行。

## Secret 结构（示意，无真实凭据）

```json
{
  "credentials": {"username": "your-id", "password": "your-password"},
  "cookies": [],
  "business": {"token": "your-token", "casual": "your-casual"},
  "settings": {"lng": "your-longitude", "lat": "your-latitude", "coord": "gcj02", "dklb": "PA"}
}
```

`.cas-session.json` 只在临时 runner 中使用。每次执行后清除认证文件，不上传为产物。

## 本地检查

```sh
python -m pip install -r requirements.txt
python -m unittest discover -v
python local_runner.py --dry-run
```
