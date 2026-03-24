import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

# ------------------------------------------------------------
# Fonctions de calcul (selon NF C 15-100)
# ------------------------------------------------------------

def calcul_courant(puissance_kva, tension_v, cos_phi=0.9, type_branchement="triphasé"):
    """Calcule le courant d'emploi Ib (A)"""
    if puissance_kva == 0:
        return 0
    if type_branchement == "triphasé":
        ib = puissance_kva * 1000 / (1.732 * tension_v * cos_phi)
    else:  # monophasé
        ib = puissance_kva * 1000 / (tension_v * cos_phi)
    return round(ib, 1)

def dimensionnement_cable(ib, mode_pose, longueur, cos_phi=0.9, type_cable="cuivre", type_branchement="triphasé"):
    """
    Détermine la section minimale du câble BT.
    Mode pose : 'souterrain' ou 'aérien'.
    Retourne (section, courant_admissible, chute_tension_pct)
    """
    # Tableaux des courants admissibles (A) pour cuivre et aluminium, PVC, 20°C
    # Valeurs simplifiées – à remplacer par les vraies tables NF C 15-100
    if type_cable == "cuivre":
        sections = {
            'souterrain': {6: 52, 10: 70, 16: 94, 25: 122, 35: 151, 50: 182},
            'aérien': {6: 44, 10: 61, 16: 82, 25: 108, 35: 135, 50: 168}
        }
    else:  # aluminium
        sections = {
            'souterrain': {6: 40, 10: 55, 16: 75, 25: 98, 35: 120, 50: 145},
            'aérien': {6: 34, 10: 48, 16: 65, 25: 86, 35: 108, 50: 134}
        }
    # Sélection de la section minimale
    sec = 6
    for sec_cour, iz in sorted(sections[mode_pose].items()):
        if iz >= ib:
            sec = sec_cour
            break
    iz_ret = sections[mode_pose][sec]
    
    # Calcul chute de tension
    # Résistivité (Ω·mm²/m) : cuivre 0.0225, aluminium 0.036
    rho = 0.0225 if type_cable == "cuivre" else 0.036
    r = rho / sec  # Ω/m
    x = 0.00008    # Ω/m (réactance)
    sin_phi = np.sqrt(1 - cos_phi**2)
    if type_branchement == "triphasé":
        du = (1.732 * longueur * ib * (r * cos_phi + x * sin_phi)) / (400 * 10)  # en %
    else:  # monophasé : ΔU% = (2 * L * I * (Rcosφ + Xsinφ)) / (U * 10)
        du = (2 * longueur * ib * (r * cos_phi + x * sin_phi)) / (230 * 10)
    du = round(du, 1)
    return sec, iz_ret, du

def generer_nomenclature_bt_souterrain(longueur, puissance, section_cable, type_cable, type_branchement):
    """Génère la liste des articles pour un raccordement BT souterrain."""
    articles = []
    # Déterminer le nombre de conducteurs
    if type_branchement == "triphasé":
        conducteurs = "4x"  # 3 phases + neutre
    else:
        conducteurs = "2x"  # phase + neutre
    
    # Câble
    longueur_cable = longueur + 5  # chutes
    if type_cable == "cuivre":
        prix_cable = 12.50
        ref_cable = f"CAB-CU-{conducteurs}{section_cable}"
        designation = f"Câble cuivre {conducteurs}{section_cable} mm² (U1000 R2V)"
    else:
        prix_cable = 8.50
        ref_cable = f"CAB-AL-{conducteurs}{section_cable}"
        designation = f"Câble aluminium {conducteurs}{section_cable} mm² (U1000 R2V)"
    articles.append({
        'Référence': ref_cable,
        'Désignation': designation,
        'Unité': 'm',
        'Quantité': longueur_cable,
        'Prix unitaire HT': prix_cable,
        'Total HT': longueur_cable * prix_cable
    })
    
    # Fourreaux (un fourreau par circuit)
    articles.append({
        'Référence': 'FOU-RED-100',
        'Désignation': 'Fourreau rouge Ø100mm',
        'Unité': 'm',
        'Quantité': longueur,
        'Prix unitaire HT': 2.80,
        'Total HT': longueur * 2.80
    })
    
    # Chambres de tirage
    nb_chambres = max(1, int(np.ceil(longueur / 50)))
    articles.append({
        'Référence': 'CHAM-TIR-4040',
        'Désignation': 'Chambre de tirage 40x40 cm',
        'Unité': 'u',
        'Quantité': nb_chambres,
        'Prix unitaire HT': 120.00,
        'Total HT': nb_chambres * 120.00
    })
    
    # Disjoncteur de branchement
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
    
    # Accessoires divers
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

