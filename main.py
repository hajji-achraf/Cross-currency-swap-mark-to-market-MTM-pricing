import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="MTM CCS Pricer", page_icon="💱", layout="wide")

st.markdown("""
<style>
    /* titre principal */
    h1 { color: #1a1a2e; font-size: 1.8rem; font-weight: 700; }

    /* headers de section */
    h2 { color: #16213e; font-size: 1.2rem; font-weight: 600;
         border-bottom: 2px solid #e8e8e8; padding-bottom: 4px; }

    /* sous-headers */
    h3 { color: #0f3460; font-size: 1.0rem; font-weight: 600; }

    /* metrics */
    [data-testid="metric-container"] {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 6px;
        padding: 12px 16px;
    }
    [data-testid="metric-container"] label {
        font-size: 0.75rem !important;
        color: #6c757d !important;
        font-weight: 500 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        color: #1a1a2e !important;
    }

    /* tableaux */
    .stDataFrame { border: 1px solid #dee2e6; border-radius: 4px; }

    /* box info/warning personnalisées */
    .info-box {
        background: #f0f4ff;
        border-left: 4px solid #4361ee;
        padding: 10px 14px;
        border-radius: 0 4px 4px 0;
        font-size: 0.9rem;
        color: #1a1a2e;
        margin: 8px 0;
    }
    .formula-box {
        background: #fafafa;
        border: 1px solid #e0e0e0;
        border-radius: 6px;
        padding: 12px 16px;
        margin: 8px 0;
        font-size: 0.88rem;
        color: #333;
    }
    .result-ok {
        background: #f0faf4;
        border-left: 4px solid #2d6a4f;
        padding: 10px 14px;
        border-radius: 0 4px 4px 0;
        font-size: 0.9rem;
        color: #1a1a2e;
    }
    .section-label {
        font-size: 0.75rem;
        font-weight: 600;
        color: #6c757d;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-bottom: 6px;
    }
</style>
""", unsafe_allow_html=True)



def libor(DF, i, tau):
    return (DF[i - 1] / DF[i] - 1.0) / tau

def fwd_fx(spot, DF_FOR, DF_DOM, i):
    return spot * DF_FOR[i] / DF_DOM[i]

def psi_for(spot):
    return spot

def psi_dom(spot, DF_FOR, DF_DOM, i):
    return fwd_fx(spot, DF_FOR, DF_DOM, i) / spot




def coupons_for(N_FOR, spot, DF_FOR, DF_DOM, tau, n, spread):
    rows, total_pv, total_ann = [], 0.0, 0.0
    for i in range(1, n + 1):
        NxPsi = N_FOR * psi_for(spot)
        L     = libor(DF_FOR, i, tau)
        rate  = L + spread
        df    = DF_FOR[i]
        cpn   = NxPsi * rate * tau
        cpnPV = cpn * df
        ann_i = abs(NxPsi) * tau * df
        total_pv  += cpnPV
        total_ann += ann_i
        rows.append({
            "Période"           : i,
            "N × Ψ_FOR"         : round(NxPsi,  0),
            "L_FOR (%)"         : round(L * 100, 5),
            "Spread (%)"        : round(spread * 100, 5),
            "Taux effectif (%)": round(rate * 100, 5),
            "Coupon"            : round(cpn,   0),
            "DF_FOR"            : round(df,    6),
            "Coupon PV"         : round(cpnPV, 0),
            "Annuity"           : round(ann_i, 0),
        })
    return rows, total_pv, total_ann


def coupons_dom(N_DOM, spot, DF_FOR, DF_DOM, tau, n, spread=0.0):
    rows, total_pv, total_ann = [], 0.0, 0.0
    for i in range(1, n + 1):
        NxPsi = N_DOM * psi_dom(spot, DF_FOR, DF_DOM, i)
        L     = libor(DF_DOM, i, tau)
        rate  = L + spread
        df    = DF_DOM[i]
        cpn   = NxPsi * rate * tau
        cpnPV = cpn * df
        ann_i = abs(NxPsi) * tau * df
        total_pv  += cpnPV
        total_ann += ann_i
        rows.append({
            "Période"           : i,
            "N × Ψ_DOM"         : round(NxPsi,  0),
            "L_DOM (%)"         : round(L * 100, 5),
            "Spread (%)"        : round(spread * 100, 5),
            "Taux effectif (%)": round(rate * 100, 5),
            "Coupon"            : round(cpn,   0),
            "DF_DOM"            : round(df,    6),
            "Coupon PV"         : round(cpnPV, 0),
            "Annuity"           : round(ann_i, 0),
        })
    return rows, total_pv, total_ann


