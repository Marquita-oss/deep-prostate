"""
infrastructure/ui/widgets/segmentation_panel.py

Panel especializado para herramientas de segmentación médica.
Integra IA automática con nnUNet, herramientas de edición manual,
y análisis cuantitativo para detección de cáncer prostático.
"""

import asyncio
from typing import List, Optional, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, 
    QPushButton, QComboBox, QSlider, QSpinBox, QDoubleSpinBox,
    QCheckBox, QListWidget, QListWidgetItem, QTextEdit, QTabWidget,
    QProgressBar, QTableWidget, QTableWidgetItem, QMessageBox,
    QSplitter, QFrame, QScrollArea, QButtonGroup, QRadioButton
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QThread, QMutex
from PyQt6.QtGui import QColor, QPixmap, QIcon, QFont

from domain.entities.medical_image import MedicalImage
from domain.entities.segmentation import (
    MedicalSegmentation, AnatomicalRegion, SegmentationType, ConfidenceLevel
)
from application.services.segmentation_services import (
    AISegmentationService, SegmentationEditingService
)


class SegmentationWorkerThread(QThread):
    """Thread worker para operaciones de segmentación en background."""
    
    progress_updated = pyqtSignal(int, str)  # progress, message
    segmentation_completed = pyqtSignal(list)  # List[MedicalSegmentation]
    error_occurred = pyqtSignal(str)  # error message
    
    def __init__(self, ai_service, image, operation_type, parameters):
        super().__init__()
        self.ai_service = ai_service
        self.image = image
        self.operation_type = operation_type
        self.parameters = parameters
        self._mutex = QMutex()
    
    def run(self):
        """Ejecuta la operación de segmentación."""
        try:
            self.progress_updated.emit(10, "Initializing AI model...")
            
            if self.operation_type == "full_analysis":
                # Análisis completo con IA
                self.progress_updated.emit(30, "Preprocessing image...")
                
                # Simular operación (en implementación real, llamar al servicio)
                import time
                time.sleep(1)
                
                self.progress_updated.emit(60, "Running AI segmentation...")
                time.sleep(2)
                
                self.progress_updated.emit(90, "Processing results...")
                time.sleep(0.5)
                
                # En implementación real:
                # segmentations = await self.ai_service.predict_prostate_segmentation(
                #     self.image,
                #     include_zones=self.parameters.get('include_zones', True),
                #     detect_lesions=self.parameters.get('detect_lesions', True)
                # )
                
                # Por ahora, simular resultado
                segmentations = self._create_mock_segmentations()
                
                self.progress_updated.emit(100, "Complete")
                self.segmentation_completed.emit(segmentations)
                
            elif self.operation_type == "prostate_only":
                self.progress_updated.emit(50, "Segmenting prostate...")
                time.sleep(1.5)
                
                segmentations = self._create_mock_prostate_segmentation()
                self.segmentation_completed.emit(segmentations)
                
            elif self.operation_type == "lesions_only":
                self.progress_updated.emit(50, "Detecting lesions...")
                time.sleep(1)
                
                segmentations = self._create_mock_lesion_segmentations()
                self.segmentation_completed.emit(segmentations)
                
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def _create_mock_segmentations(self) -> List[MedicalSegmentation]:
        """Crea segmentaciones mock para demostración."""
        from datetime import datetime
        import numpy as np
        
        segmentations = []
        
        # Simular forma de próstata
        mock_shape = (64, 64, 32)  # Dimensiones simplificadas
        
        # Próstata completa
        prostate_mask = np.zeros(mock_shape, dtype=bool)
        prostate_mask[16:48, 16:48, 8:24] = True
        
        prostate_seg = MedicalSegmentation(
            mask_data=prostate_mask,
            anatomical_region=AnatomicalRegion.PROSTATE_WHOLE,
            segmentation_type=SegmentationType.AUTOMATIC,
            creation_date=datetime.now(),
            creator_id="nnunet_ai_system",
            confidence_score=0.92
        )
        segmentations.append(prostate_seg)
        
        # Zona periférica
        pz_mask = np.zeros(mock_shape, dtype=bool)
        pz_mask[18:46, 18:46, 9:23] = True
        pz_mask[24:40, 24:40, 12:20] = False  # Hueco central
        
        pz_seg = MedicalSegmentation(
            mask_data=pz_mask,
            anatomical_region=AnatomicalRegion.PROSTATE_PERIPHERAL_ZONE,
            segmentation_type=SegmentationType.AUTOMATIC,
            creation_date=datetime.now(),
            creator_id="nnunet_ai_system",
            confidence_score=0.87
        )
        segmentations.append(pz_seg)
        
        # Lesión sospechosa
        lesion_mask = np.zeros(mock_shape, dtype=bool)
        lesion_mask[28:35, 30:37, 14:18] = True
        
        lesion_seg = MedicalSegmentation(
            mask_data=lesion_mask,
            anatomical_region=AnatomicalRegion.SUSPICIOUS_LESION,
            segmentation_type=SegmentationType.AUTOMATIC,
            creation_date=datetime.now(),
            creator_id="nnunet_ai_system",
            confidence_score=0.74
        )
        segmentations.append(lesion_seg)
        
        return segmentations
    
    def _create_mock_prostate_segmentation(self) -> List[MedicalSegmentation]:
        """Crea solo segmentación de próstata."""
        return self._create_mock_segmentations()[:1]
    
    def _create_mock_lesion_segmentations(self) -> List[MedicalSegmentation]:
        """Crea solo segmentaciones de lesiones."""
        return self._create_mock_segmentations()[2:]


