"""QuantumFlow AI — enhanced hybrid quantum-classical traffic command center."""
import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
import streamlit.components.v1 as components
import json

from modules.simulation_core import TrafficNetwork
from modules.congestion_detector import update_edge_weights, find_bottlenecks, detect_traffic_shocks
from modules.routing_engine import shortest_path, reroute_if_needed
from modules.quantum_opt import optimize_signals, build_conflict_pairs
from modules.emergency_handler import EmergencyCorridor
from modules.analytics import environmental_impact, comparison_table, scenario_comparison
from modules import traffic_ai as ai

st.set_page_config(page_title="QuantumFlow AI", page_icon="🚦", layout="wide", initial_sidebar_state="expanded")

# ----------------------------- login ---------------------------------------
# Demo authentication for the local hackathon dashboard.
DEMO_USERS = {
    "admin": "quantumflow",
    "operator": "traffic123",
}

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_role" not in st.session_state:
    st.session_state.user_role = ""

LOGIN_CSS = """
<style>
.login-shell{min-height:78vh;display:flex;align-items:center;justify-content:center;padding:30px 0}
.login-card{max-width:480px;width:100%;margin:auto;background:linear-gradient(145deg,#0d1829,#08101c);border:1px solid #243c59;border-radius:24px;padding:34px;box-shadow:0 25px 80px rgba(0,0,0,.42)}
.login-logo{width:64px;height:64px;border-radius:18px;display:grid;place-items:center;margin:0 auto 16px;background:linear-gradient(135deg,#123555,#111a2d);border:1px solid #31597d;font-size:2rem;box-shadow:0 0 35px rgba(50,200,255,.13)}
.login-title{text-align:center;font-size:2rem;font-weight:950;color:#f5f9ff;letter-spacing:-.04em}.login-sub{text-align:center;color:#8394aa;font-size:.82rem;margin:8px 0 24px}
.login-badge{text-align:center;color:#62dcff;font-size:.62rem;font-weight:900;letter-spacing:.16em;text-transform:uppercase;margin-bottom:10px}
.login-hint{text-align:center;color:#61748d;font-size:.67rem;margin-top:14px}
</style>
"""
st.markdown(LOGIN_CSS, unsafe_allow_html=True)

if not st.session_state.authenticated:
    st.markdown("""
    <div class='login-shell'><div class='login-card'>
      <div class='login-logo'>🚦</div>
      <div class='login-badge'>SMART CITY • CONTROL CENTER</div>
      <div class='login-title'>QuantumFlow AI</div>
      <div class='login-sub'>Secure access to the live hybrid quantum-classical traffic command dashboard.</div>
    </div></div>
    """, unsafe_allow_html=True)
    with st.form("login_form"):
        username = st.text_input("Username", placeholder="Enter username")
        password = st.text_input("Password", type="password", placeholder="Enter password")
        submitted = st.form_submit_button("🔐  Sign in to Dashboard", use_container_width=True)
    if submitted:
        if DEMO_USERS.get(username.strip().lower()) == password:
            st.session_state.authenticated = True
            st.session_state.user_role = "Administrator" if username.strip().lower() == "admin" else "Traffic Operator"
            st.rerun()
        else:
            st.error("Invalid username or password.")
    st.caption("Demo login: admin / quantumflow  ·  operator / traffic123")
    st.stop()

