"""
infrastructure/ui/main_window.py

Ventana principal de la aplicación de visualización médica.
Integra todos los componentes (visualización 2D/3D, herramientas, menús)
en una interfaz cohesiva con tema oscuro profesional para uso médico.
"""

import sys
import asyncio
from typing import Optional, Dict, List, Any
from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QMenuBar, QToolBar, QStatusBar, QLabel, QPushButton, QSlider,
    QGroupBox, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox,
    QListWidget, QListWidgetItem, QTabWidget, QTextEdit,
    QProgressBar, QMessageBox, QFileDialog, QFrame
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QSize
from PyQt6.QtGui import QAction, QIcon, QFont, QPalette, QColor, QPixmap

# Importar widgets personalizados que crearemos
from infrastructure.ui.widgets.image_viewer_2d import ImageViewer2D
#from infrastructure.ui.widgets.volume_viewer_3d import VolumeViewer3D
from infrastructure.ui.widgets.segmentation_panel import SegmentationPanel
#from infrastructure.ui.widgets.measurement_tools import MeasurementToolsPanel
from infrastructure.ui.widgets.patient_browser import PatientBrowserPanel

# Importar servicios de aplicación
from application.services.image_services import (
    ImageLoadingService, ImageVisualizationService
)
from application.services.segmentation_services import (
    AISegmentationService, SegmentationEditingService
)

# Importar repositorios
from infrastructure.storage.dicom_repository import DICOMImageRepository
from infrastructure.visualization.vtk_renderer import MedicalVTKRenderer

# Importar entidades del dominio
from domain.entities.medical_image import MedicalImage
from domain.entities.segmentation import MedicalSegmentation


