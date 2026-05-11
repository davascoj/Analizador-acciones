import yfinance as yf
import pandas as pd
from datetime import datetime, timezone
import json
import time

ACCIONES = [
    "NVDA", "AMD", "MSFT", "AVGO", "AAPL",
    "META", "AMZN", "TSLA", "GOOGL", "PLTR"
]

def numero(valor):
    try:
        if hasattr(valor, "iloc"):
            return float(valor.iloc[0])
        return float(valor)
    except:
        return None

def analizar(ticker):
    try:
        df = yf.download(
            ticker,
            period="6mo",
            interval="1d",
            auto_adjust=True,
            progress=False,
            threads=False
        )

        if df.empty or len(df) < 60:
            return None

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        close = df["Close"]

        precio = numero(close.iloc[-1])
        precio_5d = numero(close.iloc[-6])
        ma20 = numero(close.rolling(20).mean().iloc[-1])
        ma50 = numero(close.rolling(50).mean().iloc[-1])
        volatilidad = numero(close.pct_change().std() * 100)

        if precio is None or precio_5d is None or ma20 is None or ma50 is None:
            return None

        cambio5 = ((precio / precio_5d) - 1) * 100

        score = 50

        if precio > ma20:
            score += 10

        if ma20 > ma50:
            score += 15

        if cambio5 > 0:
            score += 10

        riesgo = "BAJO"

        if volatilidad and volatilidad > 4:
            riesgo = "ALTO"
        elif volatilidad and volatilidad > 2:
            riesgo = "MEDIO"

        entrada_min = round(precio * 0.985, 2)
        entrada_max = round(precio * 1.01, 2)
        stop = round(precio * 0.95, 2)
        objetivo = round(precio * 1.08, 2)

        if score >= 75:
            senal = "POSIBLE COMPRA"
        elif score >= 60:
            senal = "VIGILAR"
        else:
            senal = "NO COMPRAR"

        return {
            "Accion": ticker,
            "Precio actual": round(precio, 2),
            "Probabilidad tecnica": round(score, 1),
            "Entrada min": entrada_min,
            "Entrada max": entrada_max,
            "Stop loss": stop,
            "Objetivo": objetivo,
            "RSI": round(volatilidad, 2) if volatilidad else 0,
            "Riesgo": riesgo,
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
        key=lambda x: x["Probabilidad tecnica"],
        reverse=True
    )

    salida = {
        "actualizado": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "resultados": resultados
    }

    with open("datos_acciones.json", "w", encoding="utf-8") as f:
        json.dump(salida, f, ensure_ascii=False, indent=2)

    pd.DataFrame(resultados).to_excel(
        "analisis_acciones.xlsx",
        index=False
    )

    print("ARCHIVOS GENERADOS")

if __name__ == "__main__":
    main()