st.markdown("""
<style>
:root{--bg:#050914;--panel:#0b1220;--panel2:#101a2c;--line:#1c2a40;--text:#f4f8ff;--muted:#8795aa;--cyan:#57d9ff;--blue:#6d7cff;--green:#45e6a3;--amber:#ffc857;--red:#ff6574;--violet:#a98cff}
.stApp{background:radial-gradient(900px 500px at 75% -10%,rgba(72,117,255,.20),transparent 60%),radial-gradient(700px 450px at 5% 20%,rgba(0,210,255,.08),transparent 60%),#050914;color:var(--text)}
.block-container{max-width:1580px;padding:1rem 1.5rem 2.5rem}
[data-testid="stSidebar"]{background:#070d18!important;border-right:1px solid #18263a!important}
[data-testid="stSidebar"]>div:first-child{padding:.8rem .75rem}
[data-testid="stSidebar"] *{color:#edf4ff}
.brand{display:flex;align-items:center;gap:12px;padding:10px 6px 16px;margin-bottom:10px;border-bottom:1px solid #17253a}
.brand-icon{width:44px;height:44px;display:grid;place-items:center;border-radius:14px;background:linear-gradient(135deg,#132d4c,#10192a);border:1px solid #2c5276;font-size:1.35rem;box-shadow:0 0 28px rgba(55,190,255,.10)}
.brand-title{font-size:1.1rem;font-weight:900;letter-spacing:-.03em}.brand-sub{font-size:.65rem;color:#7d8ca2!important;margin-top:2px}
[data-testid="stSidebar"] [data-testid="stExpander"]{background:#0b1422!important;border:1px solid #1b2b42!important;border-radius:14px!important;margin:8px 0!important}
[data-testid="stSidebar"] [data-testid="stExpander"] details summary{font-weight:800;font-size:.82rem}
[data-testid="stSidebar"] .stButton>button{background:#101d30!important;border:1px solid #263d59!important;color:#f3f7ff!important;border-radius:10px!important;font-weight:800}
[data-testid="stSidebar"] .stButton>button:hover{background:#162941!important;border-color:#4a789f!important}
[data-testid="stSidebar"] [data-testid="stNumberInput"] [data-baseweb="input"],
[data-testid="stSidebar"] [data-testid="stNumberInput"] [data-baseweb="base-input"],
[data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"]{background:#0d1828!important;border:1px solid #263d59!important;border-radius:10px!important;color:#f5f8ff!important}
[data-testid="stSidebar"] [data-testid="stNumberInput"] input,[data-testid="stSidebar"] [data-testid="stSelectbox"] input{background:#0d1828!important;color:#f5f8ff!important;-webkit-text-fill-color:#f5f8ff!important}
[data-testid="stSidebar"] [data-testid="stNumberInput"] button{background:#13243a!important;color:#66dfff!important;border-color:#263d59!important}
[data-baseweb="popover"],[data-baseweb="popover"]>div,[data-baseweb="menu"],[data-baseweb="popover"] [role="listbox"]{background:#0b1422!important;color:#f5f8ff!important;border:1px solid #263d59!important}
[data-baseweb="popover"] [role="option"]{background:#0b1422!important;color:#f5f8ff!important}
[data-baseweb="popover"] [role="option"]:hover,[data-baseweb="popover"] [aria-selected="true"]{background:#173454!important;color:#fff!important}
.hero{position:relative;overflow:hidden;border:1px solid #1b314d;border-radius:24px;padding:25px 28px;background:linear-gradient(120deg,#0b1728 0%,#0a1220 55%,#0b1424 100%);box-shadow:0 20px 55px rgba(0,0,0,.28);margin-bottom:15px}
.hero:before{content:"";position:absolute;right:-90px;top:-150px;width:360px;height:360px;border-radius:50%;background:radial-gradient(circle,rgba(62,211,255,.18),transparent 65%)}
.hero:after{content:"";position:absolute;right:100px;bottom:-100px;width:240px;height:240px;border-radius:50%;background:radial-gradient(circle,rgba(110,92,255,.12),transparent 65%)}
.eyebrow{font-size:.65rem;letter-spacing:.18em;text-transform:uppercase;color:#63dcff;font-weight:900}.hero h1{font-size:2.25rem;line-height:1.05;margin:7px 0 7px;font-weight:950;letter-spacing:-.045em}.hero p{color:#94a5bc;margin:0;max-width:820px;font-size:.88rem}.live-pill{display:inline-flex;align-items:center;gap:7px;margin-top:15px;padding:6px 11px;border-radius:999px;background:#0c2a22;border:1px solid #235b48;color:#70efba;font-size:.68rem;font-weight:850}.dot{width:7px;height:7px;border-radius:50%;background:#45e6a3;box-shadow:0 0 12px #45e6a3}
[data-testid="stMetric"]{background:linear-gradient(145deg,#0d1727,#09111e)!important;border:1px solid #1c3049!important;border-radius:16px!important;padding:13px 14px!important;box-shadow:0 10px 28px rgba(0,0,0,.18)}
[data-testid="stMetricLabel"]{color:#8292aa!important;font-size:.68rem!important;font-weight:700}
[data-testid="stMetricValue"]{color:#f3f8ff!important;font-weight:900}
.section-head{display:flex;align-items:end;justify-content:space-between;margin:18px 0 9px}.section-title{font-size:1rem;font-weight:900}.section-sub{font-size:.7rem;color:#718197}
.stTabs [data-baseweb="tab-list"]{gap:5px;background:#080f1b;border:1px solid #192940;padding:5px;border-radius:14px;margin-bottom:13px}.stTabs [data-baseweb="tab"]{background:transparent;border-radius:10px;padding:8px 12px;color:#7f8da2;font-size:.73rem;font-weight:800}.stTabs [aria-selected="true"]{background:#13243a!important;color:#ecf8ff!important;box-shadow:inset 0 0 0 1px #2d5272}
.stDataFrame{border:1px solid #1c3048;border-radius:12px;overflow:hidden}.stButton>button{border-radius:10px;font-weight:800}.stAlert{border-radius:12px}.stPlotlyChart{border:1px solid #1b2d44;border-radius:15px;padding:4px;background:#080f1b}
hr{border-color:#18283d!important}.map-wrap{border:1px solid #1d314a;border-radius:16px;overflow:hidden}
.info-card{background:linear-gradient(145deg,#0d1828,#09111e);border:1px solid #1d324b;border-radius:16px;padding:15px 16px;height:100%;box-shadow:0 10px 28px rgba(0,0,0,.15);transition:transform .15s ease,border-color .15s ease,box-shadow .15s ease}
.info-card:hover{transform:translateY(-3px);border-color:#2d5272;box-shadow:0 16px 36px rgba(0,0,0,.28)}
.info-label{font-size:.66rem;color:#7f90a7;text-transform:uppercase;letter-spacing:.12em;font-weight:800}.info-value{font-size:1.35rem;font-weight:900;margin-top:4px}.info-note{font-size:.68rem;color:#74849b;margin-top:3px}
.status-ok{color:#5ee7ae}.status-warn{color:#ffd067}.status-danger{color:#ff7180}.sidebar-foot{font-size:.6rem;color:#5f7088!important;text-align:center;padding:12px 0}


/* ZERO-WHITE GLOBAL OVERRIDE */
html, body { background:#050914 !important; color:#f4f8ff !important; }
[data-testid="stApp"], [data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stMainBlockContainer"], [data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stBottomBlockContainer"], [data-testid="stBottom"] { background:#050914 !important; }
[data-testid="stAppViewContainer"] > .main, [data-testid="stAppViewContainer"] > .main > .block-container { background:#050914 !important; }
[data-testid="stVerticalBlock"], [data-testid="stHorizontalBlock"], [data-testid="stColumn"], [data-testid="stElementContainer"] { background:transparent !important; }
iframe, [data-testid="stIFrame"], [data-testid="stCustomComponentV1"] { background:#050914 !important; border:0 !important; }
[data-testid="stIFrame"] > iframe { background:#050914 !important; border:0 !important; display:block !important; }
[data-testid="stPlotlyChart"] > div { background:#080f1b !important; }
[data-testid="stDataFrame"] > div { background:#0b1220 !important; }

/* FORCE ALL STREAMLIT SURFACES DARK */
html, body, [data-testid="stAppViewContainer"], [data-testid="stAppViewContainer"] > .main, [data-testid="stMain"], [data-testid="stMainBlockContainer"], .main, .main .block-container {
  background: #050914 !important;
  color: #f4f8ff !important;
}
[data-testid="stAppViewContainer"] { background: #050914 !important; }
[data-testid="stHeader"] { background: rgba(5,9,20,.96) !important; }
[data-testid="stToolbar"] { background: transparent !important; }
[data-testid="stVerticalBlock"], [data-testid="stHorizontalBlock"], [data-testid="stColumn"], [data-testid="stElementContainer"], [data-testid="stMarkdownContainer"] {
  background: transparent !important;
}
.stElementContainer, .element-container { background: transparent !important; }
[data-testid="stVerticalBlockBorderWrapper"] { background: #0b1220 !important; }
[data-testid="stStatusWidget"] { background: #0b1220 !important; }
/* Remove white iframe/page flashes around embedded live simulation. */
iframe { background: #050914 !important; border: 0 !important; }
/* Native Streamlit widgets */
[data-baseweb="input"], [data-baseweb="select"], [data-baseweb="textarea"], [data-baseweb="textarea"] textarea, input, textarea {
  background: #0d1828 !important; color: #f4f8ff !important; -webkit-text-fill-color: #f4f8ff !important;
}
[data-testid="stCheckbox"] label, [data-testid="stRadio"] label, [data-testid="stSelectbox"] label, [data-testid="stNumberInput"] label, [data-testid="stTextInput"] label { color:#dfeaff !important; }
[data-testid="stExpander"] details, [data-testid="stExpander"] summary { background:#0b1220 !important; color:#f4f8ff !important; }
[data-testid="stAlert"] { background:#0b1220 !important; color:#f4f8ff !important; }
[data-testid="stFileUploaderDropzone"] { background:#0b1220 !important; border-color:#263d59 !important; }
/* Plotly/HTML visual wrappers */
[data-testid="stPlotlyChart"], [data-testid="stVegaLiteChart"], [data-testid="stDeckGlJsonChart"] { background:#080f1b !important; }
/* Keep blank Streamlit spacer areas dark too. */
[data-testid="stBottomBlockContainer"], [data-testid="stBottom"] { background:#050914 !important; }

/* Global dark surface treatment: keep every tab and every Streamlit
   container in the same dark visual system. This removes the white
   background/surface that can appear inside General Insights and the
   other tabs. */
[data-testid="stVerticalBlockBorderWrapper"],
[data-testid="stVerticalBlockBorderWrapper"] > div,
[data-testid="stExpander"],
[data-testid="stDataFrame"],
[data-testid="stTable"],
[data-testid="stAlert"],
[data-testid="stPopover"],
[data-testid="stForm"],
[data-testid="stElementContainer"] {
  background: #0b1220 !important;
  color: #f4f8ff !important;
}
[data-testid="stVerticalBlockBorderWrapper"] {
  border-color: #1c3048 !important;
  border-radius: 16px !important;
}
[data-testid="stVerticalBlockBorderWrapper"] > div:first-child {
  background: transparent !important;
}
[data-testid="stDataFrame"] > div,
[data-testid="stDataFrame"] iframe {
  background: #0b1220 !important;
}
.stMarkdown, .stCaption, .stText, .stWrite { color: #f4f8ff; }
[data-testid="stHorizontalBlock"], [data-testid="stColumn"] {
  background: transparent !important;
}
/* Main-area buttons now match the sidebar's dark, bordered style instead of
   falling back to Streamlit defaults, so navigation and action buttons feel
   like one consistent design system wherever they appear. */
.main .stButton>button{background:#101d30;border:1px solid #263d59;color:#f3f7ff;transition:background .15s ease,border-color .15s ease,transform .1s ease}
.main .stButton>button:hover{background:#162941;border-color:#4a789f;transform:translateY(-1px)}
.main .stButton>button:active{transform:translateY(0)}
/* Primary (active-state) buttons use the brand cyan so the current page in
   the sidebar navigation is always visually obvious, not just structurally
   selected. */
[data-testid="stSidebar"] .stButton>button[kind="primary"]{background:linear-gradient(135deg,#0f4d73,#0b3252)!important;border:1px solid #57d9ff!important;color:#eafcff!important;box-shadow:0 0 18px rgba(87,217,255,.22)!important}
[data-testid="stSidebar"] .stButton>button[kind="primary"]:hover{background:linear-gradient(135deg,#12588a,#0d3c62)!important}

/* Compact top bar used on every page except the Dashboard, so sub-pages
   don't repeat the full-size hero banner and instead get a slim, consistent
   breadcrumb-style header. */
.page-topbar{display:flex;align-items:center;justify-content:space-between;gap:14px;border:1px solid #1b314d;border-radius:16px;padding:13px 20px;background:linear-gradient(120deg,#0b1728 0%,#0a1220 100%);margin-bottom:14px}
.page-topbar .ptb-left{display:flex;align-items:center;gap:12px}
.page-topbar .ptb-icon{width:38px;height:38px;border-radius:11px;display:grid;place-items:center;background:linear-gradient(135deg,#132d4c,#10192a);border:1px solid #2c5276;font-size:1.05rem}
.page-topbar .ptb-title{font-size:1.02rem;font-weight:900;letter-spacing:-.02em}
.page-topbar .ptb-sub{font-size:.7rem;color:#8394aa}

.block-container{animation:qfFadeIn .28s ease}
@keyframes qfFadeIn{from{opacity:0;transform:translateY(5px)}to{opacity:1;transform:none}}
</style>
""",unsafe_allow_html=True)