class SegmentationListWidget(QListWidget):
    """Widget de lista especializado para mostrar segmentaciones."""
    
    segmentation_selected = pyqtSignal(object)  # MedicalSegmentation
    segmentation_visibility_changed = pyqtSignal(str, bool)  # id, visible
    segmentation_deleted = pyqtSignal(str)  # id
    
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(200)
        self.setAlternatingRowColors(True)
        self.itemClicked.connect(self._on_item_clicked)
        
        # Almacenar segmentaciones
        self._segmentations: Dict[str, MedicalSegmentation] = {}
    
    def add_segmentation(self, segmentation: MedicalSegmentation) -> None:
        """Añade una segmentación a la lista."""
        # Crear item de lista
        item = QListWidgetItem()
        widget = SegmentationItemWidget(segmentation)
        
        # Conectar señales
        widget.visibility_changed.connect(
            lambda visible: self.segmentation_visibility_changed.emit(
                segmentation.segmentation_id, visible
            )
        )
        widget.delete_requested.connect(
            lambda: self.segmentation_deleted.emit(segmentation.segmentation_id)
        )
        
        # Configurar item
        item.setSizeHint(widget.sizeHint())
        self.addItem(item)
        self.setItemWidget(item, widget)
        
        # Almacenar referencia
        self._segmentations[segmentation.segmentation_id] = segmentation
    
    def remove_segmentation(self, segmentation_id: str) -> None:
        """Remueve una segmentación de la lista."""
        for i in range(self.count()):
            item = self.item(i)
            widget = self.itemWidget(item)
            if hasattr(widget, 'segmentation_id') and widget.segmentation_id == segmentation_id:
                self.takeItem(i)
                break
        
        self._segmentations.pop(segmentation_id, None)
    
    def get_segmentation(self, segmentation_id: str) -> Optional[MedicalSegmentation]:
        """Obtiene una segmentación por ID."""
        return self._segmentations.get(segmentation_id)
    
    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        """Maneja click en item de segmentación."""
        widget = self.itemWidget(item)
        if hasattr(widget, 'segmentation_id'):
            segmentation = self._segmentations.get(widget.segmentation_id)
            if segmentation:
                self.segmentation_selected.emit(segmentation)


