
# ÉLECTRO CALC PRO - Application complète de calculs électriques
# Code Python/Kivy pour Android

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line, Ellipse, Rectangle
from kivy.core.window import Window
from kivy.properties import ListProperty, NumericProperty, ObjectProperty
from kivy.clock import Clock
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.anchorlayout import AnchorLayout
import math
import json
import os
from datetime import datetime

# Configuration globale
Window.clearcolor = (0.96, 0.97, 0.98, 1)
Window.softinput_mode = 'below_target'

# Constantes électriques
RHO_CUIVRE = 0.0175  # Ω·mm²/m
RHO_ALUMINIUM = 0.028  # Ω·mm²/m
SECTIONS_NORMALISEES = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240]


class StyledCard(BoxLayout):
    """Widget carte stylisée avec ombre simulée"""
    def __init__(self, title="", **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 15
        self.spacing = 10
        self.size_hint_y = None
        self.bind(minimum_height=self.setter('height'))
        
        # Titre de la carte
        if title:
            title_label = Label(
                text=title,
                font_size='18sp',
                bold=True,
                color=(0.1, 0.4, 0.7, 1),
                size_hint_y=None,
                height=35,
                halign='left'
            )
            title_label.bind(size=lambda instance, value: setattr(instance, 'text_size', (value[0], None)))
            self.add_widget(title_label)


class CalculsElectriquesScreen(Screen):
    """Écran des calculs électriques complets"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()
    
    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=8)
        
        # Header
        header = BoxLayout(size_hint_y=0.08, padding=5)
        titre = Label(
            text='⚡ CALCULS ÉLECTRIQUES',
            font_size='22sp',
            bold=True,
            color=(0.1, 0.3, 0.6, 1)
        )
        header.add_widget(titre)
        layout.add_widget(header)
        
        # ScrollView pour le contenu
        scroll = ScrollView(size_hint_y=0.82)
        content = GridLayout(cols=1, spacing=12, size_hint_y=None, padding=10)
        content.bind(minimum_height=content.setter('height'))
        
        # Section 1: Section de câble
        self.create_section_cable(content)
        
        # Section 2: Chute de tension
        self.create_section_chute_tension(content)
        
        # Section 3: Puissance
        self.create_section_puissance(content)
        
        # Section 4: Courant
        self.create_section_courant(content)
        
        # Section 5: Résistance ligne
        self.create_section_resistance(content)
        
        scroll.add_widget(content)
        layout.add_widget(scroll)
        
        # Footer avec bouton retour
        footer = BoxLayout(size_hint_y=0.1, padding=5)
        btn_retour = Button(
            text='← RETOUR AU MENU',
            font_size='16sp',
            background_color=(0.3, 0.5, 0.8, 1),
            color=(1, 1, 1, 1),
            bold=True
        )
        btn_retour.bind(on_press=lambda x: setattr(self.manager, 'current', 'menu'))
        footer.add_widget(btn_retour)
        layout.add_widget(footer)
        
        self.add_widget(layout)
    
    def create_section_cable(self, parent):
        """Section calcul section de câble selon NFC 15-100"""
        card = StyledCard(title='📏 Section de Câble (mm²) - NFC 15-100')
        
        grid = GridLayout(cols=2, spacing=10, size_hint_y=None, height=250)
        
        # Champs de saisie
        fields = [
            ('Puissance (W):', '2000', 'puissance_cable'),
            ('Tension (V):', '220', 'tension_cable'),
            ('Longueur (m):', '50', 'longueur_cable'),
            ('Chute max (%):', '3', 'chute_max_cable'),
            ('Cos φ:', '0.9', 'cosphi_cable'),
            ('Matériau:', 'Cuivre', 'materiau_cable')
        ]
        
        self.cable_inputs = {}
        for label_text, default, attr_name in fields:
            label = Label(text=label_text, color=(0.2, 0.2, 0.2, 1), font_size='14sp', size_hint_y=None, height=35)
            grid.add_widget(label)
            
            if attr_name == 'materiau_cable':
                input_field = TextInput(
                    text=default,
                    font_size='14sp',
                    size_hint_y=None,
                    height=40,
                    multiline=False
                )
            else:
                input_field = TextInput(
                    hint_text=default,
                    input_filter='float',
                    font_size='14sp',
                    size_hint_y=None,
                    height=40,
                    multiline=False,
                    text=default if attr_name in ['tension_cable', 'chute_max_cable', 'cosphi_cable'] else ''
                )
            
            self.cable_inputs[attr_name] = input_field
            grid.add_widget(input_field)
        
        card.add_widget(grid)
        
        # Bouton calcul
        btn_calc = Button(
            text='CALCULER LA SECTION',
            size_hint_y=None,
            height=50,
            background_color=(0.2, 0.7, 0.3, 1),
            color=(1, 1, 1, 1),
            font_size='16sp',
            bold=True
        )
        btn_calc.bind(on_press=self.calculer_section_cable)
        card.add_widget(btn_calc)
        
        # Résultat
        self.result_cable = Label(
            text='Section minimale: --',
            font_size='16sp',
            bold=True,
            color=(0.3, 0.3, 0.3, 1),
            size_hint_y=None,
            height=40
        )
        card.add_widget(self.result_cable)
        
        parent.add_widget(card)
    
    def create_section_chute_tension(self, parent):
        """Section calcul chute de tension"""
        card = StyledCard(title='📉 Chute de Tension (%)')
        
        grid = GridLayout(cols=2, spacing=10, size_hint_y=None, height=200)
        
        fields = [
            ('Courant (A):', '10', 'courant_chute'),
            ('Longueur (m):', '100', 'longueur_chute'),
            ('Section (mm²):', '2.5', 'section_chute'),
            ('Tension (V):', '220', 'tension_chute'),
            ('Matériau:', 'Cuivre', 'materiau_chute')
        ]
        
        self.chute_inputs = {}
        for label_text, default, attr_name in fields:
            grid.add_widget(Label(text=label_text, color=(0.2, 0.2, 0.2, 1), font_size='14sp', size_hint_y=None, height=35))
            
            if attr_name == 'materiau_chute':
                input_field = TextInput(text=default, font_size='14sp', size_hint_y=None, height=40, multiline=False)
            else:
                input_field = TextInput(
                    hint_text=default,
                    input_filter='float',
                    font_size='14sp',
                    size_hint_y=None,
                    height=40,
                    multiline=False,
                    text=default if attr_name == 'tension_chute' else ''
                )
            
            self.chute_inputs[attr_name] = input_field
            grid.add_widget(input_field)
        
        card.add_widget(grid)
        
        btn_calc = Button(
            text='CALCULER LA CHUTE',
            size_hint_y=None,
            height=50,
            background_color=(0.2, 0.7, 0.3, 1),
            color=(1, 1, 1, 1),
            font_size='16sp',
            bold=True
        )
        btn_calc.bind(on_press=self.calculer_chute_tension)
        card.add_widget(btn_calc)
        
        self.result_chute = Label(
            text='Chute de tension: --',
            font_size='16sp',
            bold=True,
            color=(0.3, 0.3, 0.3, 1),
            size_hint_y=None,
            height=40
        )
        card.add_widget(self.result_chute)
        
        parent.add_widget(card)
    
    def create_section_puissance(self, parent):
        """Section calcul puissance"""
        card = StyledCard(title='⚡ Calcul de Puissance')
        
        grid = GridLayout(cols=2, spacing=10, size_hint_y=None, height=150)
        
        fields = [
            ('Tension (V):', '220', 'tension_puiss'),
            ('Courant (A):', '10', 'courant_puiss'),
            ('Cos φ:', '0.9', 'cosphi_puiss')
        ]
        
        self.puiss_inputs = {}
        for label_text, default, attr_name in fields:
            grid.add_widget(Label(text=label_text, color=(0.2, 0.2, 0.2, 1), font_size='14sp', size_hint_y=None, height=35))
            input_field = TextInput(
                hint_text=default,
                input_filter='float',
                font_size='14sp',
                size_hint_y=None,
                height=40,
                multiline=False,
                text=default if attr_name in ['tension_puiss', 'cosphi_puiss'] else ''
            )
            self.puiss_inputs[attr_name] = input_field
            grid.add_widget(input_field)
        
        card.add_widget(grid)
        
        btn_calc = Button(
            text='CALCULER',
            size_hint_y=None,
            height=50,
            background_color=(0.2, 0.7, 0.3, 1),
            color=(1, 1, 1, 1),
            font_size='16sp',
            bold=True
        )
        btn_calc.bind(on_press=self.calculer_puissance)
        card.add_widget(btn_calc)
        
        self.result_puiss = Label(
            text='Puissance: --',
            font_size='16sp',
            bold=True,
            color=(0.3, 0.3, 0.3, 1),
            size_hint_y=None,
            height=40
        )
        card.add_widget(self.result_puiss)
        
        parent.add_widget(card)
    
    def create_section_courant(self, parent):
        """Section calcul courant"""
        card = StyledCard(title='🔌 Calcul de Courant')
        
        grid = GridLayout(cols=2, spacing=10, size_hint_y=None, height=120)
        
        grid.add_widget(Label(text='Puissance (W):', color=(0.2, 0.2, 0.2, 1), font_size='14sp', size_hint_y=None, height=35))
        self.puiss_courant_input = TextInput(hint_text='2000', input_filter='float', font_size='14sp', size_hint_y=None, height=40, multiline=False)
        grid.add_widget(self.puiss_courant_input)
        
        grid.add_widget(Label(text='Tension (V):', color=(0.2, 0.2, 0.2, 1), font_size='14sp', size_hint_y=None, height=35))
        self.tension_courant_input = TextInput(text='220', input_filter='float', font_size='14sp', size_hint_y=None, height=40, multiline=False)
        grid.add_widget(self.tension_courant_input)
        
        card.add_widget(grid)
        
        btn_calc = Button(
            text='CALCULER',
            size_hint_y=None,
            height=50,
            background_color=(0.2, 0.7, 0.3, 1),
            color=(1, 1, 1, 1),
            font_size='16sp',
            bold=True
        )
        btn_calc.bind(on_press=self.calculer_courant)
        card.add_widget(btn_calc)
        
        self.result_courant = Label(
            text='Courant: --',
            font_size='16sp',
            bold=True,
            color=(0.3, 0.3, 0.3, 1),
            size_hint_y=None,
            height=40
        )
        card.add_widget(self.result_courant)
        
        parent.add_widget(card)
    
    def create_section_resistance(self, parent):
        """Section calcul résistance d'une ligne"""
        card = StyledCard(title='🔧 Résistance de Ligne (Ω)')
        
        grid = GridLayout(cols=2, spacing=10, size_hint_y=None, height=150)
        
        fields = [
            ('Longueur (m):', '100', 'longueur_res'),
            ('Section (mm²):', '2.5', 'section_res'),
            ('Matériau:', 'Cuivre', 'materiau_res')
        ]
        
        self.res_inputs = {}
        for label_text, default, attr_name in fields:
            grid.add_widget(Label(text=label_text, color=(0.2, 0.2, 0.2, 1), font_size='14sp', size_hint_y=None, height=35))
            if attr_name == 'materiau_res':
                input_field = TextInput(text=default, font_size='14sp', size_hint_y=None, height=40, multiline=False)
            else:
                input_field = TextInput(hint_text=default, input_filter='float', font_size='14sp', size_hint_y=None, height=40, multiline=False)
            self.res_inputs[attr_name] = input_field
            grid.add_widget(input_field)
        
        card.add_widget(grid)
        
        btn_calc = Button(
            text='CALCULER',
            size_hint_y=None,
            height=50,
            background_color=(0.2, 0.7, 0.3, 1),
            color=(1, 1, 1, 1),
            font_size='16sp',
            bold=True
        )
        btn_calc.bind(on_press=self.calculer_resistance)
        card.add_widget(btn_calc)
        
        self.result_res = Label(
            text='Résistance: --',
            font_size='16sp',
            bold=True,
            color=(0.3, 0.3, 0.3, 1),
            size_hint_y=None,
            height=40
        )
        card.add_widget(self.result_res)
        
        parent.add_widget(card)
    
    # Méthodes de calcul
    def calculer_section_cable(self, instance):
        try:
            P = float(self.cable_inputs['puissance_cable'].text or 0)
            V = float(self.cable_inputs['tension_cable'].text or 220)
            L = float(self.cable_inputs['longueur_cable'].text or 0)
            chute_max = float(self.cable_inputs['chute_max_cable'].text or 3)
            cos_phi = float(self.cable_inputs['cosphi_cable'].text or 0.9)
            materiau = self.cable_inputs['materiau_cable'].text.lower()
            
            if P <= 0 or V <= 0 or L <= 0:
                self.show_error(self.result_cable, 'Valeurs invalides !')
                return
            
            # Courant nominal
            I = P / (V * cos_phi)
            
            # Résistivité
            rho = RHO_ALUMINIUM if 'alu' in materiau else RHO_CUIVRE
            
            # Section minimale pour chute de tension
            S_calc = (2 * rho * L * I) / ((chute_max / 100) * V)
            
            # Section normalisée supérieure
            section_choisie = next((s for s in SECTIONS_NORMALISEES if s >= S_calc), 240)
            
            # Vérification courant admissible (simplifiée)
            courant_admissible = section_choisie * 6  # Règle approximative
            
            status = "✓" if courant_admissible >= I else "⚠ Courant élevé"
            
            self.result_cable.text = f'Section: {section_choisie} mm² (I={I:.1f}A) {status}'
            self.result_cable.color = (0.1, 0.6, 0.2, 1) if '✓' in status else (0.9, 0.6, 0.1, 1)
            
        except ValueError:
            self.show_error(self.result_cable, 'Erreur de saisie !')
    
    def calculer_chute_tension(self, instance):
        try:
            I = float(self.chute_inputs['courant_chute'].text or 0)
            L = float(self.chute_inputs['longueur_chute'].text or 0)
            S = float(self.chute_inputs['section_chute'].text or 0)
            V = float(self.chute_inputs['tension_chute'].text or 220)
            materiau = self.chute_inputs['materiau_chute'].text.lower()
            
            if I <= 0 or L <= 0 or S <= 0 or V <= 0:
                self.show_error(self.result_chute, 'Valeurs invalides !')
                return
            
            rho = RHO_ALUMINIUM if 'alu' in materiau else RHO_CUIVRE
            
            # Chute de tension en volts (aller-retour)
            delta_V = (2 * rho * L * I) / S
            chute_pourcent = (delta_V / V) * 100
            
            # Évaluation NFC 15-100
            if chute_pourcent <= 3:
                eval_text, color = "✓ Conforme éclairage", (0.1, 0.6, 0.2, 1)
            elif chute_pourcent <= 5:
                eval_text, color = "✓ Conforme autres usages", (0.1, 0.6, 0.2, 1)
            elif chute_pourcent <= 8:
                eval_text, color = "⚠ Limite - Vérifier", (0.9, 0.6, 0.1, 1)
            else:
                eval_text, color = "✗ Non conforme - Augmenter section", (0.8, 0.2, 0.2, 1)
            
            self.result_chute.text = f'Chute: {chute_pourcent:.2f}% ({delta_V:.1f}V) - {eval_text}'
            self.result_chute.color = color
            
        except ValueError:
            self.show_error(self.result_chute, 'Erreur de saisie !')
    
    def calculer_puissance(self, instance):
        try:
            V = float(self.puiss_inputs['tension_puiss'].text or 0)
            I = float(self.puiss_inputs['courant_puiss'].text or 0)
            cos_phi = float(self.puiss_inputs['cosphi_puiss'].text or 1)
            
            if V <= 0 or I <= 0:
                self.show_error(self.result_puiss, 'Valeurs invalides !')
                return
            
            P = V * I * cos_phi  # Puissance active (W)
            S = V * I            # Puissance apparente (VA)
            Q = math.sqrt(S**2 - P**2) if S > P else 0  # Puissance réactive (VAR)
            
            self.result_puiss.text = f'P={P:.0f}W | S={S:.0f}VA | Q={Q:.0f}VAR'
            self.result_puiss.color = (0.1, 0.4, 0.1, 1)
            
        except ValueError:
            self.show_error(self.result_puiss, 'Erreur de saisie !')
    
    def calculer_courant(self, instance):
        try:
            P = float(self.puiss_courant_input.text or 0)
            V = float(self.tension_courant_input.text or 0)
            
            if P <= 0 or V <= 0:
                self.show_error(self.result_courant, 'Valeurs invalides !')
                return
            
            I = P / V
            self.result_courant.text = f'Courant: {I:.2f} A ({I:.1f}A)'
            self.result_courant.color = (0.1, 0.4, 0.1, 1)
            
        except ValueError:
            self.show_error(self.result_courant, 'Erreur de saisie !')
    
    def calculer_resistance(self, instance):
        try:
            L = float(self.res_inputs['longueur_res'].text or 0)
            S = float(self.res_inputs['section_res'].text or 0)
            materiau = self.res_inputs['materiau_res'].text.lower()
            
            if L <= 0 or S <= 0:
                self.show_error(self.result_res, 'Valeurs invalides !')
                return
            
            rho = RHO_ALUMINIUM if 'alu' in materiau else RHO_CUIVRE
            R = (rho * L) / S
            
            # Aller-retour pour installation
            R_total = 2 * R
            
            self.result_res.text = f'R ligne: {R:.3f}Ω | R A-R: {R_total:.3f}Ω'
            self.result_res.color = (0.1, 0.4, 0.1, 1)
            
        except ValueError:
            self.show_error(self.result_res, 'Erreur de saisie !')
    
    def show_error(self, label, message):
        label.text = message
        label.color = (0.8, 0.2, 0.2, 1)


class PlanPoteauxWidget(Widget):
    """Widget interactif pour dessiner le plan de poteaux"""
    poteaux = ListProperty([])
    echelle = NumericProperty(1.0)
    mode = 'add'  # 'add', 'delete', 'move'
    selected_poteau = None
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.poteaux = []
        self.lignes = []
        self.bind(pos=self.redraw, size=self.redraw)
        Clock.schedule_once(self.redraw, 0)
    
    def redraw(self, *args):
        self.canvas.clear()
        with self.canvas:
            # Fond blanc avec grille
            Color(1, 1, 1, 1)
            Rectangle(pos=self.pos, size=self.size)
            
            # Grille
            Color(0.9, 0.9, 0.95, 1)
            step = 50
            for x in range(int(self.x), int(self.right), step):
                Line(points=[x, self.y, x, self.top], width=0.5)
            for y in range(int(self.y), int(self.top), step):
                Line(points=[self.x, y, self.right, y], width=0.5)
            
            # Lignes entre poteaux consécutifs
            Color(0.3, 0.3, 0.3, 1)
            for i in range(len(self.poteaux) - 1):
                x1, y1 = self.poteaux[i]['x'], self.poteaux[i]['y']
                x2, y2 = self.poteaux[i+1]['x'], self.poteaux[i+1]['y']
                Line(points=[x1, y1, x2, y2], width=2)
            
            # Poteaux
            for i, p in enumerate(self.poteaux):
                # Couleur selon type
                if p.get('selected', False):
                    Color(0.9, 0.2, 0.2, 1)  # Rouge sélection
                elif i == 0:
                    Color(0.2, 0.6, 0.9, 1)  # Bleu départ
                elif i == len(self.poteaux) - 1 and len(self.poteaux) > 1:
                    Color(0.2, 0.8, 0.4, 1)  # Vert arrivée
                else:
                    Color(0.6, 0.6, 0.6, 1)  # Gris intermédiaire
                
                size = 16
                Ellipse(pos=(p['x']-size/2, p['y']-size/2), size=(size, size))
                
                # Numéro du poteau
                # Note: Les labels Kivy ne peuvent pas être dessinés dans canvas facilement
    
    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False
        
        if self.mode == 'add':
            # Vérifier si on clique sur un poteau existant (pour le sélectionner)
            for p in self.poteaux:
                dist = math.sqrt((touch.x - p['x'])**2 + (touch.y - p['y'])**2)
                if dist < 20:
                    # Désélectionner les autres
                    for pp in self.poteaux:
                        pp['selected'] = False
                    p['selected'] = True
                    self.selected_poteau = p
                    self.redraw()
                    return True
            
            # Ajouter nouveau poteau
            for p in self.poteaux:
                p['selected'] = False
            
            new_poteau = {
                'x': touch.x,
                'y': touch.y,
                'id': len(self.poteaux) + 1,
                'type': 'intermediaire',
                'selected': True
            }
            if len(self.poteaux) == 0:
                new_poteau['type'] = 'depart'
            
            self.poteaux.append(new_poteau)
            self.selected_poteau = new_poteau
            self.redraw()
            
        elif self.mode == 'delete':
            # Supprimer poteau proche
            for i, p in enumerate(self.poteaux):
                dist = math.sqrt((touch.x - p['x'])**2 + (touch.y - p['y'])**2)
                if dist < 20:
                    self.poteaux.pop(i)
                    self.redraw()
                    break
        
        return True
    
    def on_touch_move(self, touch):
        """Déplacer un poteau sélectionné"""
        if self.selected_poteau and self.mode == 'add':
            if self.collide_point(*touch.pos):
                self.selected_poteau['x'] = touch.x
                self.selected_poteau['y'] = touch.y
                self.redraw()
                return True
        return False
    
    def on_touch_up(self, touch):
        self.selected_poteau = None
        for p in self.poteaux:
            p['selected'] = False
        self.redraw()
    
    def set_mode(self, mode):
        self.mode = mode
        for p in self.poteaux:
            p['selected'] = False
        self.redraw()
    
    def effacer_dernier(self):
        if self.poteaux:
            self.poteaux.pop()
            self.redraw()
    
    def effacer_tout(self):
        self.poteaux = []
        self.redraw()
    
    def exporter_plan(self):
        """Exporter les données en JSON"""
        distances = []
        total_distance = 0
        
        for i in range(len(self.poteaux) - 1):
            x1, y1 = self.poteaux[i]['x'], self.poteaux[i]['y']
            x2, y2 = self.poteaux[i+1]['x'], self.poteaux[i+1]['y']
            dist_pixels = math.sqrt((x2-x1)**2 + (y2-y1)**2)
            dist_metres = dist_pixels / self.echelle
            total_distance += dist_metres
            
            distances.append({
                'segment': i + 1,
                'de_poteau': i + 1,
                'vers_poteau': i + 2,
                'distance_metres': round(dist_metres, 2)
            })
        
        data = {
            'date_export': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'nombre_poteaux': len(self.poteaux),
            'distance_totale_metres': round(total_distance, 2),
            'echelle_pixels_par_metre': self.echelle,
            'poteaux': [
                {
                    'id': i + 1,
                    'x_pixels': round(p['x'], 2),
                    'y_pixels': round(p['y'], 2),
                    'type': p.get('type', 'intermediaire')
                } for i, p in enumerate(self.poteaux)
            ],
            'segments': distances
        }
        
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def get_stats(self):
        """Retourner statistiques pour affichage"""
        nb = len(self.poteaux)
        total = 0
        for i in range(nb - 1):
            x1, y1 = self.poteaux[i]['x'], self.poteaux[i]['y']
            x2, y2 = self.poteaux[i+1]['x'], self.poteaux[i+1]['y']
            total += math.sqrt((x2-x1)**2 + (y2-y1)**2)
        
        total_metres = total / self.echelle
        return nb, total_metres


class PlanPoteauxScreen(Screen):
    """Écran du plan de poteaux"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()
    
    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=8, spacing=6)
        
        # Header
        header = BoxLayout(size_hint_y=0.06)
        titre = Label(
            text='📍 PLAN DE POSITIONNEMENT DES POTEAUX',
            font_size='18sp',
            bold=True,
            color=(0.1, 0.3, 0.6, 1)
        )
        header.add_widget(titre)
        layout.add_widget(header)
        
        # Instructions
        instr = Label(
            text='Touchez pour placer • Maintenez pour déplacer • Ligne auto entre poteaux',
            font_size='12sp',
            color=(0.4, 0.4, 0.4, 1),
            size_hint_y=0.04
        )
        layout.add_widget(instr)
        
        # Zone de dessin
        self.plan_widget = PlanPoteauxWidget(size_hint_y=0.62)
        layout.add_widget(self.plan_widget)
        
        # Contrôles échelle
        echelle_box = BoxLayout(size_hint_y=0.05, spacing=10)
        echelle_box.add_widget(Label(text='Échelle (px/m):', font_size='12sp', color=(0.3, 0.3, 0.3, 1)))
        self.echelle_input = TextInput(
            text='10',
            input_filter='float',
            font_size='12sp',
            size_hint_x=0.3,
            multiline=False
        )
        self.echelle_input.bind(text=self.update_echelle)
        echelle_box.add_widget(self.echelle_input)
        echelle_box.add_widget(Widget())  # Spacer
        layout.add_widget(echelle_box)
        
        # Boutons de contrôle
        controls = GridLayout(cols=4, spacing=8, size_hint_y=0.08)
        
        self.btn_add = Button(
            text='➕ AJOUTER',
            background_color=(0.2, 0.6, 0.9, 1),
            color=(1, 1, 1, 1),
            font_size='13sp',
            bold=True
        )
        self.btn_add.bind(on_press=lambda x: self.set_mode('add'))
        controls.add_widget(self.btn_add)
        
        self.btn_delete = Button(
            text='🗑️ SUPPR',
            background_color=(0.6, 0.6, 0.6, 1),
            color=(1, 1, 1, 1),
            font_size='13sp'
        )
        self.btn_delete.bind(on_press=lambda x: self.set_mode('delete'))
        controls.add_widget(self.btn_delete)
        
        btn_undo = Button(
            text='↩️ DEFAIRE',
            background_color=(0.9, 0.6, 0.2, 1),
            color=(1, 1, 1, 1),
            font_size='13sp'
        )
        btn_undo.bind(on_press=lambda x: self.plan_widget.effacer_dernier())
        controls.add_widget(btn_undo)
        
        btn_reset = Button(
            text='🗑️ TOUT',
            background_color=(0.9, 0.3, 0.3, 1),
            color=(1, 1, 1, 1),
            font_size='13sp'
        )
        btn_reset.bind(on_press=lambda x: self.plan_widget.effacer_tout())
        controls.add_widget(btn_reset)
        
        layout.add_widget(controls)
        
        # Bouton export
        btn_export = Button(
            text='📤 EXPORTER LE PLAN',
            size_hint_y=0.06,
            background_color=(0.3, 0.7, 0.4, 1),
            color=(1, 1, 1, 1),
            font_size='14sp',
            bold=True
        )
        btn_export.bind(on_press=self.exporter_plan)
        layout.add_widget(btn_export)
        
        # Statistiques
        self.stats_label = Label(
            text='Poteaux: 0 | Distance totale: 0m',
            font_size='13sp',
            color=(0.2, 0.2, 0.2, 1),
            size_hint_y=0.04,
            bold=True
        )
        layout.add_widget(self.stats_label)
        
        # Légende
        legende = BoxLayout(size_hint_y=0.04, spacing=20)
        legende.add_widget(Label(text='🔵 Départ  ⚪ Intermédiaire  🟢 Arrivée', font_size='11sp', color=(0.4, 0.4, 0.4, 1)))
        layout.add_widget(legende)
        
        # Footer
        footer = BoxLayout(size_hint_y=0.08, padding=5)
        btn_retour = Button(
            text='← RETOUR AU MENU',
            font_size='16sp',
            background_color=(0.3, 0.5, 0.8, 1),
            color=(1, 1, 1, 1),
            bold=True
        )
        btn_retour.bind(on_press=lambda x: setattr(self.manager, 'current', 'menu'))
        footer.add_widget(btn_retour)
        layout.add_widget(footer)
        
        self.add_widget(layout)
        
        # Mise à jour périodique
        Clock.schedule_interval(self.update_stats, 0.3)
        
        # Mode par défaut
        self.current_mode = 'add'
    
    def update_echelle(self, instance, value):
        try:
            self.plan_widget.echelle = float(value) if value else 10.0
        except:
            self.plan_widget.echelle = 10.0
    
    def set_mode(self, mode):
        self.current_mode = mode
        self.plan_widget.set_mode(mode)
        
        # Mise à jour visuelle des boutons
        if mode == 'add':
            self.btn_add.background_color = (0.2, 0.6, 0.9, 1)
            self.btn_delete.background_color = (0.6, 0.6, 0.6, 1)
        else:
            self.btn_add.background_color = (0.6, 0.6, 0.6, 1)
            self.btn_delete.background_color = (0.9, 0.3, 0.3, 1)
    
    def update_stats(self, dt):
        nb, total = self.plan_widget.get_stats()
        self.stats_label.text = f'Poteaux: {nb} | Distance totale: {total:.1f}m'
    
    def exporter_plan(self, instance):
        if not self.plan_widget.poteaux:
            self.show_popup('Erreur', 'Aucun poteau à exporter !')
            return
        
        data = self.plan_widget.exporter_plan()
        
        # Sauvegarder dans fichier
        try:
            filename = f'/sdcard/Download/plan_poteaux_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(data)
            save_msg = f'\\nSauvegardé: {filename}'
        except:
            save_msg = '\\n(Impossible de sauvegarder le fichier)'
        
        # Afficher popup avec données
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        scroll = ScrollView()
        label = Label(
            text=data + save_msg,
            font_size='11sp',
            size_hint_y=None,
            text_size=(400, None),
            halign='left',
            color=(0.2, 0.2, 0.2, 1)
        )
        label.bind(texture_size=lambda instance, value: setattr(instance, 'height', value[1]))
        scroll.add_widget(label)
        content.add_widget(scroll)
        
        btn_fermer = Button(
            text='FERMER',
            size_hint_y=None,
            height=50,
            background_color=(0.3, 0.5, 0.8, 1),
            color=(1, 1, 1, 1)
        )
        content.add_widget(btn_fermer)
        
        popup = Popup(
            title='📄 Données du Plan Exporté',
            content=content,
            size_hint=(0.95, 0.8),
            auto_dismiss=False
        )
        btn_fermer.bind(on_press=popup.dismiss)
        popup.open()
    
    def show_popup(self, title, message):
        content = BoxLayout(orientation='vertical', padding=20)
        content.add_widget(Label(text=message, font_size='14sp'))
        btn = Button(text='OK', size_hint_y=None, height=50)
        content.add_widget(btn)
        
        popup = Popup(title=title, content=content, size_hint=(0.8, 0.4))
        btn.bind(on_press=popup.dismiss)
        popup.open()


class MenuScreen(Screen):
    """Écran d'accueil"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()
    
    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=25, spacing=20)
        
        # Logo zone
        header = BoxLayout(orientation='vertical', size_hint_y=0.35, spacing=10)
        
        logo = Label(
            text='⚡',
            font_size='80sp',
            size_hint_y=0.5
        )
        header.add_widget(logo)
        
        titre = Label(
            text='ELECTRO CALC PRO',
            font_size='32sp',
            bold=True,
            color=(0.1, 0.4, 0.8, 1),
            size_hint_y=0.3
        )
        header.add_widget(titre)
        
        sous_titre = Label(
            text='Outils professionnels pour\\nétudes de réseaux électriques',
            font_size='16sp',
            color=(0.4, 0.4, 0.4, 1),
            size_hint_y=0.2,
            halign='center'
        )
        header.add_widget(sous_titre)
        
        layout.add_widget(header)
        
        # Boutons principaux
        buttons_box = BoxLayout(orientation='vertical', spacing=15, size_hint_y=0.45, padding=[20, 0])
        
        btn_calculs = Button(
            text='📊 CALCULS ÉLECTRIQUES',
            font_size='20sp',
            size_hint_y=0.45,
            background_color=(0.2, 0.6, 0.9, 1),
            color=(1, 1, 1, 1),
            bold=True
        )
        btn_calculs.bind(on_press=lambda x: setattr(self.manager, 'current', 'calculs'))
        buttons_box.add_widget(btn_calculs)
        
        btn_plan = Button(
            text='📍 PLAN DE POTEAUX',
            font_size='20sp',
            size_hint_y=0.45,
            background_color=(0.2, 0.7, 0.5, 1),
            color=(1, 1, 1, 1),
            bold=True
        )
        btn_plan.bind(on_press=lambda x: setattr(self.manager, 'current', 'plan'))
        buttons_box.add_widget(btn_plan)
        
        layout.add_widget(buttons_box)
        
        # Info footer
        footer = BoxLayout(orientation='vertical', size_hint_y=0.2, spacing=5)
        
        features = Label(
            text='✓ NFC 15-100  ✓ Chute tension  ✓ Section câble\\n✓ Plan interactif  ✓ Export données',
            font_size='13sp',
            color=(0.5, 0.5, 0.5, 1),
            halign='center'
        )
        footer.add_widget(features)
        
        version = Label(
            text='v1.0 - Application professionnelle',
            font_size='12sp',
            color=(0.6, 0.6, 0.6, 1)
        )
        footer.add_widget(version)
        
        layout.add_widget(footer)
        
        self.add_widget(layout)


class ElectroCalcApp(App):
    """Application principale"""
    
    def build(self):
        # Gestionnaire d'écrans
        sm = ScreenManager()
        
        # Ajout des écrans
        sm.add_widget(MenuScreen(name='menu'))
        sm.add_widget(CalculsElectriquesScreen(name='calculs'))
        sm.add_widget(PlanPoteauxScreen(name='plan'))
        
        return sm
    
    def on_pause(self):
        """Gestion mise en arrière-plan Android"""
        return True
    
    def on_resume(self):
        """Retour au premier plan"""
        pass


if __name__ == '__main__':
    ElectroCalcApp().run()
'''

# Sauvegarder le fichier
with open('/mnt/kimi/output/main.py', 'w', encoding='utf-8') as f:
    f.write(main_app_code)

print("✅ Fichier main.py créé (" + str(len(main_app_code)) + " caractères)")
print("📱 Application complète ÉLECTRO CALC PRO")
