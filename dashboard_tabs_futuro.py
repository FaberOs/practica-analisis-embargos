# Contenido para TAB2 (Predicciones Futuras - Demandados)
# Este archivo contiene el código completo para copiar/pegar en dashboard_predicciones.py

TAB2_CONTENT = """
# 2. PREDICCIONES FUTURAS DE DEMANDADOS (12 meses adelante)
with tab2:
    st.markdown(\"\"\"
    <div class="section-title fade-in">
        Predicciones Futuras - Demandados (Próximos 12 Meses)
    </div>
    \"\"\", unsafe_allow_html=True)
    st.markdown(\"\"\"
    <div style='font-size: 1rem; color: #4a5568; margin-bottom: 1.5rem; padding: 1rem; background: #f8f9fa; border-radius: 10px;'>
        Proyección del <b>número de demandados únicos esperados</b> para los próximos 12 meses, con intervalos de confianza.<br>
        🔹 <b>Predicción</b>: Valor más probable basado en patrones históricos<br>
        🔹 <b>Intervalo de confianza</b>: Rango donde se espera que caiga el valor real (95% de probabilidad)<br>
        🔹 <b>Nivel de confianza</b>: Alta (1-3 meses), Media (4-6 meses), Baja (7-12 meses)
    </div>
    \"\"\", unsafe_allow_html=True)
    
    # Validar que las columnas necesarias existan
    required_cols = ['mes', 'pred_demandados', 'limite_inferior', 'limite_superior', 'nivel_confianza']
    missing_cols = [col for col in required_cols if col not in df_demandados_futuro.columns]
    
    if missing_cols:
        st.error(f"El archivo de predicciones futuras no tiene las columnas esperadas.")
        st.info(f"**Columnas requeridas:** {', '.join(required_cols)}")
        st.info(f"**Columnas encontradas:** {', '.join(df_demandados_futuro.columns.tolist())}")
        st.warning("Verifica que el proceso de generación de predicciones se haya completado correctamente.")
        st.stop()
    
    # === KPIs DE PREDICCIONES FUTURAS ===
    st.markdown("### Indicadores Clave de Predicción")
    
    col1, col2, col3 = st.columns(3)
    
    # Próximo mes
    proximo_mes_dem = df_demandados_futuro.iloc[0]
    col1.metric(
        label=f"Próximo Mes ({proximo_mes_dem['mes']})",
        value=f"{int(proximo_mes_dem['pred_demandados'])} demandados",
        delta=f"± {int((proximo_mes_dem['limite_superior'] - proximo_mes_dem['limite_inferior']) / 2)}",
        help=f"Predicción para el próximo mes con nivel de confianza {proximo_mes_dem['nivel_confianza']}"
    )
    
    # Próximos 3 meses
    proximos_3_meses_dem = df_demandados_futuro.head(3)['pred_demandados'].sum()
    col2.metric(
        label="Próximos 3 Meses",
        value=f"{int(proximos_3_meses_dem)} demandados",
        help="Suma de predicciones para los próximos 3 meses (alta confianza)"
    )
    
    # Proyección anual
    proyeccion_anual_dem = df_demandados_futuro['pred_demandados'].sum()
    col3.metric(
        label="Proyección Anual (12 meses)",
        value=f"{int(proyeccion_anual_dem)} demandados",
        help="Suma total de predicciones para los próximos 12 meses"
    )
    
    # === GRÁFICO CON BANDAS DE CONFIANZA ===
    st.markdown("---")
    st.markdown("### Evolución de Predicciones con Intervalos de Confianza")
    
    import plotly.graph_objects as go
    
    fig_futuro_dem = go.Figure()
    
    # Banda de confianza (área sombreada)
    fig_futuro_dem.add_trace(go.Scatter(
        x=df_demandados_futuro['mes'],
        y=df_demandados_futuro['limite_superior'],
        fill=None,
        mode='lines',
        line=dict(color='rgba(68, 68, 68, 0)'),
        showlegend=False,
        name='Límite Superior'
    ))
    
    fig_futuro_dem.add_trace(go.Scatter(
        x=df_demandados_futuro['mes'],
        y=df_demandados_futuro['limite_inferior'],
        fill='tonexty',
        mode='lines',
        line=dict(color='rgba(68, 68, 68, 0)'),
        fillcolor='rgba(220, 38, 38, 0.2)',
        name='Intervalo de Confianza',
        showlegend=True
    ))
    
    # Línea de predicción
    fig_futuro_dem.add_trace(go.Scatter(
        x=df_demandados_futuro['mes'],
        y=df_demandados_futuro['pred_demandados'],
        mode='lines+markers',
        name='Predicción',
        line=dict(color='#dc2626', width=3),
        marker=dict(size=8, color='#dc2626')
    ))
    
    fig_futuro_dem.update_layout(
        title="Predicciones Futuras de Demandados (12 Meses)",
        xaxis_title="Mes",
        yaxis_title="Cantidad de Demandados",
        hovermode='x unified',
        height=500,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    st.plotly_chart(fig_futuro_dem, use_container_width=True)
    
    # === TABLA DE PREDICCIONES ===
    st.markdown("---")
    st.markdown("### Detalle de Predicciones Mensuales")
    
    # Formatear dataframe para visualización
    df_display_dem = df_demandados_futuro.copy()
    df_display_dem['pred_demandados'] = df_display_dem['pred_demandados'].astype(int)
    df_display_dem['limite_inferior'] = df_display_dem['limite_inferior'].astype(int)
    df_display_dem['limite_superior'] = df_display_dem['limite_superior'].astype(int)
    df_display_dem['intervalo'] = df_display_dem.apply(
        lambda row: f"[{row['limite_inferior']} - {row['limite_superior']}]", 
        axis=1
    )
    
    # Reordenar columnas
    df_display_dem = df_display_dem[['mes', 'pred_demandados', 'intervalo', 'nivel_confianza', 'horizonte_meses']]
    df_display_dem.columns = ['Mes', 'Predicción', 'Intervalo 95%', 'Confianza', 'Horizonte (meses)']
    
    # Aplicar estilo con colores según nivel de confianza
    def color_confianza_dem(val):
        if val == 'Alta':
            return 'background-color: #d1fae5; color: #065f46'
        elif val == 'Media':
            return 'background-color: #fef3c7; color: #92400e'
        else:
            return 'background-color: #fee2e2; color: #991b1b'
    
    styled_df_dem = df_display_dem.style.applymap(
        color_confianza_dem, 
        subset=['Confianza']
    ).background_gradient(
        subset=['Predicción'],
        cmap='Reds'
    )
    
    st.dataframe(styled_df_dem, use_container_width=True, height=450)
    
    # === INTERPRETACIÓN Y RECOMENDACIONES ===
    st.markdown("---")
    st.markdown("### Interpretación y Recomendaciones")
    
    # Calcular tendencia
    tendencia_3m_dem = proximos_3_meses_dem / 3
    tendencia_9_12m_dem = df_demandados_futuro.tail(4)['pred_demandados'].mean()
    
    col_int1, col_int2 = st.columns(2)
    
    with col_int1:
        st.markdown(\"\"\"
        <div style='background: #fef2f2; padding: 1rem; border-radius: 10px; border-left: 4px solid #dc2626;'>
            <h4 style='margin-top: 0;'>Análisis de Tendencia</h4>
        \"\"\", unsafe_allow_html=True)
        
        if tendencia_9_12m_dem > tendencia_3m_dem:
            st.markdown(f"**Tendencia Creciente**: Se espera un aumento gradual de {tendencia_3m_dem:.0f} demandados/mes (corto plazo) a {tendencia_9_12m_dem:.0f} demandados/mes (largo plazo).")
        elif tendencia_9_12m_dem < tendencia_3m_dem:
            st.markdown(f"**Tendencia Decreciente**: Se espera una disminución de {tendencia_3m_dem:.0f} demandados/mes (corto plazo) a {tendencia_9_12m_dem:.0f} demandados/mes (largo plazo).")
        else:
            st.markdown(f"**Tendencia Estable**: Se espera mantener aproximadamente {tendencia_3m_dem:.0f} demandados/mes durante los próximos 12 meses.")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col_int2:
        st.markdown(\"\"\"
        <div style='background: #f0fdf4; padding: 1rem; border-radius: 10px; border-left: 4px solid #16a34a;'>
            <h4 style='margin-top: 0;'>Recomendaciones</h4>
        \"\"\", unsafe_allow_html=True)
        
        st.markdown(f\"\"\"
        • **Gestión de casos**: Preparar capacidad para {int(proximo_mes_dem['pred_demandados'])} demandados el próximo mes<br>
        • **Recursos legales**: Planificar atención para {int(proximos_3_meses_dem)} demandados en 3 meses<br>
        • **Revisión mensual**: Actualizar predicciones con datos reales para mejorar precisión<br>
        • **Alertas**: Monitorear si valores reales caen fuera del intervalo de confianza
        \"\"\", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Descarga de datos
    st.markdown("---")
    st.download_button(
        "Descargar Predicciones Futuras (CSV)", 
        df_demandados_futuro.to_csv(index=False).encode("utf-8"),
        file_name="predicciones_demandados_futuro.csv",
        mime="text/csv"
    )
"""