# ----------------------------------------------------------------------
# Shared chart theming so every Plotly figure across every page uses the
# same palette and background as the rest of the dashboard, instead of the
# generic 'plotly_dark' default clashing with the app's custom CSS.
# ----------------------------------------------------------------------
BRAND_COLORWAY = ["#57d9ff", "#6d7cff", "#45e6a3", "#ffc857", "#ff6574", "#a98cff"]


def style_fig(fig, height=None):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#080f1b",
        plot_bgcolor="#080f1b",
        font=dict(color="#dce8f5", size=12),
        colorway=BRAND_COLORWAY,
        margin=dict(l=10, r=10, t=45, b=10),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        title_font=dict(size=14),
    )
    fig.update_xaxes(gridcolor="#152135", zerolinecolor="#152135")
    fig.update_yaxes(gridcolor="#152135", zerolinecolor="#152135")
    if height:
        fig.update_layout(height=height)
    return fig


def page_topbar(icon, title, subtitle):
    """Compact header shown on every page except the Dashboard (which keeps
    the full hero banner)."""
    st.markdown(f"""
    <div class="page-topbar">
      <div class="ptb-left">
        <div class="ptb-icon">{icon}</div>
        <div><div class="ptb-title">{title}</div><div class="ptb-sub">{subtitle}</div></div>
      </div>
      <div class="live-pill" style="margin-top:0"><span class="dot"></span> LIVE · T{net.time_step}</div>
    </div>
    """, unsafe_allow_html=True)

# ----------------------------- state --------------------------------------
if "network" not in st.session_state:
    net=TrafficNetwork(seed=42);net.build_default_network(6)
    st.session_state.network=net;st.session_state.emergency=EmergencyCorridor()
    st.session_state.quantum_result=None;st.session_state.last_dispatch=None
    st.session_state.previous_counts={};st.session_state.current_route=None
    st.session_state.selected_scenario="Normal";st.session_state.last_shocks=[];st.session_state.last_scenario="Normal"

net=st.session_state.network
emergency=st.session_state.emergency
# Migrate old Streamlit sessions
for attr,default in [("event_log",[]),("history",[]),("time_step",0),("adaptive_memory",[]),("active_events",{}),("closed_edges",set())]:
    if not hasattr(net,attr):setattr(net,attr,default)
update_edge_weights(net.graph)
node_names={n:net.graph.nodes[n]["name"] for n in net.graph.nodes}

# ----------------------------- top navigation tabs -------------------------
# Page navigation now lives as a horizontal tab bar at the top of the main
# content area (previously a stacked list of buttons in the sidebar).
if "page" not in st.session_state:
    st.session_state.page = "Live Traffic Simulation"

nav_items = [
    ("⌂", "Dashboard"),
    ("◈", "Traffic Network"),
    ("🚘", "Live Traffic Simulation"),
    ("▦", "Intersections"),
    ("⚛", "Quantum Optimization"),
    ("🚑", "Emergency Corridor"),
    ("◌", "Predictive Analytics"),
    ("◇", "What-If Lab"),
    ("♧", "Fuel & CO₂"),
    ("✦", "Traffic Copilot"),
]

with st.container(border=True):
    nav_cols = st.columns(len(nav_items))
    for col, (icon, label) in zip(nav_cols, nav_items):
        active = st.session_state.page == label
        with col:
            if st.button(f"{icon}  {label}", key=f"nav_{label}", use_container_width=True,
                         type="primary" if active else "secondary"):
                st.session_state.page = label
                st.rerun()

# ----------------------------- sidebar ------------------------------------
with st.sidebar:
    st.markdown("<div class='brand'><div class='brand-icon'>🚦</div><div><div class='brand-title'>QuantumFlow AI</div><div class='brand-sub'>Urban Traffic Control Center</div></div></div>", unsafe_allow_html=True)
    st.markdown(f"<div style='padding:4px 6px 12px;color:#7f90a7;font-size:.68rem'>SIGNED IN · <b style='color:#f2f7ff'>{st.session_state.user_role}</b></div>", unsafe_allow_html=True)
    if st.button("↪ Logout", use_container_width=True, key="logout_btn"):
        st.session_state.authenticated = False
        st.session_state.user_role = ""
        st.rerun()

    # ----------------------------- controls -----------------------------
    st.markdown("<div style='font-size:.62rem;color:#60738b;letter-spacing:.16em;font-weight:900;margin:8px 6px 6px'>CONTROLS</div>", unsafe_allow_html=True)

    with st.expander("⚙️  Simulation Controls", expanded=True):
        arrival=st.slider("Traffic arrival rate",.1,1.5,.6,.05)
        steps=st.number_input("Steps per tick",1,10,1)
        scenario=st.selectbox("Active scenario",["Normal","Rush Hour","Heavy Rain","Accident","Road Closure","Stadium Surge","Pedestrian Surge"],key="selected_scenario")
        pedestrian_intensity=st.slider("Pedestrian intensity",0.0,1.0,0.35,0.05,help="Controls pedestrian crossing demand and the resulting signal-service pressure at intersections.")
        s1,s2=st.columns(2)
        with s1:
            if st.button("▶ Advance",use_container_width=True):
                if scenario != st.session_state.get("last_scenario", "Normal"):
                    net.apply_scenario(scenario)
                    st.session_state.last_scenario = scenario
                for _ in range(int(steps)):
                    net.step(arrival_rate=arrival,pedestrian_intensity=pedestrian_intensity)
                    update_edge_weights(net.graph)
                update_edge_weights(net.graph)
                shocks,_=detect_traffic_shocks(net.graph,st.session_state.previous_counts)
                st.session_state.last_shocks=shocks[:5]
                st.session_state.previous_counts={e[:2]:e[2]["vehicle_count"] for e in net.graph.edges(data=True)}
        with s2:
            if st.button("↻ Reset",use_container_width=True):
                net=TrafficNetwork(seed=42);net.build_default_network(6);st.session_state.network=net;st.session_state.quantum_result=None;st.session_state.last_dispatch=None;st.session_state.previous_counts={};st.session_state.last_shocks=[];st.session_state.last_scenario="Normal";st.rerun()
        st.caption(f"Simulation time: **T{net.time_step}** · Scenario: **{scenario}**")

    with st.expander("⚛  Quantum Signal Control", expanded=False):
        use_quantum=st.toggle("Enable QAOA",True,help="If the quantum stack is unavailable, the optimizer uses the classical fallback and reports the method.")
        if st.button("⚛ Optimize Signals",use_container_width=True):
            update_edge_weights(net.graph)
            before=net.network_metrics()["total_queue"]
            q={n:sum(d["queue_length"] for _,_,d in net.graph.in_edges(n,data=True)) for n in net.graph.nodes}
            qr=optimize_signals(net.graph,q,build_conflict_pairs(net.graph),use_quantum=use_quantum)
            net.set_signal_plan(qr["green_durations"]);st.session_state.quantum_result=qr
            net.record_adaptive_memory(qr,before,before)
        if st.button("🧠 Apply AI Copilot",use_container_width=True):
            update_edge_weights(net.graph)
            q={n:sum(d["queue_length"] for _,_,d in net.graph.in_edges(n,data=True)) for n in net.graph.nodes}
            qr=optimize_signals(net.graph,q,build_conflict_pairs(net.graph),use_quantum=use_quantum)
            net.set_signal_plan(qr["green_durations"]);st.session_state.quantum_result=qr;st.session_state.copilot_applied=True

    with st.expander("🚑  Emergency Green Corridor", expanded=False):
        src=st.selectbox("Source",list(node_names),format_func=lambda x:node_names[x],key="ems_src")
        dst=st.selectbox("Hospital",list(node_names),format_func=lambda x:node_names[x],index=min(3,len(node_names)-1),key="ems_dst")
        a,b=st.columns(2)
        with a:
            if st.button("Dispatch",use_container_width=True):
                update_edge_weights(net.graph);st.session_state.last_dispatch=emergency.dispatch(net.graph,src,dst)
        with b:
            if st.button("Restore",use_container_width=True):
                emergency.clear(net.graph);st.session_state.last_dispatch=None
        if emergency.active: st.success("Corridor active")

    with st.expander("⚠  Traffic Events", expanded=False):
        event_edges=list(net.graph.edges())
        event_edge=st.selectbox("Affected road",event_edges,format_func=lambda e:f"{node_names[e[0]]} → {node_names[e[1]]}")
        ec1,ec2=st.columns(2)
        with ec1:
            if st.button("Accident",use_container_width=True):net.add_incident(*event_edge,severity=1.5,duration=6,label="Accident")
        with ec2:
            if st.button("Close Road",use_container_width=True):net.add_incident(*event_edge,severity=3,duration=6,close=True,label="Road Closure")
        if net.active_events:
            st.caption(f"Active events: **{len(net.active_events)}**")

    st.markdown("<div class='sidebar-foot'>DEMO MODE · Hybrid quantum-classical control</div>",unsafe_allow_html=True)