class SegmentationItemWidget(QWidget):
    """Widget individual para mostrar información de segmentación."""
    
    visibility_changed = pyqtSignal(bool)
    delete_requested = pyqtSignal()
    
    def __init__(self, segmentation: MedicalSegmentation):
        super().__init__()
        self.segmentation = segmentation
        self.segmentation_id = segmentation.segmentation_id
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Configura la interfaz del widget."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        
        # Checkbox de visibilidad
        self.visibility_checkbox = QCheckBox()
        self.visibility_checkbox.setChecked(True)
        self.visibility_checkbox.toggled.connect(self.visibility_changed.emit)
        layout.addWidget(self.visibility_checkbox)
        
        # Color indicator
        color_label = QLabel()
        color_label.setFixedSize(16, 16)
        color = self._get_region_color()
        color_label.setStyleSheet(f"background-color: {color}; border: 1px solid #666;")
        layout.addWidget(color_label)
        
        # Información de la segmentación
        info_layout = QVBoxLayout()
        
        # Nombre de la región
        region_name = self.segmentation.anatomical_region.value.replace('_', ' ').title()
        name_label = QLabel(region_name)
        name_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        info_layout.addWidget(name_label)
        
        # Información adicional
        info_text = []
        info_text.append(f"Type: {self.segmentation.segmentation_type.value}")
        
        if self.segmentation.confidence_level:
            info_text.append(f"Confidence: {self.segmentation.confidence_level.value}")
        
        info_text.append(f"Voxels: {self.segmentation.voxel_count}")
        
        info_label = QLabel(" | ".join(info_text))
        info_label.setFont(QFont("Arial", 8))
        info_label.setStyleSheet("color: #aaa;")
        info_layout.addWidget(info_label)
        
        layout.addLayout(info_layout)
        layout.addStretch()
        
        # Botón de eliminar
        delete_button = QPushButton("×")
        delete_button.setFixedSize(20, 20)
        delete_button.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f;
                color: white;
                border: none;
                border-radius: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f44336;
            }
        """)
        delete_button.clicked.connect(self.delete_requested.emit)
        layout.addWidget(delete_button)
    
    def _get_region_color(self) -> str:
        """Obtiene color para la región anatómica."""
        color_map = {
            AnatomicalRegion.PROSTATE_WHOLE: "#CC9966",
            AnatomicalRegion.PROSTATE_PERIPHERAL_ZONE: "#66CC66",
            AnatomicalRegion.PROSTATE_TRANSITION_ZONE: "#6666CC",
            AnatomicalRegion.SUSPICIOUS_LESION: "#FFCC00",
            AnatomicalRegion.CONFIRMED_CANCER: "#FF3333",
            AnatomicalRegion.BENIGN_HYPERPLASIA: "#99CC99",
            AnatomicalRegion.URETHRA: "#CC66CC",
            AnatomicalRegion.SEMINAL_VESICLES: "#CCCC66"
        }
        
        return color_map.get(self.segmentation.anatomical_region, "#999999")


class SegmentationPanel(QWidget):
    """
    Panel principal de herramientas de segmentación médica.
    
    Integra:
    - Herramientas de IA automática
    - Edición manual de segmentaciones
    - Análisis cuantitativo
    - Gestión de segmentaciones múltiples
    """
    
    segmentation_completed = pyqtSignal(object)  # MedicalSegmentation
    ai_prediction_requested = pyqtSignal()
    
    def __init__(self, ai_service: AISegmentationService, editing_service: SegmentationEditingService):
        super().__init__()
        
        self.ai_service = ai_service
        self.editing_service = editing_service
        self.current_image: Optional[MedicalImage] = None
        self.worker_thread: Optional[SegmentationWorkerThread] = None
        
        self._setup_ui()
        self._setup_connections()
    
    def _setup_ui(self) -> None:
        """Configura la interfaz del panel."""
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        
        # Tabs principales
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Tab 1: IA Automática
        self.ai_tab = self._create_ai_tab()
        self.tab_widget.addTab(self.ai_tab, "AI Analysis")
        
        # Tab 2: Edición Manual
        self.manual_tab = self._create_manual_editing_tab()
        self.tab_widget.addTab(self.manual_tab, "Manual Editing")
        
        # Tab 3: Análisis Cuantitativo
        self.analysis_tab = self._create_analysis_tab()
        self.tab_widget.addTab(self.analysis_tab, "Quantitative Analysis")
        
        # Lista de segmentaciones (común a todos los tabs)
        seg_group = QGroupBox("Active Segmentations")
        layout.addWidget(seg_group)
        
        seg_layout = QVBoxLayout(seg_group)
        self.segmentation_list = SegmentationListWidget()
        seg_layout.addWidget(self.segmentation_list)
        
        # Botones de gestión
        buttons_layout = QHBoxLayout()
        seg_layout.addLayout(buttons_layout)
        
        self.clear_all_button = QPushButton("Clear All")
        self.clear_all_button.clicked.connect(self._clear_all_segmentations)
        buttons_layout.addWidget(self.clear_all_button)
        
        self.export_button = QPushButton("Export")
        self.export_button.clicked.connect(self._export_segmentations)
        buttons_layout.addWidget(self.export_button)
    
    def _create_ai_tab(self) -> QWidget:
        """Crea el tab de análisis con IA."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Configuración de IA
        config_group = QGroupBox("AI Configuration")
        layout.addWidget(config_group)
        
        config_layout = QVBoxLayout(config_group)
        
        # Modelo selector
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(["nnUNet Prostate v2.1", "nnUNet Prostate v2.0"])
        model_layout.addWidget(self.model_combo)
        config_layout.addLayout(model_layout)
        
        # Umbral de confianza
        conf_layout = QHBoxLayout()
        conf_layout.addWidget(QLabel("Confidence Threshold:"))
        self.confidence_slider = QSlider(Qt.Orientation.Horizontal)
        self.confidence_slider.setRange(30, 95)
        self.confidence_slider.setValue(70)
        self.confidence_slider.valueChanged.connect(self._update_confidence_label)
        conf_layout.addWidget(self.confidence_slider)
        
        self.confidence_label = QLabel("0.70")
        conf_layout.addWidget(self.confidence_label)
        config_layout.addLayout(conf_layout)
        
        # Opciones de análisis
        options_group = QGroupBox("Analysis Options")
        layout.addWidget(options_group)
        
        options_layout = QVBoxLayout(options_group)
        
        self.segment_prostate_check = QCheckBox("Segment whole prostate")
        self.segment_prostate_check.setChecked(True)
        options_layout.addWidget(self.segment_prostate_check)
        
        self.segment_zones_check = QCheckBox("Segment prostate zones")
        self.segment_zones_check.setChecked(True)
        options_layout.addWidget(self.segment_zones_check)
        
        self.detect_lesions_check = QCheckBox("Detect suspicious lesions")
        self.detect_lesions_check.setChecked(True)
        options_layout.addWidget(self.detect_lesions_check)
        
        self.calculate_pirads_check = QCheckBox("Calculate PI-RADS scoring")
        self.calculate_pirads_check.setChecked(False)
        options_layout.addWidget(self.calculate_pirads_check)
        
        # Botones de acción
        buttons_layout = QHBoxLayout()
        layout.addLayout(buttons_layout)
        
        self.run_full_analysis_button = QPushButton("Run Full Analysis")
        self.run_full_analysis_button.clicked.connect(self._run_full_analysis)
        buttons_layout.addWidget(self.run_full_analysis_button)
        
        self.run_prostate_only_button = QPushButton("Prostate Only")
        self.run_prostate_only_button.clicked.connect(self._run_prostate_only)
        buttons_layout.addWidget(self.run_prostate_only_button)
        
        self.run_lesions_only_button = QPushButton("Lesions Only")
        self.run_lesions_only_button.clicked.connect(self._run_lesions_only)
        buttons_layout.addWidget(self.run_lesions_only_button)
        
        # Progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("Ready")
        layout.addWidget(self.progress_label)
        
        layout.addStretch()
        
        return tab
    
    def _create_manual_editing_tab(self) -> QWidget:
        """Crea el tab de edición manual."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Herramientas de pincel
        brush_group = QGroupBox("Brush Tools")
        layout.addWidget(brush_group)
        
        brush_layout = QVBoxLayout(brush_group)
        
        # Modo de edición
        mode_group = QButtonGroup(self)
        mode_layout = QHBoxLayout()
        
        self.add_mode_radio = QRadioButton("Add")
        self.add_mode_radio.setChecked(True)
        mode_group.addButton(self.add_mode_radio)
        mode_layout.addWidget(self.add_mode_radio)
        
        self.remove_mode_radio = QRadioButton("Remove")
        mode_group.addButton(self.remove_mode_radio)
        mode_layout.addWidget(self.remove_mode_radio)
        
        self.replace_mode_radio = QRadioButton("Replace")
        mode_group.addButton(self.replace_mode_radio)
        mode_layout.addWidget(self.replace_mode_radio)
        
        brush_layout.addLayout(mode_layout)
        
        # Tamaño de pincel
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Brush Size:"))
        self.brush_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.brush_size_slider.setRange(1, 20)
        self.brush_size_slider.setValue(5)
        self.brush_size_slider.valueChanged.connect(self._update_brush_size_label)
        size_layout.addWidget(self.brush_size_slider)
        
        self.brush_size_label = QLabel("5px")
        size_layout.addWidget(self.brush_size_label)
        brush_layout.addLayout(size_layout)
        
        # Herramientas de forma
        shape_group = QGroupBox("Shape Tools")
        layout.addWidget(shape_group)
        
        shape_layout = QVBoxLayout(shape_group)
        
        shape_buttons_layout = QHBoxLayout()
        
        self.circle_tool_button = QPushButton("Circle")
        self.circle_tool_button.setCheckable(True)
        shape_buttons_layout.addWidget(self.circle_tool_button)
        
        self.rectangle_tool_button = QPushButton("Rectangle")
        self.rectangle_tool_button.setCheckable(True)
        shape_buttons_layout.addWidget(self.rectangle_tool_button)
        
        self.polygon_tool_button = QPushButton("Polygon")
        self.polygon_tool_button.setCheckable(True)
        shape_buttons_layout.addWidget(self.polygon_tool_button)
        
        shape_layout.addLayout(shape_buttons_layout)
        
        # Operaciones morfológicas
        morphology_group = QGroupBox("Morphological Operations")
        layout.addWidget(morphology_group)
        
        morphology_layout = QVBoxLayout(morphology_group)
        
        morph_buttons_layout = QHBoxLayout()
        
        self.dilate_button = QPushButton("Dilate")
        self.dilate_button.clicked.connect(lambda: self._apply_morphology("dilate"))
        morph_buttons_layout.addWidget(self.dilate_button)
        
        self.erode_button = QPushButton("Erode")
        self.erode_button.clicked.connect(lambda: self._apply_morphology("erode"))
        morph_buttons_layout.addWidget(self.erode_button)
        
        self.smooth_button = QPushButton("Smooth")
        self.smooth_button.clicked.connect(lambda: self._apply_morphology("smooth"))
        morph_buttons_layout.addWidget(self.smooth_button)
        
        morphology_layout.addLayout(morph_buttons_layout)
        
        # Número de iteraciones
        iter_layout = QHBoxLayout()
        iter_layout.addWidget(QLabel("Iterations:"))
        self.iterations_spinbox = QSpinBox()
        self.iterations_spinbox.setRange(1, 10)
        self.iterations_spinbox.setValue(1)
        iter_layout.addWidget(self.iterations_spinbox)
        morphology_layout.addLayout(iter_layout)
        
        layout.addStretch()
        
        return tab
    
    def _create_analysis_tab(self) -> QWidget:
        """Crea el tab de análisis cuantitativo."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Métricas geométricas
        metrics_group = QGroupBox("Geometric Metrics")
        layout.addWidget(metrics_group)
        
        metrics_layout = QVBoxLayout(metrics_group)
        
        self.metrics_table = QTableWidget(0, 2)
        self.metrics_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.metrics_table.horizontalHeader().setStretchLastSection(True)
        metrics_layout.addWidget(self.metrics_table)
        
        # Estadísticas de intensidad
        intensity_group = QGroupBox("Intensity Statistics")
        layout.addWidget(intensity_group)
        
        intensity_layout = QVBoxLayout(intensity_group)
        
        self.intensity_table = QTableWidget(0, 2)
        self.intensity_table.setHorizontalHeaderLabels(["Statistic", "Value"])
        self.intensity_table.horizontalHeader().setStretchLastSection(True)
        intensity_layout.addWidget(self.intensity_table)
        
        # Botón de actualización
        update_button = QPushButton("Update Analysis")
        update_button.clicked.connect(self._update_quantitative_analysis)
        layout.addWidget(update_button)
        
        layout.addStretch()
        
        return tab
    
    def _setup_connections(self) -> None:
        """Configura las conexiones entre widgets."""
        # Conexiones de la lista de segmentaciones
        self.segmentation_list.segmentation_selected.connect(self._on_segmentation_selected)
        self.segmentation_list.segmentation_visibility_changed.connect(self._on_visibility_changed)
        self.segmentation_list.segmentation_deleted.connect(self._on_segmentation_deleted)
    
    # Métodos públicos
    
    def set_current_image(self, image: MedicalImage) -> None:
        """Establece la imagen actual para análisis."""
        self.current_image = image
        self._enable_ai_controls(True)
    
    def add_segmentation_to_list(self, segmentation: MedicalSegmentation) -> None:
        """Añade una segmentación a la lista."""
        self.segmentation_list.add_segmentation(segmentation)
    
    def run_full_analysis(self, image: MedicalImage) -> None:
        """Ejecuta análisis completo de IA."""
        self.set_current_image(image)
        self._run_full_analysis()
    
    def segment_prostate_only(self, image: MedicalImage) -> None:
        """Ejecuta solo segmentación de próstata."""
        self.set_current_image(image)
        self._run_prostate_only()
    
    def detect_lesions_only(self, image: MedicalImage) -> None:
        """Ejecuta solo detección de lesiones."""
        self.set_current_image(image)
        self._run_lesions_only()
    
    # Métodos privados
    
    def _enable_ai_controls(self, enabled: bool) -> None:
        """Habilita/deshabilita controles de IA."""
        self.run_full_analysis_button.setEnabled(enabled)
        self.run_prostate_only_button.setEnabled(enabled)
        self.run_lesions_only_button.setEnabled(enabled)
    
    def _update_confidence_label(self, value: int) -> None:
        """Actualiza la etiqueta de confianza."""
        self.confidence_label.setText(f"{value/100:.2f}")
    
    def _update_brush_size_label(self, value: int) -> None:
        """Actualiza la etiqueta de tamaño de pincel."""
        self.brush_size_label.setText(f"{value}px")
    
    def _run_full_analysis(self) -> None:
        """Ejecuta análisis completo con IA."""
        if not self.current_image:
            QMessageBox.warning(self, "Warning", "No image loaded for analysis")
            return
        
        parameters = {
            'include_zones': self.segment_zones_check.isChecked(),
            'detect_lesions': self.detect_lesions_check.isChecked(),
            'confidence_threshold': self.confidence_slider.value() / 100.0,
            'calculate_pirads': self.calculate_pirads_check.isChecked()
        }
        
        self._start_ai_operation("full_analysis", parameters)
    
    def _run_prostate_only(self) -> None:
        """Ejecuta solo segmentación de próstata."""
        if not self.current_image:
            return
        
        parameters = {'include_zones': self.segment_zones_check.isChecked()}
        self._start_ai_operation("prostate_only", parameters)
    
    def _run_lesions_only(self) -> None:
        """Ejecuta solo detección de lesiones."""
        if not self.current_image:
            return
        
        parameters = {'confidence_threshold': self.confidence_slider.value() / 100.0}
        self._start_ai_operation("lesions_only", parameters)
    
    def _start_ai_operation(self, operation_type: str, parameters: Dict[str, Any]) -> None:
        """Inicia una operación de IA en background."""
        if self.worker_thread and self.worker_thread.isRunning():
            QMessageBox.warning(self, "Warning", "AI operation already in progress")
            return
        
        # Deshabilitar controles
        self._enable_ai_controls(False)
        
        # Mostrar progreso
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_label.setText("Starting AI analysis...")
        
        # Crear y iniciar worker thread
        self.worker_thread = SegmentationWorkerThread(
            self.ai_service, self.current_image, operation_type, parameters
        )
        
        self.worker_thread.progress_updated.connect(self._on_ai_progress_updated)
        self.worker_thread.segmentation_completed.connect(self._on_ai_segmentation_completed)
        self.worker_thread.error_occurred.connect(self._on_ai_error)
        self.worker_thread.finished.connect(self._on_ai_finished)
        
        self.worker_thread.start()
    
    def _on_ai_progress_updated(self, progress: int, message: str) -> None:
        """Maneja actualizaciones de progreso de IA."""
        self.progress_bar.setValue(progress)
        self.progress_label.setText(message)
    
    def _on_ai_segmentation_completed(self, segmentations: List[MedicalSegmentation]) -> None:
        """Maneja segmentaciones completadas por IA."""
        for segmentation in segmentations:
            self.add_segmentation_to_list(segmentation)
            self.segmentation_completed.emit(segmentation)
        
        QMessageBox.information(
            self, 
            "AI Analysis Complete", 
            f"AI analysis completed successfully.\n{len(segmentations)} segmentations created."
        )
    
    def _on_ai_error(self, error_message: str) -> None:
        """Maneja errores de IA."""
        QMessageBox.critical(self, "AI Error", f"AI analysis failed:\n{error_message}")
    
    def _on_ai_finished(self) -> None:
        """Maneja finalización de operación de IA."""
        self.progress_bar.setVisible(False)
        self.progress_label.setText("Ready")
        self._enable_ai_controls(True)
    
    def _apply_morphology(self, operation: str) -> None:
        """Aplica operación morfológica a segmentación seleccionada."""
        # En implementación real, aplicar operación a segmentación seleccionada
        QMessageBox.information(self, "Info", f"Applied {operation} operation")
    
    def _clear_all_segmentations(self) -> None:
        """Limpia todas las segmentaciones."""
        reply = QMessageBox.question(
            self, "Confirm", "Clear all segmentations?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.segmentation_list.clear()
    
    def _export_segmentations(self) -> None:
        """Exporta las segmentaciones actuales."""
        # En implementación real, abrir diálogo de exportación
        QMessageBox.information(self, "Info", "Export functionality not yet implemented")
    
    def _on_segmentation_selected(self, segmentation: MedicalSegmentation) -> None:
        """Maneja selección de segmentación."""
        self._update_quantitative_analysis_for_segmentation(segmentation)
    
    def _on_visibility_changed(self, segmentation_id: str, visible: bool) -> None:
        """Maneja cambio de visibilidad de segmentación."""
        # Señal para actualizar visualizadores
        pass
    
    def _on_segmentation_deleted(self, segmentation_id: str) -> None:
        """Maneja eliminación de segmentación."""
        self.segmentation_list.remove_segmentation(segmentation_id)
    
    def _update_quantitative_analysis(self) -> None:
        """Actualiza el análisis cuantitativo."""
        # En implementación real, actualizar con segmentación seleccionada
        pass
    
    def _update_quantitative_analysis_for_segmentation(self, segmentation: MedicalSegmentation) -> None:
        """Actualiza análisis para una segmentación específica."""
        # Limpiar tablas
        self.metrics_table.setRowCount(0)
        self.intensity_table.setRowCount(0)
        
        # Métricas geométricas
        geometric_metrics = [
            ("Volume (mm³)", f"{segmentation.voxel_count * 0.5:.2f}"),  # Mock calculation
            ("Voxel Count", str(segmentation.voxel_count)),
            ("Confidence Level", segmentation.confidence_level.value if segmentation.confidence_level else "N/A"),
            ("Region", segmentation.anatomical_region.value.replace('_', ' ').title())
        ]
        
        for i, (metric, value) in enumerate(geometric_metrics):
            self.metrics_table.insertRow(i)
            self.metrics_table.setItem(i, 0, QTableWidgetItem(metric))
            self.metrics_table.setItem(i, 1, QTableWidgetItem(value))
        
        # Estadísticas de intensidad (mock data)
        intensity_stats = [
            ("Mean Intensity", "125.4"),
            ("Std Deviation", "32.1"),
            ("Min Intensity", "45"),
            ("Max Intensity", "255"),
            ("Median", "120")
        ]
        
        for i, (stat, value) in enumerate(intensity_stats):
            self.intensity_table.insertRow(i)
            self.intensity_table.setItem(i, 0, QTableWidgetItem(stat))
            self.intensity_table.setItem(i, 1, QTableWidgetItem(value))