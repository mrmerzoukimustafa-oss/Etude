import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import math
from datetime import datetime

# Constantes électriques
RHO_CUIVRE = 0.0175      # Ω·mm²/m
RHO_ALUMINIUM = 0.028    # Ω·mm²/m
SECTIONS_NORMALISEES = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240]

# Configuration de la page
st.set_page_config(page_title="ÉLECTRO CALC PRO", layout="wide")
st.title("⚡ ÉLECTRO CALC PRO")
st.markdown("Outils professionnels pour études de réseaux électriques")

# Création des onglets
tab1, tab2 = st.tabs(["📊 Calculs électriques", "📍 Plan de poteaux"])

# ==================== ONGLET 1 : CALCULS ÉLECTRIQUES ====================
with tab1:
    st.header("Calculs électriques selon NFC 15-100")

    # Sous-onglets pour organiser les différents calculs
    calc_tab1, calc_tab2, calc_tab3, calc_tab4, calc_tab5 = st.tabs(
        ["📏 Section de câble", "📉 Chute de tension", "⚡ Puissance", "🔌 Courant", "🔧 Résistance ligne"]
    )

    # Section de câble
    with calc_tab1:
        st.subheader("Section minimale de câble")
        col1, col2 = st.columns(2)
        with col1:
            P = st.number_input("Puissance (W)", value=2000, step=100, key="P_cable")
            V = st.number_input("Tension (V)", value=220, step=10, key="V_cable")
            L = st.number_input("Longueur (m)", value=50, step=5, key="L_cable")
        with col2:
            chute_max = st.number_input("Chute max (%)", value=3.0, step=0.5, key="chute_cable")
            cos_phi = st.number_input("Cos φ", value=0.9, step=0.01, key="cos_cable")
            materiau = st.selectbox("Matériau", ["Cuivre", "Aluminium"], key="mat_cable")

        if st.button("Calculer la section", key="btn_cable"):
            if P > 0 and V > 0 and L > 0:
                I = P / (V * cos_phi)
                rho = RHO_ALUMINIUM if materiau == "Aluminium" else RHO_CUIVRE
                S_calc = (2 * rho * L * I) / ((chute_max / 100) * V)
                section_choisie = next((s for s in SECTIONS_NORMALISEES if s >= S_calc), 240)
                courant_admissible = section_choisie * 6
                status = "✅ OK" if courant_admissible >= I else "⚠️ Courant élevé – vérifier"
                st.success(f"**Section minimale :** {section_choisie} mm²")
                st.write(f"Courant nominal : {I:.1f} A")
                st.write(f"Courant admissible (approximatif) : {courant_admissible:.0f} A")
                st.write(f"**{status}**")
            else:
                st.error("Veuillez saisir des valeurs positives.")

    # Chute de tension
    with calc_tab2:
        st.subheader("Chute de tension")
        col1, col2 = st.columns(2)
        with col1:
            I = st.number_input("Courant (A)", value=10.0, step=1.0, key="I_chute")
            L = st.number_input("Longueur (m)", value=100, step=10, key="L_chute")
            S = st.number_input("Section (mm²)", value=2.5, step=0.5, key="S_chute")
        with col2:
            V = st.number_input("Tension (V)", value=220, step=10, key="V_chute")
            materiau = st.selectbox("Matériau", ["Cuivre", "Aluminium"], key="mat_chute")

        if st.button("Calculer la chute", key="btn_chute"):
            if I > 0 and L > 0 and S > 0 and V > 0:
                rho = RHO_ALUMINIUM if materiau == "Aluminium" else RHO_CUIVRE
                delta_V = (2 * rho * L * I) / S
                chute_pourcent = (delta_V / V) * 100
                if chute_pourcent <= 3:
                    eval_text = "✅ Conforme éclairage"
                elif chute_pourcent <= 5:
                    eval_text = "✅ Conforme autres usages"
                elif chute_pourcent <= 8:
                    eval_text = "⚠️ Limite – vérifier"
                else:
                    eval_text = "❌ Non conforme – augmenter section"
                st.success(f"**Chute de tension :** {chute_pourcent:.2f}% ({delta_V:.1f} V)")
                st.write(eval_text)
            else:
                st.error("Valeurs invalides.")

    # Puissance
    with calc_tab3:
        st.subheader("Calcul de puissance (active, apparente, réactive)")
        col1, col2 = st.columns(2)
        with col1:
            V = st.number_input("Tension (V)", value=220, step=10, key="V_puiss")
            I = st.number_input("Courant (A)", value=10.0, step=1.0, key="I_puiss")
        with col2:
            cos_phi = st.number_input("Cos φ", value=0.9, step=0.01, key="cos_puiss")

        if st.button("Calculer", key="btn_puiss"):
            if V > 0 and I > 0:
                P = V * I * cos_phi
                S = V * I
                Q = math.sqrt(S**2 - P**2) if S > P else 0
                st.success(f"**Puissance active P :** {P:.0f} W")
                st.write(f"**Puissance apparente S :** {S:.0f} VA")
                st.write(f"**Puissance réactive Q :** {Q:.0f} VAR")
            else:
                st.error("Valeurs invalides.")

    # Courant
    with calc_tab4:
        st.subheader("Calcul du courant (monophasé)")
        col1, col2 = st.columns(2)
        with col1:
            P = st.number_input("Puissance (W)", value=2000, step=100, key="P_courant")
        with col2:
            V = st.number_input("Tension (V)", value=220, step=10, key="V_courant")

        if st.button("Calculer", key="btn_courant"):
            if P > 0 and V > 0:
                I = P / V
                st.success(f"**Courant :** {I:.2f} A")
            else:
                st.error("Valeurs invalides.")

    # Résistance ligne
    with calc_tab5:
        st.subheader("Résistance d'une ligne")
        col1, col2 = st.columns(2)
        with col1:
            L = st.number_input("Longueur (m)", value=100, step=10, key="L_res")
            S = st.number_input("Section (mm²)", value=2.5, step=0.5, key="S_res")
        with col2:
            materiau = st.selectbox("Matériau", ["Cuivre", "Aluminium"], key="mat_res")

        if st.button("Calculer", key="btn_res"):
            if L > 0 and S > 0:
                rho = RHO_ALUMINIUM if materiau == "Aluminium" else RHO_CUIVRE
                R = (rho * L) / S
                R_total = 2 * R
                st.success(f"**Résistance simple :** {R:.3f} Ω")
                st.write(f"**Résistance aller-retour :** {R_total:.3f} Ω")
            else:
                st.error("Valeurs invalides.")