# ----------------------------- current state -------------------------------
update_edge_weights(net.graph)
metrics=net.network_metrics();edges=net.edge_table();bottlenecks=find_bottlenecks(net.graph)
env=environmental_impact(edges);env.update(metrics)
active_events=list(net.active_events.values())
page = st.session_state.get("page", "Dashboard")

_PAGE_META = {
    "Dashboard": ("⌂", "Command Dashboard", "One-click access to every traffic intelligence module"),
    "Traffic Network": ("◈", "Traffic Network", "Connected road network, signal state, traffic density and emergency routing"),
    "Live Traffic Simulation": ("🚘", "Live Vehicle Simulation", "Animated vehicles, adaptive signals and congestion response in real time"),
    "Intersections": ("▦", "Multi-Intersection Intelligence", "Queue pressure, bottlenecks and traffic feedback"),
    "Quantum Optimization": ("⚛", "Hybrid Quantum Optimization", "QUBO formulation → QAOA search → adaptive green durations"),
    "Emergency Corridor": ("🚑", "Emergency Green Corridor", "Prioritize an ambulance route while minimizing disruption"),
    "Predictive Analytics": ("◌", "Predictive Traffic Pulse", "Forecast queue pressure before it becomes a bottleneck"),
    "What-If Lab": ("◇", "What-If Traffic Lab", "Run controlled scenarios and compare traffic strategies"),
    "Fuel & CO₂": ("♧", "Environmental Impact", "Traffic → waiting → fuel → CO₂"),
    "Traffic Copilot": ("✦", "Traffic Copilot", "Explainable local AI assistance for traffic operators"),
}

if page == "Dashboard":
    # Full hero banner only on the landing page — sub-pages get a compact
    # topbar instead so the same big block isn't repeated on every screen.
    st.markdown(f"""
    <div class="hero">
      <div class="eyebrow">SMART CITY • HYBRID QUANTUM CONTROL</div>
      <h1>QuantumFlow AI</h1>
      <p>Adaptive urban traffic optimization across connected intersections using QUBO, QAOA, dynamic routing, pedestrian-aware control and emergency green corridors.</p>
      <div class="live-pill"><span class="dot"></span> SIMULATION READY · T{net.time_step}</div>
    </div>
    """,unsafe_allow_html=True)
else:
    icon, title, subtitle = _PAGE_META.get(page, ("⌂", page, ""))
    page_topbar(icon, title, subtitle)

if emergency.active:st.success("🚑 Emergency green corridor ACTIVE")
if active_events:st.warning("⚠ Active event: "+", ".join(f"{e['label']} on {e['u']}→{e['v']}" for e in active_events))

k1,k2,k3,k4,k5,k6=st.columns(6)
k1.metric("🚗 Vehicles",metrics["total_vehicles"])
k2.metric("🛣 Queue",metrics["total_queue"])
k3.metric("⏱ Avg Delay",f"{metrics['avg_delay_min']:.1f} min")
k4.metric("📡 Density",f"{metrics['avg_density']*100:.0f}%")
k5.metric("🌱 CO₂",f"{env['co2_kg']:.1f} kg")
k6.metric("◷ Time Step",net.time_step)

# ----------------------------- pages --------------------------------------

def section_title(title, subtitle):
    st.markdown(f"<div class='section-head'><div><div class='section-title'>{title}</div><div class='section-sub'>{subtitle}</div></div></div>", unsafe_allow_html=True)

def go_button(label, target, icon="→"):
    if st.button(f"{icon}  {label}", use_container_width=True, key=f"go_{target}"):
        st.session_state.page = target
        st.rerun()

