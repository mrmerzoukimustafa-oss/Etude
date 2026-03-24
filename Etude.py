import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

# ------------------------------------------------------------
# Fonctions de calcul (simplifiées selon NF C 15-100)
# ------------------------------------------------------------

def calcul_courant(puissance_kva, tension_v, cos_phi=0.9):
    """Calcule le courant d'emploi Ib (A)"""
    if puissance_kva == 0:
        return 0
    # Pour monophasé : I = P / (U * cosφ)
    # Pour triphasé : I = P / (√3 * U * cosφ)
    # Par défaut on considère triphasé 400V
    ib = puissance_kva * 1000 / (1.732 * tension_v * cos_phi)
    return round(ib, 1)

def dimensionnement_cable(ib, mode_pose, longueur):
    """
    Détermine la section minimale du câble BT (cuivre) selon NF C 15-100.
    Mode pose : 'souterrain' ou 'aérien'.
    Retourne (section, courant_admissible, chute_tension_pct)
    """
    # Tableau simplifié des courants admissibles (cuivre, PVC, 20°C)
    # Pour un usage réel, il faudrait un tableau complet selon NF C 15-100
    sections = {
        'souterrain': {6: 52, 10: 70, 16: 94, 25: 122, 35: 151, 50: 182},
        'aérien': {6: 44, 10: 61, 16: 82, 25: 108, 35: 135, 50: 168}
    }
    # Sélection de la section minimale
    sec = 6
    for sec_cour, iz in sorted(sections[mode_pose].items()):
        if iz >= ib:
            sec = sec_cour
            break
    iz_ret = sections[mode_pose][sec]
    # Calcul chute de tension (simplifié)
    # ΔU% = (√3 * L * I * (Rcosφ + Xsinφ)) / (U * 10) en % pour triphasé
    # Valeurs approximatives : R=0.0225 Ω/m/mm², X=0.08 Ω/km (câble)
    rho = 0.0225  # Ω·mm²/m
    r = rho / sec  # Ω/m
    x = 0.00008   # Ω/m (réactance)
    du = (1.732 * longueur * ib * (r * cos_phi + x * sin_phi)) / (400 * 10)  # en %
    du = round(du, 1)
    return sec, iz_ret, du

def generer_nomenclature_bt_souterrain(longueur, puissance, section_cable):
    """Génère la liste des articles pour un raccordement BT souterrain."""
    articles = []
    # Câble
    longueur_cable = longueur + 5  # +5 m pour chutes
    articles.append({
        'Référence': 'CAB-BT-AL-4x'+str(section_cable),
        'Désignation': f'Câble aluminium 4x{section_cable} mm² (U1000 R2V)',
        'Unité': 'm',
        'Quantité': longueur_cable,
        'Prix unitaire HT': 8.50,
        'Total HT': longueur_cable * 8.50
    })
    # Fourreaux (1 fourreau par circuit)
    articles.append({
        'Référence': 'FOU-RED-100',
        'Désignation': 'Fourreau rouge Ø100mm',
        'Unité': 'm',
        'Quantité': longueur,
        'Prix unitaire HT': 2.80,
        'Total HT': longueur * 2.80
    })
    # Chambres de tirage (1 tous les 50 m)
    nb_chambres = max(1, int(np.ceil(longueur / 50)))
    articles.append({
        'Référence': 'CHAM-TIR-4040',
        'Désignation': 'Chambre de tirage 40x40 cm',
        'Unité': 'u',
        'Quantité': nb_chambres,
        'Prix unitaire HT': 120.00,
        'Total HT': nb_chambres * 120.00
    })
    # Disjoncteur de branchement (selon puissance)
    if puissance <= 36:
        calibre = 200
    else:
        calibre = 250
    articles.append({
        'Référence': f'DISJ-{calibre}A',
        'Désignation': f'Disjoncteur de branchement {calibre}A',
        'Unité': 'u',
        'Quantité': 1,
        'Prix unitaire HT': 95.00,
        'Total HT': 95.00
    })
    # Armoire de branchement
    articles.append({
        'Référence': 'ARM-BT-4P',
        'Désignation': 'Armoire de branchement BT 4 modules',
        'Unité': 'u',
        'Quantité': 1,
        'Prix unitaire HT': 210.00,
        'Total HT': 210.00
    })
    # Accessoires divers (sable, grillage avertisseur)
    articles.append({
        'Référence': 'ACC-SABLE',
        'Désignation': 'Sable de pose (lit de sable)',
        'Unité': 'm3',
        'Quantité': round(longueur * 0.05, 2),
        'Prix unitaire HT': 45.00,
        'Total HT': round(longueur * 0.05 * 45.00, 2)
    })
    articles.append({
        'Référence': 'ACC-GRILLE',
        'Désignation': 'Grillage avertisseur',
        'Unité': 'm',
        'Quantité': longueur,
        'Prix unitaire HT': 1.20,
        'Total HT': longueur * 1.20
    })
    return articles