# ==================== ONGLET 2 : PLAN DE POTEAUX ====================
with tab2:
    st.header("Plan de positionnement des poteaux")

    # Session state pour stocker les poteaux
    if "poteaux" not in st.session_state:
        st.session_state.poteaux = []   # liste de dict {x, y, type}
    if "echelle" not in st.session_state:
        st.session_state.echelle = 10.0   # pixels/mètre

    # Barre d'outils
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("➕ Ajouter un poteau"):
            # Ajoute un poteau par défaut au centre (ou on utilisera un clic sur le graphique)
            st.session_state.ajout_mode = True
            st.info("Cliquez sur le graphique pour ajouter un poteau.")
    with col2:
        if st.button("🗑️ Supprimer dernier"):
            if st.session_state.poteaux:
                st.session_state.poteaux.pop()
                st.rerun()
    with col3:
        if st.button("🗑️ Tout effacer"):
            st.session_state.poteaux = []
            st.rerun()
    with col4:
        if st.button("📤 Exporter JSON"):
            if not st.session_state.poteaux:
                st.warning("Aucun poteau à exporter.")
            else:
                export_data = exporter_plan(st.session_state.poteaux, st.session_state.echelle)
                st.download_button(
                    label="Télécharger le fichier JSON",
                    data=export_data,
                    file_name=f"plan_poteaux_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )

    # Échelle
    echelle = st.number_input("Échelle (pixels par mètre)", value=st.session_state.echelle, step=1.0,
                              key="echelle_input")
    if echelle != st.session_state.echelle:
        st.session_state.echelle = echelle
        st.rerun()

    # Zone d'affichage du plan
    if len(st.session_state.poteaux) > 0:
        df = pd.DataFrame(st.session_state.poteaux)
        df["id"] = range(1, len(df) + 1)
        df["type_label"] = df["type"].apply(lambda t: "Départ" if t == "depart" else ("Arrivée" if t == "arrivee" else "Intermédiaire"))
        df["couleur"] = df["type"].apply(lambda t: "blue" if t == "depart" else ("green" if t == "arrivee" else "gray"))

        # Création du graphique
        fig = go.Figure()

        # Ajout des points
        fig.add_trace(go.Scatter(
            x=df["x"],
            y=df["y"],
            mode="markers+text",
            marker=dict(size=12, color=df["couleur"], line=dict(width=1, color="black")),
            text=df["id"],
            textposition="top center",
            name="Poteaux"
        ))

        # Ajout des segments entre poteaux consécutifs
        for i in range(len(df) - 1):
            x1, y1 = df.iloc[i]["x"], df.iloc[i]["y"]
            x2, y2 = df.iloc[i+1]["x"], df.iloc[i+1]["y"]
            fig.add_trace(go.Scatter(
                x=[x1, x2],
                y=[y1, y2],
                mode="lines",
                line=dict(color="gray", width=2),
                showlegend=False,
                hoverinfo="none"
            ))

        # Configuration de l'affichage
        fig.update_layout(
            title="Plan des poteaux (cliquez pour ajouter)",
            xaxis_title="X (pixels)",
            yaxis_title="Y (pixels)",
            hovermode="closest",
            dragmode="select"  # pour éviter les déplacements involontaires
        )

        # Capturer les clics
        click_data = st.plotly_chart(fig, use_container_width=True, key="plotly_plan")

        if click_data and "points" in click_data and click_data["points"]:
            point = click_data["points"][0]
            x_click = point["x"]
            y_click = point["y"]

            # Vérifier si on est en mode ajout (on active via bouton)
            if "ajout_mode" in st.session_state and st.session_state.ajout_mode:
                # Déterminer le type du nouveau poteau
                if len(st.session_state.poteaux) == 0:
                    typ = "depart"
                else:
                    typ = "intermediaire"
                st.session_state.poteaux.append({
                    "x": x_click,
                    "y": y_click,
                    "type": typ
                })
                st.session_state.ajout_mode = False
                st.rerun()

        # Statistiques
        if len(st.session_state.poteaux) > 0:
            distances = []
            total = 0.0
            for i in range(len(st.session_state.poteaux)-1):
                x1, y1 = st.session_state.poteaux[i]["x"], st.session_state.poteaux[i]["y"]
                x2, y2 = st.session_state.poteaux[i+1]["x"], st.session_state.poteaux[i+1]["y"]
                dist_px = math.hypot(x2-x1, y2-y1)
                dist_m = dist_px / st.session_state.echelle
                distances.append(dist_m)
                total += dist_m
            st.metric("Nombre de poteaux", len(st.session_state.poteaux))
            st.metric("Distance totale", f"{total:.2f} m")
            with st.expander("Détails des segments"):
                for i, d in enumerate(distances, 1):
                    st.write(f"Segment {i} → {i+1} : {d:.2f} m")

    else:
        st.info("Aucun poteau. Cliquez sur 'Ajouter un poteau' puis sur le graphique pour placer le premier poteau.")

        # Afficher un graphique vide pour permettre l'ajout
        fig = go.Figure()
        fig.update_layout(
            title="Plan des poteaux (cliquez pour ajouter)",
            xaxis_title="X (pixels)",
            yaxis_title="Y (pixels)",
            xaxis_range=[0, 800],
            yaxis_range=[0, 600]
        )
        click_data = st.plotly_chart(fig, use_container_width=True, key="empty_plot")
        if click_data and "points" in click_data and click_data["points"]:
            point = click_data["points"][0]
            x_click = point["x"]
            y_click = point["y"]
            if "ajout_mode" in st.session_state and st.session_state.ajout_mode:
                st.session_state.poteaux.append({
                    "x": x_click,
                    "y": y_click,
                    "type": "depart"
                })
                st.session_state.ajout_mode = False
                st.rerun()

    # Légende
    st.markdown("**Légende :** 🔵 Départ   ⚪ Intermédiaire   🟢 Arrivée (non géré automatiquement)")

    # Option pour changer le type du dernier poteau (le faire arriver)
    if len(st.session_state.poteaux) >= 2:
        if st.button("Marquer le dernier poteau comme Arrivée"):
            st.session_state.poteaux[-1]["type"] = "arrivee"
            st.rerun()


# Fonction d'export
def exporter_plan(poteaux, echelle):
    distances = []
    total = 0.0
    for i in range(len(poteaux)-1):
        x1, y1 = poteaux[i]["x"], poteaux[i]["y"]
        x2, y2 = poteaux[i+1]["x"], poteaux[i+1]["y"]
        dist_px = math.hypot(x2-x1, y2-y1)
        dist_m = dist_px / echelle
        distances.append(round(dist_m, 2))
        total += dist_m

    data = {
        "date_export": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "nombre_poteaux": len(poteaux),
        "distance_totale_metres": round(total, 2),
        "echelle_pixels_par_metre": echelle,
        "poteaux": [
            {
                "id": i+1,
                "x_pixels": round(p["x"], 2),
                "y_pixels": round(p["y"], 2),
                "type": p.get("type", "intermediaire")
            }
            for i, p in enumerate(poteaux)
        ],
        "segments": [
            {"segment": i+1, "de_poteau": i+1, "vers_poteau": i+2, "distance_metres": d}
            for i, d in enumerate(distances)
        ]
    }
    return json.dumps(data, indent=2, ensure_ascii=False)