# Live traffic simulation -----------------------------------------------------
def render_live_simulation(net, emergency):
    """True browser-side microscopic intersection simulation: visible cars/buses/trucks, lane queues,
    per-approach signals, adaptive signal switching, and a moving ambulance green corridor."""
    # Fixed 3x2 urban grid gives a consistent visual simulation regardless of the network coordinates.
    nodes = [
        {"id": "I1", "x": 0, "y": 0}, {"id": "I2", "x": 1, "y": 0}, {"id": "I3", "x": 2, "y": 0},
        {"id": "I4", "x": 0, "y": 1}, {"id": "I5", "x": 1, "y": 1}, {"id": "I6", "x": 2, "y": 1},
    ]
    payload = {"nodes": nodes, "time": int(getattr(net, "time_step", 0))}
    data_json = json.dumps(payload)
    html = """<!doctype html><html><head><meta charset='utf-8'><style>
    html,body{margin:0;padding:0;background:#050914;color:#eaf4ff;font-family:Inter,Arial,sans-serif;overflow:hidden;width:100%;height:100%}
    #wrap{position:relative;width:100%;height:790px;background:radial-gradient(circle at 48% 45%,#0c1a2b,#040812 78%);border:1px solid #20364f;border-radius:18px;overflow:hidden;box-sizing:border-box}
    canvas{width:100%;height:100%;display:block}
    .hud{position:absolute;left:14px;right:14px;top:12px;display:flex;gap:8px;align-items:center;z-index:8;flex-wrap:wrap}
    .pill{background:rgba(5,12,22,.96);border:1px solid #28425d;border-radius:999px;padding:8px 12px;font-size:12px;font-weight:850;box-shadow:0 6px 18px rgba(0,0,0,.25)}
    .live{color:#55f0a8;border-color:#27694e}.cyan{color:#5be3ff;border-color:#28637a}.amber{color:#ffd56a;border-color:#715d2b}
    button{border:1px solid #28506a;background:#0a1b2b;color:#a9edff;border-radius:10px;padding:9px 14px;font-weight:900;cursor:pointer}
    #ambulanceBtn{margin-left:auto;background:#33141b;color:#ff9ca7;border-color:#ff596d}#ambulanceBtn.active{background:#ff344d;color:#fff}
    #event{position:absolute;left:14px;bottom:14px;max-width:520px;background:rgba(5,12,22,.96);border:1px solid #29435f;border-radius:13px;padding:11px 14px;font-size:11px;line-height:1.5;z-index:8;box-shadow:0 10px 30px rgba(0,0,0,.3)}
    #event .em{color:#59e5ff;font-weight:900}.panel{position:absolute;right:14px;bottom:14px;width:220px;background:rgba(5,12,22,.96);border:1px solid #29435f;border-radius:13px;padding:11px 13px;font-size:11px;z-index:8}
    .row{display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid rgba(70,100,130,.18)}.row:last-child{border:0}.green{color:#3ff09a}.red{color:#ff5d70}.blue{color:#54dcff}.yellow{color:#ffd35c}
    </style></head><body><div id='wrap'>
      <div class='hud'><div class='pill live'>● LIVE VEHICLE MICRO-SIMULATION</div><div class='pill cyan' id='clock'>T0</div><div class='pill' id='stats'>Cars 0 · Buses 0 · Trucks 0</div><div class='pill' id='signalMode'>ADAPTIVE SIGNALS</div><button id='startBtn'>▶ Start</button><button id='pauseBtn'>⏸ Pause</button><button id='resetBtn'>↻ Reset</button><button id='ambulanceBtn'>🚑 Dispatch Ambulance</button></div>
      <canvas id='c'></canvas>
      <div id='event'><b>Live traffic:</b> vehicles move at realistic speeds, maintain spacing, decelerate for red signals, queue at junctions, and accelerate smoothly when the automated signal gives that approach green.</div>
      <div class='panel'><b style='color:#7ceaff'>LIVE SIGNAL / QUEUE</b><div id='signalPanel'></div></div>
    </div><script>
    const DATA=__DATA__;
    const wrap=document.getElementById('wrap'), canvas=document.getElementById('c'), ctx=canvas.getContext('2d');
    let W=0,H=0, dpr=1, running=true, last=performance.now(), sim=0, vehicles=[], ambulance=null, emergency=false;
    const NS=['I1','I2','I3','I4','I5','I6'];
    const pos={};
    let signals={};
    const colors={car:['#35b9ff','#ff6b6b','#ffd34e','#54e38a','#b78cff'],bus:['#3aa7ff','#4dd7b2'],truck:['#ff9f43','#b9c4d0']};
    function resize(){W=wrap.clientWidth;H=wrap.clientHeight;dpr=devicePixelRatio||1;canvas.width=W*dpr;canvas.height=H*dpr;ctx.setTransform(dpr,0,0,dpr,0,0);layout();}
    function layout(){const left=90,right=W-310,top=145,bottom=H-105;NS.forEach((id,i)=>{const col=i%3,row=Math.floor(i/3);pos[id]={x:left+col*(right-left)/2,y:top+row*(bottom-top)};});}
    addEventListener('resize',resize); resize();
    const links=[['I1','I2'],['I2','I3'],['I4','I5'],['I5','I6'],['I1','I4'],['I2','I5'],['I3','I6']];
    const dirs=[]; links.forEach(([a,b])=>{dirs.push([a,b]);dirs.push([b,a]);});
    const key=(a,b)=>a+'>'+b;
    function makeSignals(){signals={};NS.forEach(id=>signals[id]={phase:'EW',timer:0,ns:'RED',ew:'GREEN',em:false});}
    function spawnVehicle(a,b,type,lane,t){vehicles.push({id:vehicles.length+1,a,b,type,lane,t,speed:type==='bus'?.027:type==='truck'?.024:.035,base:type==='bus'?.027:type==='truck'?.024:.035,stopped:false,color:colors[type][Math.floor(Math.random()*colors[type].length)]});}
    function reset(){vehicles=[];makeSignals();ambulance=null;emergency=false;sim=0;for(let i=0;i<110;i++){const d=dirs[Math.floor(Math.random()*dirs.length)];spawnVehicle(d[0],d[1],i%11===0?'bus':i%17===0?'truck':'car',i%2,Math.random());}for(let i=0;i<25;i++){const d=['I2','I5'];const dest=i%2?'I3':'I1';spawnVehicle(d[0],dest,'car',i%2,.15+i*.028)};setEvent('Normal traffic running. Signals automatically balance queues; vehicles stop only when their approach is red.');}
    reset();
    function vertical(a,b){return pos[a].x===pos[b].x} function approach(a,b){return vertical(a,b)?'NS':'EW';}
    function signalFor(v){const s=signals[v.b];if(!s)return 'RED';if(emergency && ambulance && corridorEdge(v.a,v.b))return 'GREEN';return approach(v.a,v.b)==='NS'?s.ns:s.ew;}
    function corridorEdge(a,b){if(!ambulance)return false;const route=ambulance.route;for(let i=ambulance.idx;i<Math.min(route.length-1,ambulance.idx+2);i++)if(route[i]===a&&route[i+1]===b)return true;return false;}
    function queueFor(id,ap){return vehicles.filter(v=>v.b===id&&approach(v.a,v.b)===ap&&v.stopped).length;}
    function adaptive(){NS.forEach(id=>{const s=signals[id];s.timer+=.016;const qns=queueFor(id,'NS'),qew=queueFor(id,'EW');if(emergency)return;if(s.timer<3)return;if(s.phase==='EW'&&qns>qew+2){s.phase='NS';s.timer=0;}else if(s.phase==='NS'&&qew>qns+2){s.phase='EW';s.timer=0;}else if(s.timer>7){s.phase=s.phase==='EW'?'NS':'EW';s.timer=0;}s.ns=s.phase==='NS'?'GREEN':'RED';s.ew=s.phase==='EW'?'GREEN':'RED';});}
    function activateEmergency(){if(emergency)return;emergency=true;ambulance={route:['I1','I2','I3','I6'],idx:0,t:.02,speed:.055};NS.forEach(id=>{signals[id].em=false;});setEvent('🚨 <b>AMBULANCE DISPATCHED</b>: I1 → I2 → I3 → I6. Signals ahead are turning GREEN; conflicting approaches turn RED and vehicles in the emergency lane are released.');document.getElementById('ambulanceBtn').classList.add('active');document.getElementById('ambulanceBtn').textContent='🚑 Emergency Active';}
    function updateEmergency(dt){if(!ambulance)return;ambulance.t+=ambulance.speed*dt/1000;if(ambulance.t>=1){ambulance.t=0;ambulance.idx++;if(ambulance.idx>=ambulance.route.length-1){ambulance=null;emergency=false;document.getElementById('ambulanceBtn').classList.remove('active');document.getElementById('ambulanceBtn').textContent='🚑 Dispatch Ambulance';setEvent('✅ <b>Ambulance cleared the corridor.</b> Signals returned to adaptive balancing and normal traffic resumed.');}}}
    function spacing(v){
      let min=99;
      for(const o of vehicles){
        if(o===v||o.a!==v.a||o.b!==v.b||o.lane!==v.lane)continue;
        const d=o.t-v.t;
        if(d>0&&d<min)min=d;
      }
      return min>.045;
    }
    function moveVehicle(v,dt){
      const sig=signalFor(v);
      const nearSignal=v.t>.84;
      const gapOk=spacing(v);
      let canMove=gapOk && (!nearSignal || sig==='GREEN');
      v.stopped=!canMove;
      const accel=v.stopped ? 0.030 : 0.018;
      const decel=v.stopped ? 0.060 : 0.0;
      if(canMove){
        v.speed=Math.min(v.base,v.speed+accel*dt/1000);
        v.t+=v.speed*dt/1000;
      }else{
        v.speed=Math.max(0,v.speed-decel*dt/1000);
      }
      if(v.t>=1){
        const choices=dirs.filter(d=>d[0]===v.b);
        if(choices.length){
          const d=choices[Math.floor(Math.random()*choices.length)];
          v.a=d[0];v.b=d[1];v.t=.015;v.speed=v.base*.55;
        }else v.t=0;
      }
    }
    function moveAmbulance(dt){if(!ambulance)return;updateEmergency(dt);}
    function drawBackground(){ctx.fillStyle='#07101b';ctx.fillRect(0,0,W,H);for(let x=20;x<W;x+=42){ctx.strokeStyle='rgba(70,120,160,.035)';ctx.beginPath();ctx.moveTo(x,90);ctx.lineTo(x,H);ctx.stroke();}for(let y=100;y<H;y+=42){ctx.strokeStyle='rgba(70,120,160,.035)';ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(W,y);ctx.stroke();}}
    function drawRoad(a,b){const A=pos[a],B=pos[b],dx=B.x-A.x,dy=B.y-A.y,len=Math.hypot(dx,dy),nx=-dy/len,ny=dx/len;ctx.lineCap='butt';ctx.strokeStyle='#172433';ctx.lineWidth=54;ctx.beginPath();ctx.moveTo(A.x,A.y);ctx.lineTo(B.x,B.y);ctx.stroke();ctx.strokeStyle='#26394b';ctx.lineWidth=2;ctx.setLineDash([13,10]);ctx.beginPath();ctx.moveTo(A.x+nx*0,A.y+ny*0);ctx.lineTo(B.x+nx*0,B.y+ny*0);ctx.stroke();ctx.setLineDash([]);if(emergency&&corridorEdge(a,b)){ctx.strokeStyle='rgba(52,229,255,.18)';ctx.lineWidth=42;ctx.beginPath();ctx.moveTo(A.x,A.y);ctx.lineTo(B.x,B.y);ctx.stroke();ctx.strokeStyle='#48ddff';ctx.lineWidth=4;ctx.setLineDash([18,9]);ctx.beginPath();ctx.moveTo(A.x,A.y);ctx.lineTo(B.x,B.y);ctx.stroke();ctx.setLineDash([]);}}
    function drawIntersection(id){const p=pos[id];ctx.fillStyle='#0b1623';ctx.strokeStyle='#3c5269';ctx.lineWidth=2;ctx.beginPath();ctx.roundRect(p.x-31,p.y-31,62,62,10);ctx.fill();ctx.stroke();ctx.fillStyle='#dce8f6';ctx.font='bold 11px Arial';ctx.textAlign='center';ctx.fillText(id,p.x,p.y+4);ctx.textAlign='left';drawLights(id);}
    function drawLights(id){const p=pos[id],s=signals[id];const lights=[{x:p.x-48,y:p.y-16,c:s.ns==='GREEN'?'#36ed9a':'#ff4f65',txt:'N/S'},{x:p.x+38,y:p.y-16,c:s.ew==='GREEN'?'#36ed9a':'#ff4f65',txt:'E/W'}];if(emergency&&ambulance){lights.forEach(l=>{l.c='#ff4f65';});for(let i=ambulance.idx;i<Math.min(ambulance.idx+2,ambulance.route.length-1);i++){const a=ambulance.route[i],b=ambulance.route[i+1];if(id===a){const l=approach(a,b)==='NS'?lights[0]:lights[1];l.c='#36ed9a';}}}lights.forEach(l=>{ctx.fillStyle='#07101a';ctx.strokeStyle='#32485f';ctx.beginPath();ctx.roundRect(l.x,l.y,34,16,5);ctx.fill();ctx.stroke();ctx.fillStyle=l.c;ctx.beginPath();ctx.arc(l.x+8,l.y+8,4,0,Math.PI*2);ctx.fill();ctx.fillStyle='#a9bfd2';ctx.font='7px Arial';ctx.fillText(l.txt,l.x+14,l.y+10);});}
    function drawVehicle(v){const A=pos[v.a],B=pos[v.b],dx=B.x-A.x,dy=B.y-A.y,len=Math.hypot(dx,dy),nx=-dy/len,ny=dx/len;const laneOffset=v.lane?9:-9;const x=A.x+dx*v.t+nx*laneOffset,y=A.y+dy*v.t+ny*laneOffset,ang=Math.atan2(dy,dx);ctx.save();ctx.translate(x,y);ctx.rotate(ang);let w=13,h=7;if(v.type==='bus'){w=24;h=9;}if(v.type==='truck'){w=19;h=9;}ctx.fillStyle=v.stopped?'#d64758':v.color;ctx.shadowBlur=v.stopped?3:9;ctx.shadowColor=ctx.fillStyle;ctx.beginPath();ctx.roundRect(-w/2,-h/2,w,h,2);ctx.fill();ctx.fillStyle='#d9f5ff';ctx.fillRect(w*.02,-h*.32,w*.28,h*.64);if(v.type==='bus'){ctx.fillStyle='#111d2c';ctx.fillRect(-w*.28,-h*.28,w*.48,h*.56);}ctx.restore();}
    function drawAmbulance(){if(!ambulance)return;const a=pos[ambulance.route[ambulance.idx]],b=pos[ambulance.route[ambulance.idx+1]],dx=b.x-a.x,dy=b.y-a.y,len=Math.hypot(dx,dy),nx=-dy/len,ny=dx/len,x=a.x+dx*ambulance.t+nx*0,y=a.y+dy*ambulance.t+ny*0,ang=Math.atan2(dy,dx);ctx.save();ctx.translate(x,y);ctx.rotate(ang);ctx.shadowBlur=24;ctx.shadowColor='#ff4058';ctx.fillStyle='#fff';ctx.beginPath();ctx.roundRect(-15,-6,30,12,3);ctx.fill();ctx.fillStyle='#ff4058';ctx.fillRect(-2,-6,4,12);ctx.fillRect(-8,-2,16,4);ctx.fillStyle='#58dfff';ctx.fillRect(5,-3,5,6);ctx.fillStyle='#ff3d53';ctx.fillRect(-13,-2,3,4);ctx.restore();}
    function panel(){let h='';NS.forEach(id=>{const s=signals[id],q=queueFor(id,'NS')+queueFor(id,'EW');const sig=emergency&&ambulance&&ambulance.route.slice(ambulance.idx,ambulance.idx+2).includes(id)?'EMERGENCY GREEN':(s.phase==='NS'?'N/S GREEN':'E/W GREEN');const cls=sig==='EMERGENCY GREEN'?'blue':sig.includes('GREEN')?'green':'red';h+=`<div class='row'><span>${id}</span><span class='${cls}'>${sig}</span><span>Q ${q}</span></div>`;});document.getElementById('signalPanel').innerHTML=h;}
    function setEvent(t){document.getElementById('event').innerHTML=t;}
    function update(dt){if(!running)return;sim+=dt/1000;if(!emergency)adaptive();vehicles.forEach(v=>moveVehicle(v,dt));moveAmbulance(dt);panel();const cars=vehicles.filter(v=>v.type==='car').length,buses=vehicles.filter(v=>v.type==='bus').length,trucks=vehicles.filter(v=>v.type==='truck').length,moving=vehicles.filter(v=>!v.stopped).length;document.getElementById('stats').textContent=`${cars} cars · ${buses} buses · ${trucks} trucks · ${moving} moving`;document.getElementById('clock').textContent='LIVE · '+Math.floor(sim)+'s';document.getElementById('signalMode').textContent=emergency?'🚑 GREEN CORRIDOR ACTIVE':'⚙ ADAPTIVE SIGNAL CONTROL';}
    function render(){drawBackground();links.forEach(l=>drawRoad(l[0],l[1]));vehicles.forEach(drawVehicle);drawAmbulance();NS.forEach(drawIntersection);requestAnimationFrame(render);}
    document.getElementById('startBtn').onclick=()=>{running=true;setEvent('▶ <b>Simulation running.</b> Automated signals are balancing traffic every few seconds.');};
    document.getElementById('pauseBtn').onclick=()=>{running=false;setEvent('⏸ <b>Simulation paused.</b> Press Start to continue vehicle movement.');};
    document.getElementById('resetBtn').onclick=()=>{reset();};
    document.getElementById('ambulanceBtn').onclick=activateEmergency;
    render();setInterval(()=>update(100),100);
    </script></body></html>"""
    components.html(html.replace("__DATA__", data_json), height=820, scrolling=False)


