"""
infrastructure/ui/widgets/volume_viewer_3d.py

Widget de UI para visualización volumétrica 3D médica.
Esta clase tiene UNA responsabilidad: manejar la interfaz de usuario.
DELEGA toda la lógica técnica a clases especializadas.

PRINCIPIO EDUCATIVO: Orchestration vs Implementation
- Esta clase ORQUESTA (coordina) pero no IMPLEMENTA funcionalidad compleja
- Actúa como "director de orquesta" que coordina músicos especializados
- Mantiene la UI simple y enfocada solo en experiencia de usuario
"""

import numpy as np
from typing import Optional, Dict, List, Any
import logging

# PyQt6 imports para UI únicamente
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, 
    QPushButton, QSlider, QComboBox, QCheckBox, QFrame, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal

# VTK integration widget
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

# Nuestras clases especializadas
from ...visualization.vtk_volume_renderer import VTKVolumeRenderer
from ...visualization.medical_preset_manager import MedicalPresetManager, PresetType

# Entidades del dominio médico
from ....domain.entities.medical_image import MedicalImage, ImageModalityType


class VolumeViewer3DWidget(QWidget):
    """
    Widget de UI para visualización volumétrica 3D médica.
    
    EDUCATIVO: Esta clase es un excelente ejemplo de "Composition over Inheritance"
    y "Delegation". En lugar de implementar renderizado 3D directamente, 
    COMPONE objetos especializados y DELEGA responsabilidades.
    
    RESPONSABILIDAD ÚNICA: Manejar la experiencia de usuario para visualización 3D.
    
    QUÉ HACE:
    - Maneja events de UI (clicks, sliders, combos)
    - Organiza layout de widgets
    - Traduce acciones de usuario a operaciones de negocio
    - Muestra feedback al usuario
    
    QUÉ NO HACE:
    - No implementa renderizado VTK (delega a VTKVolumeRenderer)
    - No gestiona presets médicos (delega a MedicalPresetManager)  
    - No procesa datos volumétricos (delega a servicios de aplicación)
    - No conoce detalles de VTK, OpenGL, o algoritmos de renderizado
    """
    
    # Señales para comunicación con otros widgets (patrón Observer)
    volume_rendered = pyqtSignal(str)      # ID del volumen renderizado
    view_changed = pyqtSignal(str)         # Tipo de vista cambiada
    preset_applied = pyqtSignal(str)       # Preset aplicado
    rendering_error = pyqtSignal(str)      # Error en renderizado
    
    def __init__(self):
        """
        Inicializa el widget de visualización 3D.
        
        EDUCATIVO: En el constructor solo creamos objetos especializados
        y configuramos la UI. No hay lógica compleja aquí - eso está
        delegado a las clases especializadas.
        """
        super().__init__()
        
        # Logger para debugging
        self._logger = logging.getLogger(__name__)
        
        # Objetos especializados (Composition Pattern)
        self._volume_renderer = VTKVolumeRenderer()
        self._preset_manager = MedicalPresetManager()
        
        # Estado actual (mínimo)
        self._current_image: Optional[MedicalImage] = None
        self._current_preset_name: Optional[str] = None
        
        # Configurar UI
        self._setup_ui()
        
        # Conectar eventos internos
        self._connect_signals()
        
        self._logger.info("VolumeViewer3DWidget inicializado")
    
    def _setup_ui(self):
        """
        Configura la interfaz de usuario.
        
        EDUCATIVO: La UI se organiza de manera lógica para el flujo de trabajo médico:
        1. Controles a la izquierda (configuración)
        2. Visualización al centro (resultado)
        3. Información a la derecha (feedback)
        """
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Título
        title_label = QLabel("🧊 Visualización Volumétrica 3D")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2E86AB; padding: 5px;")
        main_layout.addWidget(title_label)
        
        # Splitter principal para organización
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(main_splitter)
        
        # Panel izquierdo: Controles
        controls_panel = self._create_controls_panel()
        main_splitter.addWidget(controls_panel)
        
        # Panel central: Visualización VTK
        visualization_panel = self._create_visualization_panel()
        main_splitter.addWidget(visualization_panel)
        
        # Panel derecho: Información y estado
        info_panel = self._create_info_panel()
        main_splitter.addWidget(info_panel)
        
        # Configurar tamaños (20% - 60% - 20%)
        main_splitter.setSizes([200, 600, 200])
    
    def _create_controls_panel(self) -> QWidget:
        """
        Crea el panel de controles de usuario.
        
        EDUCATIVO: Los controles se agrupan lógicamente según el workflow médico.
        Primero presets (configuración rápida), luego ajustes finos.
        """
        panel = QWidget()
        panel.setMaximumWidth(220)
        layout = QVBoxLayout(panel)
        
        # Grupo: Presets médicos
        presets_group = QGroupBox("⚕️ Presets Médicos")
        presets_layout = QVBoxLayout(presets_group)
        
        # Combo para seleccionar preset
        presets_layout.addWidget(QLabel("Configuración predefinida:"))
        self._preset_combo = QComboBox()
        self._populate_preset_combo()
        presets_layout.addWidget(self._preset_combo)
        
        # Botón para aplicar preset
        self._apply_preset_btn = QPushButton("✅ Aplicar Preset")
        self._apply_preset_btn.clicked.connect(self._apply_selected_preset)
        presets_layout.addWidget(self._apply_preset_btn)
        
        layout.addWidget(presets_group)
        
        # Grupo: Ajustes manuales de opacidad
        opacity_group = QGroupBox("👁️ Opacidad")
        opacity_layout = QVBoxLayout(opacity_group)
        
        opacity_layout.addWidget(QLabel("Opacidad global:"))
        self._opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self._opacity_slider.setRange(0, 100)
        self._opacity_slider.setValue(80)
        self._opacity_slider.valueChanged.connect(self._on_opacity_changed)
        opacity_layout.addWidget(self._opacity_slider)
        
        self._opacity_label = QLabel("80%")
        self._opacity_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        opacity_layout.addWidget(self._opacity_label)
        
        layout.addWidget(opacity_group)
        
        # Grupo: Calidad de renderizado
        quality_group = QGroupBox("⚙️ Calidad")
        quality_layout = QVBoxLayout(quality_group)
        
        self._high_quality_checkbox = QCheckBox("Alta calidad (más lento)")
        self._high_quality_checkbox.stateChanged.connect(self._on_quality_changed)
        quality_layout.addWidget(self._high_quality_checkbox)
        
        layout.addWidget(quality_group)
        
        # Botón de reset
        self._reset_view_btn = QPushButton("🔄 Reset Vista")
        self._reset_view_btn.clicked.connect(self._reset_camera_view)
        layout.addWidget(self._reset_view_btn)
        
        # Espacio flexible
        layout.addStretch()
        
        return panel
    
    def _create_visualization_panel(self) -> QWidget:
        """
        Crea el panel central de visualización VTK.
        
        EDUCATIVO: Aquí integramos VTK con PyQt6. El QVTKRenderWindowInteractor
        es el "puente" entre ambos frameworks.
        """
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Sunken)
        panel.setMinimumSize(400, 400)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Widget VTK integrado
        # EDUCATIVO: Aquí delegamos al renderer especializado
        self._vtk_widget = QVTKRenderWindowInteractor(panel)
        render_window = self._volume_renderer.get_render_window()
        self._vtk_widget.SetRenderWindow(render_window)
        
        layout.addWidget(self._vtk_widget)
        
        # Inicializar VTK
        self._vtk_widget.Initialize()
        self._vtk_widget.Start()
        
        return panel
    
    def _create_info_panel(self) -> QWidget:
        """
        Crea el panel de información y estado.
        
        EDUCATIVO: Feedback al usuario es crítico en aplicaciones médicas.
        Los usuarios necesitan saber qué está pasando y si todo está bien.
        """
        panel = QWidget()
        panel.setMaximumWidth(220)
        layout = QVBoxLayout(panel)
        
        # Información del volumen actual
        volume_group = QGroupBox("📊 Información del Volumen")
        volume_layout = QVBoxLayout(volume_group)
        
        self._volume_info_label = QLabel("No hay volumen cargado")
        self._volume_info_label.setWordWrap(True)
        self._volume_info_label.setStyleSheet("color: #666; font-size: 10px;")
        volume_layout.addWidget(self._volume_info_label)
        
        layout.addWidget(volume_group)
        
        # Estado del renderizado
        status_group = QGroupBox("🎯 Estado")
        status_layout = QVBoxLayout(status_group)
        
        self._status_label = QLabel("✅ Listo")
        self._status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        status_layout.addWidget(self._status_label)
        
        layout.addWidget(status_group)
        
        # Preset actual
        current_preset_group = QGroupBox("⚕️ Preset Activo")
        current_preset_layout = QVBoxLayout(current_preset_group)
        
        self._current_preset_label = QLabel("Ninguno")
        self._current_preset_label.setWordWrap(True)
        self._current_preset_label.setStyleSheet("color: #333; font-size: 10px;")
        current_preset_layout.addWidget(self._current_preset_label)
        
        layout.addWidget(current_preset_group)
        
        # Botón de captura de pantalla
        self._screenshot_btn = QPushButton("📷 Capturar")
        self._screenshot_btn.clicked.connect(self._capture_screenshot)
        layout.addWidget(self._screenshot_btn)
        
        # Espacio flexible
        layout.addStretch()
        
        return panel
    
    def _populate_preset_combo(self):
        """
        Llena el combo box con presets disponibles.
        
        EDUCATIVO: Aquí delegamos la lógica de presets al gestor especializado.
        La UI no conoce los detalles de los presets médicos.
        """
        self._preset_combo.clear()
        
        # Obtener todos los presets del gestor especializado
        preset_names = self._preset_manager.get_all_preset_names()
        
        for name in preset_names:
            # Obtener descripción para tooltip
            description = self._preset_manager.get_preset_description(name)
            self._preset_combo.addItem(name)
            
            # Configurar tooltip con descripción médica
            index = self._preset_combo.count() - 1
            self._preset_combo.setItemData(index, description, Qt.ItemDataRole.ToolTipRole)
    
    def _connect_signals(self):
        """
        Conecta señales internas para comunicación entre componentes.
        
        EDUCATIVO: Las señales PyQt6 permiten comunicación loose-coupled
        entre componentes. Es una implementación del patrón Observer.
        """
        self._preset_combo.currentTextChanged.connect(self._on_preset_selection_changed)
    
    # Métodos públicos para interacción externa
    
    def set_medical_image(self, image: MedicalImage) -> None:
        """
        Establece la imagen médica a visualizar.
        
        EDUCATIVO: Este es el método principal para uso externo.
        Toda la complejidad se delega a los objetos especializados.
        
        Args:
            image: Imagen médica del dominio
        """
        try:
            self._logger.info(f"Configurando imagen médica: {image.modality.value}")
            
            # Guardar referencia
            self._current_image = image
            
            # Actualizar información
            self._update_volume_info(image)
            
            # Delegar renderizado al objeto especializado
            volume_id = self._volume_renderer.render_volume(
                image.image_data, 
                image.spacing
            )
            
            # Aplicar preset por defecto según modalidad
            self._apply_default_preset_for_modality(image.modality)
            
            # Actualizar UI
            self._status_label.setText("✅ Volumen renderizado")
            self._status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            
            # Emitir señal para notificar a otros widgets
            self.volume_rendered.emit(volume_id)
            
            self._logger.info("Imagen médica configurada exitosamente")
            
        except Exception as e:
            error_msg = f"Error configurando imagen: {str(e)}"
            self._logger.error(error_msg)
            
            # Actualizar UI con error
            self._status_label.setText("❌ Error")
            self._status_label.setStyleSheet("color: #F44336; font-weight: bold;")
            
            # Emitir señal de error
            self.rendering_error.emit(error_msg)
    
    def apply_preset_by_name(self, preset_name: str) -> bool:
        """
        Aplica un preset específico por nombre.
        
        EDUCATIVO: Método público que permite control externo,
        pero delega la lógica al gestor de presets.
        
        Args:
            preset_name: Nombre del preset a aplicar
            
        Returns:
            True si se aplicó exitosamente
        """
        preset = self._preset_manager.get_preset_by_name(preset_name)
        if not preset:
            self._logger.warning(f"Preset no encontrado: {preset_name}")
            return False
        
        return self._apply_preset(preset)
    
    # Métodos privados de implementación
    
    def _apply_default_preset_for_modality(self, modality: ImageModalityType) -> None:
        """
        Aplica automáticamente el preset por defecto para la modalidad.
        
        EDUCATIVO: Automatización inteligente - el sistema "sabe" qué
        configuración es mejor para cada tipo de imagen médica.
        """
        default_preset = self._preset_manager.get_default_preset_for_modality(modality)
        if default_preset:
            self._apply_preset(default_preset)
            
            # Sincronizar UI
            self._preset_combo.setCurrentText(default_preset.name)
    
    def _apply_preset(self, preset) -> bool:
        """
        Aplica un preset médico al renderizador.
        
        EDUCATIVO: Aquí vemos la colaboración entre objetos especializados:
        1. PresetManager proporciona la configuración
        2. VolumeRenderer aplica la configuración
        3. UI se actualiza para reflejar el cambio
        """
        try:
            # Convertir preset a formato del renderer
            config = preset.to_renderer_config()
            
            # Aplicar al renderer especializado
            self._volume_renderer.set_opacity_curve(config["opacity_points"])
            self._volume_renderer.set_color_map(config["color_points"])
            
            # Renderizar con nueva configuración
            self._vtk_widget.GetRenderWindow().Render()
            
            # Actualizar estado UI
            self._current_preset_name = preset.name
            self._current_preset_label.setText(f"{preset.name}\n\n{preset.description}")
            
            # Emitir señal
            self.preset_applied.emit(preset.name)
            
            self._logger.info(f"Preset aplicado: {preset.name}")
            return True
            
        except Exception as e:
            self._logger.error(f"Error aplicando preset {preset.name}: {e}")
            return False
    
    def _update_volume_info(self, image: MedicalImage) -> None:
        """
        Actualiza la información mostrada sobre el volumen actual.
        
        EDUCATIVO: Proporcionar feedback detallado ayuda a los usuarios
        médicos a entender qué están viendo y verificar que es correcto.
        """
        info_text = f"""
Modalidad: {image.modality.value}
Dimensiones: {image.dimensions}
Spacing: {image.spacing.x:.2f} × {image.spacing.y:.2f} × {image.spacing.z:.2f} mm
Paciente: {image.patient_id}
Serie: {image.series_instance_uid[:16]}...
        """.strip()
        
        self._volume_info_label.setText(info_text)
    
    # Event handlers de UI
    
    def _on_preset_selection_changed(self, preset_name: str) -> None:
        """Maneja cambios en la selección de preset."""
        if preset_name and preset_name != self._current_preset_name:
            # Cambiar automáticamente cuando el usuario selecciona
            self.apply_preset_by_name(preset_name)
    
    def _apply_selected_preset(self) -> None:
        """Aplica el preset actualmente seleccionado."""
        preset_name = self._preset_combo.currentText()
        if preset_name:
            self.apply_preset_by_name(preset_name)
    
    def _on_opacity_changed(self, value: int) -> None:
        """
        Maneja cambios en el slider de opacidad global.
        
        EDUCATIVO: Aquí traducimos eventos de UI a operaciones del renderizador.
        La UI no sabe cómo implementar opacidad - delega al especialista.
        """
        self._opacity_label.setText(f"{value}%")
        
        # Si hay un preset activo, modificarlo proporcionalmente
        if self._current_preset_name:
            preset = self._preset_manager.get_preset_by_name(self._current_preset_name)
            if preset:
                # Escalar la curva de opacidad del preset
                global_factor = value / 100.0
                scaled_points = [
                    (point.intensity, point.opacity * global_factor) 
                    for point in preset.opacity_curve
                ]
                
                self._volume_renderer.set_opacity_curve(scaled_points)
                self._vtk_widget.GetRenderWindow().Render()
    
    def _on_quality_changed(self, state) -> None:
        """Maneja cambios en la configuración de calidad."""
        high_quality = state == Qt.CheckState.Checked.value
        
        # En una implementación real, esto cambiaría configuraciones
        # del renderizador como sampling rate, interpolation, etc.
        self._logger.debug(f"Calidad alta configurada: {high_quality}")
    
    def _reset_camera_view(self) -> None:
        """Resetea la vista de la cámara al ángulo por defecto."""
        # Delegar al renderizador VTK
        render_window = self._volume_renderer.get_render_window()
        renderer = render_window.GetRenderers().GetFirstRenderer()
        if renderer:
            renderer.ResetCamera()
            self._vtk_widget.GetRenderWindow().Render()
    
    def _capture_screenshot(self) -> None:
        """Captura una imagen de la vista 3D actual."""
        # En implementación real, esto capturaría la imagen
        self._logger.info("Captura de pantalla solicitada")
        self._status_label.setText("📷 Captura realizada")
    
    def cleanup(self) -> None:
        """
        Limpia recursos para prevenir memory leaks.
        
        EDUCATIVO: En aplicaciones médicas que manejan datos grandes,
        la gestión de memoria es crítica.
        """
        if self._volume_renderer:
            self._volume_renderer.cleanup()
        
        self._current_image = None
        self._logger.info("VolumeViewer3DWidget limpiado")
