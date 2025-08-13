#!/usr/bin/env python3
"""
infrastructure/ui/factories/ui_component_factory.py

Factory para crear y configurar componentes de interfaz médica especializados.
Este factory reutiliza widgets existentes bien desarrollados, adaptándolos para
trabajar con el nuevo patrón de inyección de dependencias y coordinación.

Responsabilidades:
- Crear instancias de widgets existentes con dependencias apropiadas
- Configurar widgets con settings médicos específicos
- Conectar widgets al sistema de eventos y coordinación
- Aplicar temas y estilos de manera centralizada
- Facilitar testing mediante configuración controlada
"""

from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import logging

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QTabWidget,
    QGroupBox, QLabel, QPushButton, QSlider, QSpinBox, QDoubleSpinBox,
    QComboBox, QCheckBox, QTextEdit, QProgressBar, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor

# Imports de widgets existentes que vamos a reutilizar y adaptar
from infrastructure.ui.widgets.image_viewer_2d import ImageViewer2D
from infrastructure.ui.widgets.segmentation_panel import SegmentationPanel
from infrastructure.ui.widgets.patient_browser import PatientBrowserPanel

# Imports de servicios y coordinación
from infrastructure.di.medical_service_container import MedicalServiceContainer
from infrastructure.coordination.workflow_coordinator import MedicalWorkflowCoordinator


class WorkstationUIComponents:
    """
    Contenedor de componentes de UI ya configurados y conectados.
    
    Esta clase actúa como un "paquete de especialistas médicos ya entrenados"
    que el main window puede usar inmediatamente sin preocuparse por los
    detalles de configuración individual de cada componente.
    """
    
    def __init__(self):
        # Paneles principales
        self.central_viewer: Optional[QWidget] = None
        self.right_panel: Optional[QWidget] = None
        self.left_panel: Optional[QWidget] = None
        self.bottom_panel: Optional[QWidget] = None
        
        # Widgets especializados (ya configurados)
        self.image_viewer_2d: Optional[ImageViewer2D] = None
        self.segmentation_panel: Optional[SegmentationPanel] = None
        self.patient_browser: Optional[PatientBrowserPanel] = None
        
        # Controles de visualización (ya configurados)
        self.window_level_controls: Optional[QWidget] = None
        self.navigation_controls: Optional[QWidget] = None
        self.measurement_tools: Optional[QWidget] = None
        
        # Paneles de información (ya configurados)
        self.image_info_panel: Optional[QWidget] = None
        self.statistics_panel: Optional[QWidget] = None
        self.progress_panel: Optional[QWidget] = None


