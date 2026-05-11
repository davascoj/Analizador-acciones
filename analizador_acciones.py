import pandas as pd
import numpy as np
from urllib.request import urlopen, Request
from io import StringIO
from datetime import datetime, timezone
import json
import time

ACCIONES = [
    "NVDA", "AMD", "MSFT", "AVGO", "AAPL",
    "META", "AMZN", "TSLA", "GOOGL", "PLTR"
]

def descargar_stooq(ticker, intentos=3):
    simbolo = ticker.lower() + ".us"
    url = f"https://stooq.com/q/d/l/?s={simbolo}&i=d"

    for intento in range(1, intentos + 1):
        try:
            req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(req, timeout=60) as r:
                contenido = r.read().decode("utf-8", errors="ignore")

            lineas = [x.strip() for x in contenido.splitlines() if x.strip()]
            lineas = [x for x in lineas if x.count(",") >= 5]

            if len(lineas) < 50:
                return pd.DataFrame()

            limpio = "\n".join(lineas)
            df = pd.read_csv(StringIO(limpio))

            if df.empty or "Close" not in df.columns:
                return pd.DataFrame()

            df["Date"] = pd.to_datetime(df["Date"])
            df = df.sort_values("Date")
            return df.tail(260).copy()

        except Exception as e:
            print(f"Intento {intento} fallo con {ticker}: {e}")
            time.sleep(3)

    return pd.DataFrame()

def rsi(close, window=14):
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def ema(series, span):
    return series.ewm(span=span, adjust=False).mean()

def atr(high, low, close, window=14):
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs()
    ], axis=1).max(axis=1)
    return tr.rolling(window).mean()

def analizar(ticker):
    df = descargar_stooq(ticker)
    if df.empty or len(df) < 210:
        return None

    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    vol = df["Volume"]

    df["MA20"] = close.rolling(20).mean()
    df["MA50"] = close.rolling(50).mean()
    df["MA200"] = close.rolling(200).mean()
    df["RSI"] = rsi(close)
    df["EMA12"] = ema(close, 12)
    df["EMA26"] = ema(close, 26)
    df["MACD"] = df["EMA12"] - df["EMA26"]
    df["MACD_SIGNAL"] = ema(df["MACD"], 9)
    df["ATR"] = atr(high, low, close)
    df["VOL_PROM"] = vol.rolling(20).mean()
    df["MAX20"] = high.rolling(20).max()
    df["RET_5D"] = close.pct_change(5) * 100
    df["RET_20D"] = close.pct_change(20) * 100

    u = df.iloc[-1]

    precio = float(u["Close"])
    ma20 = float(u["MA20"])
    ma50 = float(u["MA50"])
    ma200 = float(u["MA200"])
    rsi_val = float(u["RSI"])
    volumen = float(u["Volume"])
    volprom = float(u["VOL_PROM"])
    macd_val = float(u["MACD"])
    macd_sig = float(u["MACD_SIGNAL"])
    atr_val = float(u["ATR"])
    max20 = float(u["MAX20"])
    ret5 = float(u["RET_5D"])
    ret20 = float(u["RET_20D"])

    score = 0

    if precio > ma20: score += 10
    if ma20 > ma50: score += 13
    if ma50 > ma200: score += 13

    if 50 <= rsi_val <= 68: score += 15
    elif 68 < rsi_val <= 75: score += 5
    elif rsi_val > 75: score -= 15
    elif rsi_val < 40: score -= 8

    if macd_val > macd_sig: score += 14
    else: score -= 5

    if volumen > volprom * 1.2: score += 12
    elif volumen < volprom * 0.8: score -= 4

    if precio >= max20 * 0.98: score += 9
    if precio <= ma20 * 1.08: score += 8
    else: score -= 8

    if ret5 > 12: score -= 8
    elif ret5 > 0: score += 4

    if ret20 > 0: score += 4

    prob = max(0, min(95, score))

    entrada_min = precio - atr_val * 0.40
    entrada_max = precio + atr_val * 0.25
    stop = precio - atr_val * 1.5
    objetivo = precio + atr_val * 2.5

    riesgo = "BAJO"
    if rsi_val > 75 or ret5 > 12 or precio > ma20 * 1.12:
        riesgo = "ALTO"
    elif rsi_val > 68 or precio > ma20 * 1.08:
        riesgo = "MEDIO"

    if prob >= 75 and rsi_val < 75 and riesgo != "ALTO":
        senal = "POSIBLE COMPRA"
    elif prob >= 60:
        senal = "VIGILAR / ESPERAR CONFIRMACION"
    else:
        senal = "NO COMPRAR TODAVIA"

    return {
        "Accion": ticker,
        "Fecha dato": str(u["Date"].date()),
        "Precio actual": round(precio, 2),
        "Probabilidad tecnica": round(prob, 1),
        "Entrada min": round(entrada_min, 2),
        "Entrada max": round(entrada_max, 2),
        "Stop loss": round(stop, 2),
        "Objetivo": round(objetivo, 2),
        "RSI": round(rsi_val, 2),
        "Riesgo": riesgo,
        "Senal": senal
    }

def main():
    resultados = []

    for ticker in ACCIONES:
        print(f"Analizando {ticker}...")
        try:
            r = analizar(ticker)
            if r:
                resultados.append(r)
                print("OK")
            else:
                print("SIN DATOS")
        except Exception as e:
            print(f"ERROR con {ticker}: {e}")
        time.sleep(1)

    resultados = sorted(resultados, key=lambda x: x["Probabilidad tecnica"], reverse=True)

    salida = {
        "actualizado": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "resultados": resultados,
        "nota": "Probabilidad tecnica estimada. No garantiza ganancias."
    }

    with open("datos_acciones.json", "w", encoding="utf-8") as f:
        json.dump(salida, f, ensure_ascii=False, indent=2)

    pd.DataFrame(resultados).to_excel("analisis_acciones.xlsx", index=False)

    print("Archivo datos_acciones.json creado.")
    print("Archivo analisis_acciones.xlsx creado.")

if __name__ == "__main__":
    main()