def generer_nomenclature_bt_aerien(longueur, puissance, section_cable, type_cable, type_branchement):
    """Génère la liste des articles pour une ligne aérienne BT torsadée."""
    articles = []
    # Déterminer le nombre de conducteurs
    if type_branchement == "triphasé":
        conducteurs = "4x"
    else:
        conducteurs = "2x"
    
    # Câble torsadé
    longueur_cable = longueur + 5
    if type_cable == "cuivre":
        prix_cable = 11.00
        ref_cable = f"CAB-TORS-CU-{conducteurs}{section_cable}"
        designation = f"Câble torsadé cuivre {conducteurs}{section_cable} mm²"
    else:
        prix_cable = 7.20
        ref_cable = f"CAB-TORS-AL-{conducteurs}{section_cable}"
        designation = f"Câble torsadé aluminium {conducteurs}{section_cable} mm²"
    articles.append({
        'Référence': ref_cable,
        'Désignation': designation,
        'Unité': 'm',
        'Quantité': longueur_cable,
        'Prix unitaire HT': prix_cable,
        'Total HT': longueur_cable * prix_cable
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
    
    # Console 3 fils
    articles.append({
        'Référence': 'CONS-3F',
        'Désignation': 'Console 3 fils',
        'Unité': 'u',
        'Quantité': nb_poteaux,
        'Prix unitaire HT': 25.00,
        'Total HT': nb_poteaux * 25.00
    })
    
    # Disjoncteur de branchement
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
    
    # Armoire extérieure
    articles.append({
        'Référence': 'ARM-BT-EXT',
        'Désignation': 'Armoire de branchement extérieure',
        'Unité': 'u',
        'Quantité': 1,
        'Prix unitaire HT': 280.00,
        'Total HT': 280.00
    })
    return articles

# ------------------------------------------------------------
# Application Streamlit
# ------------------------------------------------------------
st.set_page_config(page_title="Devis Électrique", layout="wide")
st.title("Application de devis pour ouvrage électrique")
st.markdown("Génération d'un devis basé sur les normes NF C")

# Barre latérale : choix général
with st.sidebar:
    st.header("Type d'ouvrage")
    type_ouvrage = st.selectbox(
        "Sélectionnez le type",
        ["Raccordement BT", "Poste MT/BT (à venir)"]
    )
    st.markdown("---")
    st.subheader("Paramètres généraux")
    type_ligne = st.radio("Type de ligne", ["Souterrain", "Aérien"], horizontal=True)
    type_cable = st.selectbox("Type de câble", ["Cuivre", "Aluminium"])
    type_branchement = st.selectbox("Type de branchement", ["Triphasé", "Monophasé"])
    cos_phi = st.number_input("Facteur de puissance", min_value=0.5, max_value=1.0, value=0.9, step=0.01)

if type_ouvrage == "Raccordement BT":
    st.header("Raccordement Basse Tension")
    col1, col2 = st.columns(2)
    with col1:
        puissance = st.number_input("Puissance demandée (kVA)", min_value=0.0, value=36.0, step=1.0)
        distance = st.number_input("Distance du point de raccordement au client (m)", min_value=0.0, value=50.0, step=10.0)
    with col2:
        # Afficher la tension selon le branchement
        if type_branchement == "Triphasé":
            tension = 400
            st.write("Tension : 400 V (triphasé)")
        else:
            tension = 230
            st.write("Tension : 230 V (monophasé)")
        st.write(f"Facteur de puissance : {cos_phi}")

    # Calcul du courant
    ib = calcul_courant(puissance, tension, cos_phi, type_branchement.lower())
    # Dimensionnement câble
    mode_pose = "souterrain" if type_ligne == "Souterrain" else "aérien"
    section, iz, du = dimensionnement_cable(
        ib, mode_pose, distance, cos_phi,
        type_cable.lower(), type_branchement.lower()
    )

    st.markdown("### Résultats des calculs")
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Courant d'emploi (A)", f"{ib:.1f} A")
    col_b.metric("Section minimale (mm²)", f"{section} mm²")
    col_c.metric("Chute de tension (%)", f"{du:.1f} %")
    if du > 8:
        st.warning("⚠️ Chute de tension > 8% – non conforme selon NF C 15-100 pour l'éclairage. Vérifiez la section ou la longueur.")

    # Génération de la nomenclature
    if type_ligne == "Souterrain":
        articles = generer_nomenclature_bt_souterrain(
            distance, puissance, section, type_cable.lower(), type_branchement.lower()
        )
    else:
        articles = generer_nomenclature_bt_aerien(
            distance, puissance, section, type_cable.lower(), type_branchement.lower()
        )

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

    # Export Excel
    if st.button("Exporter en Excel"):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_devis.to_excel(writer, sheet_name='Devis', index=False)
            recap = pd.DataFrame({
                'Paramètre': [
                    'Puissance (kVA)', 'Distance (m)', 'Type ligne', 'Type câble',
                    'Branchement', 'Courant (A)', 'Section (mm²)', 'Chute tension (%)'
                ],
                'Valeur': [
                    puissance, distance, type_ligne, type_cable,
                    type_branchement, ib, section, du
                ]
            })
            recap.to_excel(writer, sheet_name='Récapitulatif', index=False)
        output.seek(0)
        st.download_button(
            label="Télécharger le fichier Excel",
            data=output,
            file_name=f"devis_BT_{type_ligne}_{type_cable}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

else:
    st.info("La partie MT/BT sera ajoutée ultérieurement.")
