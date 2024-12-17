import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
import streamlit as st

def calcular_amortizacion_con_pagos_anuales(
    credito_total,
    tasa_interes_anual,
    plazo_anios,
    inicio_credito,
    pagos_recurrentes,
    liquidar_al_25=False,
    tasa_seguros_anual=0.005
):
    """
    Calcula la amortización mes a mes de un crédito con pagos mensuales fijos y pagos extraordinarios recurrentes anuales.
    Cuando se aplica la liquidación anticipada (si se cumple la condición), el crédito se considera saldado.
    Devuelve un DataFrame con la tabla de amortización y un diccionario con el resumen.
    """

    tasa_interes_mensual = tasa_interes_anual / 12

    # Cálculo del pago mensual sin seguros (amortización estándar)
    pago_mensual_sin_seguros = (tasa_interes_mensual * credito_total) / (1 - (1 + tasa_interes_mensual) ** -(plazo_anios * 12))

    # Seguro inicial (en base al saldo inicial)
    costo_seguros_mensual_inicial = (credito_total * tasa_seguros_anual) / 12
    pago_mensual_aproximado = pago_mensual_sin_seguros + costo_seguros_mensual_inicial

    saldo_pendiente = credito_total
    meses = 0
    liquidacion_aplicada = False
    fecha_liquidacion = None
    saldo_para_liquidar = 0.0

    current_date = inicio_credito

    # Acumuladores
    total_intereses_pagados = 0.0
    total_pagos_mensuales = 0.0
    total_pagos_extra = 0.0
    total_liquidacion = 0.0

    amort_data = []

    while saldo_pendiente > 0:
        meses += 1
        # Avanzar un mes
        current_date += relativedelta(months=1)

        saldo_inicial = saldo_pendiente
        interes_mes = saldo_pendiente * tasa_interes_mensual
        costo_seguros_mensual = (saldo_pendiente * tasa_seguros_anual) / 12

        abono_capital = pago_mensual_aproximado - interes_mes - costo_seguros_mensual
        if abono_capital < 0:
            abono_capital = 0

        # Actualizar saldo con el abono a capital
        saldo_pendiente -= abono_capital

        # Acumular datos de pago mensual (este es el pago que el acreditado hace cada mes)
        total_pagos_mensuales += pago_mensual_aproximado
        total_intereses_pagados += interes_mes

        # Aplicar pagos extraordinarios
        pago_extra_total = 0.0
        for pago_ext in pagos_recurrentes:
            mes_pago, dia_pago, monto_pago = pago_ext
            if current_date.month == mes_pago and current_date.day == dia_pago:
                saldo_pendiente -= monto_pago
                pago_extra_total += monto_pago

        total_pagos_extra += pago_extra_total

        # Aplicar liquidación anticipada
        liq_aplicada_este_mes = False
        if liquidar_al_25 and not liquidacion_aplicada and saldo_pendiente <= credito_total * 0.25 and saldo_pendiente > 0:
            monto_liquidacion_25 = saldo_pendiente / 2
            saldo_pendiente -= monto_liquidacion_25
            saldo_para_liquidar = monto_liquidacion_25
            total_liquidacion += monto_liquidacion_25
            liquidacion_aplicada = True
            fecha_liquidacion = current_date
            liq_aplicada_este_mes = True

        if saldo_pendiente < 0:
            saldo_pendiente = 0

        # Guardar datos del mes
        amort_data.append({
            "Mes": meses,
            "Fecha": current_date.strftime("%Y-%m-%d"),
            "Saldo Inicial": saldo_inicial,
            "Interés": interes_mes,
            "Seguro": costo_seguros_mensual,
            "Pago Mensual": pago_mensual_aproximado,
            "Abono a Capital": abono_capital,
            "Pago Extra": pago_extra_total,
            "Saldo Final": saldo_pendiente,
            "Liquidación Anticipada Aplicada": "Sí" if liq_aplicada_este_mes else "No"
        })

        # Si se aplicó la liquidación anticipada, asumimos que el crédito queda liquidado.
        if liq_aplicada_este_mes:
            # Forzamos saldo a cero y terminamos la amortización
            saldo_pendiente = 0
            break

    # Calcular totales finales
    total_pagado = total_pagos_mensuales + total_pagos_extra + total_liquidacion

    resumen = {
        "duracion_total_meses": meses,
        "fecha_liquidacion": fecha_liquidacion,
        "pago_mensual": round(pago_mensual_aproximado, 2),
        "credito_total": credito_total,
        "tasa_interes_anual": tasa_interes_anual,
        "saldo_liquidacion": round(saldo_para_liquidar, 2),
        "total_intereses_pagados": round(total_intereses_pagados, 2),
        "total_pagado": round(total_pagado, 2)
    }

    results_df = pd.DataFrame(amort_data)
    return results_df, resumen

