"""
infrastructure/ui/widgets/patient_browser.py

Widget de navegación de pacientes y estudios DICOM.
Proporciona interfaz jerárquica para explorar datos médicos
organizados por paciente > estudio > serie.
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QLabel, QPushButton, QLineEdit, QComboBox, QGroupBox, QSplitter,
    QTextEdit, QProgressBar, QMessageBox, QMenu, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QThread, pyqtSlot
from PyQt6.QtGui import QAction, QIcon, QFont, QPixmap

from ....domain.entities.medical_image import MedicalImage, ImageModalityType
from ....infrastructure.storage.dicom_repository import DICOMImageRepository


class PatientDataLoader(QThread):
    """Thread worker para cargar datos de pacientes en background."""
    
    data_loaded = pyqtSignal(dict)  # patient_data
    progress_updated = pyqtSignal(int, str)  # progress, message
    error_occurred = pyqtSignal(str)  # error message
    
    def __init__(self, repository: DICOMImageRepository, search_params: Dict[str, Any]):
        super().__init__()
        self.repository = repository
        self.search_params = search_params
    
    def run(self):
        """Carga datos de pacientes según parámetros de búsqueda."""
        try:
            self.progress_updated.emit(10, "Scanning DICOM repository...")
            
            # Simular carga de datos (en implementación real, usar repositorio)
            import time
            time.sleep(0.5)
            
            self.progress_updated.emit(30, "Loading patient list...")
            
            # Generar datos de demostración
            demo_data = self._generate_demo_data()
            
            self.progress_updated.emit(80, "Organizing studies...")
            time.sleep(0.3)
            
            self.progress_updated.emit(100, "Complete")
            self.data_loaded.emit(demo_data)
            
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def _generate_demo_data(self) -> Dict[str, Any]:
        """Genera datos de demostración para el navegador."""
        return {
            "patients": {
                "PATIENT_001": {
                    "patient_name": "Demo Patient 1",
                    "patient_id": "PATIENT_001",
                    "birth_date": "1970-05-15",
                    "sex": "M",
                    "studies": {
                        "1.2.3.4.5.001": {
                            "study_uid": "1.2.3.4.5.001",
                            "study_date": "2024-01-15",
                            "study_time": "14:30:00",
                            "study_description": "MRI Prostate with Contrast",
                            "modality": "MRI",
                            "series": {
                                "1.2.3.4.5.001.1": {
                                    "series_uid": "1.2.3.4.5.001.1",
                                    "series_number": "1",
                                    "series_description": "T2W Axial",
                                    "modality": "MRI",
                                    "images_count": 32,
                                    "slice_thickness": "3.0mm"
                                },
                                "1.2.3.4.5.001.2": {
                                    "series_uid": "1.2.3.4.5.001.2", 
                                    "series_number": "2",
                                    "series_description": "DWI b=1000",
                                    "modality": "MRI",
                                    "images_count": 24,
                                    "slice_thickness": "3.0mm"
                                }
                            }
                        }
                    }
                },
                "PATIENT_002": {
                    "patient_name": "Demo Patient 2",
                    "patient_id": "PATIENT_002", 
                    "birth_date": "1965-11-22",
                    "sex": "M",
                    "studies": {
                        "1.2.3.4.5.002": {
                            "study_uid": "1.2.3.4.5.002",
                            "study_date": "2024-01-20",
                            "study_time": "10:15:00",
                            "study_description": "CT Pelvis without Contrast",
                            "modality": "CT",
                            "series": {
                                "1.2.3.4.5.002.1": {
                                    "series_uid": "1.2.3.4.5.002.1",
                                    "series_number": "1", 
                                    "series_description": "Axial CT 1.25mm",
                                    "modality": "CT",
                                    "images_count": 128,
                                    "slice_thickness": "1.25mm"
                                }
                            }
                        }
                    }
                }
            }
        }


class PatientTreeWidget(QTreeWidget):
    """Widget de árbol especializado para navegación de pacientes."""
    
    patient_selected = pyqtSignal(str)  # patient_id
    study_selected = pyqtSignal(str)    # study_uid
    series_selected = pyqtSignal(str)   # series_uid
    
    def __init__(self):
        super().__init__()
        self._setup_tree()
        self._current_data = {}
        
    def _setup_tree(self):
        """Configura el widget de árbol."""
        # Configurar headers
        self.setHeaderLabels(["Name", "Date", "Modality", "Description"])
        self.setAlternatingRowColors(True)
        self.setExpandsOnDoubleClick(True)
        
        # Configurar selección
        self.itemSelectionChanged.connect(self._on_selection_changed)
        self.itemDoubleClicked.connect(self._on_item_double_clicked)
        
        # Menú contextual
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
        # Configurar columnas
        header = self.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
    
    def populate_tree(self, patient_data: Dict[str, Any]):
        """Puebla el árbol con datos de pacientes."""
        self._current_data = patient_data
        self.clear()
        
        patients = patient_data.get("patients", {})
        
        for patient_id, patient_info in patients.items():
            # Crear nodo de paciente
            patient_item = QTreeWidgetItem(self)
            patient_item.setText(0, f"👤 {patient_info['patient_name']}")
            patient_item.setText(1, patient_info.get('birth_date', ''))
            patient_item.setText(2, "Patient")
            patient_item.setText(3, f"ID: {patient_id}")
            patient_item.setData(0, Qt.ItemDataRole.UserRole, {
                "type": "patient",
                "patient_id": patient_id,
                "data": patient_info
            })
            
            # Configurar fuente del paciente
            font = QFont()
            font.setBold(True)
            patient_item.setFont(0, font)
            
            # Añadir estudios
            studies = patient_info.get("studies", {})
            for study_uid, study_info in studies.items():
                study_item = QTreeWidgetItem(patient_item)
                study_item.setText(0, f"📁 {study_info['study_description']}")
                study_item.setText(1, study_info['study_date'])
                study_item.setText(2, study_info['modality'])
                study_item.setText(3, f"Study: {study_info['study_date']}")
                study_item.setData(0, Qt.ItemDataRole.UserRole, {
                    "type": "study",
                    "study_uid": study_uid,
                    "patient_id": patient_id,
                    "data": study_info
                })
                
                # Añadir series
                series_list = study_info.get("series", {})
                for series_uid, series_info in series_list.items():
                    series_item = QTreeWidgetItem(study_item)
                    series_item.setText(0, f"🖼️ {series_info['series_description']}")
                    series_item.setText(1, f"#{series_info['series_number']}")
                    series_item.setText(2, series_info['modality'])
                    series_item.setText(3, f"{series_info['images_count']} images")
                    series_item.setData(0, Qt.ItemDataRole.UserRole, {
                        "type": "series",
                        "series_uid": series_uid,
                        "study_uid": study_uid,
                        "patient_id": patient_id,
                        "data": series_info
                    })
        
        # Expandir todos los pacientes por defecto
        self.expandAll()
    
    def _on_selection_changed(self):
        """Maneja cambios de selección en el árbol."""
        selected_items = self.selectedItems()
        if not selected_items:
            return
        
        item = selected_items[0]
        data = item.data(0, Qt.ItemDataRole.UserRole)
        
        if not data:
            return
        
        item_type = data.get("type")
        
        if item_type == "patient":
            self.patient_selected.emit(data["patient_id"])
        elif item_type == "study":
            self.study_selected.emit(data["study_uid"])
        elif item_type == "series":
            self.series_selected.emit(data["series_uid"])
    
    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Maneja doble click en items."""
        data = item.data(0, Qt.ItemDataRole.UserRole)
        
        if not data:
            return
        
        item_type = data.get("type")
        
        if item_type == "series":
            # Doble click en serie = cargar imagen
            self.series_selected.emit(data["series_uid"])
        elif item_type == "study":
            # Doble click en estudio = expandir/colapsar
            if item.isExpanded():
                item.setExpanded(False)
            else:
                item.setExpanded(True)
    
    def _show_context_menu(self, position):
        """Muestra menú contextual."""
        item = self.itemAt(position)
        if not item:
            return
        
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return
        
        menu = QMenu(self)
        item_type = data.get("type")
        
        if item_type == "patient":
            menu.addAction("👤 View Patient Info", lambda: self._show_patient_info(data))
            menu.addAction("📁 Load All Studies", lambda: self._load_all_studies(data))
        
        elif item_type == "study":
            menu.addAction("📁 View Study Info", lambda: self._show_study_info(data))
            menu.addAction("🖼️ Load All Series", lambda: self._load_all_series(data))
        
        elif item_type == "series":
            menu.addAction("🖼️ Load Series", lambda: self.series_selected.emit(data["series_uid"]))
            menu.addAction("ℹ️ View Series Info", lambda: self._show_series_info(data))
        
        menu.addSeparator()
        menu.addAction("🔄 Refresh", self._refresh_data)
        
        menu.exec(self.mapToGlobal(position))
    
    def _show_patient_info(self, data):
        """Muestra información detallada del paciente."""
        patient_data = data["data"]
        info = f"""
Patient Information:
- Name: {patient_data['patient_name']}
- ID: {patient_data['patient_id']}
- Birth Date: {patient_data.get('birth_date', 'Unknown')}
- Sex: {patient_data.get('sex', 'Unknown')}
- Studies: {len(patient_data.get('studies', {}))}
        """
        QMessageBox.information(self, "Patient Information", info.strip())
    
    def _show_study_info(self, data):
        """Muestra información detallada del estudio."""
        study_data = data["data"]
        info = f"""
Study Information:
- Description: {study_data['study_description']}
- Date: {study_data['study_date']} {study_data.get('study_time', '')}
- Modality: {study_data['modality']}
- Series: {len(study_data.get('series', {}))}
- UID: {study_data['study_uid']}
        """
        QMessageBox.information(self, "Study Information", info.strip())
    
    def _show_series_info(self, data):
        """Muestra información detallada de la serie."""
        series_data = data["data"]
        info = f"""
Series Information:
- Description: {series_data['series_description']}
- Number: {series_data['series_number']}
- Modality: {series_data['modality']}
- Images: {series_data['images_count']}
- Slice Thickness: {series_data.get('slice_thickness', 'Unknown')}
- UID: {series_data['series_uid']}
        """
        QMessageBox.information(self, "Series Information", info.strip())
    
    def _load_all_studies(self, data):
        """Carga todos los estudios de un paciente."""
        # En implementación real, cargar múltiples estudios
        QMessageBox.information(self, "Info", "Load all studies functionality - To be implemented")
    
    def _load_all_series(self, data):
        """Carga todas las series de un estudio."""
        # En implementación real, cargar múltiples series
        QMessageBox.information(self, "Info", "Load all series functionality - To be implemented")
    
    def _refresh_data(self):
        """Actualiza los datos del árbol."""
        # Señal para refrescar datos
        self.parent().refresh_data()