# ═════════════════════════════════════════════════════════════
#  ÉCHANGES
# ═════════════════════════════════════════════════════════════

def exchanges_for(N_FOR, spot, DF_FOR, n):
    psi   = psi_for(spot)
    e_t0  = -N_FOR * psi
    pv_t0 =  e_t0  * DF_FOR[0]
    e_tm  =  N_FOR * psi
    pv_tm =  e_tm  * DF_FOR[n]

    rows = [{"t": 0,
             "Montant": round(e_t0, 0),
             "DF_FOR": round(DF_FOR[0], 6),
             "PV": round(pv_t0, 0)}]

    for i in range(1, n):
        rows.append({"t": i,
                     "Montant": 0,
                     "DF_FOR": round(DF_FOR[i], 6),
                     "PV": 0})

    rows.append({"t": n,
                 "Montant": round(e_tm, 0),
                 "DF_FOR": round(DF_FOR[n], 6),
                 "PV": round(pv_tm, 0)})

    return rows, pv_t0 + pv_tm


def exchanges_dom(N_DOM, spot, DF_FOR, DF_DOM, n):
    e_t0  = -N_DOM * 1.0
    pv_t0 =  e_t0  * DF_DOM[0]
    psi_n = psi_dom(spot, DF_FOR, DF_DOM, n)
    e_tm  =  N_DOM * psi_n
    pv_tm =  e_tm  * DF_DOM[n]

    rows = [{"t": 0,
             "Montant": round(e_t0, 0),
             "DF_DOM": round(DF_DOM[0], 6),
             "PV": round(pv_t0, 0)}]

    for i in range(1, n):
        rows.append({"t": i,
                     "Montant": 0,
                     "DF_DOM": round(DF_DOM[i], 6),
                     "PV": 0})

    rows.append({"t": n,
                 "Montant": round(e_tm, 0),
                 "DF_DOM": round(DF_DOM[n], 6),
                 "PV": round(pv_tm, 0)})

    return rows, pv_t0 + pv_tm


# ═════════════════════════════════════════════════════════════
#  RESETS
# ═════════════════════════════════════════════════════════════

def resets_dom(N_DOM, spot, DF_FOR, DF_DOM, n):
    rows = [{"t": 0,
             "Ψ_DOM"  : round(psi_dom(spot, DF_FOR, DF_DOM, 0), 5),
             "Reset"  : 0,
             "DF_DOM" : round(DF_DOM[0], 6),
             "PV"     : 0,
             "Note"   : "pas de reset à t0"}]
    total_pv = 0.0
    for j in range(1, n):
        psi_j  = psi_dom(spot, DF_FOR, DF_DOM, j)
        psi_j1 = psi_dom(spot, DF_FOR, DF_DOM, j + 1)
        reset  = N_DOM * (psi_j - psi_j1)
        pv     = reset * DF_DOM[j]
        total_pv += pv
        rows.append({"t": j,
                     "Ψ_DOM" : round(psi_j, 5),
                     "Reset" : round(reset, 0),
                     "DF_DOM": round(DF_DOM[j], 6),
                     "PV"    : round(pv, 0),
                     "Note"  : "Paie (EUR hausse)" if reset < 0 else "Reçoit (EUR baisse)"})
    rows.append({"t": n,
                 "Ψ_DOM" : round(psi_dom(spot, DF_FOR, DF_DOM, n), 5),
                 "Reset" : 0,
                 "DF_DOM": round(DF_DOM[n], 6),
                 "PV"    : 0,
                 "Note"  : "dans l'échange final"})
    return rows, total_pv


# ═════════════════════════════════════════════════════════════
#  ANNUITÉ & SWAP NPV
# ═════════════════════════════════════════════════════════════

def annuity(N_FOR, spot, DF_FOR, tau, n):
    return sum(abs(N_FOR * psi_for(spot)) * tau * DF_FOR[i] for i in range(1, n + 1))

