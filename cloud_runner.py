"""从 GitHub Actions Secret 装配临时认证文件，执行后清理。"""
import json
import os
from pathlib import Path
import sys

import local_runner as runner

AUTH_FILES = ('.local-credentials.json', '.cas-session.json', 'checkin_config.json', '.env')


def mask(value):
    if isinstance(value, str) and value:
        escaped = value.replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')
        print('::add-mask::' + escaped, flush=True)


def prepare(raw):
    bundle = json.loads(raw)
    credentials, cookies = bundle['credentials'], bundle.get('cookies', [])
    business, settings = bundle.get('business', {}), bundle['settings']
    if not credentials.get('username') or not credentials.get('password'):
        raise ValueError('缺少账号配置')
    lng, lat = float(settings['lng']), float(settings['lat'])
    if not (-180 <= lng <= 180 and -90 <= lat <= 90):
        raise ValueError('坐标不合法')
    if settings.get('coord', 'gcj02') not in ('gcj02', 'wgs84', 'bd09'):
        raise ValueError('坐标系不合法')
    for value in (*credentials.values(), *business.values()):
        mask(value)
    for cookie in cookies:
        mask(cookie.get('value'))
    runner.write_json(runner.ROOT / '.local-credentials.json', credentials)
    runner.write_json(runner.ROOT / '.cas-session.json', cookies)
    runner.write_json(runner.ROOT / 'checkin_config.json', business)
    for key, value in (('LNG', lng), ('LAT', lat), ('COORD', settings.get('coord', 'gcj02')),
                       ('DKLB', settings.get('dklb', 'PA')), ('DKDZ', settings.get('dkdz', ''))):
        os.environ['CHECKIN_' + key] = str(value)


def main():
    os.umask(0o077)
    raw = os.environ.pop('CHECKIN_AUTH_JSON', '')
    if not raw:
        print('缺少 Actions Secret CHECKIN_AUTH_JSON。')
        return 1
    try:
        try:
            prepare(raw)
        except (ValueError, TypeError, KeyError):
            print('CHECKIN_AUTH_JSON 格式或必需字段不正确。')
            return 1
        if os.environ.get('CHECKIN_VERIFY_LOGIN') == 'true':
            runner.get_auth(force=True)
            print('云端重新登录验证成功。')
        return runner.main()
    except Exception as exc:
        print(runner.error_message(exc))
        return 1
    finally:
        for name in AUTH_FILES:
            (runner.ROOT / name).unlink(missing_ok=True)
        summary = os.environ.get('GITHUB_STEP_SUMMARY')
        if summary:
            state = runner.read_json(runner.STATE)
            safe = {key: state[key] for key in ('date', 'planned_at', 'phase', 'finished_at', 'message') if key in state}
            with open(summary, 'a', encoding='utf-8') as file:
                file.write('## 平安打卡执行状态\n\n')
                if safe:
                    file.write('```json\n' + json.dumps(safe, ensure_ascii=False, indent=2) + '\n```\n')
                else:
                    file.write('本次为手动只查询验证，请查看步骤日志。\n')


if __name__ == '__main__':
    raise SystemExit(main())