class PatientBrowserPanel(QWidget):
    """
    Panel completo de navegación de pacientes.
    
    Integra búsqueda, filtrado, navegación jerárquica,
    y carga de imágenes médicas desde repositorio DICOM.
    """
    
    image_selected = pyqtSignal(str)  # series_uid
    patient_changed = pyqtSignal(str)  # patient_id
    
    def __init__(self, repository: DICOMImageRepository):
        super().__init__()
        self.repository = repository
        self.current_patient_data = {}
        self.loader_thread: Optional[PatientDataLoader] = None
        
        self._setup_ui()
        self._setup_connections()
        
        # Cargar datos iniciales
        QTimer.singleShot(100, self._load_initial_data)
    
    def _setup_ui(self):
        """Configura la interfaz del panel."""
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        
        # Grupo de búsqueda y filtros
        search_group = QGroupBox("Search & Filters")
        layout.addWidget(search_group)
        
        search_layout = QVBoxLayout(search_group)
        
        # Barra de búsqueda
        search_row = QHBoxLayout()
        search_layout.addLayout(search_row)
        
        search_row.addWidget(QLabel("Search:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Patient name, ID, or study description...")
        search_row.addWidget(self.search_edit)
        
        self.search_button = QPushButton("🔍")
        self.search_button.setFixedWidth(30)
        search_row.addWidget(self.search_button)
        
        # Filtros
        filter_row = QHBoxLayout()
        search_layout.addLayout(filter_row)
        
        filter_row.addWidget(QLabel("Modality:"))
        self.modality_filter = QComboBox()
        self.modality_filter.addItems(["All", "CT", "MRI", "US", "XR", "PT"])
        filter_row.addWidget(self.modality_filter)
        
        filter_row.addWidget(QLabel("Date:"))
        self.date_filter = QComboBox()
        self.date_filter.addItems(["All", "Today", "This Week", "This Month", "This Year"])
        filter_row.addWidget(self.date_filter)
        
        # Botón de actualización
        self.refresh_button = QPushButton("🔄 Refresh")
        search_layout.addWidget(self.refresh_button)
        
        # Árbol de navegación
        tree_group = QGroupBox("Patient Studies")
        layout.addWidget(tree_group)
        
        tree_layout = QVBoxLayout(tree_group)
        
        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        tree_layout.addWidget(self.progress_bar)
        
        # Widget de árbol
        self.patient_tree = PatientTreeWidget()
        tree_layout.addWidget(self.patient_tree)
        
        # Panel de información
        info_group = QGroupBox("Details")
        layout.addWidget(info_group)
        
        info_layout = QVBoxLayout(info_group)
        
        self.info_text = QTextEdit()
        self.info_text.setMaximumHeight(100)
        self.info_text.setReadOnly(True)
        info_layout.addWidget(self.info_text)
        
        # Botones de acción
        buttons_layout = QHBoxLayout()
        layout.addLayout(buttons_layout)
        
        self.load_button = QPushButton("📂 Load Selected")
        self.load_button.setEnabled(False)
        buttons_layout.addWidget(self.load_button)
        
        self.info_button = QPushButton("ℹ️ Info")
        self.info_button.setEnabled(False)
        buttons_layout.addWidget(self.info_button)
    
    def _setup_connections(self):
        """Configura las conexiones entre widgets."""
        # Conexiones de búsqueda
        self.search_button.clicked.connect(self._perform_search)
        self.search_edit.returnPressed.connect(self._perform_search)
        self.refresh_button.clicked.connect(self.refresh_data)
        
        # Conexiones de filtros
        self.modality_filter.currentTextChanged.connect(self._apply_filters)
        self.date_filter.currentTextChanged.connect(self._apply_filters)
        
        # Conexiones del árbol
        self.patient_tree.patient_selected.connect(self._on_patient_selected)
        self.patient_tree.study_selected.connect(self._on_study_selected)
        self.patient_tree.series_selected.connect(self._on_series_selected)
        
        # Conexiones de botones
        self.load_button.clicked.connect(self._load_selected_item)
        self.info_button.clicked.connect(self._show_selected_info)
    
    def _load_initial_data(self):
        """Carga datos iniciales del repositorio."""
        self.refresh_data()
    
    def refresh_data(self):
        """Actualiza los datos del navegador."""
        if self.loader_thread and self.loader_thread.isRunning():
            return
        
        self._show_loading("Loading patient data...")
        
        # Configurar parámetros de búsqueda
        search_params = {
            "search_text": self.search_edit.text(),
            "modality": self.modality_filter.currentText(),
            "date_range": self.date_filter.currentText()
        }
        
        # Iniciar carga en background
        self.loader_thread = PatientDataLoader(self.repository, search_params)
        self.loader_thread.data_loaded.connect(self._on_data_loaded)
        self.loader_thread.progress_updated.connect(self._on_progress_updated)
        self.loader_thread.error_occurred.connect(self._on_loading_error)
        self.loader_thread.finished.connect(self._on_loading_finished)
        
        self.loader_thread.start()
    
    def _perform_search(self):
        """Ejecuta búsqueda con texto actual."""
        self.refresh_data()
    
    def _apply_filters(self):
        """Aplica filtros de modalidad y fecha."""
        # En implementación real, filtrar datos localmente o re-consultar
        self.refresh_data()
    
    def _show_loading(self, message: str):
        """Muestra indicador de carga."""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.info_text.setText(f"🔄 {message}")
    
    def _hide_loading(self):
        """Oculta indicador de carga."""
        self.progress_bar.setVisible(False)
    
    @pyqtSlot(dict)
    def _on_data_loaded(self, patient_data: Dict[str, Any]):
        """Maneja datos cargados."""
        self.current_patient_data = patient_data
        self.patient_tree.populate_tree(patient_data)
        
        # Actualizar información
        patients_count = len(patient_data.get("patients", {}))
        studies_count = sum(
            len(p.get("studies", {})) 
            for p in patient_data.get("patients", {}).values()
        )
        
        self.info_text.setText(
            f"📊 Loaded: {patients_count} patients, {studies_count} studies"
        )
    
    @pyqtSlot(int, str)
    def _on_progress_updated(self, progress: int, message: str):
        """Actualiza progreso de carga."""
        self.progress_bar.setValue(progress)
        if message:
            self.info_text.setText(f"🔄 {message}")
    
    @pyqtSlot(str)
    def _on_loading_error(self, error_message: str):
        """Maneja errores de carga."""
        self.info_text.setText(f"❌ Error: {error_message}")
        QMessageBox.warning(self, "Loading Error", f"Failed to load patient data:\n{error_message}")
    
    def _on_loading_finished(self):
        """Maneja finalización de carga."""
        self._hide_loading()
    
    def _on_patient_selected(self, patient_id: str):
        """Maneja selección de paciente."""
        self.patient_changed.emit(patient_id)
        
        # Actualizar información del paciente
        patient_data = self._get_patient_data(patient_id)
        if patient_data:
            info = f"""
<b>Patient:</b> {patient_data['patient_name']}<br>
<b>ID:</b> {patient_id}<br>
<b>Birth Date:</b> {patient_data.get('birth_date', 'Unknown')}<br>
<b>Studies:</b> {len(patient_data.get('studies', {}))}
            """
            self.info_text.setHtml(info.strip())
        
        self.load_button.setEnabled(False)
        self.info_button.setEnabled(True)
    
    def _on_study_selected(self, study_uid: str):
        """Maneja selección de estudio."""
        study_data = self._get_study_data(study_uid)
        if study_data:
            info = f"""
<b>Study:</b> {study_data['study_description']}<br>
<b>Date:</b> {study_data['study_date']}<br>
<b>Modality:</b> {study_data['modality']}<br>
<b>Series:</b> {len(study_data.get('series', {}))}
            """
            self.info_text.setHtml(info.strip())
        
        self.load_button.setEnabled(False)
        self.info_button.setEnabled(True)
    
    def _on_series_selected(self, series_uid: str):
        """Maneja selección de serie."""
        series_data = self._get_series_data(series_uid)
        if series_data:
            info = f"""
<b>Series:</b> {series_data['series_description']}<br>
<b>Modality:</b> {series_data['modality']}<br>
<b>Images:</b> {series_data['images_count']}<br>
<b>Thickness:</b> {series_data.get('slice_thickness', 'Unknown')}
            """
            self.info_text.setHtml(info.strip())
        
        self.load_button.setEnabled(True)
        self.info_button.setEnabled(True)
    
    def _load_selected_item(self):
        """Carga el item seleccionado."""
        selected_items = self.patient_tree.selectedItems()
        if not selected_items:
            return
        
        item = selected_items[0]
        data = item.data(0, Qt.ItemDataRole.UserRole)
        
        if data and data.get("type") == "series":
            series_uid = data["series_uid"]
            self.image_selected.emit(series_uid)
    
    def _show_selected_info(self):
        """Muestra información detallada del item seleccionado."""
        selected_items = self.patient_tree.selectedItems()
        if not selected_items:
            return
        
        item = selected_items[0]
        data = item.data(0, Qt.ItemDataRole.UserRole)
        
        if not data:
            return
        
        item_type = data.get("type")
        
        if item_type == "patient":
            self.patient_tree._show_patient_info(data)
        elif item_type == "study":
            self.patient_tree._show_study_info(data)
        elif item_type == "series":
            self.patient_tree._show_series_info(data)
    
    def _get_patient_data(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene datos de un paciente específico."""
        return self.current_patient_data.get("patients", {}).get(patient_id)
    
    def _get_study_data(self, study_uid: str) -> Optional[Dict[str, Any]]:
        """Obtiene datos de un estudio específico."""
        for patient_data in self.current_patient_data.get("patients", {}).values():
            if study_uid in patient_data.get("studies", {}):
                return patient_data["studies"][study_uid]
        return None
    
    def _get_series_data(self, series_uid: str) -> Optional[Dict[str, Any]]:
        """Obtiene datos de una serie específica."""
        for patient_data in self.current_patient_data.get("patients", {}).values():
            for study_data in patient_data.get("studies", {}).values():
                if series_uid in study_data.get("series", {}):
                    return study_data["series"][series_uid]
        return None