"""把一个子任务整理成系统提示词模板的变量。

模板 system.md 集中放在 utils 目录，由各框架加载、注入。
用户指令不进模板，作为用户消息单独发送。
"""

from __future__ import annotations

from utils.data import Case, weekday


def prompt_vars(case: Case) -> dict[str, str]:
    # 环境中的天气包含任务日前后多天，只把当前任务日期对应的天气传给模型。
    current_date = case.time[:10]
    weather = next((item for item in case.weather if item.get('datetime') == current_date), None)
    if weather is None and case.weather:
        weather = case.weather[0]

    weather_text = ''
    if weather:
        temperature = weather.get('temperature') or ['', '']
        weather_text = (
            f"天气{weather.get('category', '')}，"
            f"温度{temperature[0]}到{temperature[1]}，"
            f"湿度{weather.get('humidity', '')}"
        )

    profile_items = [
        (key, value) for key, value in case.profile.items() if key != 'user_id'
    ]
    current_preferences = case.personalized_preference_memory.get('current', {})
    profile_items.extend(current_preferences.items())
    profile_text = '\n'.join(f'- {key}：{_format_profile_value(value)}' for key, value in profile_items)

    return {
        'time': f'{case.time} {weekday(case.time)}',
        'weather': weather_text,
        'addresses': '；'.join(case.addresses),
        'profile': profile_text,
        'history': '',
    }


def _format_profile_value(value: object) -> str:
    if isinstance(value, (list, tuple)):
        return '、'.join(_format_profile_value(item) for item in value)
    if isinstance(value, dict):
        return '；'.join(f'{key}：{_format_profile_value(item)}' for key, item in value.items())
    return str(value)
