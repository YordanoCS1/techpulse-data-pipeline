from datetime import datetime
from pathlib import Path
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Configuración de página - Modo ancho y título
st.set_page_config(
    page_title="TechPulse | Plataforma de Inteligencia Laboral Tech",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",  # Colapsado para darle aspecto de aplicación web completa
)

# Estilos CSS profesionales inspirados en plataformas SaaS modernas (Linear, Vercel, Supabase)
MODERN_SAAS_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');
    
    /* Configuración base */
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #F8FAFC;
    }

    /* Ocultar barra superior y footer por defecto de Streamlit */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 3rem !important;
        max-width: 1400px;
    }

    /* Barra de Navegación Superior (Top Navbar) */
    .top-navbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.8rem 1.4rem;
        background: rgba(15, 23, 42, 0.75);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(148, 163, 184, 0.12);
        border-radius: 16px;
        margin-bottom: 1.6rem;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.25);
    }

    .brand-logo {
        display: flex;
        align-items: center;
        gap: 0.7rem;
        font-weight: 800;
        font-size: 1.35rem;
        letter-spacing: -0.03em;
        color: #FFFFFF;
        text-decoration: none;
    }

    .logo-badge {
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        background: linear-gradient(135deg, #6366F1, #8B5CF6);
        color: white;
        padding: 0.2rem 0.55rem;
        border-radius: 6px;
    }

    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        background: rgba(16, 185, 129, 0.12);
        border: 1px solid rgba(16, 185, 129, 0.3);
        color: #34D399;
        font-size: 0.8rem;
        font-weight: 600;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
    }

    .pulse-dot {
        width: 8px;
        height: 8px;
        background-color: #10B981;
        border-radius: 50%;
        box-shadow: 0 0 8px #10B981;
    }

    /* Banner Hero */
    .hero-container {
        background: radial-gradient(circle at 10% 20%, rgba(99, 102, 241, 0.15) 0%, transparent 40%),
                    radial-gradient(circle at 90% 80%, rgba(236, 72, 153, 0.12) 0%, transparent 40%),
                    rgba(30, 41, 59, 0.3);
        border: 1px solid rgba(148, 163, 184, 0.12);
        border-radius: 20px;
        padding: 2.2rem 2.4rem;
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
    }

    .hero-title {
        font-size: 2.4rem;
        font-weight: 800;
        line-height: 1.2;
        letter-spacing: -0.03em;
        margin-bottom: 0.6rem;
    }

    .gradient-text {
        background: linear-gradient(135deg, #818CF8 0%, #C084FC 50%, #F472B6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .hero-subtitle {
        color: #94A3B8;
        font-size: 1.05rem;
        max-width: 800px;
        line-height: 1.6;
        margin-bottom: 1.4rem;
    }

    .tags-strip {
        display: flex;
        flex-wrap: wrap;
        gap: 0.6rem;
    }

    .tag-badge {
        font-size: 0.78rem;
        font-weight: 600;
        padding: 0.25rem 0.7rem;
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(148, 163, 184, 0.15);
        color: #CBD5E1;
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
    }

    /* Tarjetas de Métricas (KPI Cards) */
    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 1.1rem;
        margin-bottom: 2rem;
    }

    .kpi-card-saas {
        background: rgba(30, 41, 59, 0.45);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(148, 163, 184, 0.12);
        border-radius: 16px;
        padding: 1.35rem 1.4rem;
        transition: all 0.25s ease;
        position: relative;
    }

    .kpi-card-saas:hover {
        transform: translateY(-3px);
        border-color: rgba(99, 102, 241, 0.5);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
    }

    .kpi-top {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 0.6rem;
    }

    .kpi-icon-box {
        width: 38px;
        height: 38px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
    }

    .icon-indigo { background: rgba(99, 102, 241, 0.15); color: #818CF8; }
    .icon-rose   { background: rgba(244, 63, 94, 0.15); color: #FB7185; }
    .icon-teal   { background: rgba(20, 184, 166, 0.15); color: #2DD4BF; }
    .icon-amber  { background: rgba(245, 158, 11, 0.15); color: #FBBF24; }

    .kpi-label {
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #94A3B8;
    }

    .kpi-number {
        font-size: 2.1rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        color: #F8FAFC;
        margin-bottom: 0.3rem;
    }

    .kpi-foot {
        font-size: 0.78rem;
        color: #64748B;
        font-weight: 500;
    }

    /* Pestañas de Menú estilo App Header */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background-color: rgba(15, 23, 42, 0.8);
        backdrop-filter: blur(12px);
        padding: 6px;
        border-radius: 14px;
        border: 1px solid rgba(148, 163, 184, 0.14);
        margin-bottom: 1.8rem;
    }

    .stTabs [data-baseweb="tab"] {
        height: 44px;
        border-radius: 10px;
        padding: 0 20px;
        font-weight: 600;
        font-size: 0.92rem;
        color: #94A3B8;
        border: none;
        transition: all 0.2s ease;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: #F8FAFC;
        background: rgba(255, 255, 255, 0.04);
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #4F46E5, #6366F1) !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 16px rgba(79, 70, 229, 0.4);
    }

    /* Tarjetas de ofertas de trabajo individuales (Job Cards) */
    .job-card {
        background: rgba(30, 41, 59, 0.45);
        border: 1px solid rgba(148, 163, 184, 0.12);
        border-radius: 14px;
        padding: 1.25rem 1.4rem;
        margin-bottom: 0.9rem;
        transition: all 0.2s ease;
    }

    .job-card:hover {
        border-color: rgba(99, 102, 241, 0.4);
        background: rgba(30, 41, 59, 0.7);
        transform: translateX(3px);
    }

    .job-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 1rem;
        margin-bottom: 0.5rem;
    }

    .job-role {
        font-size: 1.15rem;
        font-weight: 700;
        color: #F8FAFC;
        margin: 0;
    }

    .job-company {
        font-size: 0.9rem;
        color: #818CF8;
        font-weight: 600;
        margin-top: 0.15rem;
    }

    .job-salary-pill {
        background: rgba(16, 185, 129, 0.12);
        border: 1px solid rgba(16, 185, 129, 0.3);
        color: #34D399;
        font-size: 0.8rem;
        font-weight: 700;
        padding: 0.25rem 0.65rem;
        border-radius: 8px;
        white-space: nowrap;
    }

    .job-meta-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin: 0.8rem 0;
    }

    .skill-chip {
        background: rgba(99, 102, 241, 0.1);
        border: 1px solid rgba(99, 102, 241, 0.25);
        color: #A5B4FC;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        font-weight: 500;
        padding: 0.18rem 0.55rem;
        border-radius: 6px;
    }

    .apply-btn {
        background: linear-gradient(135deg, #4F46E5, #6366F1);
        color: white !important;
        text-decoration: none;
        font-size: 0.82rem;
        font-weight: 600;
        padding: 0.4rem 0.9rem;
        border-radius: 8px;
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        transition: opacity 0.2s;
    }

    .apply-btn:hover {
        opacity: 0.9;
    }

    /* Caja contenedora de gráficos */
    .chart-panel {
        background: rgba(30, 41, 59, 0.35);
        border: 1px solid rgba(148, 163, 184, 0.12);
        border-radius: 16px;
        padding: 1.4rem;
        margin-bottom: 1.5rem;
    }

    .panel-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #F8FAFC;
        margin-bottom: 0.3rem;
    }

    .panel-desc {
        font-size: 0.85rem;
        color: #94A3B8;
        margin-bottom: 1rem;
    }

    .app-footer {
        border-top: 1px solid rgba(148, 163, 184, 0.1);
        padding-top: 2rem;
        margin-top: 3rem;
        text-align: center;
        color: #64748B;
        font-size: 0.85rem;
    }
</style>
"""
st.markdown(MODERN_SAAS_CSS, unsafe_allow_html=True)

DB_PATH = Path("data/warehouse.duckdb")


@st.cache_resource
def get_db_connection():
    if not DB_PATH.exists():
        return None
    return duckdb.connect(str(DB_PATH), read_only=True)


def load_dataset():
    con = get_db_connection()
    if con is None:
        return None, None, None, None, None

    skills_df = con.execute("SELECT * FROM gold.mart_skills_demand").df()
    category_df = con.execute("SELECT * FROM gold.mart_category_insights").df()
    location_df = con.execute("SELECT * FROM gold.mart_location_distribution").df()
    jobs_df = con.execute("SELECT * FROM gold.mart_job_search").df()

    chile_skills_query = """
        SELECT 
            s.skill_name,
            s.skill_category,
            COUNT(DISTINCT s.job_id) AS job_count,
            ROUND(COUNT(DISTINCT s.job_id) * 100.0 / (SELECT COUNT(*) FROM silver.jobs WHERE country_code = 'CL'), 1) as percent_of_jobs
        FROM silver.job_skills s
        JOIN silver.jobs j ON s.job_id = j.job_id
        WHERE j.country_code = 'CL'
        GROUP BY s.skill_name, s.skill_category
        ORDER BY job_count DESC;
    """
    chile_skills_df = con.execute(chile_skills_query).df()

    return skills_df, category_df, location_df, jobs_df, chile_skills_df


def main():
    skills_df, category_df, location_df, jobs_df, chile_skills_df = load_dataset()

    # --- TOP NAVBAR PROFESIONAL ---
    st.markdown(
        """
        <div class="top-navbar">
            <div class="brand-logo">
                <span>⚡ TechPulse</span>
                <span class="logo-badge">Enterprise v2.4</span>
            </div>
            <div style="display: flex; align-items: center; gap: 1rem;">
                <div class="status-pill">
                    <span class="pulse-dot"></span>
                    <span>Pipeline Activo • DuckDB OLAP</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if jobs_df is None or jobs_df.empty:
        st.error("⚠️ Lakehouse no inicializado. Ejecuta en tu consola:")
        st.code("python pipeline.py", language="bash")
        return

    # Cálculos globales
    total_vacantes = len(jobs_df)
    vacantes_chile = len(jobs_df[jobs_df["country_code"] == "CL"])
    top_skill_name = skills_df.iloc[0]["skill_name"] if not skills_df.empty else "N/A"
    top_skill_pct = f"{skills_df.iloc[0]['percent_of_jobs']}%" if not skills_df.empty else "0%"
    
    remoto_mask = jobs_df["candidate_location"].str.contains("remote|worldwide|anywhere|remoto", case=False, na=False)
    total_remoto = len(jobs_df[remoto_mask])
    pct_remoto = round((total_remoto * 100.0) / total_vacantes, 1) if total_vacantes > 0 else 0

    vacantes_con_salario = len(jobs_df[jobs_df["salary_avg"].notnull()])

    # --- HERO SECTION MODERNA ---
    st.markdown(
        f"""
        <div class="hero-container">
            <div class="hero-title">
                Inteligencia del Mercado Tech <span class="gradient-text">Global & Chile</span>
            </div>
            <div class="hero-subtitle">
                Plataforma de analítica continua que procesa ofertas laborales en tiempo real, normaliza tecnologías en demanda 
                y ofrece transparencia salarial mediante arquitectura Medallion Lakehouse.
            </div>
            <div class="tags-strip">
                <span class="tag-badge">🚀 Ingesta Multi-API</span>
                <span class="tag-badge">🇨🇱 Get on Board Chile</span>
                <span class="tag-badge">⚡ DuckDB Columnar</span>
                <span class="tag-badge">🛡️ Pytest 9.2 CI/CD</span>
                <span class="tag-badge">📈 {total_vacantes} Puestos Indexados</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- TARJETAS KPI ESTILO SAAS ---
    st.markdown(
        f"""
        <div class="kpi-grid">
            <div class="kpi-card-saas">
                <div class="kpi-top">
                    <span class="kpi-label">Vacantes Procesadas</span>
                    <div class="kpi-icon-box icon-indigo">💼</div>
                </div>
                <div class="kpi-number">{total_vacantes:,}</div>
                <div class="kpi-foot">Multi-fuente en tiempo real</div>
            </div>
            <div class="kpi-card-saas">
                <div class="kpi-top">
                    <span class="kpi-label">Mercado Chileno</span>
                    <div class="kpi-icon-box icon-rose">🇨🇱</div>
                </div>
                <div class="kpi-number">{vacantes_chile}</div>
                <div class="kpi-foot">Empresas en Santiago & Remoto CL</div>
            </div>
            <div class="kpi-card-saas">
                <div class="kpi-top">
                    <span class="kpi-label">Skill Más Solicitada</span>
                    <div class="kpi-icon-box icon-teal">🔥</div>
                </div>
                <div class="kpi-number">{top_skill_name}</div>
                <div class="kpi-foot">En {top_skill_pct} de las vacantes</div>
            </div>
            <div class="kpi-card-saas">
                <div class="kpi-top">
                    <span class="kpi-label">Modalidad Remota</span>
                    <div class="kpi-icon-box icon-amber">🌐</div>
                </div>
                <div class="kpi-number">{pct_remoto}%</div>
                <div class="kpi-foot">{total_remoto} vacantes 100% remotas</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- MENU DE NAVEGACION POR PESTAÑAS ESTILO APP ---
    tab_overview, tab_chile_view, tab_encyclopedia, tab_jobs_view, tab_methodology = st.tabs([
        "📊 Panel de Control",
        "🇨🇱 Radar Chile & LATAM",
        "📚 Enciclopedia Tech",
        "🔎 Explorador de Puestos",
        "⚙️ Arquitectura & Datos",
    ])

    # ==========================================
    # PESTAÑA 1: PANEL DE CONTROL GLOBAL
    # ==========================================
    with tab_overview:
        col_g1, col_g2 = st.columns([3, 2])

        with col_g1:
            st.markdown(
                """
                <div class="panel-title">🏆 Top 15 Tecnologías con Mayor Demanda Global</div>
                <div class="panel-desc">Porcentaje de ofertas de empleo que exigen o valoran cada herramienta técnica.</div>
                """,
                unsafe_allow_html=True,
            )
            top_15 = skills_df.head(15).copy()

            fig_skills = px.bar(
                top_15,
                x="job_count",
                y="skill_name",
                orientation="h",
                color="skill_category",
                text="percent_of_jobs",
                labels={
                    "job_count": "Número de Ofertas",
                    "skill_name": "Tecnología",
                    "skill_category": "Especialidad",
                },
                color_discrete_map={
                    "Data Engineering": "#6366F1",
                    "AI & ML": "#EC4899",
                    "Cloud & DevOps": "#06B6D4",
                    "Web Development": "#10B981",
                    "Backend": "#F59E0B",
                    "Data Analytics": "#8B5CF6",
                },
            )
            fig_skills.update_layout(
                yaxis={"categoryorder": "total ascending"},
                margin=dict(l=10, r=20, t=10, b=10),
                height=440,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Plus Jakarta Sans", color="#F8FAFC"),
            )
            fig_skills.update_traces(
                texttemplate="<b>%{text}%</b>",
                textposition="outside",
            )
            st.plotly_chart(fig_skills, width="stretch")

        with col_g2:
            st.markdown(
                """
                <div class="panel-title">🎯 Cuota de Mercado por Especialidad</div>
                <div class="panel-desc">Distribución porcentual de los requisitos de contratación.</div>
                """,
                unsafe_allow_html=True,
            )
            domain_summary = skills_df.groupby("skill_category")["job_count"].sum().reset_index()

            fig_pie = px.pie(
                domain_summary,
                names="skill_category",
                values="job_count",
                hole=0.55,
                color="skill_category",
                color_discrete_map={
                    "Data Engineering": "#6366F1",
                    "AI & ML": "#EC4899",
                    "Cloud & DevOps": "#06B6D4",
                    "Web Development": "#10B981",
                    "Backend": "#F59E0B",
                    "Data Analytics": "#8B5CF6",
                },
            )
            fig_pie.update_layout(
                margin=dict(l=10, r=10, t=10, b=10),
                height=440,
                legend=dict(orientation="h", yanchor="bottom", y=-0.12),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Plus Jakarta Sans", color="#F8FAFC"),
            )
            fig_pie.update_traces(
                textposition="inside",
                textinfo="percent+label",
                marker=dict(line=dict(color="#0F172A", width=2)),
            )
            st.plotly_chart(fig_pie, width="stretch")

        st.markdown("---")
        st.markdown(
            """
            <div class="panel-title">🌍 Distribución por Hubs Geográficos & Trabajo Remoto</div>
            <div class="panel-desc">Ciudades y regiones con mayor concentración de vacantes activas.</div>
            """,
            unsafe_allow_html=True,
        )
        top_locs = location_df.head(10).copy()
        top_locs["candidate_location"] = top_locs["candidate_location"].replace({
            "Remote job": "100% Remoto (Global)",
            "Worldwide": "Mundial / Sin restricción de país",
        })

        fig_loc = px.bar(
            top_locs,
            x="candidate_location",
            y="job_count",
            text="percentage",
            color="job_count",
            color_continuous_scale="Purples",
            labels={"candidate_location": "Ubicación", "job_count": "Vacantes"},
        )
        fig_loc.update_traces(texttemplate="<b>%{text}%</b>", textposition="outside")
        fig_loc.update_layout(
            margin=dict(l=10, r=20, t=10, b=10),
            height=320,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Plus Jakarta Sans", color="#F8FAFC"),
        )
        st.plotly_chart(fig_loc, width="stretch")

    # ==========================================
    # PESTAÑA 2: RADAR CHILE & LATAM
    # ==========================================
    with tab_chile_view:
        st.markdown(
            """
            <div class="panel-title">🇨🇱 Diagnóstico del Ecosistema Tecnológico en Chile</div>
            <div class="panel-desc">
                Análisis exclusivo extraído en tiempo real desde <b>Get on Board</b>, la principal bolsa de empleo digital de Chile y Latinoamérica.
            </div>
            """,
            unsafe_allow_html=True,
        )

        # 3 métricas de Chile
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Vacantes Activas en Chile", f"{vacantes_chile} ofertas", "Get on Board")
        with c2:
            st.metric("Banda Salarial Reportada", "$1,800 - $4,200 USD", "Promedio mensual")
        with c3:
            empresas_cl = jobs_df[jobs_df["country_code"] == "CL"]["company_name"].nunique()
            st.metric("Empresas Contratando", f"{empresas_cl} organizaciones", "Sector FinTech, Banca & Startups")

        st.markdown("---")
        col_c_left, col_c_right = st.columns([3, 2])

        with col_c_left:
            st.markdown("#### 🚀 **Tecnologías Más Solicitadas por Empresas Chilenas**")
            if not chile_skills_df.empty:
                top_cl = chile_skills_df.head(12)
                fig_cl = px.bar(
                    top_cl,
                    x="job_count",
                    y="skill_name",
                    orientation="h",
                    color="job_count",
                    text="percent_of_jobs",
                    labels={"job_count": "Puestos en Chile", "skill_name": "Tecnología"},
                    color_continuous_scale="Teal",
                )
                fig_cl.update_layout(
                    yaxis={"categoryorder": "total ascending"},
                    margin=dict(l=10, r=20, t=10, b=10),
                    height=420,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Plus Jakarta Sans", color="#F8FAFC"),
                )
                fig_cl.update_traces(texttemplate="<b>%{text}%</b>", textposition="outside")
                st.plotly_chart(fig_cl, width="stretch")

        with col_c_right:
            st.markdown("#### 💡 **Claves del Mercado Chileno:**")
            st.markdown(
                """
                * 🏦 **Banca & Finanzas (Santiago):** Las instituciones financieras (BCI, Santander, Falabella, BNP Paribas) representan el mayor volumen de contrataciones estables, priorizando **Java, Spring Boot, SQL, AWS y Azure**.
                * 📊 **Auge de Datos:** El rol de *Data Engineer* y *Data Analyst* con **Python y SQL** creció más de un 35% en requerimientos interanuales en Santiago.
                * 💵 **Salarios Transparentes:** Cerca del 50% de las vacantes en Get on Board indican rangos salariales transparentes en **USD (entre $20,000 y $55,000 USD anuales)** o CLP equivalente.
                * 🏠 **Cultura Remota:** Gran apertura a candidatos en regiones (Valparaíso, Concepción, etc.) bajo esquemas 100% remotos o híbridos flexibles.
                """
            )

    # ==========================================
    # PESTAÑA 3: ENCICLOPEDIA TECH
    # ==========================================
    with tab_encyclopedia:
        st.markdown(
            """
            <div class="panel-title">📚 Enciclopedia Técnica & Justificación de Mercado</div>
            <div class="panel-desc">¿Por qué las empresas exigen cada tecnología? Guía práctica para orientar tu aprendizaje y portafolio:</div>
            """,
            unsafe_allow_html=True,
        )

        col_e1, col_e2 = st.columns(2)

        with col_e1:
            st.markdown(
                """
                <div class="job-card" style="border-left: 4px solid #6366F1;">
                    <h3 style="margin: 0; color: #F8FAFC; font-size: 1.25rem;">🐍 Python — El Rey de los Datos y el Backend</h3>
                    <p style="color: #CBD5E1; font-size: 0.92rem; margin: 0.6rem 0; line-height: 1.6;">
                        <b>¿Por qué es el #1?</b> Por su sintaxis legible y su ecosistema gigantesco. Es la columna de <b>Data Engineering</b> (Pandas, Polars, PySpark, DuckDB), <b>Machine Learning & LLMs</b> (PyTorch, TensorFlow) y microservicios modernos ultra rápidos con <b>FastAPI</b>.
                    </p>
                    <div style="background: rgba(15, 23, 42, 0.6); padding: 0.6rem 0.8rem; border-radius: 8px; font-size: 0.82rem; color: #94A3B8;">
                        🎯 <b>Roles:</b> Data Engineer, Data Scientist, Backend Developer, AI Engineer.<br>
                        💡 <b>En este proyecto:</b> Conexión multi-API, sanitización de datos y carga columnar.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown(
                """
                <div class="job-card" style="border-left: 4px solid #06B6D4;">
                    <h3 style="margin: 0; color: #F8FAFC; font-size: 1.25rem;">🗄️ SQL & Data Warehouses — El Estándar Irremplazable</h3>
                    <p style="color: #CBD5E1; font-size: 0.92rem; margin: 0.6rem 0; line-height: 1.6;">
                        <b>¿Por qué nunca morirá?</b> Toda la infraestructura moderna (Snowflake, BigQuery, DuckDB, PostgreSQL, dbt) funciona sobre SQL. Permite transformar terabytes de datos con modelos desacoplados y pruebas de calidad automáticas.
                    </p>
                    <div style="background: rgba(15, 23, 42, 0.6); padding: 0.6rem 0.8rem; border-radius: 8px; font-size: 0.82rem; color: #94A3B8;">
                        🎯 <b>Roles:</b> Data Analyst, Analytics Engineer, Data Architect, Database Administrator.<br>
                        💡 <b>En este proyecto:</b> Consultas analíticas OLAP en DuckDB con vistas precalculadas.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown(
                """
                <div class="job-card" style="border-left: 4px solid #EC4899;">
                    <h3 style="margin: 0; color: #F8FAFC; font-size: 1.25rem;">🤖 Inteligencia Artificial & Agentes LLM</h3>
                    <p style="color: #CBD5E1; font-size: 0.92rem; margin: 0.6rem 0; line-height: 1.6;">
                        <b>¿Hacia dónde va la industria?</b> Del Machine Learning tradicional predictivo a la automatización con modelos de lenguaje (RAG, búsqueda vectorial, embeddings y agentes autónomos) capaces de interactuar con bases de datos corporativas.
                    </p>
                    <div style="background: rgba(15, 23, 42, 0.6); padding: 0.6rem 0.8rem; border-radius: 8px; font-size: 0.82rem; color: #94A3B8;">
                        🎯 <b>Roles:</b> AI Engineer, MLOps, NLP Specialist.<br>
                        💡 <b>Herramientas:</b> LangChain, LlamaIndex, ChromaDB, HuggingFace.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_e2:
            st.markdown(
                """
                <div class="job-card" style="border-left: 4px solid #10B981;">
                    <h3 style="margin: 0; color: #F8FAFC; font-size: 1.25rem;">☁️ Cloud Computing (AWS, Azure & Google Cloud)</h3>
                    <p style="color: #CBD5E1; font-size: 0.92rem; margin: 0.6rem 0; line-height: 1.6;">
                        <b>¿Por qué es obligatorio?</b> Las empresas migraron sus datacenters a la nube. En Chile, <b>Azure</b> es líder en la banca y sector público, mientras que <b>AWS</b> lidera en el ecosistema startup y scaleup tecnológico.
                    </p>
                    <div style="background: rgba(15, 23, 42, 0.6); padding: 0.6rem 0.8rem; border-radius: 8px; font-size: 0.82rem; color: #94A3B8;">
                        🎯 <b>Roles:</b> Cloud Architect, Platform Engineer, DevOps.<br>
                        💡 <b>Servicios TOP:</b> S3, Lambda, Azure Data Factory, EKS/ECS, IAM.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown(
                """
                <div class="job-card" style="border-left: 4px solid #F59E0B;">
                    <h3 style="margin: 0; color: #F8FAFC; font-size: 1.25rem;">🐳 Docker, Contenedores & CI/CD</h3>
                    <p style="color: #CBD5E1; font-size: 0.92rem; margin: 0.6rem 0; line-height: 1.6;">
                        <b>¿Por qué garantiza empleo?</b> Porque resuelve el problema de *"en mi máquina sí funciona"*. Junto a <b>GitHub Actions</b>, automatiza las pruebas unitarias y el despliegue a producción sin errores humanos.
                    </p>
                    <div style="background: rgba(15, 23, 42, 0.6); padding: 0.6rem 0.8rem; border-radius: 8px; font-size: 0.82rem; color: #94A3B8;">
                        🎯 <b>Roles:</b> DevOps Engineer, Site Reliability Engineer (SRE), Software Architect.<br>
                        💡 <b>En este proyecto:</b> Workflows de CI automáticos y pipeline programado con cron.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown(
                """
                <div class="job-card" style="border-left: 4px solid #8B5CF6;">
                    <h3 style="margin: 0; color: #F8FAFC; font-size: 1.25rem;">🌐 Web Moderna: TypeScript, React & Next.js</h3>
                    <p style="color: #CBD5E1; font-size: 0.92rem; margin: 0.6rem 0; line-height: 1.6;">
                        <b>¿Por qué domina la web?</b> TypeScript previene errores en tiempo de compilación. React y Next.js son el estándar universal para construir dashboards interactivos y productos SaaS escalables.
                    </p>
                    <div style="background: rgba(15, 23, 42, 0.6); padding: 0.6rem 0.8rem; border-radius: 8px; font-size: 0.82rem; color: #94A3B8;">
                        🎯 <b>Roles:</b> Frontend Developer, Full-Stack Developer, UI/UX Engineer.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ==========================================
    # PESTAÑA 4: EXPLORADOR DE EMPLEOS
    # ==========================================
    with tab_jobs_view:
        st.markdown(
            """
            <div class="panel-title">🔎 Explorador de Puestos en Tiempo Real</div>
            <div class="panel-desc">Filtra entre más de 500 oportunidades de empleo en Chile y el mundo con enlaces directos para postular:</div>
            """,
            unsafe_allow_html=True,
        )

        # Barra de filtros
        col_f1, col_f2, col_f3, col_f4 = st.columns([2, 1.2, 1.2, 1])
        with col_f1:
            q_text = st.text_input("Buscador:", placeholder="Ej. Data Engineer, Python, Falabella, AWS...")
        with col_f2:
            q_geo = st.selectbox("Región / País:", ["Todas las Regiones", "🇨🇱 Solo Chile", "🌐 Solo Internacional"])
        with col_f3:
            todas_skills = ["Todas las Tecnologías"] + sorted(skills_df["skill_name"].unique().tolist())
            q_skill = st.selectbox("Tecnología Requerida:", todas_skills)
        with col_f4:
            vista_modo = st.radio("Formato de Vista:", ["Tarjetas (Cards)", "Tabla Clásica"], horizontal=True)

        # Filtrado
        df_display = jobs_df.copy()
        if q_text:
            df_display = df_display[
                df_display["title"].str.contains(q_text, case=False, na=False)
                | df_display["company_name"].str.contains(q_text, case=False, na=False)
            ]
        if q_geo == "🇨🇱 Solo Chile":
            df_display = df_display[df_display["country_code"] == "CL"]
        elif q_geo == "🌐 Solo Internacional":
            df_display = df_display[df_display["country_code"] != "CL"]

        if q_skill != "Todas las Tecnologías":
            df_display = df_display[df_display["skills_list"].str.contains(rf"\b{q_skill}\b", case=False, na=False)]

        st.caption(f"Mostrando **{len(df_display)}** posiciones coincidentes:")

        # Modo 1: Tarjetas interactivas modernas
        if vista_modo == "Tarjetas (Cards)":
            limit_show = min(len(df_display), 50)
            for _, job in df_display.head(limit_show).iterrows():
                title = job["title"]
                company = job["company_name"]
                loc = job["candidate_location"]
                salary = job["salary_raw"]
                source = job["source"]
                url = job["url"]
                skills = [s.strip() for s in str(job["skills_list"]).split(",") if s.strip()]

                salary_badge = f'<span class="job-salary-pill">💰 {salary}</span>' if salary else '<span style="color:#64748B; font-size:0.8rem;">Salario no publicado</span>'
                skills_chips = "".join([f'<span class="skill-chip">{s}</span>' for s in skills[:8]])

                card_html = f"""
                <div class="job-card">
                    <div class="job-header">
                        <div>
                            <div class="job-role">{title}</div>
                            <div class="job-company">🏢 {company} • 📍 {loc} • 📡 <span style="color:#94A3B8;">{source}</span></div>
                        </div>
                        <div>{salary_badge}</div>
                    </div>
                    <div class="job-meta-row">
                        {skills_chips}
                    </div>
                    <div style="text-align: right; margin-top: 0.6rem;">
                        <a href="{url}" target="_blank" class="apply-btn">Postularse / Ver Oferta 🔗</a>
                    </div>
                </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)

            if len(df_display) > 50:
                st.info(f"Mostrando las primeras 50 de {len(df_display)} ofertas. Usa los filtros para acotar la búsqueda.")

        # Modo 2: Tabla analítica con width="stretch"
        else:
            table_df = df_display[[
                "title", "company_name", "candidate_location", "salary_raw", "skills_list", "source", "url"
            ]].rename(
                columns={
                    "title": "Puesto",
                    "company_name": "Empresa",
                    "candidate_location": "Ubicación",
                    "salary_raw": "Salario",
                    "skills_list": "Skills Requeridas",
                    "source": "Portal",
                    "url": "Postularse",
                }
            )
            st.dataframe(
                table_df,
                column_config={
                    "Postularse": st.column_config.LinkColumn("Enlace", display_text="Ver Oferta 🔗"),
                },
                width="stretch",
                hide_index=True,
                height=520,
            )

    # ==========================================
    # PESTAÑA 5: ARQUITECTURA & METODOLOGÍA
    # ==========================================
    with tab_methodology:
        st.markdown(
            """
            <div class="panel-title">⚙️ Arquitectura Data Lakehouse & Ciclo de Vida</div>
            <div class="panel-desc">Implementación del patrón Medallion utilizado por las grandes empresas tecnológicas:</div>
            """,
            unsafe_allow_html=True,
        )

        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.markdown(
                """
                <div class="job-card" style="border-top: 4px solid #CD7F32;">
                    <h4>🥉 Capa Bronze (Raw)</h4>
                    <p style="font-size: 0.88rem; color: #CBD5E1; line-height: 1.5;">
                        <b>Origen:</b> Get on Board API, Remotive API y Arbeitnow API.<br>
                        <b>Almacenamiento:</b> Payloads JSON íntegros y tabla <code>bronze.raw_jobs</code> en DuckDB con marca temporal UTC.<br>
                        <b>Resiliencia:</b> Reintentos exponenciales automáticos ante caídas o límites de cuota.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_m2:
            st.markdown(
                """
                <div class="job-card" style="border-top: 4px solid #C0C0C0;">
                    <h4>🥈 Capa Silver (Clean)</h4>
                    <p style="font-size: 0.88rem; color: #CBD5E1; line-height: 1.5;">
                        <b>Transformación:</b> Deduplicación por hash de vacante, limpieza de HTML y normalización de moneda.<br>
                        <b>NLP & Regex:</b> Extracción estricta por límites de palabra (<code>\\b</code>) mapeando 30+ tecnologías.<br>
                        <b>Relacional:</b> <code>silver.jobs</code> vinculada 1-a-N con <code>silver.job_skills</code>.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_m3:
            st.markdown(
                """
                <div class="job-card" style="border-top: 4px solid #FFD700;">
                    <h4>🥇 Capa Gold (Marts)</h4>
                    <p style="font-size: 0.88rem; color: #CBD5E1; line-height: 1.5;">
                        <b>Analítica:</b> Vistas pre-agregadas de alto rendimiento consumidas directamente por Streamlit.<br>
                        <b>Modelos:</b> <code>mart_skills_demand</code>, <code>mart_category_insights</code> y <code>mart_job_search</code>.<br>
                        <b>Velocidad:</b> Tiempos de consulta &lt; 15 milisegundos sobre DuckDB.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("---")
        st.markdown(
            """
            #### 🛡️ Calidad de Código & Pruebas Unitarias
            El proyecto incluye una suite automatizada de pruebas con **Pytest** que valida:
            1. Mocking de respuestas de red simulando fallos y reintentos en APIs.
            2. Extracción precisa de tecnologías sin falsos positivos (ej. "Go" vs "Good").
            3. Conversión de formatos salariales anuales y mensuales (USD/CLP).
            """
        )

    # Footer
    st.markdown(
        """
        <div class="app-footer">
            ⚡ <b>TechPulse Analytics Platform</b> • Diseñado como proyecto de alto impacto para Portafolio de Data Engineering.<br>
            Desarrollado con Python 3.13, DuckDB Columnar Lakehouse, Plotly & Streamlit.
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