def swap_npv_fn(N_FOR, N_DOM, spot, DF_FOR, DF_DOM, tau, n, spread_for):
    _, pv_c_for, _ = coupons_for(N_FOR, spot, DF_FOR, DF_DOM, tau, n, spread_for)
    _, pv_e_for    = exchanges_for(N_FOR, spot, DF_FOR, n)
    _, pv_c_dom, _ = coupons_dom(N_DOM, spot, DF_FOR, DF_DOM, tau, n, 0.0)
    _, pv_e_dom    = exchanges_dom(N_DOM, spot, DF_FOR, DF_DOM, n)
    _, pv_r_dom    = resets_dom(N_DOM, spot, DF_FOR, DF_DOM, n)
    pv_FOR = pv_c_for + pv_e_for
    pv_DOM = pv_c_dom + pv_e_dom + pv_r_dom
    return pv_FOR - pv_DOM

def par_spread_fn(N_FOR, N_DOM, spot, DF_FOR, DF_DOM, tau, n):
    npv_zero = swap_npv_fn(N_FOR, N_DOM, spot, DF_FOR, DF_DOM, tau, n, 0.0)
    ann      = annuity(N_FOR, spot, DF_FOR, tau, n)
    return npv_zero, ann, -npv_zero / ann


# ═════════════════════════════════════════════════════════════
#  SENSIBILITÉS
# ═════════════════════════════════════════════════════════════

def dv01_fn(N_FOR, N_DOM, spot, DF_FOR, DF_DOM, tau, n, ps):
    bump     = 0.0001
    DF_DOM_b = [DF_DOM[i] * np.exp(-bump * i * tau) for i in range(n + 1)]
    DF_FOR_b = [DF_FOR[i] * np.exp(-bump * i * tau) for i in range(n + 1)]
    npv_base = swap_npv_fn(N_FOR, N_DOM, spot, DF_FOR,   DF_DOM,   tau, n, ps)
    npv_bump = swap_npv_fn(N_FOR, N_DOM, spot, DF_FOR_b, DF_DOM_b, tau, n, ps)
    return npv_bump - npv_base

def fx_delta_fn(N_FOR, N_DOM, spot, DF_FOR, DF_DOM, tau, n, ps):
    spot_b  = spot * 1.01
    N_FOR_b = -N_DOM / spot_b
    npv_base = swap_npv_fn(N_FOR,   N_DOM, spot,   DF_FOR, DF_DOM, tau, n, ps)
    npv_bump = swap_npv_fn(N_FOR_b, N_DOM, spot_b, DF_FOR, DF_DOM, tau, n, ps)
    return npv_bump - npv_base


# ═════════════════════════════════════════════════════════════
#  SIDEBAR
# ═════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("### Paramètres du Swap")

    spot  = st.number_input("Spot FX  (EUR / USD)",
                             value=1.1403, step=0.0001, format="%.5f")
    N_DOM = st.number_input("Notionnel DOM  (USD)",
                             value=1_000_000, step=100_000, format="%d")
    n     = st.slider("Nombre de périodes", 2, 12, 4)
    freq  = st.selectbox("Fréquence",
                          ["Trimestriel (τ = 0.2528)",
                           "Semestriel  (τ = 0.5)",
                           "Annuel      (τ = 1.0)"])
    tau   = {"Trimestriel (τ = 0.2528)": 0.2528,
             "Semestriel  (τ = 0.5)"   : 0.50,
             "Annuel      (τ = 1.0)"   : 1.00}[freq]

    st.markdown("---")
    st.markdown("**Courbe zéro coupon — DOM (USD)**")
    st.caption("DF_DOM(t = 0) = 1  (fixe)")
    defaults_dom = [0.994180, 0.988041, 0.981419, 0.974803,
                    0.968237, 0.961720, 0.955252, 0.948832,
                    0.942460, 0.936136, 0.929859, 0.923629]
    DF_DOM = [1.0]
    for i in range(1, n + 1):
        DF_DOM.append(st.number_input(f"DF_DOM ( t{i} )", value=defaults_dom[i-1],
                                       step=0.0001, format="%.6f", key=f"dom_{i}"))

    st.markdown("---")
    st.markdown("**Courbe zéro coupon — FOR (EUR)**")
    st.caption("DF_FOR(t = 0) = 1  (fixe)")
    defaults_for = [1.002365, 1.004182, 1.005926, 1.007807,
                    1.009625, 1.011380, 1.013072, 1.014701,
                    1.016267, 1.017770, 1.019210, 1.020587]
    DF_FOR = [1.0]
    for i in range(1, n + 1):
        DF_FOR.append(st.number_input(f"DF_FOR ( t{i} )", value=defaults_for[i-1],
                                       step=0.0001, format="%.6f", key=f"for_{i}"))

