"""
infrastructure/visualization/vtk_renderer.py

Motor de renderizado 3D usando VTK para visualización de imágenes médicas
y segmentaciones. Proporciona renderizado volumétrico, visualización de
superficies, y herramientas de manipulación 3D para análisis médico.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Callable
import vtk
from vtk.util import numpy_support
import asyncio

from ...domain.entities.medical_image import MedicalImage, ImageSpacing
from ...domain.entities.segmentation import MedicalSegmentation, AnatomicalRegion


class MedicalVTKRenderer:
    """
    Motor de renderizado 3D especializado para visualización médica.
    
    Esta clase encapsula toda la complejidad de VTK para proporcionar
    una interfaz médica simple y potente. Maneja renderizado volumétrico,
    visualización de segmentaciones, y herramientas de medición 3D.
    """
    
    def __init__(self, width: int = 800, height: int = 600):
        """
        Inicializa el motor de renderizado VTK.
        
        Args:
            width: Ancho de la ventana de renderizado
            height: Alto de la ventana de renderizado
        """
        # Configuración básica del pipeline VTK
        self._renderer = vtk.vtkRenderer()
        self._render_window = vtk.vtkRenderWindow()
        self._render_window_interactor = vtk.vtkRenderWindowInteractor()
        
        # Configurar ventana de renderizado
        self._render_window.AddRenderer(self._renderer)
        self._render_window.SetSize(width, height)
        self._render_window_interactor.SetRenderWindow(self._render_window)
        
        # Configurar estilo de interacción médica
        self._setup_medical_interaction_style()
        
        # Configurar iluminación médica óptima
        self._setup_medical_lighting()
        
        # Configurar background oscuro por defecto
        self._renderer.SetBackground(0.1, 0.1, 0.1)  # Tema oscuro
        
        # Almacenar objetos VTK activos para gestión de memoria
        self._active_volumes: Dict[str, vtk.vtkVolume] = {}
        self._active_segmentations: Dict[str, vtk.vtkActor] = {}
        self._active_measurements: Dict[str, List[vtk.vtkActor]] = {}
        
        # Configuraciones de renderizado por modalidad
        self._modality_presets = self._create_modality_presets()
        
        # Sistema de callbacks para eventos
        self._event_callbacks: Dict[str, List[Callable]] = {
            "volume_loaded": [],
            "segmentation_added": [],
            "measurement_created": [],
            "view_changed": []
        }
    
    async def render_volume(
        self,
        image: MedicalImage,
        rendering_mode: str = "mip",  # "mip", "composite", "isosurface"
        opacity_curve: Optional[List[Tuple[float, float]]] = None
    ) -> str:
        """
        Renderiza un volumen médico en 3D.
        
        Args:
            image: Imagen médica volumétrica a renderizar
            rendering_mode: Modo de renderizado ("mip", "composite", "isosurface")
            opacity_curve: Curva de opacidad personalizada [(valor, opacidad), ...]
            
        Returns:
            ID único del volumen renderizado
            
        Raises:
            VTKRenderingError: Si hay problemas durante el renderizado
        """
        try:
            volume_id = f"volume_{image.series_instance_uid}"
            
            # Convertir datos de imagen a VTK
            vtk_image_data = await self._create_vtk_image_data(image)
            
            # Configurar mapper volumétrico según modalidad
            volume_mapper = self._create_volume_mapper(
                image.modality, rendering_mode
            )
            volume_mapper.SetInputData(vtk_image_data)
            
            # Configurar propiedades volumétricas
            volume_property = self._create_volume_property(
                image, rendering_mode, opacity_curve
            )
            
            # Crear volume actor
            volume = vtk.vtkVolume()
            volume.SetMapper(volume_mapper)
            volume.SetProperty(volume_property)
            
            # Aplicar transformación de espaciado físico
            transform = self._create_physical_transform(image.spacing)
            volume.SetUserTransform(transform)
            
            # Añadir al renderer
            self._renderer.AddVolume(volume)
            self._active_volumes[volume_id] = volume
            
            # Ajustar cámara automáticamente
            self._renderer.ResetCamera()
            
            # Notificar callbacks
            await self._notify_callbacks("volume_loaded", {
                "volume_id": volume_id,
                "image": image,
                "rendering_mode": rendering_mode
            })
            
            return volume_id
            
        except Exception as e:
            raise VTKRenderingError(f"Error renderizando volumen: {e}") from e
    
    async def add_segmentation_surface(
        self,
        segmentation: MedicalSegmentation,
        image_spacing: ImageSpacing,
        surface_color: Optional[Tuple[float, float, float]] = None,
        opacity: float = 0.6,
        smoothing_iterations: int = 15
    ) -> str:
        """
        Añade una superficie 3D de segmentación al renderizado.
        
        Args:
            segmentation: Segmentación médica a visualizar
            image_spacing: Espaciado físico de la imagen padre
            surface_color: Color RGB de la superficie [0-1]
            opacity: Opacidad de la superficie [0-1]
            smoothing_iterations: Iteraciones de suavizado de superficie
            
        Returns:
            ID único de la superficie de segmentación
        """
        try:
            surface_id = f"surface_{segmentation.segmentation_id}"
            
            # Convertir máscara a VTK image data
            vtk_mask_data = await self._create_vtk_mask_data(
                segmentation, image_spacing
            )
            
            # Generar superficie usando Marching Cubes
            surface_filter = vtk.vtkMarchingCubes()
            surface_filter.SetInputData(vtk_mask_data)
            surface_filter.SetValue(0, 0.5)  # Isovalor para superficie
            surface_filter.Update()
            
            # Aplicar suavizado de superficie
            if smoothing_iterations > 0:
                smoother = vtk.vtkSmoothPolyDataFilter()
                smoother.SetInputConnection(surface_filter.GetOutputPort())
                smoother.SetNumberOfIterations(smoothing_iterations)
                smoother.SetRelaxationFactor(0.1)
                smoother.FeatureEdgeSmoothingOff()
                smoother.BoundarySmoothingOn()
                smoother.Update()
                polydata = smoother.GetOutput()
            else:
                polydata = surface_filter.GetOutput()
            
            # Calcular normales para iluminación correcta
            normals = vtk.vtkPolyDataNormals()
            normals.SetInputData(polydata)
            normals.ConsistencyOn()
            normals.SplittingOff()
            normals.Update()
            
            # Crear mapper y actor
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(normals.GetOutputPort())
            mapper.ScalarVisibilityOff()
            
            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            
            # Configurar propiedades visuales
            property = actor.GetProperty()
            
            # Color basado en región anatómica si no se especifica
            if surface_color is None:
                surface_color = self._get_anatomical_color(segmentation.anatomical_region)
            
            property.SetColor(surface_color)
            property.SetOpacity(opacity)
            property.SetSpecular(0.6)
            property.SetSpecularPower(30)
            
            # Añadir al renderer
            self._renderer.AddActor(actor)
            self._active_segmentations[surface_id] = actor
            
            # Notificar callbacks
            await self._notify_callbacks("segmentation_added", {
                "surface_id": surface_id,
                "segmentation": segmentation,
                "color": surface_color,
                "opacity": opacity
            })
            
            return surface_id
            
        except Exception as e:
            raise VTKRenderingError(f"Error añadiendo superficie de segmentación: {e}") from e
    
    async def create_3d_measurement(
        self,
        points: List[Tuple[float, float, float]],
        measurement_type: str = "distance",  # "distance", "angle", "volume"
        color: Tuple[float, float, float] = (1.0, 1.0, 0.0),
        font_size: int = 14
    ) -> str:
        """
        Crea una medición 3D interactiva.
        
        Args:
            points: Lista de puntos 3D para la medición
            measurement_type: Tipo de medición
            color: Color de la medición
            font_size: Tamaño de fuente para etiquetas
            
        Returns:
            ID único de la medición
        """
        try:
            measurement_id = f"measurement_{len(self._active_measurements)}"
            measurement_actors = []
            
            if measurement_type == "distance" and len(points) >= 2:
                # Crear línea de distancia
                line_actor = self._create_line_actor(points[0], points[1], color)
                measurement_actors.append(line_actor)
                
                # Calcular distancia
                p1, p2 = np.array(points[0]), np.array(points[1])
                distance = np.linalg.norm(p2 - p1)
                
                # Crear etiqueta de distancia
                midpoint = (p1 + p2) / 2
                text_actor = self._create_text_actor(
                    f"{distance:.2f} mm", midpoint, color, font_size
                )
                measurement_actors.append(text_actor)
            
            elif measurement_type == "angle" and len(points) >= 3:
                # Crear líneas del ángulo
                line1_actor = self._create_line_actor(points[1], points[0], color)
                line2_actor = self._create_line_actor(points[1], points[2], color)
                measurement_actors.extend([line1_actor, line2_actor])
                
                # Calcular ángulo
                v1 = np.array(points[0]) - np.array(points[1])
                v2 = np.array(points[2]) - np.array(points[1])
                angle = np.arccos(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))
                angle_degrees = np.degrees(angle)
                
                # Crear etiqueta de ángulo
                text_actor = self._create_text_actor(
                    f"{angle_degrees:.1f}°", points[1], color, font_size
                )
                measurement_actors.append(text_actor)
            
            # Añadir todos los actores al renderer
            for actor in measurement_actors:
                self._renderer.AddActor(actor)
            
            self._active_measurements[measurement_id] = measurement_actors
            
            # Notificar callbacks
            await self._notify_callbacks("measurement_created", {
                "measurement_id": measurement_id,
                "type": measurement_type,
                "points": points,
                "color": color
            })
            
            return measurement_id
            
        except Exception as e:
            raise VTKRenderingError(f"Error creando medición 3D: {e}") from e
    
    async def set_camera_view(
        self,
        view_type: str = "axial",  # "axial", "sagittal", "coronal", "oblique"
        custom_position: Optional[Tuple[float, float, float]] = None,
        custom_focal_point: Optional[Tuple[float, float, float]] = None
    ) -> None:
        """
        Configura la vista de cámara para visualización médica estándar.
        
        Args:
            view_type: Tipo de vista anatómica estándar
            custom_position: Posición personalizada de cámara
            custom_focal_point: Punto focal personalizado
        """
        camera = self._renderer.GetActiveCamera()
        
        # Obtener bounds de todos los objetos para centramiento
        bounds = self._renderer.ComputeVisiblePropBounds()
        center = [
            (bounds[0] + bounds[1]) / 2,
            (bounds[2] + bounds[3]) / 2,
            (bounds[4] + bounds[5]) / 2
        ]
        
        # Calcular distancia apropiada
        max_dimension = max(
            bounds[1] - bounds[0],
            bounds[3] - bounds[2],
            bounds[5] - bounds[4]
        )
        camera_distance = max_dimension * 2.5
        
        if custom_position and custom_focal_point:
            camera.SetPosition(custom_position)
            camera.SetFocalPoint(custom_focal_point)
        else:
            # Vistas anatómicas estándar
            if view_type == "axial":
                camera.SetPosition(center[0], center[1], center[2] + camera_distance)
                camera.SetViewUp(0, 1, 0)
            elif view_type == "sagittal":
                camera.SetPosition(center[0] + camera_distance, center[1], center[2])
                camera.SetViewUp(0, 0, 1)
            elif view_type == "coronal":
                camera.SetPosition(center[0], center[1] + camera_distance, center[2])
                camera.SetViewUp(0, 0, 1)
            else:  # oblique
                camera.SetPosition(
                    center[0] + camera_distance * 0.7,
                    center[1] + camera_distance * 0.7,
                    center[2] + camera_distance * 0.7
                )
                camera.SetViewUp(0, 0, 1)
            
            camera.SetFocalPoint(center)
        
        self._renderer.ResetCameraClippingRange()
        
        # Notificar cambio de vista
        await self._notify_callbacks("view_changed", {
            "view_type": view_type,
            "camera_position": camera.GetPosition(),
            "focal_point": camera.GetFocalPoint()
        })
    
    def remove_volume(self, volume_id: str) -> bool:
        """
        Remueve un volumen del renderizado.
        
        Args:
            volume_id: ID del volumen a remover
            
        Returns:
            True si se removió exitosamente
        """
        if volume_id in self._active_volumes:
            volume = self._active_volumes[volume_id]
            self._renderer.RemoveVolume(volume)
            del self._active_volumes[volume_id]
            return True
        return False
    
    def remove_segmentation(self, surface_id: str) -> bool:
        """
        Remueve una superficie de segmentación del renderizado.
        
        Args:
            surface_id: ID de la superficie a remover
            
        Returns:
            True si se removió exitosamente
        """
        if surface_id in self._active_segmentations:
            actor = self._active_segmentations[surface_id]
            self._renderer.RemoveActor(actor)
            del self._active_segmentations[surface_id]
            return True
        return False
    
    def remove_measurement(self, measurement_id: str) -> bool:
        """
        Remueve una medición del renderizado.
        
        Args:
            measurement_id: ID de la medición a remover
            
        Returns:
            True si se removió exitosamente
        """
        if measurement_id in self._active_measurements:
            actors = self._active_measurements[measurement_id]
            for actor in actors:
                self._renderer.RemoveActor(actor)
            del self._active_measurements[measurement_id]
            return True
        return False
    
    def clear_all(self) -> None:
        """Limpia todos los objetos del renderizado."""
        self._renderer.RemoveAllViewProps()
        self._active_volumes.clear()
        self._active_segmentations.clear()
        self._active_measurements.clear()
    
    def render(self) -> None:
        """Ejecuta el renderizado de la escena."""
        self._render_window.Render()
    
    def start_interaction(self) -> None:
        """Inicia el loop de interacción VTK."""
        self._render_window_interactor.Start()
    
    def add_event_callback(self, event_type: str, callback: Callable) -> None:
        """
        Añade un callback para eventos del renderizador.
        
        Args:
            event_type: Tipo de evento
            callback: Función callback a ejecutar
        """
        if event_type in self._event_callbacks:
            self._event_callbacks[event_type].append(callback)
    
    async def _create_vtk_image_data(self, image: MedicalImage) -> vtk.vtkImageData:
        """
        Convierte una imagen médica del dominio a vtkImageData.
        
        Args:
            image: Imagen médica a convertir
            
        Returns:
            vtkImageData configurado correctamente
        """
        image_data = image.image_data
        
        # Crear vtkImageData
        vtk_image = vtk.vtkImageData()
        
        if len(image_data.shape) == 3:
            depth, height, width = image_data.shape
            vtk_image.SetDimensions(width, height, depth)
        else:
            height, width = image_data.shape
            vtk_image.SetDimensions(width, height, 1)
        
        # Configurar espaciado
        spacing = image.spacing
        vtk_image.SetSpacing(spacing.x, spacing.y, spacing.z)
        
        # Configurar origen
        vtk_image.SetOrigin(0.0, 0.0, 0.0)
        
        # Convertir datos numpy a VTK
        flat_data = image_data.flatten()
        vtk_array = numpy_support.numpy_to_vtk(flat_data)
        vtk_image.GetPointData().SetScalars(vtk_array)
        
        return vtk_image
    
    async def _create_vtk_mask_data(
        self,
        segmentation: MedicalSegmentation,
        spacing: ImageSpacing
    ) -> vtk.vtkImageData:
        """
        Convierte una máscara de segmentación a vtkImageData.
        
        Args:
            segmentation: Segmentación a convertir
            spacing: Espaciado físico
            
        Returns:
            vtkImageData con la máscara
        """
        mask_data = segmentation.mask_data.astype(np.uint8)
        
        vtk_mask = vtk.vtkImageData()
        
        if len(mask_data.shape) == 3:
            depth, height, width = mask_data.shape
            vtk_mask.SetDimensions(width, height, depth)
        else:
            height, width = mask_data.shape
            vtk_mask.SetDimensions(width, height, 1)
        
        vtk_mask.SetSpacing(spacing.x, spacing.y, spacing.z)
        vtk_mask.SetOrigin(0.0, 0.0, 0.0)
        
        flat_mask = mask_data.flatten()
        vtk_array = numpy_support.numpy_to_vtk(flat_mask)
        vtk_mask.GetPointData().SetScalars(vtk_array)
        
        return vtk_mask
    
    def _create_volume_mapper(
        self,
        modality: 'ImageModalityType',
        rendering_mode: str
    ) -> vtk.vtkVolumeMapper:
        """
        Crea un volume mapper optimizado para modalidad específica.
        
        Args:
            modality: Modalidad de imagen médica
            rendering_mode: Modo de renderizado
            
        Returns:
            Volume mapper configurado
        """
        if rendering_mode == "mip":
            # Maximum Intensity Projection
            mapper = vtk.vtkGPUVolumeRayCastMapper()
            mapper.SetBlendModeToMaximumIntensity()
        elif rendering_mode == "isosurface":
            # Renderizado de isosuperficie
            mapper = vtk.vtkGPUVolumeRayCastMapper()
            mapper.SetBlendModeToIsoSurface()
        else:  # composite
            # Renderizado composito estándar
            mapper = vtk.vtkGPUVolumeRayCastMapper()
            mapper.SetBlendModeToComposite()
        
        # Configuraciones específicas por modalidad
        if modality.value == "CT":
            mapper.SetSampleDistance(0.5)
        elif modality.value == "MRI":
            mapper.SetSampleDistance(1.0)
        
        return mapper
    
    def _create_volume_property(
        self,
        image: MedicalImage,
        rendering_mode: str,
        opacity_curve: Optional[List[Tuple[float, float]]]
    ) -> vtk.vtkVolumeProperty:
        """
        Crea propiedades volumétricas para visualización médica.
        
        Args:
            image: Imagen médica
            rendering_mode: Modo de renderizado
            opacity_curve: Curva de opacidad personalizada
            
        Returns:
            Propiedades volumétricas configuradas
        """
        property = vtk.vtkVolumeProperty()
        
        # Función de color
        color_func = vtk.vtkColorTransferFunction()
        
        # Función de opacidad
        opacity_func = vtk.vtkPiecewiseFunction()
        
        # Configuración basada en modalidad
        modality_preset = self._modality_presets.get(image.modality.value, {})
        
        if opacity_curve:
            # Usar curva personalizada
            for value, opacity in opacity_curve:
                opacity_func.AddPoint(value, opacity)
        else:
            # Usar preset por modalidad
            opacity_points = modality_preset.get("opacity_points", [(0, 0), (255, 1)])
            for value, opacity in opacity_points:
                opacity_func.AddPoint(value, opacity)
        
        # Configurar colores
        color_points = modality_preset.get("color_points", [
            (0, 0, 0, 0), (255, 1, 1, 1)
        ])
        for value, r, g, b in color_points:
            color_func.AddRGBPoint(value, r, g, b)
        
        property.SetColor(color_func)
        property.SetScalarOpacity(opacity_func)
        
        # Configuraciones adicionales
        property.SetInterpolationTypeToLinear()
        property.ShadeOn()
        property.SetAmbient(0.4)
        property.SetDiffuse(0.6)
        property.SetSpecular(0.2)
        
        return property
    
    def _create_physical_transform(self, spacing: ImageSpacing) -> vtk.vtkTransform:
        """
        Crea transformación para espaciado físico correcto.
        
        Args:
            spacing: Espaciado de imagen
            
        Returns:
            Transformación VTK
        """
        transform = vtk.vtkTransform()
        # VTK usa transformación identidad por defecto
        # El espaciado ya se configura en vtkImageData
        return transform
    
    def _get_anatomical_color(
        self,
        region: AnatomicalRegion
    ) -> Tuple[float, float, float]:
        """
        Obtiene color estándar para región anatómica.
        
        Args:
            region: Región anatómica
            
        Returns:
            Color RGB [0-1]
        """
        color_map = {
            AnatomicalRegion.PROSTATE_WHOLE: (0.8, 0.6, 0.4),  # Marrón claro
            AnatomicalRegion.PROSTATE_PERIPHERAL_ZONE: (0.4, 0.8, 0.4),  # Verde
            AnatomicalRegion.PROSTATE_TRANSITION_ZONE: (0.4, 0.4, 0.8),  # Azul
            AnatomicalRegion.SUSPICIOUS_LESION: (1.0, 0.8, 0.0),  # Amarillo
            AnatomicalRegion.CONFIRMED_CANCER: (1.0, 0.2, 0.2),  # Rojo
            AnatomicalRegion.BENIGN_HYPERPLASIA: (0.6, 0.8, 0.6),  # Verde claro
            AnatomicalRegion.URETHRA: (0.8, 0.4, 0.8),  # Magenta
            AnatomicalRegion.SEMINAL_VESICLES: (0.8, 0.8, 0.4)  # Amarillo verdoso
        }
        
        return color_map.get(region, (0.7, 0.7, 0.7))  # Gris por defecto
    
    def _create_line_actor(
        self,
        point1: Tuple[float, float, float],
        point2: Tuple[float, float, float],
        color: Tuple[float, float, float]
    ) -> vtk.vtkActor:
        """Crea un actor de línea 3D."""
        # Crear línea
        line = vtk.vtkLineSource()
        line.SetPoint1(point1)
        line.SetPoint2(point2)
        
        # Crear mapper
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(line.GetOutputPort())
        
        # Crear actor
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(color)
        actor.GetProperty().SetLineWidth(2)
        
        return actor
    
    def _create_text_actor(
        self,
        text: str,
        position: Tuple[float, float, float],
        color: Tuple[float, float, float],
        font_size: int
    ) -> vtk.vtkTextActor3D:
        """Crea un actor de texto 3D."""
        text_actor = vtk.vtkTextActor3D()
        text_actor.SetInput(text)
        text_actor.SetPosition(position)
        
        # Configurar propiedades de texto
        text_property = text_actor.GetTextProperty()
        text_property.SetFontSize(font_size)
        text_property.SetColor(color)
        text_property.SetFontFamilyToArial()
        text_property.BoldOn()
        
        return text_actor
    
    def _create_modality_presets(self) -> Dict[str, Dict]:
        """Crea presets de visualización por modalidad."""
        return {
            "CT": {
                "opacity_points": [(0, 0), (100, 0.1), (500, 0.3), (1000, 0.8), (3000, 1.0)],
                "color_points": [
                    (0, 0, 0, 0),
                    (100, 0.5, 0.3, 0.3),
                    (500, 0.8, 0.8, 0.6),
                    (1000, 1.0, 1.0, 0.9),
                    (3000, 1.0, 1.0, 1.0)
                ]
            },
            "MRI": {
                "opacity_points": [(0, 0), (50, 0.2), (100, 0.5), (200, 0.8), (255, 1.0)],
                "color_points": [
                    (0, 0, 0, 0),
                    (50, 0.3, 0.3, 0.8),
                    (100, 0.6, 0.6, 0.9),
                    (200, 0.9, 0.9, 1.0),
                    (255, 1.0, 1.0, 1.0)
                ]
            }
        }
    
    def _setup_medical_interaction_style(self) -> None:
        """Configura estilo de interacción optimizado para uso médico."""
        style = vtk.vtkInteractorStyleTrackballCamera()
        self._render_window_interactor.SetInteractorStyle(style)
    
    def _setup_medical_lighting(self) -> None:
        """Configura iluminación óptima para visualización médica."""
        # Luz principal
        light1 = vtk.vtkLight()
        light1.SetPosition(1, 1, 1)
        light1.SetIntensity(0.8)
        light1.SetColor(1, 1, 1)
        self._renderer.AddLight(light1)
        
        # Luz de relleno
        light2 = vtk.vtkLight()
        light2.SetPosition(-1, -1, 1)
        light2.SetIntensity(0.4)
        light2.SetColor(1, 1, 1)
        self._renderer.AddLight(light2)
    
    async def _notify_callbacks(self, event_type: str, data: Dict[str, Any]) -> None:
        """Notifica callbacks registrados para un evento."""
        if event_type in self._event_callbacks:
            for callback in self._event_callbacks[event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    print(f"Error en callback {event_type}: {e}")


class VTKRenderingError(Exception):
    """Excepción para errores del motor de renderizado VTK."""
    pass