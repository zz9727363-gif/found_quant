import os
import warnings
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import requests
import yfinance as yf

# yfinance 1.7.0 内部仍使用 pandas 已弃用参数；仅隐藏这条第三方弃用提示。
if hasattr(pd.errors, "Pandas4Warning"):
    warnings.filterwarnings("ignore", category=pd.errors.Pandas4Warning, module=r"yfinance\..*")

base = Decimal("10")  # 基础定投金额，单位：元
MAX_AMOUNT = Decimal("40")
MA_DAYS = 250
PUSHPLUS_API = "https://www.pushplus.plus/send"


def send_pushplus(content, title="纳指定投提醒"):
    """使用环境变量中的 PushPlus Token 推送结果；未配置时安全跳过。"""
    token = os.getenv("PUSHPLUS_TOKEN", "").strip()
    if not token:
        print("未配置 PUSHPLUS_TOKEN，跳过微信推送。")
        return False

    payload = {
        "token": token,
        "title": title,
        "content": content,
        "template": "txt",
    }
    try:
        # 云端环境直接访问 PushPlus，忽略可能存在的代理环境变量。
        session = requests.Session()
        session.trust_env = False
        response = session.post(
            PUSHPLUS_API,
            json=payload,
            timeout=10,
            proxies={"http": None, "https": None},
        )
        response.raise_for_status()
        result = response.json()
        if str(result.get("code")) != "200":
            message = result.get("msg", "PushPlus 返回失败")
            detail = result.get("data")
            if detail:
                message = f"{message}（{detail}）"
            raise RuntimeError(message)
        print("PushPlus 微信推送成功。")
        return True
    except (requests.RequestException, ValueError, RuntimeError) as error:
        print(f"PushPlus 推送失败：{error}")
        return False


def calculate_ma250_metrics(closes):
    """根据最近 250 个有效收盘价计算最新价格、MA250 和偏离度。"""
    values = [Decimal(str(value)) for value in closes]
    if len(values) < MA_DAYS:
        raise ValueError(f"有效交易日不足 {MA_DAYS} 个，无法计算 MA250")
    values = values[-MA_DAYS:]
    if not all(value.is_finite() and value > 0 for value in values):
        raise ValueError("纳指收盘价包含无效数据")

    latest_close = values[-1]
    ma250 = sum(values, Decimal("0")) / Decimal(MA_DAYS)
    deviation = (latest_close / ma250 - Decimal("1")) * Decimal("100")
    return latest_close, ma250, deviation


def calculate_investment_amount(deviation):
    """用均线偏离度计算乘数、限额后的金额和估值警告。"""
    deviation = Decimal(str(deviation))
    if not deviation.is_finite():
        raise ValueError("均线偏离度必须是有效数值")

    multiplier = Decimal("1") - deviation / Decimal("50")
    raw_amount = base * multiplier
    # 先应用 0～40 元边界，再按四舍五入保留到分。
    amount = min(MAX_AMOUNT, max(Decimal("0"), raw_amount))
    amount = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    warning = None
    if deviation > Decimal("30"):
        warning = "极度高估警告"
    elif deviation < Decimal("-30"):
        warning = "极度低估警告"
    return multiplier, amount, warning


def main():
    try:
        # 获取过去一年日线，周末及休市日自然跳过。
        history = yf.Ticker("^NDX").history(
            period="1y", interval="1d", auto_adjust=False, timeout=20,
        )
        if history.empty or "Close" not in history.columns:
            raise ValueError("未获取到纳指行情，请检查云端网络")

        closes = pd.to_numeric(history["Close"], errors="coerce").dropna().sort_index()
        # 美东常规收盘前排除当天尚未结束的日线，避免盘中值改变结果。
        now = datetime.now(ZoneInfo("America/New_York"))
        closes = closes[[
            stamp.date() < now.date()
            or (stamp.date() == now.date() and now.hour >= 16)
            for stamp in closes.index
        ]]

        latest_close, ma250, deviation = calculate_ma250_metrics(closes)
        multiplier, amount, warning = calculate_investment_amount(deviation)

        # 显示行情日期，避免休市日被误认为是当天的新信号。
        report_lines = [
            "纳斯达克100指数 · MA250 定投参考",
            f"最新交易日期：{closes.index[-1]:%Y-%m-%d}（美东）",
            f"当前收盘价：{latest_close:,.2f} 点",
            f"MA250：{ma250:,.2f} 点",
            f"均线偏离度：{deviation:+.4f}%",
            f"基础金额：{base:.2f} 元",
            f"投资乘数（1 - 偏离度 / 50）：{multiplier:.6f}",
        ]
        if warning:
            report_lines.append(f"⚠ {warning}：当前偏离度为 {deviation:+.4f}%！")
        report_lines.append(f"按设定规则，建议买入：{amount:.2f} 元")
        report = "\n".join(report_lines)

        print("=" * 54)
        print(report)
        print("=" * 54)
        print("仅按纳指相对 MA250 的偏离度计算；不会自动下单。")
        print("休市日沿用最近行情；同一交易日期重复运行不会产生新信号。")
        send_pushplus(report)
    except Exception as error:
        print(f"获取或计算失败：{error}")
        print("数据不可用，本次暂停。按设定规则，建议买入：0.00 元")


if __name__ == "__main__":
    main()