class MedicalUIComponentFactory:
    """
    Factory para crear y configurar la interfaz médica completa.
    
    Este factory implementa el patrón Factory Method, pero con un enfoque
    inteligente: en lugar de recrear todo desde cero, toma los widgets
    especializados que ya están desarrollados y los configura apropiadamente
    para trabajar en nuestra nueva arquitectura.
    
    Ventajas de este enfoque:
    - Preserva el trabajo ya invertido en widgets especializados
    - Aplica configuración médica de manera centralizada
    - Facilita testing mediante inyección controlada de dependencias
    - Permite evolución incremental sin "big bang" rewrites
    - Mantiene separación de responsabilidades clara
    """
    
    def __init__(
        self, 
        service_container: MedicalServiceContainer,
        workflow_coordinator: MedicalWorkflowCoordinator
    ):
        """
        Inicializa el factory con acceso a servicios y coordinación.
        
        Args:
            service_container: Contenedor con servicios médicos configurados
            workflow_coordinator: Coordinador para flujos de trabajo médicos
        """
        self._services = service_container
        self._coordinator = workflow_coordinator
        self._logger = logging.getLogger(__name__)
        
        # Configuración médica centralizada
        self._medical_theme_config = self._load_medical_theme_config()
        self._widget_configurations = self._load_widget_configurations()
        
        self._logger.info("Factory de componentes UI médicos inicializado")
    
    def create_workstation_interface(self) -> WorkstationUIComponents:
        """
        Crea la interfaz completa del workstation médico.
        
        Este método orquesta la creación de todos los componentes principales,
        asegurando que estén correctamente configurados y conectados entre sí.
        Es como organizar todo el personal médico especializado para que
        trabajen de manera coordinada.
        
        Returns:
            Componentes de UI ya configurados y listos para usar
        """
        self._logger.info("Creando interfaz completa del workstation médico")
        
        components = WorkstationUIComponents()
        
        try:
            # 1. Crear panel central de visualización (reutilizando widgets existentes)
            components.central_viewer = self._create_central_viewer_panel()
            
            # 2. Crear panel derecho de herramientas médicas
            components.right_panel = self._create_right_tools_panel()
            
            # 3. Crear panel izquierdo de navegación de pacientes
            components.left_panel = self._create_left_navigation_panel()
            
            # 4. Crear panel inferior de controles (opcional)
            components.bottom_panel = self._create_bottom_controls_panel()
            
            # 5. Configurar referencias a widgets especializados para acceso directo
            self._setup_specialized_widget_references(components)
            
            # 6. Conectar todos los componentes al sistema de coordinación
            self._connect_components_to_coordination(components)
            
            # 7. Aplicar configuración médica centralizada
            self._apply_medical_configuration(components)
            
            self._logger.info("Interfaz del workstation médico creada exitosamente")
            return components
            
        except Exception as e:
            self._logger.error(f"Error creando interfaz médica: {e}")
            raise RuntimeError(f"Fallo en creación de interfaz médica: {e}")
    
    def _create_central_viewer_panel(self) -> QWidget:
        """
        Crea el panel central de visualización médica.
        
        Este panel reutiliza el ImageViewer2D existente, pero lo configura
        apropiadamente para trabajar con nuestro nuevo sistema de servicios
        y coordinación. Es como tomar a un radilogo ya entrenado y darle
        acceso a los nuevos sistemas de información del hospital.
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Crear tabs para diferentes tipos de visualización
        view_tabs = QTabWidget()
        layout.addWidget(view_tabs)
        
        # 1. Reutilizar y adaptar ImageViewer2D existente
        self._image_viewer_2d = self._create_configured_image_viewer_2d()
        view_tabs.addTab(self._image_viewer_2d, "2D Views")
        
        # 2. Crear visualizador 3D (placeholder por ahora, puede ser desarrollado después)
        volume_viewer_3d = self._create_placeholder_3d_viewer()
        view_tabs.addTab(volume_viewer_3d, "3D Volume")
        
        # 3. Añadir controles de navegación reutilizando componentes existentes
        navigation_controls = self._create_navigation_controls()
        layout.addWidget(navigation_controls)
        
        # Almacenar referencia para configuración posterior
        panel._image_viewer_2d = self._image_viewer_2d
        panel._view_tabs = view_tabs
        panel._navigation_controls = navigation_controls
        
        return panel
    
    def _create_configured_image_viewer_2d(self) -> ImageViewer2D:
        """
        Crea y configura ImageViewer2D para trabajar con nueva arquitectura.
        
        Este método toma el widget ImageViewer2D ya desarrollado y lo adapta
        para trabajar con nuestro sistema de inyección de dependencias.
        En lugar de que el widget cree sus propias dependencias, se las
        proporcionamos desde el exterior.
        """
        # Crear instancia del widget existente
        # Nota: Pasamos las dependencias que necesita desde nuestro contenedor
        image_viewer = ImageViewer2D()
        
        # Configurar el viewer con configuraciones médicas específicas
        medical_config = self._widget_configurations.get('image_viewer_2d', {})
        
        # Aplicar configuraciones de visualización médica
        if 'default_layout' in medical_config:
            layout_mode = medical_config['default_layout']
            image_viewer.set_layout_mode(layout_mode)
        
        # Configurar espaciado y tema médico
        self._apply_medical_theme_to_widget(image_viewer)
        
        # El viewer ya tiene toda la funcionalidad implementada,
        # solo necesitamos configurarlo apropiadamente
        self._logger.debug("ImageViewer2D configurado para uso médico")
        
        return image_viewer
    
    def _create_right_tools_panel(self) -> QWidget:
        """
        Crea el panel derecho con herramientas médicas especializadas.
        
        Este panel reutiliza SegmentationPanel existente y añade otros
        controles médicos necesarios, todo configurado para trabajar
        con nuestro nuevo sistema de coordinación.
        """
        panel = QWidget()
        panel.setFixedWidth(350)  # Ancho apropiado para herramientas médicas
        layout = QVBoxLayout(panel)
        
        # 1. Reutilizar y adaptar SegmentationPanel existente
        self._segmentation_panel = self._create_configured_segmentation_panel()
        layout.addWidget(self._segmentation_panel)
        
        # 2. Crear panel de información de imagen (reutilizando código existente)
        image_info_panel = self._create_image_info_panel()
        layout.addWidget(image_info_panel)
        
        # 3. Crear panel de estadísticas (reutilizando código existente)
        statistics_panel = self._create_statistics_panel()
        layout.addWidget(statistics_panel)
        
        # 4. Crear panel de progreso para operaciones IA (reutilizando código existente)
        progress_panel = self._create_progress_panel()
        layout.addWidget(progress_panel)
        
        # Almacenar referencias para acceso posterior
        panel._segmentation_panel = self._segmentation_panel
        panel._image_info_panel = image_info_panel
        panel._statistics_panel = statistics_panel
        panel._progress_panel = progress_panel
        
        return panel
    
    def _create_configured_segmentation_panel(self) -> SegmentationPanel:
        """
        Crea y configura SegmentationPanel para nueva arquitectura.
        
        Adaptamos el panel existente para que use servicios del contenedor
        en lugar de crear sus propias dependencias. Es como actualizar
        el equipamiento de un laboratorio médico sin cambiar al personal
        especializado que ya sabe usarlo.
        """
        # Crear instancia pasando servicios desde nuestro contenedor
        # En lugar de que SegmentationPanel cree sus propios servicios,
        # le proporcionamos los servicios ya configurados
        segmentation_panel = SegmentationPanel(
            ai_service=self._services.ai_segmentation_service,
            editing_service=self._services.segmentation_editing_service
        )
        
        # Aplicar configuración médica específica
        medical_config = self._widget_configurations.get('segmentation_panel', {})
        
        # Configurar umbrales de IA según estándares médicos
        if 'ai_confidence_threshold' in medical_config:
            # El panel ya tiene métodos para configurar estos valores
            pass  # Configurar umbral cuando el panel lo soporte
        
        # Aplicar tema médico
        self._apply_medical_theme_to_widget(segmentation_panel)
        
        self._logger.debug("SegmentationPanel configurado para uso médico")
        
        return segmentation_panel
    
    def _create_left_navigation_panel(self) -> QWidget:
        """
        Crea el panel izquierdo con navegación de pacientes.
        
        Reutiliza PatientBrowserPanel existente, configurándolo para
        trabajar con nuestro repositorio de imágenes desde el contenedor
        de servicios.
        """
        panel = QWidget()
        panel.setFixedWidth(300)
        layout = QVBoxLayout(panel)
        
        # Reutilizar PatientBrowserPanel existente
        # Le pasamos el repositorio desde nuestro contenedor de servicios
        self._patient_browser = PatientBrowserPanel(
            repository=self._services.image_repository
        )
        
        # Aplicar tema médico
        self._apply_medical_theme_to_widget(self._patient_browser)
        
        layout.addWidget(self._patient_browser)
        
        # Almacenar referencia
        panel._patient_browser = self._patient_browser
        
        return panel
    
    def _create_navigation_controls(self) -> QWidget:
        """
        Crea controles de navegación reutilizando código existente.
        
        Este método extrae y reutiliza la lógica de controles de navegación
        que ya estaba desarrollada en main_window.py, pero la encapsula
        en un componente independiente.
        """
        nav_frame = QFrame()
        nav_frame.setFixedHeight(60)
        nav_frame.setFrameStyle(QFrame.Shape.Box)
        
        nav_layout = QHBoxLayout(nav_frame)
        
        # Controles de slice (reutilizando lógica existente)
        nav_layout.addWidget(QLabel("Slice:"))
        slice_slider = QSlider(Qt.Orientation.Horizontal)
        slice_slider.setEnabled(False)
        nav_layout.addWidget(slice_slider)
        
        slice_label = QLabel("0 / 0")
        nav_layout.addWidget(slice_label)
        
        # Botones de navegación rápida (reutilizando código existente)
        nav_layout.addWidget(QLabel("Plane:"))
        plane_combo = QComboBox()
        plane_combo.addItems(["Axial", "Sagittal", "Coronal"])
        nav_layout.addWidget(plane_combo)
        
        # Controles de window/level (reutilizando lógica existente)
        nav_layout.addWidget(QLabel("W/L:"))
        window_slider = QSlider(Qt.Orientation.Horizontal)
        window_slider.setRange(1, 4000)
        window_slider.setValue(400)
        nav_layout.addWidget(window_slider)
        
        level_slider = QSlider(Qt.Orientation.Horizontal)
        level_slider.setRange(-1000, 3000)
        level_slider.setValue(40)
        nav_layout.addWidget(level_slider)
        
        # Almacenar referencias para conexión posterior
        nav_frame._slice_slider = slice_slider
        nav_frame._slice_label = slice_label
        nav_frame._plane_combo = plane_combo
        nav_frame._window_slider = window_slider
        nav_frame._level_slider = level_slider
        
        # Aplicar tema médico
        self._apply_medical_theme_to_widget(nav_frame)
        
        return nav_frame
    
    def _create_image_info_panel(self) -> QWidget:
        """Crea panel de información de imagen reutilizando código existente."""
        info_group = QGroupBox("Image Information")
        info_layout = QVBoxLayout(info_group)
        
        info_text = QTextEdit()
        info_text.setFixedHeight(150)
        info_text.setReadOnly(True)
        info_layout.addWidget(info_text)
        
        # Almacenar referencia para updates posteriores
        info_group._info_text = info_text
        
        self._apply_medical_theme_to_widget(info_group)
        
        return info_group
    
    def _create_statistics_panel(self) -> QWidget:
        """Crea panel de estadísticas reutilizando código existente."""
        stats_group = QGroupBox("Statistics")
        stats_layout = QVBoxLayout(stats_group)
        
        stats_text = QTextEdit()
        stats_text.setFixedHeight(100)
        stats_text.setReadOnly(True)
        stats_layout.addWidget(stats_text)
        
        # Almacenar referencia
        stats_group._stats_text = stats_text
        
        self._apply_medical_theme_to_widget(stats_group)
        
        return stats_group
    
    def _create_progress_panel(self) -> QWidget:
        """Crea panel de progreso reutilizando código existente."""
        progress_group = QGroupBox("AI Processing")
        progress_layout = QVBoxLayout(progress_group)
        
        progress_bar = QProgressBar()
        progress_bar.setVisible(False)
        progress_layout.addWidget(progress_bar)
        
        progress_label = QLabel("Ready")
        progress_layout.addWidget(progress_label)
        
        # Almacenar referencias
        progress_group._progress_bar = progress_bar
        progress_group._progress_label = progress_label
        
        self._apply_medical_theme_to_widget(progress_group)
        
        return progress_group
    
    def _create_bottom_controls_panel(self) -> QWidget:
        """Crea panel inferior opcional con controles adicionales."""
        # Por ahora retornamos None, puede ser implementado después si se necesita
        return None
    
    def _create_placeholder_3d_viewer(self) -> QWidget:
        """Crea placeholder para visualizador 3D (puede ser desarrollado después)."""
        placeholder = QLabel("3D Volume Viewer\n(Implementation in progress)")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("border: 1px solid #666; background-color: #2a2a2a;")
        return placeholder
    
    def _setup_specialized_widget_references(self, components: WorkstationUIComponents) -> None:
        """Configura referencias directas a widgets especializados."""
        # Estas referencias permiten al main window acceder directamente
        # a widgets específicos cuando sea necesario, manteniendo encapsulación
        components.image_viewer_2d = self._image_viewer_2d
        components.segmentation_panel = self._segmentation_panel
        components.patient_browser = self._patient_browser
        
        # Referencias a paneles para acceso directo
        if hasattr(components.right_panel, '_image_info_panel'):
            components.image_info_panel = components.right_panel._image_info_panel
        if hasattr(components.right_panel, '_statistics_panel'):
            components.statistics_panel = components.right_panel._statistics_panel
        if hasattr(components.right_panel, '_progress_panel'):
            components.progress_panel = components.right_panel._progress_panel
        
        if hasattr(components.central_viewer, '_navigation_controls'):
            components.navigation_controls = components.central_viewer._navigation_controls
    
    def _connect_components_to_coordination(self, components: WorkstationUIComponents) -> None:
        """
        Conecta todos los componentes al sistema de coordinación.
        
        Este método es crucial porque establece la comunicación entre
        los widgets reutilizados y nuestro nuevo sistema de coordinación.
        Es como establecer el sistema de comunicación interno en el hospital
        renovado.
        """
        # Conectar eventos del patient browser al coordinador
        if components.patient_browser:
            components.patient_browser.image_selected.connect(
                lambda series_uid: self._coordinator.start_image_loading_workflow(series_uid)
            )
        
        # Conectar eventos del segmentation panel al coordinador
        if components.segmentation_panel:
            components.segmentation_panel.ai_prediction_requested.connect(
                lambda: self._coordinator.start_ai_analysis_workflow(
                    self._get_current_image(), "full"
                )
            )
        
        # Conectar eventos del coordinador a widgets
        self._coordinator.image_loaded.connect(
            lambda image: self._update_all_components_with_image(components, image)
        )
        
        self._coordinator.ai_analysis_completed.connect(
            lambda segmentations: self._update_all_components_with_segmentations(
                components, segmentations
            )
        )
        
        # Conectar progreso de workflow a UI
        self._coordinator.workflow_progress.connect(
            lambda workflow_id, progress, message: self._update_progress_display(
                components, progress, message
            )
        )
        
        self._logger.debug("Componentes conectados al sistema de coordinación")
    
    def _apply_medical_configuration(self, components: WorkstationUIComponents) -> None:
        """Aplica configuración médica centralizada a todos los componentes."""
        # Aplicar configuraciones específicas médicas
        medical_config = self._medical_theme_config
        
        # Configurar espaciado y márgenes para uso médico
        if components.central_viewer:
            self._apply_medical_spacing(components.central_viewer)
        
        # Configurar colores y fuentes para lectura médica
        if components.right_panel:
            self._apply_medical_colors(components.right_panel)
        
        self._logger.debug("Configuración médica aplicada a componentes")
    
    # Métodos de utilidad para configuración
    
    def _load_medical_theme_config(self) -> Dict[str, Any]:
        """Carga configuración de tema médico."""
        # En implementación real, esto vendría de archivo de configuración
        return {
            'background_color': '#1a1a1a',
            'text_color': '#dcdcdc',
            'accent_color': '#0078d4',
            'medical_red': '#ff3333',
            'medical_green': '#66cc66',
            'font_size': 9,
            'font_family': 'Segoe UI'
        }
    
    def _load_widget_configurations(self) -> Dict[str, Any]:
        """Carga configuraciones específicas para widgets médicos."""
        return {
            'image_viewer_2d': {
                'default_layout': 'single',
                'enable_measurements': True,
                'show_overlays': True
            },
            'segmentation_panel': {
                'ai_confidence_threshold': 0.7,
                'show_confidence_scores': True,
                'enable_manual_editing': True
            },
            'patient_browser': {
                'auto_refresh_interval': 30,
                'show_study_previews': True
            }
        }
    
    def _apply_medical_theme_to_widget(self, widget: QWidget) -> None:
        """Aplica tema médico a un widget específico."""
        theme = self._medical_theme_config
        
        # Aplicar estilos médicos básicos
        widget.setStyleSheet(f"""
            QWidget {{
                background-color: {theme['background_color']};
                color: {theme['text_color']};
                font-family: {theme['font_family']};
                font-size: {theme['font_size']}pt;
            }}
            QGroupBox {{
                font-weight: bold;
                border: 1px solid #666;
                margin: 3px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }}
        """)
    
    def _apply_medical_spacing(self, widget: QWidget) -> None:
        """Aplica espaciado apropiado para uso médico."""
        if hasattr(widget, 'layout') and widget.layout():
            widget.layout().setSpacing(5)
            widget.layout().setContentsMargins(5, 5, 5, 5)
    
    def _apply_medical_colors(self, widget: QWidget) -> None:
        """Aplica colores médicos apropiados."""
        # Implementar colorización específica para elementos médicos
        pass
    
    # Métodos de utilidad para coordinación
    
    def _get_current_image(self):
        """Obtiene la imagen actualmente cargada."""
        # En implementación real, obtener de estado global
        return None
    
    def _update_all_components_with_image(self, components: WorkstationUIComponents, image) -> None:
        """Actualiza todos los componentes cuando se carga una nueva imagen."""
        if components.image_viewer_2d and image:
            # El ImageViewer2D ya tiene método para establecer imagen
            # components.image_viewer_2d.set_image(image, initial_slice_data)
            pass
    
    def _update_all_components_with_segmentations(
        self, 
        components: WorkstationUIComponents, 
        segmentations: List
    ) -> None:
        """Actualiza componentes cuando se completan segmentaciones."""
        if components.image_viewer_2d and segmentations:
            for segmentation in segmentations:
                # El ImageViewer2D ya tiene método para añadir segmentaciones
                # components.image_viewer_2d.add_segmentation(segmentation)
                pass
    
    def _update_progress_display(
        self, 
        components: WorkstationUIComponents, 
        progress: int, 
        message: str
    ) -> None:
        """Actualiza display de progreso."""
        if components.progress_panel:
            progress_bar = getattr(components.progress_panel, '_progress_bar', None)
            progress_label = getattr(components.progress_panel, '_progress_label', None)
            
            if progress_bar:
                progress_bar.setValue(progress)
                progress_bar.setVisible(True)
            
            if progress_label:
                progress_label.setText(message)