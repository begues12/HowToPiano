"""
Modern Theme - Configuración de estilos modernos para HowToPiano
Paleta de colores y estilos consistentes
"""

class ModernTheme:
    """Tema moderno con gradientes y diseño profesional"""
    
    # Colores principales
    PRIMARY = '#667eea'          # Púrpura moderno
    PRIMARY_DARK = '#5a67d8'     # Púrpura oscuro
    PRIMARY_LIGHT = '#7c3aed'    # Púrpura claro
    
    SECONDARY = '#48bb78'        # Verde moderno
    SECONDARY_DARK = '#38a169'   # Verde oscuro
    
    ACCENT = '#f6ad55'           # Naranja/ámbar
    ACCENT_BRIGHT = '#ed8936'    # Naranja brillante
    
    # Backgrounds
    BG_DARK = '#1a202c'          # Fondo oscuro principal
    BG_MEDIUM = '#2d3748'        # Fondo medio
    BG_LIGHT = '#4a5568'         # Fondo claro
    BG_CARD = '#2d3748'          # Fondo de tarjetas
    
    # Texto
    TEXT_PRIMARY = '#ffffff'     # Texto principal
    TEXT_SECONDARY = '#cbd5e0'   # Texto secundario
    TEXT_MUTED = '#a0aec0'       # Texto apagado
    
    # Estados
    SUCCESS = '#48bb78'          # Verde éxito
    WARNING = '#f6ad55'          # Naranja advertencia
    ERROR = '#f56565'            # Rojo error
    INFO = '#4299e1'             # Azul información
    
    # Botones
    BTN_PRIMARY_BG = '#667eea'
    BTN_PRIMARY_HOVER = '#5a67d8'
    BTN_PRIMARY_ACTIVE = '#4c51bf'
    
    BTN_SUCCESS_BG = '#48bb78'
    BTN_SUCCESS_HOVER = '#38a169'
    
    BTN_DANGER_BG = '#f56565'
    BTN_DANGER_HOVER = '#e53e3e'
    
    # Teclas de piano
    KEY_WHITE = '#f7fafc'
    KEY_WHITE_HOVER = '#edf2f7'
    KEY_BLACK = '#1a202c'
    KEY_BLACK_HOVER = '#2d3748'
    
    # Highlights
    HIGHLIGHT_NOTE = '#f6ad55'
    HIGHLIGHT_CURRENT = '#667eea'
    HIGHLIGHT_ACTIVE = '#48bb78'
    
    # Bordes
    BORDER_SUBTLE = '#4a5568'
    BORDER_DEFAULT = '#718096'
    
    # Sombras (para simular con borders)
    SHADOW_COLOR = '#000000'
    
    @staticmethod
    def gradient_bg(color1, color2):
        """Simula un gradiente con un color intermedio"""
        return color1  # tkinter no soporta gradientes nativos
    
    @staticmethod
    def get_button_style(variant='primary'):
        """Retorna estilo de botón según variante"""
        styles = {
            'primary': {
                'bg': ModernTheme.BTN_PRIMARY_BG,
                'fg': ModernTheme.TEXT_PRIMARY,
                'activebackground': ModernTheme.BTN_PRIMARY_HOVER,
                'activeforeground': ModernTheme.TEXT_PRIMARY,
                'relief': 'flat',
                'bd': 0,
                'padx': 20,
                'pady': 10,
                'cursor': 'hand2'
            },
            'success': {
                'bg': ModernTheme.BTN_SUCCESS_BG,
                'fg': ModernTheme.TEXT_PRIMARY,
                'activebackground': ModernTheme.BTN_SUCCESS_HOVER,
                'activeforeground': ModernTheme.TEXT_PRIMARY,
                'relief': 'flat',
                'bd': 0,
                'padx': 20,
                'pady': 10,
                'cursor': 'hand2'
            },
            'danger': {
                'bg': ModernTheme.BTN_DANGER_BG,
                'fg': ModernTheme.TEXT_PRIMARY,
                'activebackground': ModernTheme.BTN_DANGER_HOVER,
                'activeforeground': ModernTheme.TEXT_PRIMARY,
                'relief': 'flat',
                'bd': 0,
                'padx': 20,
                'pady': 10,
                'cursor': 'hand2'
            },
            'secondary': {
                'bg': ModernTheme.BG_LIGHT,
                'fg': ModernTheme.TEXT_PRIMARY,
                'activebackground': ModernTheme.BG_MEDIUM,
                'activeforeground': ModernTheme.TEXT_PRIMARY,
                'relief': 'flat',
                'bd': 0,
                'padx': 20,
                'pady': 10,
                'cursor': 'hand2'
            }
        }
        return styles.get(variant, styles['primary'])
    
    @staticmethod
    def get_card_style():
        """Retorna estilo de tarjeta"""
        return {
            'bg': ModernTheme.BG_CARD,
            'relief': 'flat',
            'bd': 2,
            'highlightthickness': 1,
            'highlightbackground': ModernTheme.BORDER_SUBTLE
        }
    
    @staticmethod
    def get_label_style(variant='primary'):
        """Retorna estilo de label"""
        styles = {
            'primary': {
                'bg': ModernTheme.BG_DARK,
                'fg': ModernTheme.TEXT_PRIMARY,
                'font': ('Segoe UI', 10)
            },
            'secondary': {
                'bg': ModernTheme.BG_DARK,
                'fg': ModernTheme.TEXT_SECONDARY,
                'font': ('Segoe UI', 9)
            },
            'title': {
                'bg': ModernTheme.BG_DARK,
                'fg': ModernTheme.TEXT_PRIMARY,
                'font': ('Segoe UI', 18, 'bold')
            },
            'heading': {
                'bg': ModernTheme.BG_DARK,
                'fg': ModernTheme.TEXT_PRIMARY,
                'font': ('Segoe UI', 14, 'bold')
            }
        }
        return styles.get(variant, styles['primary'])