N_FOR = -N_DOM / spot


# ─────────────────────────────────────────────────────────────
#  CALCULS CENTRAUX
# ─────────────────────────────────────────────────────────────

rows_cf_0, pv_c_for_0, ann_for = coupons_for(N_FOR, spot, DF_FOR, DF_DOM, tau, n, 0.0)
rows_cd_0, pv_c_dom_0, ann_dom = coupons_dom(N_DOM, spot, DF_FOR, DF_DOM, tau, n, 0.0)

rows_ef, pv_e_for = exchanges_for(N_FOR, spot, DF_FOR, n)
rows_ed, pv_e_dom = exchanges_dom(N_DOM, spot, DF_FOR, DF_DOM, n)
rows_rd, pv_r_dom = resets_dom(N_DOM, spot, DF_FOR, DF_DOM, n)

pv_FOR_0 = pv_c_for_0 + pv_e_for
pv_DOM_0 = pv_c_dom_0 + pv_e_dom + pv_r_dom
npv_0    = pv_FOR_0 - pv_DOM_0

npv_zero, ann, ps = par_spread_fn(N_FOR, N_DOM, spot, DF_FOR, DF_DOM, tau, n)

rows_cf_ps, pv_c_for_ps, _ = coupons_for(N_FOR, spot, DF_FOR, DF_DOM, tau, n, ps)
pv_FOR_ps = pv_c_for_ps + pv_e_for
npv_ps    = pv_FOR_ps - pv_DOM_0

dv01_val = dv01_fn(N_FOR, N_DOM, spot, DF_FOR, DF_DOM, tau, n, ps)
fxd_val  = fx_delta_fn(N_FOR, N_DOM, spot, DF_FOR, DF_DOM, tau, n, ps)


# ═════════════════════════════════════════════════════════════
#  PAGE PRINCIPALE
# ═══════════════════════════════════════════════════════════��═

# ─────────────────────────────────────────────────────────────
# À METTRE JUSTE APRÈS le st.title(...) et AVANT st.divider()
# ─────────────────────────────────────────────────────────────

st.title("MTM Cross-Currency Swap — Pricer et Sensibilités")

st.markdown("""
<div class="formula-box">
<strong>Définition (Cross Currency Swap / CCS)</strong><br>
Un <strong>cross currency swap</strong> est un contrat dans lequel deux contreparties
<strong>échangent des flux de trésorerie dans deux devises différentes</strong>.<br><br>

&bull; un <strong>échange initial</strong> de notionnels ,<br>
&bull; des <strong>coupons</strong> payés/reçus sur chaque devise (souvent à taux flottant),<br>
&bull; un <strong>échange final</strong> de notionnels (retour des notionnels),<br>
&bull; dans un CCS <strong>MTM</strong>, des <strong>resets</strong> peuvent ajuster le notionnel de la jambe “reset”
pour réduire le risque de change sur le notionnel.
</div>
""", unsafe_allow_html=True)

# Image explicative des échanges de flux
# 1) Mets un fichier image dans ton projet, par ex : assets/ccs_flows.png
# 2) Streamlit l'affichera avec la ligne ci-dessous
st.image(
    "CCS.png",
    width=500, 
    
    
)

st.divider()


# ─────────────────────────────────────────────────────────────
# 0. PARAMÈTRES
# ─────────────────────────────────────────────────────────────
st.header("0  —  Paramètres du Swap")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Spot EUR/USD", f"{spot:.5f}")
c2.metric("Notionnel DOM (USD)", f"${N_DOM:,.0f}")
c4.metric("Périodes  /  Tau", f"{n}  /  {tau}")
c5.metric("MTM Reset", "Activé")


st.divider()


# ─────────────────────────────────────────────────────────────
# 1. COURBES ZÉRO COUPON
# ─────────────────────────────────────────────────────────────
st.header("1  —  Courbes Zéro Coupon  (Input)")

st.markdown("""
<div class="formula-box">
<strong>DF(t)</strong> = prix aujourd'hui d'un flux de 1 $ reçu à la date t<br>
&bull; DF_DOM &lt; 1  →  taux USD <strong>positifs</strong><br>
&bull; DF_FOR &ge; 1  →  taux EUR <strong>négatifs</strong> 
</div>
""", unsafe_allow_html=True)

