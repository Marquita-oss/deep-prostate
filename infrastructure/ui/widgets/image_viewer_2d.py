"""
infrastructure/ui/widgets/image_viewer_2d.py

Visualizador 2D especializado para imágenes médicas con soporte para
múltiples planos anatómicos, herramientas de medición, y visualización
de segmentaciones superpuestas.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import math

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSplitter,
    QFrame, QScrollArea, QComboBox, QPushButton, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QPointF, QTimer
from PyQt6.QtGui import (
    QPainter, QPen, QBrush, QColor, QPixmap, QImage, 
    QPainterPath, QFont, QMouseEvent, QPaintEvent
)

from domain.entities.medical_image import MedicalImage, ImagePlaneType
from domain.entities.segmentation import MedicalSegmentation, AnatomicalRegion


class MedicalImageCanvas(QLabel):
    """
    Canvas especializado para visualización de imágenes médicas.
    Maneja zoom, pan, mediciones, y overlay de segmentaciones.
    """
    
    # Señales para comunicación con la ventana principal
    pixel_clicked = pyqtSignal(int, int, float)  # x, y, intensity
    measurement_created = pyqtSignal(dict)  # measurement data
    slice_changed = pyqtSignal(int)  # new slice index
    
    def __init__(self):
        super().__init__()
        
        # Estado de la imagen
        self._image_data: Optional[np.ndarray] = None
        self._display_pixmap: Optional[QPixmap] = None
        self._image_spacing: Tuple[float, float] = (1.0, 1.0)
        
        # Estado de visualización
        self._zoom_factor = 1.0
        self._pan_offset = QPointF(0, 0)
        self._window = 400
        self._level = 40
        
        # Estado de segmentaciones
        self._segmentation_overlays: Dict[str, np.ndarray] = {}
        self._segmentation_colors: Dict[str, QColor] = {}
        self._segmentation_opacity = 0.4
        
        # Herramientas de medición
        self._measurement_mode = None  # "distance", "angle", "roi"
        self._measurement_points: List[QPointF] = []
        self._active_measurements: List[Dict[str, Any]] = []
        self._temp_measurement_path = QPainterPath()
        
        # Configuración del widget
        self.setMinimumSize(400, 400)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("border: 1px solid #666; background-color: #1a1a1a;")
        self.setMouseTracking(True)
        
        # Timer para actualizaciones fluidas
        self._update_timer = QTimer()
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._update_display)
    
    def set_image_data(
        self, 
        image_data: np.ndarray, 
        spacing: Tuple[float, float] = (1.0, 1.0)
    ) -> None:
        """
        Establece los datos de imagen a visualizar.
        
        Args:
            image_data: Array 2D con datos de imagen
            spacing: Espaciado de pixel en mm (x, y)
        """
        self._image_data = image_data.copy()
        self._image_spacing = spacing
        
        # Resetear estado de visualización
        self._zoom_factor = 1.0
        self._pan_offset = QPointF(0, 0)
        
        # Actualizar display
        self._update_image_display()
        
        # Ajustar zoom para que la imagen encaje en el widget
        self._fit_to_window()
    
    def set_window_level(self, window: float, level: float) -> None:
        """
        Actualiza la configuración de ventana y nivel.
        
        Args:
            window: Ancho de ventana
            level: Centro de ventana
        """
        self._window = window
        self._level = level
        self._update_image_display()
    
    def add_segmentation_overlay(
        self, 
        segmentation: MedicalSegmentation,
        color: Optional[QColor] = None
    ) -> None:
        """
        Añade una segmentación como overlay semi-transparente.
        
        Args:
            segmentation: Segmentación a visualizar
            color: Color del overlay (auto si es None)
        """
        seg_id = segmentation.segmentation_id
        
        # Obtener máscara 2D (asumiendo que coincide con la imagen actual)
        if len(segmentation.mask_data.shape) == 3:
            # Si es 3D, tomar el slice central por ahora
            mask_2d = segmentation.mask_data[segmentation.mask_data.shape[0] // 2]
        else:
            mask_2d = segmentation.mask_data
        
        self._segmentation_overlays[seg_id] = mask_2d
        
        # Color basado en región anatómica si no se especifica
        if color is None:
            color = self._get_anatomical_color(segmentation.anatomical_region)
        
        self._segmentation_colors[seg_id] = color
        
        # Actualizar visualización
        self._update_display()
    
    def remove_segmentation_overlay(self, segmentation_id: str) -> None:
        """Remueve un overlay de segmentación."""
        self._segmentation_overlays.pop(segmentation_id, None)
        self._segmentation_colors.pop(segmentation_id, None)
        self._update_display()
    
    def set_measurement_mode(self, mode: Optional[str]) -> None:
        """
        Establece el modo de medición activo.
        
        Args:
            mode: "distance", "angle", "roi", o None para desactivar
        """
        self._measurement_mode = mode
        self._measurement_points.clear()
        self._temp_measurement_path = QPainterPath()
        self.setCursor(Qt.CursorShape.CrossCursor if mode else Qt.CursorShape.ArrowCursor)
        self.update()
    
    def clear_measurements(self) -> None:
        """Limpia todas las mediciones."""
        self._active_measurements.clear()
        self._measurement_points.clear()
        self._temp_measurement_path = QPainterPath()
        self.update()
    
    def zoom_in(self, factor: float = 1.2) -> None:
        """Aumenta el zoom manteniendo el centro."""
        self._zoom_factor *= factor
        self._zoom_factor = min(self._zoom_factor, 10.0)  # Límite máximo
        self._update_display()
    
    def zoom_out(self, factor: float = 1.2) -> None:
        """Disminuye el zoom manteniendo el centro."""
        self._zoom_factor /= factor
        self._zoom_factor = max(self._zoom_factor, 0.1)  # Límite mínimo
        self._update_display()
    
    def reset_zoom(self) -> None:
        """Resetea el zoom y centrado."""
        self._zoom_factor = 1.0
        self._pan_offset = QPointF(0, 0)
        self._fit_to_window()
    
    def _fit_to_window(self) -> None:
        """Ajusta el zoom para que la imagen encaje en el widget."""
        if self._image_data is None:
            return
        
        widget_size = self.size()
        image_size = self._image_data.shape
        
        # Calcular factor de escala para que encaje
        scale_x = widget_size.width() / image_size[1]
        scale_y = widget_size.height() / image_size[0]
        self._zoom_factor = min(scale_x, scale_y) * 0.9  # 90% para margen
        
        self._update_display()
    
    def _update_image_display(self) -> None:
        """Actualiza la visualización de la imagen con ventana/nivel."""
        if self._image_data is None:
            return
        
        # Aplicar ventana/nivel
        normalized_image = self._apply_window_level(self._image_data)
        
        # Convertir a QImage
        height, width = normalized_image.shape
        bytes_per_line = width
        
        q_image = QImage(
            normalized_image.data.tobytes(),
            width, height,
            bytes_per_line,
            QImage.Format.Format_Grayscale8
        )
        
        # Crear pixmap base
        self._display_pixmap = QPixmap.fromImage(q_image)
        
        # Programar actualización del display
        self._update_timer.start(16)  # ~60 FPS
    
    def _update_display(self) -> None:
        """Actualiza el display completo con overlays y mediciones."""
        if self._display_pixmap is None:
            return
        
        # Crear pixmap compuesto
        composite_pixmap = QPixmap(self._display_pixmap.size())
        composite_pixmap.fill(Qt.GlobalColor.black)
        
        painter = QPainter(composite_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Dibujar imagen base
        painter.drawPixmap(0, 0, self._display_pixmap)
        
        # Dibujar overlays de segmentación
        self._draw_segmentation_overlays(painter)
        
        # Dibujar mediciones
        self._draw_measurements(painter)
        
        painter.end()
        
        # Aplicar zoom y pan
        final_pixmap = self._apply_zoom_and_pan(composite_pixmap)
        
        # Mostrar en el widget
        self.setPixmap(final_pixmap)
    
    def _apply_window_level(self, image_data: np.ndarray) -> np.ndarray:
        """
        Aplica ventana/nivel y convierte a uint8 para visualización.
        
        Args:
            image_data: Imagen original
            
        Returns:
            Imagen normalizada [0-255]
        """
        # Calcular rango de ventana
        min_val = self._level - (self._window / 2.0)
        max_val = self._level + (self._window / 2.0)
        
        # Aplicar clipping y normalización
        clipped = np.clip(image_data, min_val, max_val)
        
        if max_val != min_val:
            normalized = ((clipped - min_val) / (max_val - min_val) * 255).astype(np.uint8)
        else:
            normalized = np.zeros_like(clipped, dtype=np.uint8)
        
        return normalized
    
    def _draw_segmentation_overlays(self, painter: QPainter) -> None:
        """Dibuja overlays de segmentación semi-transparentes."""
        if not self._segmentation_overlays:
            return
        
        painter.save()
        
        for seg_id, mask in self._segmentation_overlays.items():
            color = self._segmentation_colors.get(seg_id, QColor(255, 0, 0))
            
            # Crear overlay coloreado
            overlay_image = self._create_colored_overlay(mask, color)
            overlay_pixmap = QPixmap.fromImage(overlay_image)
            
            # Dibujar con transparencia
            painter.setOpacity(self._segmentation_opacity)
            painter.drawPixmap(0, 0, overlay_pixmap)
        
        painter.restore()
    
    def _create_colored_overlay(self, mask: np.ndarray, color: QColor) -> QImage:
        """
        Crea una imagen coloreada a partir de una máscara binaria.
        
        Args:
            mask: Máscara binaria
            color: Color del overlay
            
        Returns:
            QImage coloreada con transparencia
        """
        height, width = mask.shape
        
        # Crear imagen RGBA
        overlay_array = np.zeros((height, width, 4), dtype=np.uint8)
        
        # Aplicar color donde la máscara es True
        mask_indices = mask > 0
        overlay_array[mask_indices, 0] = color.red()    # R
        overlay_array[mask_indices, 1] = color.green()  # G  
        overlay_array[mask_indices, 2] = color.blue()   # B
        overlay_array[mask_indices, 3] = 180           # A (transparencia)
        
        return QImage(
            overlay_array.data.tobytes(),
            width, height,
            QImage.Format.Format_RGBA8888
        )
    
    def _draw_measurements(self, painter: QPainter) -> None:
        """Dibuja mediciones activas y temporales."""
        painter.save()
        
        # Configurar estilo de dibujo
        pen = QPen(QColor(255, 255, 0), 2)  # Amarillo para mediciones
        painter.setPen(pen)
        
        font = QFont("Arial", 12, QFont.Weight.Bold)
        painter.setFont(font)
        
        # Dibujar mediciones completadas
        for measurement in self._active_measurements:
            self._draw_single_measurement(painter, measurement)
        
        # Dibujar medición temporal si está activa
        if self._measurement_points and self._measurement_mode:
            temp_measurement = {
                "type": self._measurement_mode,
                "points": self._measurement_points,
                "complete": False
            }
            self._draw_single_measurement(painter, temp_measurement)
        
        painter.restore()
    
    def _draw_single_measurement(self, painter: QPainter, measurement: Dict[str, Any]) -> None:
        """Dibuja una medición individual."""
        points = measurement["points"]
        measurement_type = measurement["type"]
        
        if measurement_type == "distance" and len(points) >= 2:
            # Dibujar línea de distancia
            p1, p2 = points[0], points[1]
            painter.drawLine(p1, p2)
            
            # Calcular y mostrar distancia
            if measurement.get("complete", True):
                distance_px = math.sqrt((p2.x() - p1.x())**2 + (p2.y() - p1.y())**2)
                distance_mm = distance_px * self._image_spacing[0]  # Aproximación
                
                # Punto medio para la etiqueta
                mid_point = QPointF((p1.x() + p2.x()) / 2, (p1.y() + p2.y()) / 2)
                painter.drawText(mid_point, f"{distance_mm:.1f} mm")
        
        elif measurement_type == "angle" and len(points) >= 3:
            # Dibujar líneas del ángulo
            p1, vertex, p3 = points[0], points[1], points[2]
            painter.drawLine(vertex, p1)
            painter.drawLine(vertex, p3)
            
            # Calcular y mostrar ángulo
            if measurement.get("complete", True):
                v1 = QPointF(p1.x() - vertex.x(), p1.y() - vertex.y())
                v2 = QPointF(p3.x() - vertex.x(), p3.y() - vertex.y())
                
                # Producto punto para calcular ángulo
                dot_product = v1.x() * v2.x() + v1.y() * v2.y()
                mag1 = math.sqrt(v1.x()**2 + v1.y()**2)
                mag2 = math.sqrt(v2.x()**2 + v2.y()**2)
                
                if mag1 > 0 and mag2 > 0:
                    cos_angle = dot_product / (mag1 * mag2)
                    cos_angle = max(-1, min(1, cos_angle))  # Clamp para evitar errores
                    angle_rad = math.acos(cos_angle)
                    angle_deg = math.degrees(angle_rad)
                    
                    painter.drawText(vertex, f"{angle_deg:.1f}°")
        
        elif measurement_type == "roi" and len(points) >= 3:
            # Dibujar ROI como polígono
            if len(points) > 2:
                path = QPainterPath()
                path.moveTo(points[0])
                for point in points[1:]:
                    path.lineTo(point)
                
                if measurement.get("complete", True):
                    path.closeSubpath()
                
                painter.drawPath(path)
    
    def _apply_zoom_and_pan(self, pixmap: QPixmap) -> QPixmap:
        """
        Aplica zoom y pan a un pixmap.
        
        Args:
            pixmap: Pixmap base
            
        Returns:
            Pixmap transformado
        """
        if self._zoom_factor == 1.0 and self._pan_offset.isNull():
            return pixmap
        
        # Calcular tamaño final
        original_size = pixmap.size()
        scaled_width = int(original_size.width() * self._zoom_factor)
        scaled_height = int(original_size.height() * self._zoom_factor)
        
        # Escalar pixmap
        scaled_pixmap = pixmap.scaled(
            scaled_width, scaled_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        # Crear pixmap final con pan offset
        widget_size = self.size()
        final_pixmap = QPixmap(widget_size)
        final_pixmap.fill(Qt.GlobalColor.black)
        
        painter = QPainter(final_pixmap)
        
        # Calcular posición con offset de pan
        x = (widget_size.width() - scaled_width) // 2 + int(self._pan_offset.x())
        y = (widget_size.height() - scaled_height) // 2 + int(self._pan_offset.y())
        
        painter.drawPixmap(x, y, scaled_pixmap)
        painter.end()
        
        return final_pixmap
    
    def _get_anatomical_color(self, region: AnatomicalRegion) -> QColor:
        """Obtiene color estándar para región anatómica."""
        color_map = {
            AnatomicalRegion.PROSTATE_WHOLE: QColor(204, 153, 102),          # Marrón claro
            AnatomicalRegion.PROSTATE_PERIPHERAL_ZONE: QColor(102, 204, 102), # Verde
            AnatomicalRegion.PROSTATE_TRANSITION_ZONE: QColor(102, 102, 204), # Azul
            AnatomicalRegion.SUSPICIOUS_LESION: QColor(255, 204, 0),         # Amarillo
            AnatomicalRegion.CONFIRMED_CANCER: QColor(255, 51, 51),          # Rojo
            AnatomicalRegion.BENIGN_HYPERPLASIA: QColor(153, 204, 153),      # Verde claro
            AnatomicalRegion.URETHRA: QColor(204, 102, 204),                 # Magenta
            AnatomicalRegion.SEMINAL_VESICLES: QColor(204, 204, 102)         # Amarillo verdoso
        }
        
        return color_map.get(region, QColor(179, 179, 179))  # Gris por defecto
    
    def _image_to_widget_coords(self, image_point: QPointF) -> QPointF:
        """Convierte coordenadas de imagen a coordenadas del widget."""
        if self._display_pixmap is None:
            return image_point
        
        # Aplicar zoom y pan
        widget_size = self.size()
        pixmap_size = self._display_pixmap.size()
        
        scaled_width = pixmap_size.width() * self._zoom_factor
        scaled_height = pixmap_size.height() * self._zoom_factor
        
        # Posición base del pixmap en el widget
        x_offset = (widget_size.width() - scaled_width) / 2 + self._pan_offset.x()
        y_offset = (widget_size.height() - scaled_height) / 2 + self._pan_offset.y()
        
        # Convertir coordenadas
        widget_x = image_point.x() * self._zoom_factor + x_offset
        widget_y = image_point.y() * self._zoom_factor + y_offset
        
        return QPointF(widget_x, widget_y)
    
    def _widget_to_image_coords(self, widget_point: QPointF) -> QPointF:
        """Convierte coordenadas del widget a coordenadas de imagen."""
        if self._display_pixmap is None:
            return widget_point
        
        # Proceso inverso al anterior
        widget_size = self.size()
        pixmap_size = self._display_pixmap.size()
        
        scaled_width = pixmap_size.width() * self._zoom_factor
        scaled_height = pixmap_size.height() * self._zoom_factor
        
        x_offset = (widget_size.width() - scaled_width) / 2 + self._pan_offset.x()
        y_offset = (widget_size.height() - scaled_height) / 2 + self._pan_offset.y()
        
        # Convertir coordenadas
        image_x = (widget_point.x() - x_offset) / self._zoom_factor
        image_y = (widget_point.y() - y_offset) / self._zoom_factor
        
        return QPointF(image_x, image_y)
    
    # Event handlers
    
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Maneja clicks del mouse."""
        if event.button() == Qt.MouseButton.LeftButton:
            image_point = self._widget_to_image_coords(QPointF(event.pos()))
            
            # Verificar que el punto esté dentro de la imagen
            if (self._image_data is not None and 
                0 <= image_point.x() < self._image_data.shape[1] and
                0 <= image_point.y() < self._image_data.shape[0]):
                
                # Obtener intensidad del pixel
                intensity = self._image_data[int(image_point.y()), int(image_point.x())]
                self.pixel_clicked.emit(int(image_point.x()), int(image_point.y()), float(intensity))
                
                # Manejar herramientas de medición
                if self._measurement_mode:
                    self._handle_measurement_click(image_point)
        
        elif event.button() == Qt.MouseButton.RightButton:
            # Click derecho cancela medición actual
            if self._measurement_mode:
                self._measurement_points.clear()
                self.update()
        
        super().mousePressEvent(event)
    
    def _handle_measurement_click(self, point: QPointF) -> None:
        """Maneja clicks para herramientas de medición."""
        self._measurement_points.append(point)
        
        # Verificar si la medición está completa
        complete = False
        
        if self._measurement_mode == "distance" and len(self._measurement_points) >= 2:
            complete = True
        elif self._measurement_mode == "angle" and len(self._measurement_points) >= 3:
            complete = True
        elif self._measurement_mode == "roi" and len(self._measurement_points) >= 3:
            # ROI se completa con doble click o tecla Enter
            pass
        
        if complete:
            # Crear medición permanente
            measurement = {
                "type": self._measurement_mode,
                "points": self._measurement_points.copy(),
                "complete": True,
                "timestamp": QTimer().currentTime()
            }
            
            self._active_measurements.append(measurement)
            self.measurement_created.emit(measurement)
            
            # Resetear para nueva medición
            self._measurement_points.clear()
        
        self.update()
    
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Maneja movimiento del mouse."""
        if self._image_data is not None:
            image_point = self._widget_to_image_coords(QPointF(event.pos()))
            
            # Verificar bounds
            if (0 <= image_point.x() < self._image_data.shape[1] and
                0 <= image_point.y() < self._image_data.shape[0]):
                
                intensity = self._image_data[int(image_point.y()), int(image_point.x())]
                # Actualizar coordenadas en status bar (vía señal padre)
                self.pixel_clicked.emit(int(image_point.x()), int(image_point.y()), float(intensity))
        
        super().mouseMoveEvent(event)
    
    def wheelEvent(self, event) -> None:
        """Maneja zoom con rueda del mouse."""
        delta = event.angleDelta().y()
        
        if delta > 0:
            self.zoom_in(1.1)
        else:
            self.zoom_out(1.1)
    
    def keyPressEvent(self, event) -> None:
        """Maneja atajos de teclado."""
        if event.key() == Qt.Key.Key_Escape:
            # Cancelar medición actual
            if self._measurement_mode:
                self._measurement_points.clear()
                self.update()
        
        elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            # Completar ROI si hay al menos 3 puntos
            if (self._measurement_mode == "roi" and len(self._measurement_points) >= 3):
                measurement = {
                    "type": "roi",
                    "points": self._measurement_points.copy(),
                    "complete": True
                }
                
                self._active_measurements.append(measurement)
                self.measurement_created.emit(measurement)
                self._measurement_points.clear()
                self.update()
        
        super().keyPressEvent(event)


class ImageViewer2D(QWidget):
    """
    Widget completo de visualización 2D con controles y múltiples vistas.
    Integra múltiples canvas para visualización multi-planar.
    """
    
    slice_changed = pyqtSignal(int)
    measurement_added = pyqtSignal(dict)
    view_changed = pyqtSignal(str)  # plane name
    
    def __init__(self):
        super().__init__()
        
        # Estado actual
        self._current_image: Optional[MedicalImage] = None
        self._current_slice_data: Dict[str, Any] = {}
        self._layout_mode = "single"  # "single" or "quad"
        
        self._setup_ui()
        self._setup_connections()
    
    def _setup_ui(self) -> None:
        """Configura la interfaz del visualizador 2D."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Barra de controles superior
        controls_frame = QFrame()
        controls_frame.setFixedHeight(40)
        controls_frame.setFrameStyle(QFrame.Shape.Box)
        layout.addWidget(controls_frame)
        
        controls_layout = QHBoxLayout(controls_frame)
        
        # Selector de layout
        controls_layout.addWidget(QLabel("Layout:"))
        self._layout_combo = QComboBox()
        self._layout_combo.addItems(["Single View", "Quad View"])
        self._layout_combo.currentTextChanged.connect(self._change_layout)
        controls_layout.addWidget(self._layout_combo)
        
        controls_layout.addStretch()
        
        # Controles de overlay
        self._overlay_checkbox = QCheckBox("Show Segmentations")
        self._overlay_checkbox.setChecked(True)
        self._overlay_checkbox.toggled.connect(self._toggle_overlays)
        controls_layout.addWidget(self._overlay_checkbox)
        
        # Área principal de visualización
        self._main_splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(self._main_splitter)
        
        # Crear canvas principales
        self._create_canvas_widgets()
        
        # Configurar layout inicial
        self._setup_single_view()
    
    def _create_canvas_widgets(self) -> None:
        """Crea los widgets canvas para diferentes vistas."""
        self._axial_canvas = MedicalImageCanvas()
        self._axial_canvas.pixel_clicked.connect(
            lambda x, y, i: self._on_pixel_info(x, y, i, "Axial")
        )
        self._axial_canvas.measurement_created.connect(self.measurement_added.emit)
        
        self._sagittal_canvas = MedicalImageCanvas()
        self._sagittal_canvas.pixel_clicked.connect(
            lambda x, y, i: self._on_pixel_info(x, y, i, "Sagittal")
        )
        self._sagittal_canvas.measurement_created.connect(self.measurement_added.emit)
        
        self._coronal_canvas = MedicalImageCanvas()
        self._coronal_canvas.pixel_clicked.connect(
            lambda x, y, i: self._on_pixel_info(x, y, i, "Coronal")
        )
        self._coronal_canvas.measurement_created.connect(self.measurement_added.emit)
        
        # Canvas principal para vista única
        self._main_canvas = self._axial_canvas  # Por defecto axial
    
    def _setup_single_view(self) -> None:
        """Configura layout de vista única."""
        # Limpiar splitter
        for i in range(self._main_splitter.count()):
            child = self._main_splitter.widget(i)
            if child:
                child.setParent(None)
        
        # Añadir solo canvas principal
        self._main_splitter.addWidget(self._main_canvas)
        self._layout_mode = "single"
    
    def _setup_quad_view(self) -> None:
        """Configura layout de vista cuádruple."""
        # Limpiar splitter
        for i in range(self._main_splitter.count()):
            child = self._main_splitter.widget(i)
            if child:
                child.setParent(None)
        
        # Crear splitters para layout 2x2
        left_splitter = QSplitter(Qt.Orientation.Vertical)
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Añadir canvas a splitters
        left_splitter.addWidget(self._axial_canvas)
        left_splitter.addWidget(self._sagittal_canvas)
        
        right_splitter.addWidget(self._coronal_canvas)
        # Cuarto panel podría ser para información o herramientas
        info_widget = QLabel("Additional View\nor Tools")
        info_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_widget.setStyleSheet("border: 1px solid #666; background-color: #2a2a2a;")
        right_splitter.addWidget(info_widget)
        
        # Añadir splitters al principal
        self._main_splitter.addWidget(left_splitter)
        self._main_splitter.addWidget(right_splitter)
        self._main_splitter.setSizes([400, 400])
        
        self._layout_mode = "quad"
    
    def _setup_connections(self) -> None:
        """Configura conexiones entre widgets."""
        pass  # Conexiones ya configuradas en _create_canvas_widgets
    
    def set_image(self, image: MedicalImage, initial_slice_data: Dict[str, Any]) -> None:
        """
        Establece la imagen médica a visualizar.
        
        Args:
            image: Imagen médica
            initial_slice_data: Datos del slice inicial preparados
        """
        self._current_image = image
        self._current_slice_data = initial_slice_data
        
        # Configurar canvas principal
        if "image_data" in initial_slice_data:
            spacing = (image.spacing.x, image.spacing.y)
            self._main_canvas.set_image_data(initial_slice_data["image_data"], spacing)
        
        # Si estamos en vista cuádruple, preparar otros planos
        if self._layout_mode == "quad":
            self._update_all_planes()
    
    def update_slice(self, slice_data: Dict[str, Any], slice_index: int) -> None:
        """
        Actualiza el slice actual en visualización.
        
        Args:
            slice_data: Nuevos datos del slice
            slice_index: Índice del slice
        """
        self._current_slice_data = slice_data
        
        if "image_data" in slice_data and self._current_image:
            spacing = (self._current_image.spacing.x, self._current_image.spacing.y)
            self._main_canvas.set_image_data(slice_data["image_data"], spacing)
        
        self.slice_changed.emit(slice_index)
    
    def update_window_level(self, window: float, level: float) -> None:
        """Actualiza ventana/nivel en todos los canvas."""
        self._axial_canvas.set_window_level(window, level)
        self._sagittal_canvas.set_window_level(window, level)
        self._coronal_canvas.set_window_level(window, level)
    
    def add_segmentation(self, segmentation: MedicalSegmentation) -> None:
        """Añade segmentación a todos los canvas."""
        if self._overlay_checkbox.isChecked():
            self._axial_canvas.add_segmentation_overlay(segmentation)
            self._sagittal_canvas.add_segmentation_overlay(segmentation)
            self._coronal_canvas.add_segmentation_overlay(segmentation)
    
    def set_measurement_mode(self, mode: Optional[str]) -> None:
        """Establece modo de medición en todos los canvas."""
        self._axial_canvas.set_measurement_mode(mode)
        self._sagittal_canvas.set_measurement_mode(mode)
        self._coronal_canvas.set_measurement_mode(mode)
    
    def set_layout_mode(self, mode: str) -> None:
        """Cambia el modo de layout."""
        if mode == "single":
            self._setup_single_view()
        elif mode == "quad":
            self._setup_quad_view()
    
    def _change_layout(self, layout_name: str) -> None:
        """Maneja cambio de layout desde combo box."""
        if layout_name == "Single View":
            self.set_layout_mode("single")
        elif layout_name == "Quad View":
            self.set_layout_mode("quad")
    
    def _toggle_overlays(self, enabled: bool) -> None:
        """Activa/desactiva overlays de segmentación."""
        # En implementación real, manejar visibilidad de overlays
        pass
    
    def _update_all_planes(self) -> None:
        """Actualiza todos los planos en vista cuádruple."""
        if not self._current_image:
            return
        
        # En implementación real, preparar slices para cada plano
        # Por ahora, usar la misma imagen en todos
        spacing = (self._current_image.spacing.x, self._current_image.spacing.y)
        
        if "image_data" in self._current_slice_data:
            image_data = self._current_slice_data["image_data"]
            self._axial_canvas.set_image_data(image_data, spacing)
            self._sagittal_canvas.set_image_data(image_data, spacing)
            self._coronal_canvas.set_image_data(image_data, spacing)
    
    def _on_pixel_info(self, x: int, y: int, intensity: float, plane: str) -> None:
        """Maneja información de pixel desde canvas."""
        # En implementación real, actualizar status bar o info panel
        pass