class ModernWidgets:
    """Widgets personalizados con estilo moderno"""
    
    @staticmethod
    def create_hover_button(parent, text, command, variant='primary'):
        """Crea un botón con efecto hover"""
        import tkinter as tk
        
        style = ModernTheme.get_button_style(variant)
        btn = tk.Button(parent, text=text, command=command, **style)
        
        # Efecto hover
        original_bg = style['bg']
        hover_bg = style['activebackground']
        
        def on_enter(e):
            btn.config(bg=hover_bg)
        
        def on_leave(e):
            btn.config(bg=original_bg)
        
        btn.bind('<Enter>', on_enter)
        btn.bind('<Leave>', on_leave)
        
        return btn
    
    @staticmethod
    def create_card_frame(parent, title=None):
        """Crea un frame tipo tarjeta moderna"""
        import tkinter as tk
        
        # Frame contenedor con padding
        container = tk.Frame(parent, bg=ModernTheme.BG_DARK)
        
        # Frame de la tarjeta con estilo
        card = tk.Frame(container, **ModernTheme.get_card_style())
        card.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        if title:
            title_frame = tk.Frame(card, bg=ModernTheme.BG_CARD)
            title_frame.pack(fill=tk.X, padx=15, pady=(15, 10))
            
            tk.Label(
                title_frame,
                text=title,
                **ModernTheme.get_label_style('heading')
            ).pack(anchor=tk.W)
            
            # Línea separadora
            separator = tk.Frame(card, bg=ModernTheme.BORDER_SUBTLE, height=1)
            separator.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        return container, card
    
    @staticmethod
    def create_icon_button(parent, icon, text, command, variant='primary'):
        """Crea un botón con icono"""
        import tkinter as tk
        
        style = ModernTheme.get_button_style(variant)
        full_text = f"{icon}  {text}"
        
        return ModernWidgets.create_hover_button(parent, full_text, command, variant)
