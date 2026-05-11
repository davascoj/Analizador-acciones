import yfinance as yf
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
import json
import time

ACCIONES_INFO = {
    "NVDA": "IA / Chips", "AMD": "IA / Chips", "MSFT": "Tecnología",
    "AVGO": "IA / Chips", "AAPL": "Tecnología", "META": "Tecnología",
    "AMZN": "Tecnología", "GOOGL": "Tecnología", "TSLA": "Autos / Tech",
    "PLTR": "IA / Software", "SMCI": "Servidores IA", "MU": "Memoria / Chips",
    "ARM": "Chips", "QCOM": "Chips", "INTC": "Chips", "TSM": "Chips",
    "ASML": "Chips", "AMAT": "Equipos chips", "LRCX": "Equipos chips",
    "KLAC": "Equipos chips", "SOFI": "Fintech", "COIN": "Cripto / Trading",
    "HOOD": "Trading", "PYPL": "Pagos", "SQ": "Pagos", "XOM": "Energía",
    "CVX": "Energía", "OXY": "Energía", "SLB": "Energía",
    "SPY": "ETF Mercado", "QQQ": "ETF Nasdaq", "SOXX": "ETF Chips",
    "RKLB": "Espacial", "IONQ": "Computación cuántica",
    "SOUN": "IA", "AI": "IA", "UPST": "Fintech IA"
}

ACCIONES = list(ACCIONES_INFO.keys())

def numero(valor):
    try:
        if hasattr(valor, "iloc"):
            return float(valor.iloc[0])
        return float(valor)
    except:
        return None

def rsi_real(close, periodo=14):
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(periodo).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(periodo).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calcular_atr(high, low, close, periodo=14):
    cierre_anterior = close.shift(1)
    tr1 = high - low
    tr2 = (high - cierre_anterior).abs()
    tr3 = (low - cierre_anterior).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(periodo).mean()

def analizar(ticker):
    try:
        df = yf.download(
            ticker,
            period="1y",
            interval="1d",
            auto_adjust=True,
            progress=False,
            threads=False
        )

        if df.empty or len(df) < 220:
            return None

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        close = df["Close"]
        high = df["High"]
        low = df["Low"]
        volume = df["Volume"]

        precio = numero(close.iloc[-1])
        precio_5d = numero(close.iloc[-6])
        ma20 = numero(close.rolling(20).mean().iloc[-1])
        ma50 = numero(close.rolling(50).mean().iloc[-1])
        ma200 = numero(close.rolling(200).mean().iloc[-1])
        rsi = numero(rsi_real(close).iloc[-1])
        volumen_actual = numero(volume.iloc[-1])
        volumen_prom = numero(volume.rolling(20).mean().iloc[-1])
        max20 = numero(high.rolling(20).max().iloc[-1])

        atr = numero(calcular_atr(high, low, close).iloc[-1])
        atr_pct = (atr / precio) * 100 if precio and atr else 0

        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        macd_signal = macd.ewm(span=9, adjust=False).mean()

        macd_val = numero(macd.iloc[-1])
        macd_sig = numero(macd_signal.iloc[-1])

        if None in [precio, precio_5d, ma20, ma50, ma200, rsi, volumen_actual, volumen_prom, max20, macd_val, macd_sig, atr]:
            return None

        momentum = ((precio / precio_5d) - 1) * 100
        volumen_relativo = volumen_actual / volumen_prom if volumen_prom else 0

        score = 40

        if precio > ma20:
            score += 8
        if ma20 > ma50:
            score += 10
        if ma50 > ma200:
            score += 10

        if 50 <= rsi <= 68:
            score += 12
        elif 68 < rsi <= 75:
            score += 5
        elif rsi > 75:
            score -= 12
        elif rsi < 40:
            score -= 8

        if macd_val > macd_sig:
            score += 10

        if volumen_relativo >= 1.5:
            score += 12
        elif volumen_relativo >= 1.2:
            score += 7

        if momentum > 0:
            score += 8
        if momentum > 8:
            score -= 6

        if precio >= max20 * 0.98:
            score += 8

        if atr_pct > 8:
            score -= 8
        elif atr_pct > 5:
            score -= 4
        elif 2 <= atr_pct <= 5:
            score += 4

        score = max(0, min(95, score))

        riesgo = "BAJO"
        if rsi > 75 or momentum > 12 or atr_pct > 8:
            riesgo = "ALTO"
        elif rsi > 68 or momentum > 6 or atr_pct > 5:
            riesgo = "MEDIO"

        hot_score = 0
        if score >= 80:
            hot_score += 1
        if volumen_relativo >= 1.2:
            hot_score += 1
        if momentum > 2:
            hot_score += 1
        if riesgo != "ALTO":
            hot_score += 1

        if hot_score >= 4:
            hot = "🔥🔥🔥"
        elif hot_score == 3:
            hot = "🔥🔥"
        elif hot_score == 2:
            hot = "🔥"
        else:
            hot = ""

        entrada_min = round(precio - (atr * 0.40), 2)
        entrada_max = round(precio + (atr * 0.25), 2)
        stop = round(precio - (atr * 1.5), 2)
        objetivo = round(precio + (atr * 2.5), 2)

        if score >= 75 and riesgo != "ALTO":
            senal = "POSIBLE COMPRA"
        elif score >= 60:
            senal = "VIGILAR"
        else:
            senal = "NO COMPRAR"

        return {
            "Accion": ticker,
            "Sector": ACCIONES_INFO.get(ticker, "Otro"),
            "Precio actual": round(precio, 2),
            "Probabilidad tecnica": round(score, 1),
            "Momentum": round(momentum, 2),
            "Volumen relativo": round(volumen_relativo, 2),
            "ATR": round(atr, 2),
            "ATR %": round(atr_pct, 2),
            "Entrada min": entrada_min,
            "Entrada max": entrada_max,
            "Stop loss": stop,
            "Objetivo": objetivo,
            "RSI": round(rsi, 2),
            "Riesgo": riesgo,
            "Hot Score": hot,
            "Senal": senal
        }

    except Exception as e:
        print(f"ERROR con {ticker}: {e}")
        return None

def main():
    resultados = []

    for ticker in ACCIONES:
        print(f"Analizando {ticker}...")
        r = analizar(ticker)

        if r:
            resultados.append(r)
            print("OK")
        else:
            print("SIN DATOS")

        time.sleep(1)

    resultados = sorted(
        resultados,
        key=lambda x: (
            1 if x["Senal"] == "POSIBLE COMPRA" else 0,
            1 if x["Riesgo"] in ["BAJO", "MEDIO"] else 0,
            len(x["Hot Score"]),
            x["Probabilidad tecnica"]
        ),
        reverse=True
    )

    salida = {
        "actualizado": datetime.now(
            ZoneInfo("America/Bogota")
        ).strftime("%d-%m-%Y %I:%M %p Colombia"),
        "resultados": resultados
    }

    with open("datos_acciones.json", "w", encoding="utf-8") as f:
        json.dump(salida, f, ensure_ascii=False, indent=2)

    pd.DataFrame(resultados).to_excel("analisis_acciones.xlsx", index=False)

    print("ARCHIVOS GENERADOS")

if __name__ == "__main__":
    main()