# Dashboard ------------------------------------------------------------------
if page == "Dashboard":
    section_title("Command Dashboard", "One-click access to every traffic intelligence module")
    st.markdown("""
    <div class='info-card' style='margin-bottom:14px'>
      <div class='info-label'>CONTROL CENTER</div>
      <div style='font-size:1.55rem;font-weight:950;margin-top:5px'>Urban Traffic • Quantum Optimization • Emergency Response</div>
      <div class='info-note'>Use the navigation on the left or the module cards below. The simulation advances only when you choose Advance.</div>
    </div>
    """, unsafe_allow_html=True)
    cards = [
        ("🗺️", "Traffic Network", "Explore roads, traffic density, signals and live simulation state."),
        ("🚘", "Live Traffic Simulation", "Watch vehicles move, queues form, signals react and congestion clear in real time."),
        ("🚦", "Intersections", "Inspect queue pressure, bottlenecks and traffic feedback."),
        ("⚛", "Quantum Optimization", "Run QUBO + QAOA signal optimization and compare strategies."),
        ("🚑", "Emergency Corridor", "Dispatch an emergency route and inspect saved travel time."),
        ("🔮", "Predictive Analytics", "Forecast queue pressure from recent simulation history."),
        ("🧪", "What-If Lab", "Test traffic scenarios with controlled experiments."),
        ("🌱", "Fuel & CO₂", "Track environmental impact of traffic conditions."),
        ("🤖", "Traffic Copilot", "Generate local explainable traffic insights."),
    ]
    cols = st.columns(4)
    for i,(icon,title,desc) in enumerate(cards):
        with cols[i%4]:
            st.markdown(f"<div class='info-card' style='min-height:145px;margin-bottom:12px'><div style='font-size:1.65rem'>{icon}</div><div style='font-size:.95rem;font-weight:900;margin-top:7px'>{title}</div><div class='info-note' style='line-height:1.45'>{desc}</div></div>", unsafe_allow_html=True)
            if st.button("Open module  →", use_container_width=True, key=f"dash_{title}"):
                st.session_state.page = title
                st.rerun()
    st.markdown("<div class='section-head'><div><div class='section-title'>Network Snapshot</div><div class='section-sub'>Current simulation state</div></div></div>", unsafe_allow_html=True)
    s1,s2,s3,s4,s5,s6 = st.columns(6)
    s1.metric("Vehicles", metrics["total_vehicles"])
    s2.metric("Queue", metrics["total_queue"])
    s3.metric("Avg Delay", f"{metrics['avg_delay_min']:.1f} min")
    s4.metric("Density", f"{metrics['avg_density']*100:.0f}%")
    s5.metric("CO₂", f"{env['co2_kg']:.1f} kg")
    s6.metric("Time Step", net.time_step)