# Contenido para TAB3 (Validación Histórica del Modelo)
TAB3_CONTENT = """
# 3. VALIDACIÓN HISTÓRICA DEL MODELO
with tab3:
    st.markdown(\"\"\"
    <div class="section-title fade-in">
        Validación Histórica del Modelo Predictivo
    </div>
    \"\"\", unsafe_allow_html=True)
    st.markdown(\"\"\"
    <div style='font-size: 1rem; color: #4a5568; margin-bottom: 1.5rem; padding: 1rem; background: #f8f9fa; border-radius: 10px;'>
        Evaluación del <b>rendimiento del modelo</b> comparando predicciones contra valores reales del último año.<br>
        Esta sección muestra qué tan bien el modelo predice valores conocidos, lo cual indica su confiabilidad para predicciones futuras.
    </div>
    \"\"\", unsafe_allow_html=True)
    
    # === OFICIOS: VALIDACIÓN HISTÓRICA ===
    st.markdown("## Oficios por Mes - Validación Histórica")
    
    # Validar columnas
    if 'mes' in df_oficios_val.columns and 'real_oficios' in df_oficios_val.columns and 'pred_oficios' in df_oficios_val.columns:
        # Gráfico comparativo
        fig_val_oficios = px.line(
            df_oficios_val,
            x="mes",
            y=["real_oficios", "pred_oficios"],
            markers=True,
            labels={"value": "Cantidad de oficios", "variable": "Serie"},
            title="Oficios: Real vs Predicción (Año de Validación)"
        )
        fig_val_oficios.update_traces(line=dict(width=3))
        st.plotly_chart(fig_val_oficios, use_container_width=True)
        
        # Métricas de error
        col1, col2, col3 = st.columns(3)
        
        mae_oficios = (df_oficios_val['real_oficios'] - df_oficios_val['pred_oficios']).abs().mean()
        col1.metric("MAE", f"{mae_oficios:.2f}")
        
        rmse_oficios = np.sqrt(((df_oficios_val['real_oficios'] - df_oficios_val['pred_oficios'])**2).mean())
        col2.metric("RMSE", f"{rmse_oficios:.2f}")
        
        mape_oficios = (100 * (df_oficios_val['real_oficios'] - df_oficios_val['pred_oficios']).abs() / df_oficios_val['real_oficios'].replace(0, np.nan)).mean()
        col3.metric("MAPE", f"{mape_oficios:.2f}%")
        
        # Interpretación
        if mape_oficios < 10:
            st.success(f" **Excelente precisión**: El modelo tiene un error promedio de {mape_oficios:.2f}%")
        elif mape_oficios < 20:
            st.info(f"**Precisión aceptable**: El modelo tiene un error promedio de {mape_oficios:.2f}%")
        else:
            st.warning(f" **Precisión mejorable**: El modelo tiene un error promedio de {mape_oficios:.2f}%")
        
        # Tabla de datos
        st.markdown("### Datos de Validación - Oficios")
        st.dataframe(df_oficios_val, use_container_width=True, height=300)
    else:
        st.warning("El archivo de validación de oficios no tiene la estructura esperada")
    
    st.markdown("---")
    
    # === DEMANDADOS: VALIDACIÓN HISTÓRICA ===
    st.markdown("## Demandados por Mes - Validación Histórica")
    
    # Validar columnas
    if 'mes' in df_demandados_val.columns and 'real_demandados' in df_demandados_val.columns and 'pred_demandados' in df_demandados_val.columns:
        # Gráfico comparativo
        fig_val_dem = px.line(
            df_demandados_val,
            x="mes",
            y=["real_demandados", "pred_demandados"],
            markers=True,
            labels={"value": "Cantidad de demandados", "variable": "Serie"},
            title="Demandados: Real vs Predicción (Año de Validación)"
        )
        fig_val_dem.update_traces(line=dict(width=3))
        st.plotly_chart(fig_val_dem, use_container_width=True)
        
        # Métricas de error
        col1, col2, col3 = st.columns(3)
        
        mae_dem = (df_demandados_val['real_demandados'] - df_demandados_val['pred_demandados']).abs().mean()
        col1.metric("MAE", f"{mae_dem:.2f}")
        
        rmse_dem = np.sqrt(((df_demandados_val['real_demandados'] - df_demandados_val['pred_demandados'])**2).mean())
        col2.metric("RMSE", f"{rmse_dem:.2f}")
        
        mape_dem = (100 * (df_demandados_val['real_demandados'] - df_demandados_val['pred_demandados']).abs() / df_demandados_val['real_demandados'].replace(0, np.nan)).mean()
        col3.metric("MAPE", f"{mape_dem:.2f}%")
        
        # Interpretación
        if mape_dem < 10:
            st.success(f"✅ **Excelente precisión**: El modelo tiene un error promedio de {mape_dem:.2f}%")
        elif mape_dem < 20:
            st.info(f"ℹ️ **Precisión aceptable**: El modelo tiene un error promedio de {mape_dem:.2f}%")
        else:
            st.warning(f"⚠️ **Precisión mejorable**: El modelo tiene un error promedio de {mape_dem:.2f}%")
        
        # Tabla de datos
        st.markdown("### Datos de Validación - Demandados")
        st.dataframe(df_demandados_val, use_container_width=True, height=300)
    else:
        st.warning("⚠️ El archivo de validación de demandados no tiene la estructura esperada")
    
    st.markdown("---")
    
    # === INFORMACIÓN SOBRE VALIDACIÓN ===
    st.markdown("### Sobre la Validación del Modelo")
    st.markdown(\"\"\"
    <div style='background: #eff6ff; padding: 1rem; border-radius: 10px; border-left: 4px solid #3b82f6;'>
        <p><b>¿Qué es la validación histórica?</b></p>
        <p>El modelo se entrena con datos de años anteriores y se evalúa prediciendo el último año completo (del cual ya conocemos los valores reales). 
        Esto nos permite medir qué tan bien predice el modelo antes de usarlo para predicciones futuras.</p>
        
        <p><b>Métricas utilizadas:</b></p>
        <ul>
            <li><b>MAE (Error Absoluto Medio)</b>: Promedio de la diferencia absoluta entre real y predicción</li>
            <li><b>RMSE (Error Cuadrático Medio)</b>: Penaliza más los errores grandes</li>
            <li><b>MAPE (Error Porcentual Medio)</b>: Error expresado como porcentaje del valor real</li>
        </ul>
        
        <p><b>Interpretación:</b></p>
        <ul>
            <li>MAPE &lt; 10%: Excelente precisión</li>
            <li>MAPE 10-20%: Precisión aceptable</li>
            <li>MAPE &gt; 20%: El modelo necesita mejoras</li>
        </ul>
    </div>
    \"\"\", unsafe_allow_html=True)
"""

print("Archivo creado con el contenido de tab2 y tab3")
print("Este código debe copiarse manualmente al dashboard_predicciones.py")