df_curves = pd.DataFrame({
    "t"            : list(range(n + 1)),
    "DF_DOM (USD)" : DF_DOM,
    "DF_FOR (EUR)" : DF_FOR,
})
st.dataframe(
    df_curves.style.format({"DF_DOM (USD)": "{:.6f}", "DF_FOR (EUR)": "{:.6f}"}),
    use_container_width=True,
)
st.divider()


# ─────────────────────────────────────────────────────────────
# 2. TAUX FORWARD
# ─────────────────────────────────────────────────────────────
st.header("2  —  Taux Forward")

st.latex(r"L(t_i) = \frac{DF(t_{i-1})\;/\;DF(t_i)\;-\;1}{\tau}")

rows_fwd = []
for i in range(1, n + 1):
    Ld = libor(DF_DOM, i, tau)
    Lf = libor(DF_FOR, i, tau)
    rows_fwd.append({
        "Période" : i,
        "L_DOM (%)" : round(Ld * 100, 5),
        "L_FOR (%)" : round(Lf * 100, 5),
    })

with st.expander("Voir le détail des calculs"):
    for i in range(1, n + 1):
        Ld = libor(DF_DOM, i, tau)
        Lf = libor(DF_FOR, i, tau)
        st.code(
            f"t{i}  L_DOM = ({DF_DOM[i-1]:.6f} / {DF_DOM[i]:.6f} - 1) / {tau} = {Ld*100:.5f} %\n"
            f"t{i}  L_FOR = ({DF_FOR[i-1]:.6f} / {DF_FOR[i]:.6f} - 1) / {tau} = {Lf*100:.5f} %"
        )

st.dataframe(
    pd.DataFrame(rows_fwd).style.format({"L_DOM (%)": "{:.5f}", "L_FOR (%)": "{:.5f}"}),
    use_container_width=True,
)
st.divider()


# ─────────────────────────────────────────────────────────────
# 3. FORWARD FX
# ─────────────────────────────────────────────────────────────
st.header("3  —  Forward FX")

st.latex(
    r"F(t_i) = \text{Spot} \times "
    r"\frac{DF_{\text{FOR}}(t_i)}{DF_{\text{DOM}}(t_i)}"
)

st.markdown("""
<div class="formula-box">
Le Forward FX est entièrement déterminé par le Spot et les deux courbes
.<br>
&bull; DF_FOR &gt; DF_DOM  →  F &gt; Spot  →  EUR s'apprécie dans le futur<br>
&bull; DF_FOR &lt; DF_DOM  →  F &lt; Spot  →  EUR se déprécie
</div>
""", unsafe_allow_html=True)

rows_ffx = []
for i in range(1, n + 1):
    F = fwd_fx(spot, DF_FOR, DF_DOM, i)
    rows_ffx.append({
        "Période"   : i,
        "DF_FOR"    : round(DF_FOR[i], 6),
        "DF_DOM"    : round(DF_DOM[i], 6),
        "Forward FX": round(F, 6),
    })

with st.expander("Voir le détail des calculs"):
    for r in rows_ffx:
        i = r["Période"]
        st.code(
            f"t{i}  F = {spot:.5f} × {DF_FOR[i]:.6f} / {DF_DOM[i]:.6f}"
            f" = {r['Forward FX']:.6f}"
        )

st.dataframe(
    pd.DataFrame(rows_ffx).style.format(
        {"DF_FOR": "{:.6f}", "DF_DOM": "{:.6f}", "Forward FX": "{:.6f}"}),
    use_container_width=True,
)
st.divider()


# ─────────────────────────────────────────────────────────────
# 4. FACTEUR PSI
# ─────────────────────────────────────────────────────────────
st.header("4  —  Facteur d'Ajustement  Ψ = α × β")


# ─────────────────────────────────────────────────────────────
# Ajout "formules comme sur l'image" (dans la section 4)
# ─────────────────────────────────────────────────────────────





st.latex(r"N_i = N_0 \psi_i")

st.markdown("**Notional Reset Factor**")
st.latex(
    r"\psi_i = \underbrace{\alpha(t_0, C^{leg})}_{\text{Valuation Adj}}"
    r"\underbrace{\beta(t_i, C^{leg})}_{\text{FX Reset Adj}}"
)