# Interfaz con Streamlit
st.title("Simulador de Crédito Infonavit con Pagos Extra Recurrentes")

st.sidebar.header("Parámetros del Crédito")
credito_total = st.sidebar.number_input("Crédito Total (MXN)", value=968374.92, step=1000.0)
tasa_interes_anual = st.sidebar.number_input("Tasa de Interés Anual (decimal)", value=0.1045, step=0.001, format="%.4f")
plazo_anios = st.sidebar.number_input("Plazo (años)", value=16, step=1, min_value=1)
tasa_seguros_anual = st.sidebar.number_input("Tasa Anual de Seguro (decimal)", value=0.005, step=0.001, format="%.3f")

st.sidebar.header("Fecha de Inicio del Crédito")
inicio_anio = st.sidebar.number_input("Año de Inicio", value=2025, step=1)
inicio_mes = st.sidebar.number_input("Mes de Inicio", value=2, step=1, min_value=1, max_value=12)
inicio_dia = st.sidebar.number_input("Día de Inicio", value=1, step=1, min_value=1, max_value=31)
inicio_credito = datetime(inicio_anio, inicio_mes, inicio_dia)

st.sidebar.header("Pagos Extra Recurrentes Anuales")
st.sidebar.markdown("Definir pagos extra que se repiten cada año en la misma fecha.")
num_pagos_extra = st.sidebar.number_input("Número de tipos de Pagos Extra", value=1, step=1, min_value=0)

pagos_recurrentes = []
for i in range(num_pagos_extra):
    st.sidebar.subheader(f"Pago Extra {i+1}")
    mes_pago = st.sidebar.number_input(f"Mes pago extra {i+1}", min_value=1, max_value=12, value=12)
    dia_pago = st.sidebar.number_input(f"Día pago extra {i+1}", min_value=1, max_value=31, value=1)
    monto_pago = st.sidebar.number_input(f"Monto pago extra {i+1}", value=45000.0, step=1000.0)
    pagos_recurrentes.append((mes_pago, dia_pago, monto_pago))

liquidar_al_25 = st.sidebar.checkbox("Aplicar Descuento por Liquidación Anticipada (25%)", value=True)

if st.sidebar.button("Calcular"):
    results_df, resumen = calcular_amortizacion_con_pagos_anuales(
        credito_total,
        tasa_interes_anual,
        plazo_anios,
        inicio_credito,
        pagos_recurrentes,
        liquidar_al_25=liquidar_al_25,
        tasa_seguros_anual=tasa_seguros_anual
    )

    st.write("### Resultados")
    duracion_anios = resumen['duracion_total_meses'] // 12
    duracion_meses = resumen['duracion_total_meses'] % 12

    st.markdown(f"**Duración total del crédito:** {duracion_anios} años y {duracion_meses} meses")

    if resumen['fecha_liquidacion']:
        st.markdown(f"**Fecha de liquidación anticipada:** {resumen['fecha_liquidacion'].strftime('%Y-%m-%d')}")
        st.markdown(f"**Monto de liquidación anticipada:** {resumen['saldo_liquidacion']:.2f} MXN")

    st.markdown(f"**Pago mensual (aprox. con seguros):** {resumen['pago_mensual']:.2f} MXN")
    st.markdown(f"**Total Intereses Pagados:** {resumen['total_intereses_pagados']:.2f} MXN")
    st.markdown(f"**Total Pagado (Mensualidades + Extras + Liquidación):** {resumen['total_pagado']:.2f} MXN")

    st.write("### Tabla de Amortización")
    format_dict = {
        "Saldo Inicial": "{:,.2f}",
        "Interés": "{:,.2f}",
        "Seguro": "{:,.2f}",
        "Pago Mensual": "{:,.2f}",
        "Abono a Capital": "{:,.2f}",
        "Pago Extra": "{:,.2f}",
        "Saldo Final": "{:,.2f}"
    }
    st.dataframe(results_df.style.format(format_dict))