class MedicalImagingMainWindow(QMainWindow):
    """
    Ventana principal de la aplicación de visualización médica.
    
    Esta clase coordina todos los componentes de la aplicación:
    - Visualización 2D y 3D de imágenes médicas
    - Herramientas de segmentación manual y automática
    - Navegación de pacientes y estudios
    - Herramientas de medición y análisis
    - Integración con IA para detección de cáncer prostático
    """
    
    # Señales para comunicación entre componentes
    image_loaded = pyqtSignal(object)  # MedicalImage
    segmentation_created = pyqtSignal(object)  # MedicalSegmentation
    ai_prediction_completed = pyqtSignal(list)  # List[MedicalSegmentation]
    measurement_created = pyqtSignal(dict)  # measurement data
    
    def __init__(self, storage_path: str = "./medical_data"):
        super().__init__()
        
        # Configurar repositorios y servicios
        self._storage_path = Path(storage_path)
        self._setup_services()
        
        # Estado de la aplicación
        self._current_image: Optional[MedicalImage] = None
        self._current_segmentations: List[MedicalSegmentation] = []
        self._loading_progress = False
        
        # Configurar interfaz
        self._setup_ui()
        self._setup_dark_theme()
        self._setup_connections()
        self._setup_shortcuts()
        
        # Timer para actualizaciones periódicas
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._update_status)
        self._update_timer.start(1000)  # Actualizar cada segundo
    
    def _setup_services(self) -> None:
        """Inicializa repositorios y servicios de aplicación."""
        # Repositorio DICOM
        self._image_repository = DICOMImageRepository(str(self._storage_path))
        
        # Servicios de aplicación
        self._image_loading_service = ImageLoadingService(self._image_repository)
        self._image_visualization_service = ImageVisualizationService()
        
        # Configuración IA (en implementación real, cargar desde config)
        ai_config = {
            "model_path": "./models/nnunet_prostate",
            "confidence_threshold": 0.7,
            "preprocessing_params": {}
        }
        
        # Servicios de segmentación e IA
        self._ai_segmentation_service = AISegmentationService(
            self._image_repository, ai_config
        )
        self._segmentation_editing_service = SegmentationEditingService(
            self._image_repository
        )
        
        # Motor de renderizado 3D
        self._vtk_renderer = MedicalVTKRenderer()
    
    def _setup_ui(self) -> None:
        """Configura la interfaz de usuario principal."""
        # Configurar ventana principal
        self.setWindowTitle("Medical Imaging Workstation - Prostate Cancer Detection")
        self.setMinimumSize(1400, 900)
        self.resize(1600, 1000)
        
        # Crear widget central con splitter principal
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Splitter principal (horizontal)
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(main_splitter)
        
        # Panel izquierdo (navegación y herramientas)
        left_panel = self._create_left_panel()
        main_splitter.addWidget(left_panel)
        
        # Panel central (visualización)
        center_panel = self._create_center_panel()
        main_splitter.addWidget(center_panel)
        
        # Panel derecho (análisis y segmentación)
        right_panel = self._create_right_panel()
        main_splitter.addWidget(right_panel)
        
        # Configurar proporciones del splitter
        main_splitter.setSizes([300, 800, 300])
        main_splitter.setStretchFactor(1, 1)  # El panel central se estira
        
        # Crear menús y barras de herramientas
        self._create_menu_bar()
        self._create_tool_bars()
        self._create_status_bar()
    
    def _create_left_panel(self) -> QWidget:
        """Crea el panel izquierdo con navegación y herramientas."""
        panel = QWidget()
        panel.setFixedWidth(300)
        layout = QVBoxLayout(panel)
        
        # Panel de navegación de pacientes
        self._patient_browser = PatientBrowserPanel(self._image_repository)
        self._patient_browser.image_selected.connect(self._load_selected_image)
        layout.addWidget(self._patient_browser)
        
        # Panel de herramientas de medición
        measurement_group = QGroupBox("Measurement Tools")
        layout.addWidget(measurement_group)
        
        self._measurement_tools = MeasurementToolsPanel()
        self._measurement_tools.measurement_requested.connect(self._create_measurement)
        measurement_layout = QVBoxLayout(measurement_group)
        measurement_layout.addWidget(self._measurement_tools)
        
        # Panel de configuración de visualización
        viz_group = QGroupBox("Visualization Settings")
        layout.addWidget(viz_group)
        
        viz_layout = QVBoxLayout(viz_group)
        
        # Control de ventana/nivel
        wl_layout = QHBoxLayout()
        wl_layout.addWidget(QLabel("Window:"))
        self._window_slider = QSlider(Qt.Orientation.Horizontal)
        self._window_slider.setRange(1, 4000)
        self._window_slider.setValue(400)
        self._window_slider.valueChanged.connect(self._update_window_level)
        wl_layout.addWidget(self._window_slider)
        
        self._window_spinbox = QSpinBox()
        self._window_spinbox.setRange(1, 4000)
        self._window_spinbox.setValue(400)
        self._window_spinbox.valueChanged.connect(self._window_slider.setValue)
        wl_layout.addWidget(self._window_spinbox)
        viz_layout.addLayout(wl_layout)
        
        # Control de nivel
        level_layout = QHBoxLayout()
        level_layout.addWidget(QLabel("Level:"))
        self._level_slider = QSlider(Qt.Orientation.Horizontal)
        self._level_slider.setRange(-1000, 3000)
        self._level_slider.setValue(40)
        self._level_slider.valueChanged.connect(self._update_window_level)
        level_layout.addWidget(self._level_slider)
        
        self._level_spinbox = QSpinBox()
        self._level_spinbox.setRange(-1000, 3000)
        self._level_spinbox.setValue(40)
        self._level_spinbox.valueChanged.connect(self._level_slider.setValue)
        level_layout.addWidget(self._level_spinbox)
        viz_layout.addLayout(level_layout)
        
        # Presets de ventana/nivel
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("Preset:"))
        self._preset_combo = QComboBox()
        self._preset_combo.addItems([
            "Soft Tissue", "Bone", "Lung", "Brain", "Liver", "Custom"
        ])
        self._preset_combo.currentTextChanged.connect(self._apply_window_level_preset)
        preset_layout.addWidget(self._preset_combo)
        viz_layout.addLayout(preset_layout)
        
        # Spacer para empujar todo hacia arriba
        layout.addStretch()
        
        return panel
    
    def _create_center_panel(self) -> QWidget:
        """Crea el panel central con visualización de imágenes."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Tabs para diferentes vistas
        self._view_tabs = QTabWidget()
        layout.addWidget(self._view_tabs)
        
        # Vista 2D multi-planar
        self._image_viewer_2d = ImageViewer2D()
        self._image_viewer_2d.slice_changed.connect(self._on_slice_changed)
        self._image_viewer_2d.measurement_added.connect(self._on_2d_measurement)
        self._view_tabs.addTab(self._image_viewer_2d, "2D Views")
        
        # Vista 3D volumétrica
        self._volume_viewer_3d = VolumeViewer3D(self._vtk_renderer)
        self._volume_viewer_3d.volume_rendered.connect(self._on_volume_rendered)
        self._view_tabs.addTab(self._volume_viewer_3d, "3D Volume")
        
        # Barra de controles de navegación
        nav_frame = QFrame()
        nav_frame.setFixedHeight(50)
        nav_frame.setFrameStyle(QFrame.Shape.Box)
        layout.addWidget(nav_frame)
        
        nav_layout = QHBoxLayout(nav_frame)
        
        # Controles de slice
        nav_layout.addWidget(QLabel("Slice:"))
        self._slice_slider = QSlider(Qt.Orientation.Horizontal)
        self._slice_slider.setEnabled(False)
        self._slice_slider.valueChanged.connect(self._navigate_slice)
        nav_layout.addWidget(self._slice_slider)
        
        self._slice_label = QLabel("0 / 0")
        nav_layout.addWidget(self._slice_label)
        
        # Botones de navegación rápida
        nav_layout.addWidget(QLabel("Plane:"))
        self._plane_combo = QComboBox()
        self._plane_combo.addItems(["Axial", "Sagittal", "Coronal"])
        self._plane_combo.currentTextChanged.connect(self._change_view_plane)
        nav_layout.addWidget(self._plane_combo)
        
        return panel
    
    def _create_right_panel(self) -> QWidget:
        """Crea el panel derecho con herramientas de segmentación y análisis."""
        panel = QWidget()
        panel.setFixedWidth(300)
        layout = QVBoxLayout(panel)
        
        # Panel de segmentación con IA
        self._segmentation_panel = SegmentationPanel(
            self._ai_segmentation_service,
            self._segmentation_editing_service
        )
        self._segmentation_panel.segmentation_completed.connect(self._on_segmentation_completed)
        self._segmentation_panel.ai_prediction_requested.connect(self._run_ai_prediction)
        layout.addWidget(self._segmentation_panel)
        
        # Panel de información de imagen
        info_group = QGroupBox("Image Information")
        layout.addWidget(info_group)
        
        info_layout = QVBoxLayout(info_group)
        self._info_text = QTextEdit()
        self._info_text.setFixedHeight(150)
        self._info_text.setReadOnly(True)
        info_layout.addWidget(self._info_text)
        
        # Panel de estadísticas
        stats_group = QGroupBox("Statistics")
        layout.addWidget(stats_group)
        
        stats_layout = QVBoxLayout(stats_group)
        self._stats_text = QTextEdit()
        self._stats_text.setFixedHeight(100)
        self._stats_text.setReadOnly(True)
        stats_layout.addWidget(self._stats_text)
        
        # Panel de progreso para operaciones AI
        progress_group = QGroupBox("AI Processing")
        layout.addWidget(progress_group)
        
        progress_layout = QVBoxLayout(progress_group)
        self._progress_bar = QProgressBar()
        self._progress_bar.setVisible(False)
        progress_layout.addWidget(self._progress_bar)
        
        self._progress_label = QLabel("Ready")
        progress_layout.addWidget(self._progress_label)
        
        # Spacer
        layout.addStretch()
        
        return panel
    
    def _create_menu_bar(self) -> None:
        """Crea la barra de menús principal."""
        menubar = self.menuBar()
        
        # Menú File
        file_menu = menubar.addMenu("&File")
        
        # Acción abrir imagen/estudio
        open_action = QAction("&Open Image/Study...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.setStatusTip("Open DICOM image or study")
        open_action.triggered.connect(self._open_dicom_file)
        file_menu.addAction(open_action)
        
        # Acción importar directorio DICOM
        import_action = QAction("&Import DICOM Directory...", self)
        import_action.setShortcut("Ctrl+I")
        import_action.setStatusTip("Import DICOM directory")
        import_action.triggered.connect(self._import_dicom_directory)
        file_menu.addAction(import_action)
        
        file_menu.addSeparator()
        
        # Acción exportar
        export_action = QAction("&Export Segmentations...", self)
        export_action.setShortcut("Ctrl+E")
        export_action.setStatusTip("Export segmentations")
        export_action.triggered.connect(self._export_segmentations)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # Acción salir
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Menú View
        view_menu = menubar.addMenu("&View")
        
        # Submenú de layouts
        layout_menu = view_menu.addMenu("&Layout")
        
        single_view_action = QAction("Single View", self)
        single_view_action.triggered.connect(lambda: self._set_layout("single"))
        layout_menu.addAction(single_view_action)
        
        quad_view_action = QAction("Quad View", self)
        quad_view_action.triggered.connect(lambda: self._set_layout("quad"))
        layout_menu.addAction(quad_view_action)
        
        # Menú Tools
        tools_menu = menubar.addMenu("&Tools")
        
        # Herramientas de IA
        ai_menu = tools_menu.addMenu("&AI Analysis")
        
        segment_prostate_action = QAction("Segment Prostate", self)
        segment_prostate_action.triggered.connect(self._segment_prostate_ai)
        ai_menu.addAction(segment_prostate_action)
        
        detect_lesions_action = QAction("Detect Lesions", self)
        detect_lesions_action.triggered.connect(self._detect_lesions_ai)
        ai_menu.addAction(detect_lesions_action)
        
        # Menú Help
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _create_tool_bars(self) -> None:
        """Crea las barras de herramientas."""
        # Toolbar principal
        main_toolbar = self.addToolBar("Main")
        main_toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        
        # Botón abrir
        open_btn = QPushButton("Open")
        open_btn.setToolTip("Open DICOM file or directory")
        open_btn.clicked.connect(self._open_dicom_file)
        main_toolbar.addWidget(open_btn)
        
        main_toolbar.addSeparator()
        
        # Botón segmentación AI
        ai_btn = QPushButton("AI Analysis")
        ai_btn.setToolTip("Run AI segmentation")
        ai_btn.clicked.connect(self._run_full_ai_analysis)
        main_toolbar.addWidget(ai_btn)
        
        # Toolbar de medición
        measurement_toolbar = self.addToolBar("Measurement")
        
        distance_btn = QPushButton("Distance")
        distance_btn.setCheckable(True)
        distance_btn.clicked.connect(lambda: self._set_measurement_mode("distance"))
        measurement_toolbar.addWidget(distance_btn)
        
        angle_btn = QPushButton("Angle")
        angle_btn.setCheckable(True)
        angle_btn.clicked.connect(lambda: self._set_measurement_mode("angle"))
        measurement_toolbar.addWidget(angle_btn)
        
        roi_btn = QPushButton("ROI")
        roi_btn.setCheckable(True)
        roi_btn.clicked.connect(lambda: self._set_measurement_mode("roi"))
        measurement_toolbar.addWidget(roi_btn)
    
    def _create_status_bar(self) -> None:
        """Crea la barra de estado."""
        self._status_bar = self.statusBar()
        
        # Etiquetas de estado
        self._status_patient = QLabel("No patient loaded")
        self._status_bar.addWidget(self._status_patient)
        
        self._status_bar.addPermanentWidget(QLabel("|"))
        
        self._status_coordinates = QLabel("Position: ---")
        self._status_bar.addPermanentWidget(self._status_coordinates)
        
        self._status_bar.addPermanentWidget(QLabel("|"))
        
        self._status_intensity = QLabel("Intensity: ---")
        self._status_bar.addPermanentWidget(self._status_intensity)
    
    def _setup_dark_theme(self) -> None:
        """Configura el tema oscuro profesional para uso médico."""
        # Configurar palette oscuro
        palette = QPalette()
        
        # Colores principales
        bg_color = QColor(45, 45, 48)           # Fondo principal
        alt_bg_color = QColor(60, 60, 65)       # Fondo alternativo
        text_color = QColor(220, 220, 220)      # Texto principal
        disabled_color = QColor(120, 120, 120)  # Texto deshabilitado
        highlight_color = QColor(0, 120, 215)   # Selección/resaltado
        
        # Aplicar colores al palette
        palette.setColor(QPalette.ColorRole.Window, bg_color)
        palette.setColor(QPalette.ColorRole.WindowText, text_color)
        palette.setColor(QPalette.ColorRole.Base, alt_bg_color)
        palette.setColor(QPalette.ColorRole.AlternateBase, bg_color)
        palette.setColor(QPalette.ColorRole.Text, text_color)
        palette.setColor(QPalette.ColorRole.Disabled, QPalette.ColorRole.Text, disabled_color)
        palette.setColor(QPalette.ColorRole.Button, bg_color)
        palette.setColor(QPalette.ColorRole.ButtonText, text_color)
        palette.setColor(QPalette.ColorRole.Highlight, highlight_color)
        palette.setColor(QPalette.ColorRole.HighlightedText, text_color)
        
        self.setPalette(palette)
        
        # Stylesheet adicional para componentes específicos
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2d2d30;
                color: #dcdcdc;
            }
            QMenuBar {
                background-color: #3c3c3f;
                color: #dcdcdc;
                border-bottom: 1px solid #555;
            }
            QMenuBar::item:selected {
                background-color: #0078d4;
            }
            QMenu {
                background-color: #3c3c3f;
                color: #dcdcdc;
                border: 1px solid #555;
            }
            QMenu::item:selected {
                background-color: #0078d4;
            }
            QToolBar {
                background-color: #3c3c3f;
                border: 1px solid #555;
                spacing: 3px;
            }
            QStatusBar {
                background-color: #3c3c3f;
                color: #dcdcdc;
                border-top: 1px solid #555;
            }
            QGroupBox {
                color: #dcdcdc;
                border: 2px solid #555;
                border-radius: 5px;
                margin-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #404040;
                border: 1px solid #666;
                border-radius: 3px;
                padding: 5px 10px;
                color: #dcdcdc;
            }
            QPushButton:hover {
                background-color: #505050;
                border-color: #0078d4;
            }
            QPushButton:pressed {
                background-color: #0078d4;
            }
            QPushButton:checked {
                background-color: #0078d4;
                border-color: #106ebe;
            }
            QSlider::groove:horizontal {
                border: 1px solid #999;
                height: 8px;
                background: #404040;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #0078d4;
                border: 1px solid #106ebe;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QComboBox {
                background-color: #404040;
                border: 1px solid #666;
                border-radius: 3px;
                padding: 3px;
                color: #dcdcdc;
            }
            QComboBox:hover {
                border-color: #0078d4;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #dcdcdc;
            }
            QSpinBox, QDoubleSpinBox {
                background-color: #404040;
                border: 1px solid #666;
                border-radius: 3px;
                padding: 3px;
                color: #dcdcdc;
            }
            QTextEdit, QListWidget {
                background-color: #3c3c41;
                border: 1px solid #666;
                border-radius: 3px;
                color: #dcdcdc;
            }
            QTabWidget::pane {
                border: 1px solid #666;
                background-color: #2d2d30;
            }
            QTabBar::tab {
                background-color: #404040;
                border: 1px solid #666;
                padding: 8px 12px;
                margin-right: 2px;
                color: #dcdcdc;
            }
            QTabBar::tab:selected {
                background-color: #0078d4;
                border-color: #106ebe;
            }
            QTabBar::tab:hover {
                background-color: #505050;
            }
            QProgressBar {
                border: 1px solid #666;
                border-radius: 3px;
                text-align: center;
                color: #dcdcdc;
            }
            QProgressBar::chunk {
                background-color: #0078d4;
                border-radius: 2px;
            }
        """)
    
    def _setup_connections(self) -> None:
        """Configura las conexiones entre señales y slots."""
        # Conectar señales internas
        self.image_loaded.connect(self._update_image_info)
        self.segmentation_created.connect(self._update_segmentation_display)
        
        # Conectar sliders con spinboxes
        self._window_slider.valueChanged.connect(self._window_spinbox.setValue)
        self._window_spinbox.valueChanged.connect(self._window_slider.setValue)
        self._level_slider.valueChanged.connect(self._level_spinbox.setValue)
        self._level_spinbox.valueChanged.connect(self._level_slider.setValue)
    
    def _setup_shortcuts(self) -> None:
        """Configura atajos de teclado médicos estándar."""
        # Atajos de navegación rápida
        from PyQt6.QtGui import QKeySequence, QShortcut
        
        # Cambio rápido de vistas
        QShortcut(QKeySequence("1"), self, lambda: self._view_tabs.setCurrentIndex(0))
        QShortcut(QKeySequence("2"), self, lambda: self._view_tabs.setCurrentIndex(1))
        
        # Navegación de slices
        QShortcut(QKeySequence("Up"), self, self._previous_slice)
        QShortcut(QKeySequence("Down"), self, self._next_slice)
        QShortcut(QKeySequence("Page Up"), self, lambda: self._jump_slices(-10))
        QShortcut(QKeySequence("Page Down"), self, lambda: self._jump_slices(10))
        
        # Herramientas rápidas
        QShortcut(QKeySequence("M"), self, lambda: self._set_measurement_mode("distance"))
        QShortcut(QKeySequence("A"), self, lambda: self._set_measurement_mode("angle"))
        QShortcut(QKeySequence("R"), self, lambda: self._set_measurement_mode("roi"))
        
        # AI shortcuts
        QShortcut(QKeySequence("Ctrl+Shift+A"), self, self._run_full_ai_analysis)
    
    # Métodos de funcionalidad principal
    
    async def _load_selected_image(self, series_uid: str) -> None:
        """Carga una imagen seleccionada del navegador de pacientes."""
        try:
            self._show_loading(f"Loading image {series_uid}...")
            
            # Cargar imagen usando el servicio
            image = await self._image_loading_service.load_image_by_series_uid(series_uid)
            
            if image is None:
                QMessageBox.warning(self, "Error", f"Could not load image {series_uid}")
                return
            
            # Actualizar estado actual
            self._current_image = image
            self._current_segmentations.clear()
            
            # Actualizar visualizadores
            await self._update_image_viewers(image)
            
            # Configurar controles de navegación
            self._setup_slice_navigation(image)
            
            # Emitir señal
            self.image_loaded.emit(image)
            
            self._hide_loading()
            self.statusBar().showMessage(f"Loaded: {image.patient_id} - {image.series_instance_uid}", 3000)
            
        except Exception as e:
            self._hide_loading()
            QMessageBox.critical(self, "Loading Error", f"Failed to load image: {str(e)}")
    
    async def _update_image_viewers(self, image: MedicalImage) -> None:
        """Actualiza todos los visualizadores con la nueva imagen."""
        # Preparar imagen para visualización 2D
        axial_slice = await self._image_visualization_service.prepare_slice_for_display(
            image, ImagePlaneType.AXIAL, image.dimensions[0] // 2
        )
        
        # Actualizar visualizador 2D
        self._image_viewer_2d.set_image(image, axial_slice)
        
        # Preparar y actualizar visualizador 3D
        volume_data = await self._image_visualization_service.prepare_volume_for_3d(
            image, downsample_factor=2  # Optimizar para renderizado fluido
        )
        
        volume_id = await self._vtk_renderer.render_volume(image, "composite")
        self._volume_viewer_3d.set_volume_data(volume_data, volume_id)
    
    def _setup_slice_navigation(self, image: MedicalImage) -> None:
        """Configura los controles de navegación de slices."""
        if len(image.dimensions) >= 3:
            max_slices = image.dimensions[0]  # Profundidad (axial por defecto)
            self._slice_slider.setMaximum(max_slices - 1)
            self._slice_slider.setValue(max_slices // 2)
            self._slice_slider.setEnabled(True)
            self._slice_label.setText(f"{max_slices // 2} / {max_slices - 1}")
        else:
            self._slice_slider.setEnabled(False)
            self._slice_label.setText("0 / 0")
    
    def _update_window_level(self) -> None:
        """Actualiza la configuración de ventana y nivel."""
        if not self._current_image:
            return
        
        window = self._window_slider.value()
        level = self._level_slider.value()
        
        # Actualizar imagen del dominio
        self._current_image.set_window_level(window, level)
        
        # Actualizar visualizadores
        self._image_viewer_2d.update_window_level(window, level)
        self._volume_viewer_3d.update_window_level(window, level)
        
        # Sincronizar controles
        self._window_spinbox.blockSignals(True)
        self._level_spinbox.blockSignals(True)
        self._window_spinbox.setValue(window)
        self._level_spinbox.setValue(level)
        self._window_spinbox.blockSignals(False)
        self._level_spinbox.blockSignals(False)
    
    async def _apply_window_level_preset(self, preset_name: str) -> None:
        """Aplica un preset predefinido de ventana/nivel."""
        if not self._current_image or preset_name == "Custom":
            return
        
        try:
            preset_mapping = {
                "Soft Tissue": "soft_tissue",
                "Bone": "bone", 
                "Lung": "lung",
                "Brain": "brain",
                "Liver": "liver"
            }
            
            preset_key = preset_mapping.get(preset_name)
            if preset_key:
                wl = await self._image_visualization_service.apply_window_level_preset(
                    self._current_image, preset_key
                )
                
                # Actualizar controles
                self._window_slider.setValue(int(wl.window))
                self._level_slider.setValue(int(wl.level))
                
        except Exception as e:
            QMessageBox.warning(self, "Preset Error", f"Could not apply preset: {str(e)}")
    
    def _run_ai_prediction(self) -> None:
        """Ejecuta predicción de IA en background thread."""
        if not self._current_image:
            QMessageBox.warning(self, "AI Error", "No image loaded for AI analysis")
            return
        
        # Crear worker thread para IA
        self._ai_worker = AIWorkerThread(
            self._current_image,
            self._ai_segmentation_service
        )
        self._ai_worker.prediction_completed.connect(self._on_ai_prediction_completed)
        self._ai_worker.progress_updated.connect(self._update_ai_progress)
        self._ai_worker.error_occurred.connect(self._on_ai_error)
        
        # Mostrar progreso
        self._show_ai_progress("Running AI analysis...")
        self._ai_worker.start()
    
    def _run_full_ai_analysis(self) -> None:
        """Ejecuta análisis completo de IA (próstata + lesiones)."""
        if not self._current_image:
            QMessageBox.warning(self, "AI Error", "No image loaded for AI analysis")
            return
        
        self._segmentation_panel.run_full_analysis(self._current_image)
    
    def _segment_prostate_ai(self) -> None:
        """Ejecuta solo segmentación de próstata."""
        if not self._current_image:
            QMessageBox.warning(self, "AI Error", "No image loaded for AI analysis")
            return
        
        self._segmentation_panel.segment_prostate_only(self._current_image)
    
    def _detect_lesions_ai(self) -> None:
        """Ejecuta solo detección de lesiones."""
        if not self._current_image:
            QMessageBox.warning(self, "AI Error", "No image loaded for AI analysis")
            return
        
        self._segmentation_panel.detect_lesions_only(self._current_image)
    
    def _navigate_slice(self, slice_index: int) -> None:
        """Navega a un slice específico."""
        if not self._current_image:
            return
        
        try:
            plane_map = {
                "Axial": ImagePlaneType.AXIAL,
                "Sagittal": ImagePlaneType.SAGITTAL,
                "Coronal": ImagePlaneType.CORONAL
            }
            
            current_plane = plane_map[self._plane_combo.currentText()]
            
            # Preparar nuevo slice
            slice_data = self._image_visualization_service.prepare_slice_for_display(
                self._current_image, current_plane, slice_index
            )
            
            # Actualizar visualizador 2D
            self._image_viewer_2d.update_slice(slice_data, slice_index)
            
            # Actualizar etiqueta
            max_slices = self._slice_slider.maximum() + 1
            self._slice_label.setText(f"{slice_index} / {max_slices - 1}")
            
        except Exception as e:
            print(f"Error navegando slice: {e}")
    
    def _change_view_plane(self, plane_name: str) -> None:
        """Cambia el plano de visualización."""
        if not self._current_image:
            return
        
        # Reconfigurar slider para el nuevo plano
        plane_dims = {
            "Axial": self._current_image.dimensions[0],     # depth
            "Sagittal": self._current_image.dimensions[2],  # width  
            "Coronal": self._current_image.dimensions[1]    # height
        }
        
        max_slices = plane_dims.get(plane_name, 1)
        self._slice_slider.setMaximum(max_slices - 1)
        self._slice_slider.setValue(max_slices // 2)
        
        # Navegar al slice central del nuevo plano
        self._navigate_slice(max_slices // 2)
    
    def _previous_slice(self) -> None:
        """Navega al slice anterior."""
        current = self._slice_slider.value()
        if current > 0:
            self._slice_slider.setValue(current - 1)
    
    def _next_slice(self) -> None:
        """Navega al slice siguiente."""
        current = self._slice_slider.value()
        if current < self._slice_slider.maximum():
            self._slice_slider.setValue(current + 1)
    
    def _jump_slices(self, delta: int) -> None:
        """Salta múltiples slices."""
        current = self._slice_slider.value()
        new_value = max(0, min(self._slice_slider.maximum(), current + delta))
        self._slice_slider.setValue(new_value)
    
    def _set_measurement_mode(self, mode: str) -> None:
        """Configura el modo de medición activo."""
        self._measurement_tools.set_active_mode(mode)
        self._image_viewer_2d.set_measurement_mode(mode)
        self._volume_viewer_3d.set_measurement_mode(mode)
    
    def _set_layout(self, layout_type: str) -> None:
        """Cambia el layout de visualización."""
        if layout_type == "single":
            self._image_viewer_2d.set_layout_mode("single")
        elif layout_type == "quad":
            self._image_viewer_2d.set_layout_mode("quad")
    
    def _create_measurement(self, measurement_data: Dict[str, Any]) -> None:
        """Crea una nueva medición."""
        measurement_type = measurement_data.get("type")
        points = measurement_data.get("points", [])
        
        if measurement_type == "distance" and len(points) >= 2:
            # Crear medición de distancia
            distance = np.linalg.norm(np.array(points[1]) - np.array(points[0]))
            
            # Añadir a visualizadores
            self._image_viewer_2d.add_measurement(measurement_data)
            
            if len(points[0]) == 3:  # Puntos 3D
                self._vtk_renderer.create_3d_measurement(points, measurement_type)
            
            self.measurement_created.emit({
                "type": measurement_type,
                "value": distance,
                "points": points,
                "units": "mm"
            })
    
    # Métodos de eventos y callbacks
    
    def _on_slice_changed(self, slice_index: int) -> None:
        """Maneja cambios de slice desde el visualizador 2D."""
        self._slice_slider.setValue(slice_index)
    
    def _on_2d_measurement(self, measurement_data: Dict[str, Any]) -> None:
        """Maneja mediciones creadas en la vista 2D."""
        self._create_measurement(measurement_data)
    
    def _on_volume_rendered(self, volume_id: str) -> None:
        """Maneja cuando se completa el renderizado 3D."""
        self.statusBar().showMessage(f"3D volume rendered: {volume_id}", 2000)
    
    def _on_segmentation_completed(self, segmentation: MedicalSegmentation) -> None:
        """Maneja segmentaciones completadas."""
        self._current_segmentations.append(segmentation)
        
        # Añadir a visualizadores
        self._image_viewer_2d.add_segmentation(segmentation)
        
        if self._current_image:
            self._vtk_renderer.add_segmentation_surface(
                segmentation, 
                self._current_image.spacing
            )
        
        self.segmentation_created.emit(segmentation)
    
    def _on_ai_prediction_completed(self, segmentations: List[MedicalSegmentation]) -> None:
        """Maneja predicciones de IA completadas."""
        self._hide_ai_progress()
        
        for seg in segmentations:
            self._on_segmentation_completed(seg)
        
        self.ai_prediction_completed.emit(segmentations)
        
        QMessageBox.information(
            self, 
            "AI Analysis Complete", 
            f"AI analysis completed. Found {len(segmentations)} regions."
        )
    
    def _on_ai_error(self, error_message: str) -> None:
        """Maneja errores en predicciones de IA."""
        self._hide_ai_progress()
        QMessageBox.critical(self, "AI Error", f"AI analysis failed: {error_message}")
    
    def _update_ai_progress(self, progress: int, message: str) -> None:
        """Actualiza el progreso de IA."""
        self._progress_bar.setValue(progress)
        self._progress_label.setText(message)
    
    def _update_image_info(self, image: MedicalImage) -> None:
        """Actualiza el panel de información de imagen."""
        info_text = f"""
        <b>Patient ID:</b> {image.patient_id}<br>
        <b>Study UID:</b> {image.study_instance_uid}<br>
        <b>Series UID:</b> {image.series_instance_uid}<br>
        <b>Modality:</b> {image.modality.value}<br>
        <b>Acquisition Date:</b> {image.acquisition_date.strftime('%Y-%m-%d %H:%M:%S')}<br>
        <b>Dimensions:</b> {' × '.join(map(str, image.dimensions))}<br>
        <b>Spacing:</b> {image.spacing.x:.2f} × {image.spacing.y:.2f} × {image.spacing.z:.2f} mm<br>
        <b>Physical Size:</b> {' × '.join(f'{dim:.1f}' for dim in image.get_physical_dimensions())} mm
        """
        
        self._info_text.setHtml(info_text)
        
        # Actualizar estadísticas
        stats = image.get_intensity_statistics()
        stats_text = f"""
        <b>Intensity Range:</b> {stats['min']:.0f} - {stats['max']:.0f}<br>
        <b>Mean:</b> {stats['mean']:.1f}<br>
        <b>Std Dev:</b> {stats['std']:.1f}<br>
        <b>Median:</b> {stats['median']:.1f}
        """
        
        self._stats_text.setHtml(stats_text)
    
    def _update_segmentation_display(self, segmentation: MedicalSegmentation) -> None:
        """Actualiza la visualización cuando se añade una segmentación."""
        self._segmentation_panel.add_segmentation_to_list(segmentation)
    
    # Métodos de interfaz
    
    def _show_loading(self, message: str) -> None:
        """Muestra indicador de carga."""
        self._loading_progress = True
        self.statusBar().showMessage(message)
        self.setCursor(Qt.CursorShape.WaitCursor)
    
    def _hide_loading(self) -> None:
        """Oculta indicador de carga."""
        self._loading_progress = False
        self.setCursor(Qt.CursorShape.ArrowCursor)
    
    def _show_ai_progress(self, message: str) -> None:
        """Muestra progreso de IA."""
        self._progress_bar.setVisible(True)
        self._progress_bar.setValue(0)
        self._progress_label.setText(message)
    
    def _hide_ai_progress(self) -> None:
        """Oculta progreso de IA."""
        self._progress_bar.setVisible(False)
        self._progress_label.setText("Ready")
    
    # Métodos de menú
    
    def _open_dicom_file(self) -> None:
        """Abre un archivo DICOM individual."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open DICOM File",
            "",
            "DICOM Files (*.dcm *.dicom *.ima);;All Files (*)"
        )
        
        if file_path:
            # TODO: Implementar carga de archivo DICOM individual
            QMessageBox.information(self, "Info", f"Would load: {file_path}")
    
    def _import_dicom_directory(self) -> None:
        """Importa un directorio completo de archivos DICOM."""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select DICOM Directory"
        )
        
        if dir_path:
            # TODO: Implementar importación de directorio DICOM
            QMessageBox.information(self, "Info", f"Would import: {dir_path}")
    
    def _export_segmentations(self) -> None:
        """Exporta las segmentaciones actuales."""
        if not self._current_segmentations:
            QMessageBox.warning(self, "Export Error", "No segmentations to export")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Segmentations",
            "",
            "NIFTI Files (*.nii *.nii.gz);;All Files (*)"
        )
        
        if file_path:
            # TODO: Implementar exportación de segmentaciones
            QMessageBox.information(self, "Info", f"Would export to: {file_path}")
    
    def _show_about(self) -> None:
        """Muestra el diálogo Acerca de."""
        QMessageBox.about(
            self,
            "About Medical Imaging Workstation",
            """
            <h3>Medical Imaging Workstation</h3>
            <p>Professional medical imaging software for prostate cancer detection and analysis.</p>
            <p><b>Features:</b></p>
            <ul>
            <li>DICOM image visualization (2D/3D)</li>
            <li>AI-powered segmentation with nnUNet</li>
            <li>Advanced measurement tools</li>
            <li>Prostate cancer detection and analysis</li>
            </ul>
            <p><b>Version:</b> 1.0.0</p>
            <p><b>Architecture:</b> Clean Architecture / Hexagonal</p>
            """
        )
    
    def _update_status(self) -> None:
        """Actualiza información en la barra de estado."""
        if self._current_image:
            patient_text = f"Patient: {self._current_image.patient_id}"
            self._status_patient.setText(patient_text)
        else:
            self._status_patient.setText("No patient loaded")
    
    # Método de cierre
    
    def closeEvent(self, event) -> None:
        """Maneja el cierre de la aplicación."""
        reply = QMessageBox.question(
            self,
            "Confirm Exit",
            "Are you sure you want to exit?\nAny unsaved work will be lost.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Limpiar recursos VTK
            self._vtk_renderer.clear_all()
            event.accept()
        else:
            event.ignore()


# Worker thread para operaciones de IA
class AIWorkerThread(QThread):
    """Thread worker para ejecutar operaciones de IA en background."""
    
    prediction_completed = pyqtSignal(list)  # List[MedicalSegmentation]
    progress_updated = pyqtSignal(int, str)  # progress, message
    error_occurred = pyqtSignal(str)  # error message
    
    def __init__(self, image: MedicalImage, ai_service: AISegmentationService):
        super().__init__()
        self._image = image
        self._ai_service = ai_service
    
    def run(self) -> None:
        """Ejecuta la predicción de IA."""
        try:
            self.progress_updated.emit(10, "Preprocessing image...")
            
            # Simular progreso de procesamiento
            import time
            time.sleep(1)
            
            self.progress_updated.emit(30, "Running AI model...")
            time.sleep(2)
            
            self.progress_updated.emit(70, "Processing results...")
            
            # En implementación real, llamar al servicio de IA
            # segmentations = await self._ai_service.predict_prostate_segmentation(
            #     self._image, include_zones=True, detect_lesions=True
            # )
            
            # Por ahora, simular resultado
            segmentations = []
            
            self.progress_updated.emit(100, "Complete")
            self.prediction_completed.emit(segmentations)
            
        except Exception as e:
            self.error_occurred.emit(str(e))


# Crear clases para widgets personalizados (placeholders)
class ImageViewer2D(QWidget):
    slice_changed = pyqtSignal(int)
    measurement_added = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("2D Image Viewer - Implementation in progress"))


class VolumeViewer3D(QWidget):
    volume_rendered = pyqtSignal(str)
    
    def __init__(self, vtk_renderer):
        super().__init__()
        self._vtk_renderer = vtk_renderer
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("3D Volume Viewer - Implementation in progress"))


class SegmentationPanel(QWidget):
    segmentation_completed = pyqtSignal(object)
    ai_prediction_requested = pyqtSignal()
    
    def __init__(self, ai_service, editing_service):
        super().__init__()
        self._ai_service = ai_service
        self._editing_service = editing_service
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Segmentation Panel - Implementation in progress"))


class MeasurementToolsPanel(QWidget):
    measurement_requested = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Measurement Tools - Implementation in progress"))


class PatientBrowserPanel(QWidget):
    image_selected = pyqtSignal(str)
    
    def __init__(self, repository):
        super().__init__()
        self._repository = repository
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Patient Browser - Implementation in progress"))