# Traffic Network ------------------------------------------------------------
elif page == "Live Traffic Simulation":
    section_title("Live Vehicle Simulation", "Vehicles move continuously; congested approaches turn red and receive adaptive green priority.")
    st.markdown("<div class='info-card' style='margin-bottom:12px'><div class='info-label'>LIVE CONTROL LOOP</div><div class='info-note' style='font-size:.76rem;color:#a6b5c8'>Red roads indicate congestion. When an approach becomes heavily congested, the signal adapts and queued vehicles begin moving.</div></div>", unsafe_allow_html=True)
    render_live_simulation(net, emergency)
    st.divider()
    st.subheader("Live control feedback")
    live_df=pd.DataFrame([{
        "Road": f"{r['from']} → {r['to']}", "Vehicles": r["vehicle_count"], "Capacity": r["capacity"],
        "Density": f"{r['density']*100:.0f}%", "Queue": r["queue_length"], "Signal response": "CONGESTED → ADAPTIVE GREEN" if r["density"]>=0.75 else "NORMAL"
    } for r in edges])
    st.dataframe(live_df,use_container_width=True,hide_index=True)

elif page == "Traffic Network":
    center_lat=sum(net.graph.nodes[n]["lat"] for n in net.graph)/len(net.graph); center_lon=sum(net.graph.nodes[n]["lon"] for n in net.graph)/len(net.graph)
    # NOTE: 'CartoDB dark_matter' now requires a Carto API key (a "please
    # register a free key" watermark shows instead of the map without one).
    # We avoid that dependency entirely: load standard, always-free
    # OpenStreetMap tiles, then apply a CSS color-inversion filter to the
    # tile layer only (not the markers/lines drawn on top), which fakes a
    # clean dark basemap with zero external API key required.
    fmap=folium.Map(location=[center_lat,center_lon],zoom_start=15,tiles="OpenStreetMap")
    fmap.get_root().html.add_child(folium.Element(
        "<style>.leaflet-tile-pane{filter:invert(92%) hue-rotate(180deg) brightness(94%) contrast(90%);}"
        ".leaflet-marker-pane,.leaflet-overlay-pane{filter:none;}</style>"
    ))
    cmap={"GREEN":"#25c77a","YELLOW":"#f1c40f","RED":"#e74c3c"}
    for u,v,d in net.graph.edges(data=True):
        p=[(net.graph.nodes[u]["lat"],net.graph.nodes[u]["lon"]),(net.graph.nodes[v]["lat"],net.graph.nodes[v]["lon"])]
        color="#111827" if d.get("closed") else cmap.get(d.get("level"),"#25c77a")
        folium.PolyLine(p,color=color,weight=7 if d.get("closed") else 5,opacity=.9,dash_array="8,8" if d.get("closed") else None,tooltip=f"{node_names[u]} → {node_names[v]} | {d.get('level')} | queue {d['queue_length']} | {d['avg_speed']:.1f} km/h").add_to(fmap)
    if emergency.active:
        pts=[(net.graph.nodes[n]["lat"],net.graph.nodes[n]["lon"]) for n in emergency.path]
        folium.PolyLine(pts,color="#00bfff",weight=10,opacity=.95,tooltip="🚑 GREEN CORRIDOR").add_to(fmap)
    for n,d in net.graph.nodes(data=True):
        phase=d.get("signal_phase","NS_GREEN");ic="blue" if emergency.active and n in emergency.path else ("green" if phase=="NS_GREEN" else "orange")
        folium.CircleMarker([d["lat"],d["lon"]],radius=9,popup=f"{d['name']} | {phase} | green {d.get('green_duration',30)}s",color=ic,fill=True,fill_color=ic).add_to(fmap)
    st_folium(fmap,width=None,height=560,key="qf_map")
    a,b,c=st.columns(3); a.metric("Intersections",len(net.graph.nodes)); b.metric("Road Segments",len(net.graph.edges)); c.metric("Active Events",len(active_events))
    if st.session_state.last_dispatch and st.session_state.last_dispatch.get("success"):
        ld=st.session_state.last_dispatch; st.info(f"🚑 Ambulance: {ld['normal_time_min']} min → {ld['emergency_time_min']} min | saved {ld['time_saved_min']} min")

# Intersections --------------------------------------------------------------
elif page == "Intersections":
    df=pd.DataFrame(edges)
    st.dataframe(df,use_container_width=True,hide_index=True)
    c1,c2=st.columns(2)
    with c1:
        chart=style_fig(px.bar(df,x=df.apply(lambda r:f"{r['from']}→{r['to']}",axis=1),y="queue_length",title="Queue Pressure"))
        chart.update_layout(paper_bgcolor="#080f1b",plot_bgcolor="#080f1b")
        st.plotly_chart(chart,use_container_width=True)
    with c2:
        st.markdown("**Current bottlenecks**")
        if bottlenecks:
            for b in bottlenecks: st.warning(f"🔴 {b['from']} → {b['to']} | {b['density']*100:.0f}% | queue {b['queue_length']}")
        else: st.success("No major bottleneck detected.")
    st.divider(); st.markdown("**Traffic Shock Detector**")
    if st.session_state.last_shocks:
        for s in st.session_state.last_shocks: st.warning(f"⚡ {s['from']} → {s['to']}: {s['direction']} {abs(s['change_pct']):.0f}%")
    else: st.caption("Advance the simulation to detect sudden traffic changes.")
    if net.history:
        h=pd.DataFrame(net.history)
        st.plotly_chart(style_fig(px.line(h,x="t",y=["total_vehicles","total_queue","avg_density"],title="Traffic Feedback Loop")),use_container_width=True)