# ------------------------------------------------------------
# Application Streamlit
# ------------------------------------------------------------
st.set_page_config(page_title="Devis Électrique", layout="wide")
st.title("Application de devis pour ouvrage électrique")
st.markdown("Génération d'un devis basé sur les normes NF C")

# --- Barre latérale pour la configuration générale ---
with st.sidebar:
    st.header("Type d'ouvrage")
    type_ouvrage = st.selectbox(
        "Sélectionnez le type",
        ["Raccordement BT souterrain", "Raccordement BT aérien", "Poste MT/BT (à venir)"]
    )
    st.markdown("---")
    st.subheader("Paramètres généraux")
    tension = st.selectbox("Tension (V)", [400, 230], index=0)
    cos_phi = st.number_input("Facteur de puissance", min_value=0.5, max_value=1.0, value=0.9, step=0.01)

# --- Zone de saisie principale ---
if type_ouvrage == "Raccordement BT souterrain":
    st.header("Raccordement BT souterrain")
    col1, col2, col3 = st.columns(3)
    with col1:
        puissance = st.number_input("Puissance installée (kVA)", min_value=0.0, value=36.0, step=1.0)
    with col2:
        longueur = st.number_input("Longueur du raccordement (m)", min_value=0.0, value=50.0, step=10.0)
    with col3:
        mode_pose = "souterrain"  # fixe pour ce cas

    # Calcul du courant
    ib = calcul_courant(puissance, tension, cos_phi)
    # Dimensionnement câble
    section, iz, du = dimensionnement_cable(ib, mode_pose, longueur)

    st.markdown("### Résultats des calculs")
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Courant d'emploi (A)", f"{ib:.1f} A")
    col_b.metric("Section minimale (mm²)", f"{section} mm²")
    col_c.metric("Chute de tension (%)", f"{du:.1f} %")

    # Génération de la nomenclature
    articles = generer_nomenclature_bt_souterrain(longueur, puissance, section)

    # Création du DataFrame
    df_devis = pd.DataFrame(articles)
    total_ht = df_devis["Total HT"].sum()
    tva = total_ht * 0.20
    total_ttc = total_ht + tva

    # Affichage du tableau
    st.markdown("### Devis détaillé")
    st.dataframe(df_devis, use_container_width=True)

    # Totaux
    col_tot1, col_tot2, col_tot3 = st.columns(3)
    col_tot1.metric("Total HT", f"{total_ht:.2f} €")
    col_tot2.metric("TVA (20%)", f"{tva:.2f} €")
    col_tot3.metric("Total TTC", f"{total_ttc:.2f} €")

    # Export Excel
    if st.button("Exporter en Excel"):
        # Préparer le fichier Excel avec plusieurs onglets
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_devis.to_excel(writer, sheet_name='Devis', index=False)
            # Ajouter un onglet récapitulatif
            recap = pd.DataFrame({
                'Paramètre': ['Puissance (kVA)', 'Longueur (m)', 'Courant (A)', 'Section (mm²)', 'Chute tension (%)'],
                'Valeur': [puissance, longueur, ib, section, du]
            })
            recap.to_excel(writer, sheet_name='Récapitulatif', index=False)
        output.seek(0)
        st.download_button(
            label="Télécharger le fichier Excel",
            data=output,
            file_name=f"devis_{type_ouvrage.replace(' ', '_')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

elif type_ouvrage == "Raccordement BT aérien":
    st.header("Raccordement BT aérien (torsadé)")
    col1, col2 = st.columns(2)
    with col1:
        puissance = st.number_input("Puissance installée (kVA)", min_value=0.0, value=36.0, step=1.0)
    with col2:
        longueur = st.number_input("Longueur de la ligne (m)", min_value=0.0, value=100.0, step=10.0)

    ib = calcul_courant(puissance, tension, cos_phi)
    section, iz, du = dimensionnement_cable(ib, "aérien", longueur)

    st.markdown("### Résultats des calculs")
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Courant d'emploi (A)", f"{ib:.1f} A")
    col_b.metric("Section minimale (mm²)", f"{section} mm²")
    col_c.metric("Chute de tension (%)", f"{du:.1f} %")

    # Nomenclature simplifiée pour aérien
    articles = []
    longueur_cable = longueur + 5
    articles.append({
        'Référence': 'CAB-TORS-4x'+str(section),
        'Désignation': f'Câble torsadé 4x{section} mm² (aluminium)',
        'Unité': 'm',
        'Quantité': longueur_cable,
        'Prix unitaire HT': 7.20,
        'Total HT': longueur_cable * 7.20
    })
    # Poteaux (1 tous les 40 m environ)
    nb_poteaux = max(2, int(np.ceil(longueur / 40)) + 1)
    articles.append({
        'Référence': 'POT-8M',
        'Désignation': 'Poteau bois 8 m',
        'Unité': 'u',
        'Quantité': nb_poteaux,
        'Prix unitaire HT': 180.00,
        'Total HT': nb_poteaux * 180.00
    })
    # Accessoires par poteau
    articles.append({
        'Référence': 'CONS-3F',
        'Désignation': 'Console 3 fils',
        'Unité': 'u',
        'Quantité': nb_poteaux,
        'Prix unitaire HT': 25.00,
        'Total HT': nb_poteaux * 25.00
    })
    # Disjoncteur
    if puissance <= 36:
        calibre = 200
    else:
        calibre = 250
    articles.append({
        'Référence': f'DISJ-{calibre}A',
        'Désignation': f'Disjoncteur de branchement {calibre}A',
        'Unité': 'u',
        'Quantité': 1,
        'Prix unitaire HT': 95.00,
        'Total HT': 95.00
    })
    # Armoire
    articles.append({
        'Référence': 'ARM-BT-EXT',
        'Désignation': 'Armoire de branchement extérieure',
        'Unité': 'u',
        'Quantité': 1,
        'Prix unitaire HT': 280.00,
        'Total HT': 280.00
    })

    df_devis = pd.DataFrame(articles)
    total_ht = df_devis["Total HT"].sum()
    tva = total_ht * 0.20
    total_ttc = total_ht + tva

    st.markdown("### Devis détaillé")
    st.dataframe(df_devis, use_container_width=True)

    col_tot1, col_tot2, col_tot3 = st.columns(3)
    col_tot1.metric("Total HT", f"{total_ht:.2f} €")
    col_tot2.metric("TVA (20%)", f"{tva:.2f} €")
    col_tot3.metric("Total TTC", f"{total_ttc:.2f} €")

    # Export Excel (identique au précédent)
    if st.button("Exporter en Excel"):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_devis.to_excel(writer, sheet_name='Devis', index=False)
            recap = pd.DataFrame({
                'Paramètre': ['Puissance (kVA)', 'Longueur (m)', 'Courant (A)', 'Section (mm²)', 'Chute tension (%)'],
                'Valeur': [puissance, longueur, ib, section, du]
            })
            recap.to_excel(writer, sheet_name='Récapitulatif', index=False)
        output.seek(0)
        st.download_button(
            label="Télécharger le fichier Excel",
            data=output,
            file_name=f"devis_{type_ouvrage.replace(' ', '_')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

else:
    st.info("Les autres types d'ouvrage seront ajoutés ultérieurement.")
