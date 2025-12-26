"""
Estilos CSS centralizados para los dashboards
Paleta de colores: #bfe084, #3c8198, #424e71, #252559
"""

def get_dashboard_styles():
    """Retorna los estilos CSS para los dashboards"""
    return """
<style>
    /* Variables de color */
    :root {
        --color-primary: #bfe084;
        --color-secondary: #3c8198;
        --color-tertiary: #424e71;
        --color-quaternary: #252559;
    }
    
    /* Sidebar personalizado */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #bfe084 0%, #3c8198 25%, #424e71 75%, #252559 100%);
    }
    
    [data-testid="stSidebar"] .stMarkdown, 
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p {
        color: white !important;
    }
    
    /* Botones del sidebar - navegación */
    [data-testid="stSidebar"] button {
        background-color: transparent !important;
        color: white !important;
        border: none !important;
        border-radius: 0 !important;
        text-align: left !important;
        padding: 0.6rem 1rem !important;
        font-size: 1rem !important;
        font-weight: 500 !important;
        transition: all 0.3s !important;
        justify-content: flex-start !important;
    }
    
    [data-testid="stSidebar"] button p {
        text-align: left !important;
    }
    
    [data-testid="stSidebar"] button:hover {
        background-color: rgba(191, 224, 132, 0.1) !important;
        color: white !important;
    }
    
    [data-testid="stSidebar"] button:active,
    [data-testid="stSidebar"] button:focus {
        background-color: rgba(191, 224, 132, 0.2) !important;
        color: #bfe084 !important;
        box-shadow: none !important;
        font-weight: 600 !important;
    }
    
    /* Estado activo para botones seleccionados */
    [data-testid="stSidebar"] button[aria-pressed="true"],
    [data-testid="stSidebar"] button.active {
        color: #bfe084 !important;
        background-color: rgba(191, 224, 132, 0.15) !important;
        font-weight: 600 !important;
    }
    
    /* Cards de métricas mejoradas */
    .metric-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
        border-left: 5px solid;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #3c8198, #bfe084);
        transform: scaleX(0);
        transition: transform 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 24px rgba(0,0,0,0.15);
    }
    .metric-card:hover::before {
        transform: scaleX(1);
    }
    
    /* Métricas con gradientes - Paleta personalizada */
    .metric-card-1 { border-left-color: #bfe084; }
    .metric-card-2 { border-left-color: #3c8198; }
    .metric-card-3 { border-left-color: #424e71; }
    .metric-card-4 { border-left-color: #252559; }
    .metric-card-5 { border-left-color: #bfe084; }
    
    /* Styling para st.metric - Modo claro/oscuro */
    [data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: bold !important;
        color: #3c8198 !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 1rem !important;
        color: #64748b !important;
        font-weight: 600 !important;
    }
    
    /* Modo oscuro */
    @media (prefers-color-scheme: dark) {
        [data-testid="stMetricValue"] {
            color: #bfe084 !important;
        }
        [data-testid="stMetricLabel"] {
            color: #94a3b8 !important;
        }
        
        /* KPI Cards en modo oscuro - usar clases específicas */
        .kpi-card {
            background: #1e293b !important;
            border-color: #334155 !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3) !important;
        }
        
        /* Labels en modo oscuro - color blanco */
        .kpi-label {
            color: white !important;
        }
        
        /* Valores en modo oscuro - color #bfe084 */
        .kpi-value {
            color: #bfe084 !important;
        }
    }
    
    /* Secciones de contenido */
    .content-section {
        background: rgba(60, 129, 152, 0.05);
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin-bottom: 2rem;
        border: 1px solid rgba(60, 129, 152, 0.1);
    }
    .section-title {
        font-size: 1.8rem;
        font-weight: bold;
        background: linear-gradient(135deg, #3c8198, #424e71);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid;
        border-image: linear-gradient(90deg, #3c8198, #bfe084) 1;
    }
    
    /* Tabs mejorados */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: rgba(60, 129, 152, 0.1);
        padding: 10px;
        border-radius: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        background: rgba(60, 129, 152, 0.1);
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 600;
        transition: all 0.3s;
        color: #424e71;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #3c8198, #424e71);
        color: white;
        box-shadow: 0 4px 12px rgba(60, 129, 152, 0.3);
    }
    
    /* Filtros */
    .filter-chip {
        display: inline-block;
        padding: 0.5rem 1rem;
        margin: 0.25rem;
        background: rgba(60, 129, 152, 0.1);
        border-radius: 20px;
        border: 1px solid rgba(60, 129, 152, 0.3);
        cursor: pointer;
        transition: all 0.3s;
    }
    .filter-chip:hover {
        background: #bfe084;
        color: #252559;
        transform: scale(1.05);
    }
    .filter-chip.active {
        background: #3c8198;
        color: white;
        border-color: #3c8198;
        box-shadow: 0 2px 8px rgba(60, 129, 152, 0.4);
    }
    .filter-section {
        background: rgba(60, 129, 152, 0.1);
        padding: 1.5rem;
        border-radius: 15px;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
    .filter-title {
        font-size: 1.1rem;
        font-weight: bold;
        color: #252559;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* Animaciones suaves */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .fade-in {
        animation: fadeIn 0.6s ease-out;
    }
    
    /* Mejoras generales */
    .main .block-container {
        padding-top: 3rem;
        padding-bottom: 3rem;
    }
    
    /* Cards de gráficos */
    .chart-card {
        background: rgba(60, 129, 152, 0.05);
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin-bottom: 1.5rem;
        border: 1px solid rgba(60, 129, 152, 0.1);
    }
    
    /* Estilos para headers y secciones - Modo claro/oscuro */
    h1, h2, h3 {
        color: #252559;
    }
    
    @media (prefers-color-scheme: dark) {
        h1, h2, h3 {
            color: #bfe084;
        }
    }
    
    /* Separadores */
    .separator {
        height: 2px;
        background: linear-gradient(90deg, transparent, #3c8198, #bfe084, transparent);
        margin: 2rem 0;
        border-radius: 2px;
    }
    
    /* Multiselect y selectbox - Modo claro/oscuro */
    [data-baseweb="select"] {
        background-color: rgba(60, 129, 152, 0.1) !important;
    }
    
    [data-baseweb="tag"] {
        background-color: #3c8198 !important;
        color: white !important;
    }
    
    [data-baseweb="tag"] svg {
        fill: white !important;
    }
    
    [data-baseweb="popover"] {
        background-color: white !important;
        border: 1px solid rgba(60, 129, 152, 0.3) !important;
    }
    
    [role="option"] {
        background-color: transparent !important;
        color: #252559 !important;
    }
    
    [role="option"]:hover {
        background-color: rgba(191, 224, 132, 0.2) !important;
        color: #252559 !important;
    }
    
    /* Modo oscuro */
    @media (prefers-color-scheme: dark) {
        [data-baseweb="select"] {
            background-color: rgba(60, 129, 152, 0.2) !important;
        }
        
        [data-baseweb="popover"] {
            background-color: #1e293b !important;
            border: 1px solid rgba(60, 129, 152, 0.5) !important;
        }
        
        [role="option"] {
            color: #e2e8f0 !important;
        }
        
        [role="option"]:hover {
            background-color: rgba(191, 224, 132, 0.15) !important;
            color: #bfe084 !important;
        }
    }
    
    /* Info boxes */
    .info-box {
        font-size: 1rem;
        color: #424e71;
        margin-bottom: 1.5rem;
        padding: 1rem;
        background: rgba(60, 129, 152, 0.15);
        border-radius: 10px;
        border-left: 4px solid #3c8198;
    }
    
    .info-box-success {
        background: rgba(191, 224, 132, 0.15);
        border-left-color: #bfe084;
    }
    
    .info-box-warning {
        background: rgba(66, 78, 113, 0.15);
        border-left-color: #424e71;
    }
    
    /* Header principal */
    .main-header {
        background: linear-gradient(135deg, #3c8198 0%, #424e71 100%);
        padding: 2.5rem 2rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 12px rgba(60, 129, 152, 0.3);
    }
    .main-header h1 {
        font-size: 2.2rem;
        margin-bottom: 0.5rem;
        font-weight: 700;
        letter-spacing: -0.5px;
        color: white;
    }
    .main-header p {
        font-size: 1rem;
        opacity: 0.95;
        margin: 0;
        color: white;
    }
    
    /* Stats cards */
    .stat-card {
        background: linear-gradient(135deg, rgba(60, 129, 152, 0.1) 0%, rgba(191, 224, 132, 0.1) 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid rgba(60, 129, 152, 0.2);
        transition: all 0.3s ease;
    }
    .stat-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 20px rgba(60, 129, 152, 0.15);
        border-color: #3c8198;
    }
    .stat-value {
        font-size: 2rem;
        font-weight: 700;
        color: #3c8198;
        margin: 0.5rem 0;
    }
    .stat-label {
        font-size: 0.9rem;
        color: #424e71;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .stat-change {
        font-size: 0.85rem;
        margin-top: 0.5rem;
    }
    .stat-change.positive {
        color: #bfe084;
    }
    .stat-change.negative {
        color: #dc2626;
    }
    
    /* KPI Values - Control de overflow */
    .kpi-value {
        font-weight: 700;
        letter-spacing: -0.5px;
        word-wrap: break-word;
        overflow-wrap: break-word;
        line-height: 1.2;
    }
    
    .kpi-value-small {
        font-size: 1.4rem;
    }
    
    .kpi-value-medium {
        font-size: 1.8rem;
    }
    
    .kpi-value-large {
        font-size: 2.2rem;
    }
    
    /* Tablas */
    .dataframe {
        font-size: 0.9rem;
    }
    .dataframe thead tr th {
        background: linear-gradient(135deg, #3c8198, #424e71) !important;
        color: white !important;
        font-weight: 600;
        padding: 0.75rem !important;
    }
    .dataframe tbody tr:hover {
        background-color: rgba(191, 224, 132, 0.1) !important;
    }
</style>
"""

def get_sidebar_header(title_line1, title_line2):
    """Retorna el HTML del header del sidebar"""
    return f"""
    <div style='margin-bottom: 2rem; margin-top: 1rem;'>
        <div style='font-size: 2rem; font-weight: 700; line-height: 1.2; text-align: left;'>
            <div style='color: #252559;'>{title_line1}</div>
            <div style='color: white;'>{title_line2}</div>
        </div>
    </div>
    """