# Quantum --------------------------------------------------------------------
elif page == "Quantum Optimization":
    qr=st.session_state.quantum_result
    if qr:
        st.success(f"Method: {qr['method']} | QUBO energy: {qr['energy']:.2f}")
        qdf=pd.DataFrame([{"Intersection":node_names[n],"Priority":p,"Green (s)":qr["green_durations"][n],"Reason":qr.get("reasons",{}).get(n,"")} for n,p in qr["priorities"].items()])
        st.dataframe(qdf,use_container_width=True,hide_index=True)
        st.caption(qr.get("objective","Queue/conflict optimization"))
        st.plotly_chart(style_fig(px.bar(qdf,x="Intersection",y="Green (s)",color="Priority",title="Optimized Green Durations")),use_container_width=True)
    else: st.info("Run **Optimize Signals** from the left control panel.")
    st.divider(); st.subheader("Strategy Comparison")
    comp=pd.DataFrame(comparison_table(steps=10,use_quantum=use_quantum)); st.dataframe(comp,use_container_width=True,hide_index=True)
    metric=st.selectbox("Compare metric",["waiting_time","queue_length","throughput","travel_time_min","fuel_liters","co2_kg"])
    st.plotly_chart(style_fig(px.bar(comp,x="strategy",y=metric,color="strategy",title=f"Strategy Comparison • {metric}")),use_container_width=True)
    if net.adaptive_memory: st.info(f"Adaptive signal memory: {len(net.adaptive_memory)} control records. Best observed queue improvement: {max(x['improvement'] for x in net.adaptive_memory):.1f} vehicles.")

# Emergency ------------------------------------------------------------------
elif page == "Emergency Corridor":
    e1,e2=st.columns(2)
    with e1:
        src=st.selectbox("Source",list(node_names),format_func=lambda x:node_names[x],key="page_ems_src")
        dst=st.selectbox("Hospital",list(node_names),format_func=lambda x:node_names[x],index=min(3,len(node_names)-1),key="page_ems_dst")
        c1,c2=st.columns(2)
        with c1:
            if st.button("🚑 Dispatch Ambulance",use_container_width=True,key="page_dispatch"):
                update_edge_weights(net.graph); st.session_state.last_dispatch=emergency.dispatch(net.graph,src,dst); st.rerun()
        with c2:
            if st.button("↻ Restore Normal Signals",use_container_width=True,key="page_restore"):
                emergency.clear(net.graph); st.session_state.last_dispatch=None; st.rerun()
    with e2:
        if emergency.active: st.success("🚑 GREEN CORRIDOR ACTIVE")
        else: st.info("No emergency corridor is active.")
        if st.session_state.last_dispatch:
            ld=st.session_state.last_dispatch
            if ld.get("success"):
                a,b,c=st.columns(3); a.metric("Normal",f"{ld['normal_time_min']:.1f} min"); b.metric("Emergency",f"{ld['emergency_time_min']:.1f} min"); c.metric("Time Saved",f"{ld['time_saved_min']:.1f} min")
                st.markdown(f"**Route:** {' → '.join(node_names.get(x,x) for x in ld.get('path',[]))}")
            else: st.warning(ld.get("message","Emergency route unavailable."))

# Predictive -----------------------------------------------------------------
elif page == "Predictive Analytics":
    st.write("Recent simulation history is used to estimate the next few steps and trigger proactive control.")
    if len(net.history)>=3:
        h=pd.DataFrame(net.history).tail(12); x=h["t"].to_numpy()
        import numpy as np
        def pred(col):
            y=h[col].to_numpy(); slope=np.polyfit(x,y,1)[0] if len(set(x))>1 else 0; return max(0,float(y[-1]+slope*3))
        pqueue=pred("total_queue"); pveh=pred("total_vehicles")
        a,b,c=st.columns(3); a.metric("Predicted queue (+3)",f"{pqueue:.0f}"); b.metric("Predicted vehicles",f"{pveh:.0f}"); c.metric("Trend","Rising" if pqueue>h['total_queue'].iloc[-1] else "Stable/Falling")
        st.plotly_chart(style_fig(px.line(h,x="t",y="total_queue",markers=True,title="Predictive Traffic Pulse")),use_container_width=True)
        if pqueue>h["total_queue"].iloc[-1]*1.15: st.warning("⚠ Predictive warning: queue pressure is trending upward. Proactive signal optimization is recommended.")
        else: st.success("✓ No strong near-term queue surge detected.")
    else: st.info("Advance the simulation at least 3 times to build the predictive signal.")

# What-if --------------------------------------------------------------------
elif page == "What-If Lab":
    lab=st.selectbox("Scenario",["Normal","Rush Hour","Heavy Rain","Accident","Road Closure","Stadium Surge","Pedestrian Surge"])
    lab_steps=st.slider("Simulation steps",4,20,10)
    if st.button("▶ Run Scenario Experiment",use_container_width=True,key="run_lab"):
        st.session_state.lab_result=scenario_comparison(lab,steps=lab_steps,use_quantum=use_quantum)
    if st.session_state.get("lab_result"):
        labdf=pd.DataFrame(st.session_state.lab_result); st.dataframe(labdf,use_container_width=True,hide_index=True)
        lm=st.selectbox("Scenario metric",["waiting_time","queue_length","throughput","fuel_liters","co2_kg"],key="lab_metric")
        st.plotly_chart(style_fig(px.bar(labdf,x="strategy",y=lm,color="strategy",title=f"{lab}: {lm}")),use_container_width=True)
    st.caption("Separate simulations compare Fixed, Classical Adaptive and QuantumFlow Hybrid under the selected scenario.")

# Environment ----------------------------------------------------------------
elif page == "Fuel & CO₂":
    e1,e2,e3,e4=st.columns(4); e1.metric("CO₂",f"{env['co2_kg']:.2f} kg"); e2.metric("Fuel",f"{env['fuel_liters']:.2f} L"); e3.metric("Queued",env['avg_wait_vehicles_queued']); e4.metric("Throughput",env['throughput'])
    st.markdown("**Traffic → Waiting → Fuel → CO₂**")
    if net.history:
        h=pd.DataFrame(net.history); h["estimated_co2"]=h["total_queue"]*.045+h["total_vehicles"]*.02
        st.plotly_chart(style_fig(px.area(h,x="t",y="estimated_co2",title="Estimated CO₂ Trend")),use_container_width=True)
    else: st.info("Advance the simulation to build the environmental trend.")

# Copilot --------------------------------------------------------------------
elif page == "Traffic Copilot":
    st.caption("Built-in offline Traffic Copilot — uses current simulation data locally; no external API is required.")
    persona=st.radio("Assistant",["Traffic Analyst","Optimization Advisor","Emergency Response Assistant","Smart City Report","Traffic Copilot"],horizontal=True)
    if st.button("✦ Generate Insight",use_container_width=True,key="generate_copilot"):
        if persona=="Traffic Analyst": out=ai.traffic_analyst(metrics,bottlenecks)
        elif persona=="Optimization Advisor": out=ai.optimization_advisor(st.session_state.quantum_result or {"method":"n/a","energy":0,"priorities":{},"green_durations":{}},metrics)
        elif persona=="Emergency Response Assistant": out=ai.emergency_response_assistant(emergency.status())
        elif persona=="Traffic Copilot": out=ai.copilot(metrics,bottlenecks,st.session_state.quantum_result,scenario)
        else: out=ai.smart_city_report(metrics,env,st.session_state.quantum_result or {})
        st.markdown(out)
    st.divider(); st.markdown("**Explainable control loop**")
    st.write("Detect → Predict → Optimize → Act → Measure → Adapt")
    if st.session_state.get("copilot_applied"): st.success("AI Copilot recommendation has been applied to the signal plan.")

st.divider();st.caption("QuantumFlow AI · Predictive + Explainable + Hybrid Quantum-Classical Traffic Optimization")