st.markdown("**Spot FX Valuation Adjustment, $\\alpha$**")
st.latex(
    r"""\alpha(t, C^{leg}) =
\begin{cases}
1, & \text{if } C^{leg} = C^{val} \\
s^{FOR/DOM}, & \text{if } C^{leg} \ne C^{val} \text{ and } C^{leg} = C^{FOR} \\
s^{DOM/FOR}, & \text{if } C^{leg} \ne C^{val} \text{ and } C^{leg} = C^{DOM}
\end{cases}"""
)

st.markdown("**Forward FX MtM Reset Adjustment, $\\beta$**")
st.latex(
    r"""\beta(t, C^{leg}) =
\begin{cases}
1, & \text{if } C^{leg} \ne C^{reset} \\
\dfrac{f(t)^{FOR/DOM}}{s^{FOR/DOM}}, & \text{if } C^{leg} = C^{reset} \text{ and } C^{leg} = C^{FOR} \\
\dfrac{f(t)^{DOM/FOR}}{s^{DOM/FOR}}, & \text{if } C^{leg} = C^{reset} \text{ and } C^{leg} = C^{DOM}
\end{cases}"""
)


c1, c2 = st.columns(2)
with c1:
    st.markdown("**Jambe FOR (EUR)**")
    st.latex(
        r"\Psi_{\text{FOR}} = \underbrace{\text{Spot}}_{\alpha}"
        r"\times \underbrace{1}_{\beta} = \text{Spot} = " + f"{spot:.5f}"
    )
    st.markdown("""
    <div class="formula-box">
    &alpha; = Spot  (EUR n'est pas la devise de valorisation)<br>
    &beta; = 1  car  EUR &ne; C<sup>Reset</sup><br>
    <strong>Ψ_FOR est constant</strong> — le notionnel EUR ne change pas
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown("**Jambe DOM (USD)**")
    st.latex(
        r"\Psi_{\text{DOM}}(t_i) = \underbrace{1}_{\alpha}"
        r"\times \underbrace{\dfrac{F(t_i)}{\text{Spot}}}_{\beta}"
        r"= \frac{F(t_i)}{\text{Spot}}"
    )
    st.markdown("""
    <div class="formula-box">
    &alpha; = 1  (USD = devise de valorisation)<br>
    &beta; = F(t<sub>i</sub>)/Spot  car  USD = C<sup>Reset</sup><br>
    <strong>Ψ_DOM varie</strong> — le notionnel USD suit le Forward FX
    </div>
    """, unsafe_allow_html=True)

rows_psi = [{
    "Période"        : i,
    "Ψ_FOR (cst)"    : round(psi_for(spot), 5),
    "Ψ_DOM (ti)"     : round(psi_dom(spot, DF_FOR, DF_DOM, i), 5),
} for i in range(1, n + 1)]

st.dataframe(pd.DataFrame(rows_psi), use_container_width=True)
st.divider()


# ─────────────────────────────────────────────────────────────
# 5. COUPONS  (spread = 0)
# ─────────────────────────────────────────────────────────────
st.header("5  —  Coupons  (spread = 0 sur les deux jambes)")

st.latex(
    r"\text{Coupon}(t_i) = N \times \Psi \times "
    r"\underbrace{(L + s)}_{s\,=\,0} \times \tau"
    r"\qquad"
    r"\text{Coupon PV}(t_i) = \text{Coupon}(t_i) \times DF(t_i)"
)

st.markdown("""
<div class="info-box">
On commence avec <strong>spread = 0</strong> sur les deux jambes.
Le déséquilibre obtenu permettra de calculer le Par Spread à l'étape suivante.
</div>
""", unsafe_allow_html=True)

c1, c2 = st.columns(2)
with c1:
    st.markdown("**Jambe FOR (EUR)  —  vous payez  —  spread = 0**")
    st.dataframe(pd.DataFrame(rows_cf_0), use_container_width=True)
    ca, cb = st.columns(2)
    ca.metric("Total Coupon PV", f"${pv_c_for_0:,.0f}")
    cb.metric("Annuity", f"${ann_for:,.0f}")

with c2:
    st.markdown("**Jambe DOM (USD)  —  vous recevez  —  spread = 0**")
    st.dataframe(pd.DataFrame(rows_cd_0), use_container_width=True)
    ca, cb = st.columns(2)
    ca.metric("Total Coupon PV", f"${pv_c_dom_0:,.0f}")
    cb.metric("Annuity", f"${ann_dom:,.0f}")

st.divider()


# ─────────────────────────────────────────────────────────────
# 6. ÉCHANGES DE NOTIONNEL
# ─────────────────────────────────────────────────────────────
st.header("6  —  Échanges de Notionnel")


c1, c2 = st.columns(2)
with c1:
    st.markdown("**Jambe FOR (EUR)**")
    st.dataframe(pd.DataFrame(rows_ef), use_container_width=True)
    st.metric("Total PV Échanges FOR", f"${pv_e_for:,.0f}")

with c2:
    st.markdown("**Jambe DOM (USD)**")
    st.dataframe(pd.DataFrame(rows_ed), use_container_width=True)
    st.metric("Total PV Échanges DOM", f"${pv_e_dom:,.0f}")

st.divider()


# ─────────────────────────────────────────────────────────────
# 7. RESETS MtM
# ────────────────────────────────────────���────────────────────
st.header("7  —  Resets MtM")

st.latex(
    r"\text{Reset}(t_j) = N_{\text{DOM}} \times "
    r"\bigl(\Psi_{\text{DOM}}(t_j) - \Psi_{\text{DOM}}(t_{j+1})\bigr) "
    r"\times DF_{\text{DOM}}(t_j) \qquad j = 1, \ldots, n-1"
)

st.markdown("""
<div class="formula-box">
<strong>Rôle :</strong> compenser la variation du Forward FX sur le notionnel entre deux périodes.<br>
&bull; EUR hausse  →  Ψ(t<sub>j+1</sub>) &gt; Ψ(t<sub>j</sub>)  →  Reset &lt; 0  →  vous <strong>payez</strong><br>
&bull; EUR baisse  →  Ψ(t<sub>j+1</sub>) &lt; Ψ(t<sub>j</sub>)  →  Reset &gt; 0  →  vous <strong>recevez</strong><br>
&bull; t<sub>0</sub> et t<sub>m</sub> : aucun reset (t<sub>0</sub> = pas encore de période / t<sub>m</sub> = dans l'échange final)
</div>
""", unsafe_allow_html=True)

c1, c2 = st.columns(2)
with c1:
    st.markdown("**Jambe FOR (EUR)  —  Resets = 0**")
    st.caption("EUR ≠ C Reset  →  Ind(CReset) = 0  →  aucun reset")
    st.dataframe(
        pd.DataFrame([{"t": i, "Reset": 0, "PV": 0} for i in range(n + 1)]),
        use_container_width=True,
    )
    st.metric("Total PV Resets FOR", "$0")

with c2:
    st.markdown("**Jambe DOM (USD)  —  USD = C Reset**")
    st.dataframe(pd.DataFrame(rows_rd), use_container_width=True)
    st.metric("Total PV Resets DOM", f"${pv_r_dom:,.0f}")

st.divider()


# ─────────────────────────────────────────────────────────────
# 8. SWAP NPV + PAR SPREAD
# ─────────────────────────────────────────────────────────────
st.header("8  —  Swap NPV et Par Spread")

# ── 8a : NPV à spread = 0 ────────────────────────────────────
st.markdown("#### 8a  —  Swap NPV avec spread = 0")
st.latex(r"\text{Swap NPV}(s=0) = PV(\text{FOR}) - PV(\text{DOM})")

c1, c2, c3 = st.columns(3)
c1.metric("Leg FOR  (s = 0)", f"${pv_FOR_0:,.0f}")
c2.metric("Leg DOM  (s = 0)", f"${pv_DOM_0:,.0f}")
c3.metric("Swap NPV  (s = 0)", f"${npv_0:,.0f}")



st.divider()

# ── 8b : calcul du Par Spread ─────────────────────────────────
st.markdown("#### 8b  —  Calcul du Par Spread")
st.latex(
    r"s^* = \frac{-\;\text{Swap NPV}(s=0)}{\text{Annuity}}"
)

st.markdown(f"""
<div class="formula-box">
Annuity &nbsp;=&nbsp; <strong>${ann:,.2f}</strong><br><br>
Swap NPV (s=0) &nbsp;=&nbsp; <strong>${npv_0:,.2f}</strong><br><br>
s* &nbsp;=&nbsp; &minus;({npv_0:,.2f}) / {ann:,.2f}
&nbsp;=&nbsp; <strong>{ps*10000:.4f} bp</strong>
</div>
""", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
c1.metric("Swap NPV (s = 0)", f"${npv_0:,.0f}")
c2.metric("Annuity", f"${ann:,.0f}")
c3.metric("Par Spread", f"{ps*10000:.4f} bp")

st.divider()


st.divider()


# ─────────────────────────────────────────────────────────────
# 9. SENSIBILITÉS
# ────────────��────────────────────────────────────────────────
st.header("9  —  Sensibilités")

c1, c2 = st.columns(2)

with c1:
    st.markdown("#### DV01  —  Sensibilité aux taux d'intérêt")
    st.latex(
        r"\text{DV01} = "
        r"\text{Swap NPV}\!\bigl(DF \cdot e^{-0.0001\,i\,\tau}\bigr)"
        r"- \text{Swap NPV}(\text{base})"
    )
    st.markdown("""
    <div class="formula-box">
    On augmente tous les taux de <strong>+1 bp</strong> en appliquant
    DF_bumpé(i) = DF(i) &times; exp(&minus;0.0001 &times; i &times; &tau;)
    sur les deux courbes simultanément.<br>
    </div>
    """, unsafe_allow_html=True)
    st.metric("DV01  (taux + 1 bp)", f"${dv01_val:,.2f}")

    with st.expander("Détail du calcul"):
        bump     = 0.0001
        DF_DOM_b = [DF_DOM[i] * np.exp(-bump * i * tau) for i in range(n + 1)]
        DF_FOR_b = [DF_FOR[i] * np.exp(-bump * i * tau) for i in range(n + 1)]
        nb  = swap_npv_fn(N_FOR, N_DOM, spot, DF_FOR_b, DF_DOM_b, tau, n, ps)
        nb0 = swap_npv_fn(N_FOR, N_DOM, spot, DF_FOR,   DF_DOM,   tau, n, ps)
        st.code(
            f"Swap NPV base    = ${nb0:,.2f}\n"
            f"Swap NPV bumpé   = ${nb:,.2f}\n"
            f"DV01             = ${nb - nb0:,.2f}"
        )

with c2:
    st.markdown("#### FX Delta  —  Sensibilité au Spot EUR/USD")
    st.latex(
        r"\text{FX Delta} = "
        r"\text{Swap NPV}(\text{Spot} \times 1.01)"
        r"- \text{Swap NPV}(\text{base})"
    )
    st.markdown("""
    <div class="formula-box">
    On augmente le Spot de <strong>+1 %</strong>.<br>
    </div>
    """, unsafe_allow_html=True)
    st.metric("FX Delta  (spot + 1 %)", f"${fxd_val:,.2f}")

    with st.expander("Détail du calcul"):
        spot_b  = spot * 1.01
        N_FOR_b = -N_DOM / spot_b
        nb  = swap_npv_fn(N_FOR_b, N_DOM, spot_b, DF_FOR, DF_DOM, tau, n, ps)
        nb0 = swap_npv_fn(N_FOR,   N_DOM, spot,   DF_FOR, DF_DOM, tau, n, ps)
        st.code(
            f"Spot base        = {spot:.5f}\n"
            f"Spot bumpé       = {spot_b:.5f}\n"
            f"Swap NPV base    = ${nb0:,.2f}\n"
            f"Swap NPV bumpé   = ${nb:,.2f}\n"
            f"FX Delta         = ${nb - nb0:,.2f}"
        )

st.divider()


# ─────────────────────────────────────────────────────────────
# RÉCAPITULATIF
# ──────────────────────────────────────────────────────────��──
st.header("Récapitulatif")

recap = pd.DataFrame({
    "Composante": [
        "Coupon PV — FOR  (s = 0)",
        "Échanges PV — FOR",
        "Leg FOR NPV  (s = 0)",
        "Coupon PV — DOM  (s = 0)",
        "Échanges PV — DOM",
        "Resets PV — DOM",
        "Leg DOM NPV",
        "Swap NPV  (s = 0)",
        "Annuity",
        "Par Spread  (bp)",
        "DV01  (taux + 1 bp)",
        "FX Delta  (spot + 1 %)",
    ],
    "Valeur": [
        pv_c_for_0, pv_e_for, pv_FOR_0,
        pv_c_dom_0, pv_e_dom, pv_r_dom, pv_DOM_0,
        npv_0,
        ann,
        ps * 10000,
        dv01_val,
        fxd_val,
    ],
})

def _color(v):
    return "color: #2d6a4f; font-weight:600" if v >= 0 \
           else "color: #c62828; font-weight:600"

st.dataframe(
    recap.style
    .map(_color, subset=["Valeur"])
    .format({"Valeur": "{:,.2f}"}),
    use_container_width=True,
)

