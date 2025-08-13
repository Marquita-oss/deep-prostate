"""
application/services/segmentation_services.py

Servicios de aplicación para gestión de segmentaciones médicas y análisis de IA.
Orquestan el flujo completo desde la predicción automática con nnUNet hasta
la validación clínica y edición manual por parte de los médicos.
"""

import numpy as np
from typing import List, Optional, Dict, Any, Tuple, Union
from datetime import datetime
import asyncio
from pathlib import Path

from ...domain.entities.medical_image import MedicalImage, ImageSpacing
from ...domain.entities.segmentation import (
    MedicalSegmentation, AnatomicalRegion, SegmentationType,
    SegmentationMetrics, IntensityStatistics, ConfidenceLevel
)
from ...domain.repositories.repositories import (
    MedicalImageRepository, SegmentationRepository,
    SegmentationNotFoundError, RepositoryError
)


class AISegmentationService:
    """
    Servicio para segmentación automática usando modelos de IA (nnUNetv2).
    
    Este servicio encapsula toda la lógica de negocio relacionada con 
    la predicción automática, validación de resultados, y conversión
    de salidas del modelo a entidades del dominio médico.
    """
    
    def __init__(
        self, 
        segmentation_repository: SegmentationRepository,
        model_config: Dict[str, Any]
    ):
        self._segmentation_repository = segmentation_repository
        self._model_config = model_config
        self._confidence_thresholds = {
            AnatomicalRegion.PROSTATE_WHOLE: 0.85,
            AnatomicalRegion.SUSPICIOUS_LESION: 0.70,
            AnatomicalRegion.CONFIRMED_CANCER: 0.80,
            AnatomicalRegion.PROSTATE_PERIPHERAL_ZONE: 0.75,
            AnatomicalRegion.PROSTATE_TRANSITION_ZONE: 0.75
        }
        
        # Cache para modelos cargados en memoria
        self._loaded_models: Dict[str, Any] = {}
    
    async def predict_prostate_segmentation(
        self,
        image: MedicalImage,
        include_zones: bool = True,
        detect_lesions: bool = True
    ) -> List[MedicalSegmentation]:
        """
        Realiza segmentación automática completa de próstata usando nnUNet.
        
        Args:
            image: Imagen médica de próstata para segmentar
            include_zones: Si incluir segmentación de zonas prostáticas
            detect_lesions: Si incluir detección de lesiones sospechosas
            
        Returns:
            Lista de segmentaciones generadas automáticamente
            
        Raises:
            AISegmentationError: Si falla la predicción del modelo
        """
        try:
            # Validar que la imagen sea apropiada para segmentación prostática
            await self._validate_prostate_image(image)
            
            # Preparar datos de entrada para nnUNet
            preprocessed_data = await self._preprocess_for_nnunet(image)
            
            # Ejecutar predicción del modelo principal (próstata completa)
            main_prediction = await self._run_nnunet_inference(
                preprocessed_data, 
                model_task="prostate_whole"
            )
            
            # Convertir predicción a segmentación del dominio
            segmentations = []
            
            # Segmentación de próstata completa
            prostate_segmentation = await self._create_segmentation_from_prediction(
                mask_data=main_prediction["prostate_mask"],
                confidence_map=main_prediction["confidence_map"],
                anatomical_region=AnatomicalRegion.PROSTATE_WHOLE,
                parent_image=image
            )
            segmentations.append(prostate_segmentation)
            
            # Segmentación de zonas prostáticas si se solicita
            if include_zones:
                zone_predictions = await self._run_nnunet_inference(
                    preprocessed_data,
                    model_task="prostate_zones"
                )
                
                zone_segmentations = await self._create_zone_segmentations(
                    zone_predictions, image
                )
                segmentations.extend(zone_segmentations)
            
            # Detección de lesiones si se solicita
            if detect_lesions:
                lesion_predictions = await self._run_nnunet_inference(
                    preprocessed_data,
                    model_task="lesion_detection"
                )
                
                lesion_segmentations = await self._create_lesion_segmentations(
                    lesion_predictions, image
                )
                segmentations.extend(lesion_segmentations)
            
            # Guardar todas las segmentaciones generadas
            save_tasks = [
                self._segmentation_repository.save_segmentation(seg) 
                for seg in segmentations
            ]
            await asyncio.gather(*save_tasks)
            
            return segmentations
            
        except Exception as e:
            raise AISegmentationError(f"Error en predicción automática: {e}") from e
    
    async def refine_segmentation_with_ai(
        self,
        original_segmentation: MedicalSegmentation,
        refinement_hints: Dict[str, Any]
    ) -> MedicalSegmentation:
        """
        Refina una segmentación existente usando asistencia de IA.
        
        Args:
            original_segmentation: Segmentación base a refinar
            refinement_hints: Pistas del usuario para el refinamiento
            
        Returns:
            Nueva segmentación refinada
        """
        try:
            # Aplicar algoritmos de refinamiento basados en las pistas
            refined_mask = await self._apply_ai_refinement(
                original_segmentation.mask_data,
                refinement_hints
            )
            
            # Crear nueva segmentación refinada
            refined_segmentation = MedicalSegmentation(
                mask_data=refined_mask,
                anatomical_region=original_segmentation.anatomical_region,
                segmentation_type=SegmentationType.SEMI_AUTOMATIC,
                creation_date=datetime.now(),
                creator_id="ai_refinement_system",
                parent_image_uid=original_segmentation._parent_image_uid,
                description=f"AI-refined {original_segmentation._description}"
            )
            
            # Guardar segmentación refinada
            await self._segmentation_repository.save_segmentation(refined_segmentation)
            
            return refined_segmentation
            
        except Exception as e:
            raise AISegmentationError(f"Error refinando segmentación: {e}") from e
    
    async def validate_ai_predictions(
        self,
        segmentations: List[MedicalSegmentation],
        validation_criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Valida automáticamente la calidad de predicciones de IA.
        
        Args:
            segmentations: Lista de segmentaciones a validar
            validation_criteria: Criterios de validación específicos
            
        Returns:
            Diccionario con resultados de validación y métricas de calidad
        """
        validation_results = {
            "overall_quality": "unknown",
            "individual_results": [],
            "recommendations": [],
            "requires_manual_review": False
        }
        
        total_confidence = 0.0
        high_quality_count = 0
        
        for segmentation in segmentations:
            # Validar métricas geométricas
            geometric_validation = await self._validate_geometric_properties(
                segmentation, validation_criteria
            )
            
            # Validar consistencia anatómica
            anatomic_validation = await self._validate_anatomic_consistency(
                segmentation, validation_criteria
            )
            
            # Calcular score de calidad combinado
            quality_score = self._calculate_quality_score(
                geometric_validation, anatomic_validation, segmentation
            )
            
            # Determinar si requiere revisión manual
            needs_review = quality_score < validation_criteria.get("min_quality_threshold", 0.7)
            
            individual_result = {
                "segmentation_id": segmentation.segmentation_id,
                "region": segmentation.anatomical_region.value,
                "quality_score": quality_score,
                "confidence_level": segmentation.confidence_level.value if segmentation.confidence_level else "unknown",
                "geometric_validation": geometric_validation,
                "anatomic_validation": anatomic_validation,
                "needs_manual_review": needs_review
            }
            
            validation_results["individual_results"].append(individual_result)
            
            # Acumular estadísticas generales
            total_confidence += quality_score
            if quality_score >= 0.8:
                high_quality_count += 1
            
            if needs_review:
                validation_results["requires_manual_review"] = True
        
        # Calcular calidad general
        avg_confidence = total_confidence / len(segmentations) if segmentations else 0.0
        high_quality_ratio = high_quality_count / len(segmentations) if segmentations else 0.0
        
        if avg_confidence >= 0.85 and high_quality_ratio >= 0.8:
            validation_results["overall_quality"] = "excellent"
        elif avg_confidence >= 0.7 and high_quality_ratio >= 0.6:
            validation_results["overall_quality"] = "good"
        elif avg_confidence >= 0.5:
            validation_results["overall_quality"] = "acceptable"
        else:
            validation_results["overall_quality"] = "poor"
        
        # Generar recomendaciones automáticas
        validation_results["recommendations"] = self._generate_validation_recommendations(
            validation_results
        )
        
        return validation_results
    
    async def _validate_prostate_image(self, image: MedicalImage) -> None:
        """
        Valida que una imagen sea apropiada para segmentación prostática.
        
        Args:
            image: Imagen a validar
            
        Raises:
            ImageValidationError: Si la imagen no es apropiada
        """
        # Validar modalidad
        if image.modality not in [image.modality.MRI, image.modality.CT]:
            raise ImageValidationError(
                f"Modalidad {image.modality} no soportada para segmentación prostática"
            )
        
        # Validar dimensiones mínimas
        min_dimensions = (64, 64, 8)  # Mínimo para análisis prostático útil
        if any(dim < min_dim for dim, min_dim in zip(image.dimensions, min_dimensions)):
            raise ImageValidationError(
                f"Dimensiones {image.dimensions} insuficientes para análisis prostático"
            )
        
        # Validar región anatómica en metadatos si está disponible
        body_part = image.get_dicom_tag("BodyPartExamined")
        if body_part and "pelvis" not in body_part.lower() and "prostate" not in body_part.lower():
            raise ImageValidationError(
                f"Región anatómica '{body_part}' no apropiada para análisis prostático"
            )
    
    async def _preprocess_for_nnunet(self, image: MedicalImage) -> Dict[str, Any]:
        """
        Preprocesa una imagen médica para entrada a nnUNet.
        
        Args:
            image: Imagen médica a preprocesar
            
        Returns:
            Diccionario con datos preprocesados listos para nnUNet
        """
        # Obtener datos de imagen y metadatos
        image_data = image.image_data.astype(np.float32)
        spacing = image.spacing
        
        # Normalización específica para cada modalidad
        if image.modality == image.modality.MRI:
            # Normalización Z-score para MRI
            mean_intensity = np.mean(image_data)
            std_intensity = np.std(image_data)
            normalized_data = (image_data - mean_intensity) / (std_intensity + 1e-8)
        else:
            # Clipping y normalización para CT
            normalized_data = np.clip(image_data, -1000, 1000)
            normalized_data = (normalized_data + 1000) / 2000.0
        
        # Preparar metadatos en formato nnUNet
        nnunet_metadata = {
            "spacing": [spacing.z, spacing.y, spacing.x],  # nnUNet usa orden ZYX
            "origin": [0.0, 0.0, 0.0],
            "direction": np.eye(3).tolist(),
            "modality": image.modality.value,
            "original_shape": image.dimensions
        }
        
        return {
            "image_data": normalized_data,
            "metadata": nnunet_metadata,
            "preprocessing_info": {
                "normalization_method": "z_score" if image.modality == image.modality.MRI else "clip_norm",
                "intensity_statistics": image.get_intensity_statistics()
            }
        }
    
    async def _run_nnunet_inference(
        self,
        preprocessed_data: Dict[str, Any],
        model_task: str
    ) -> Dict[str, np.ndarray]:
        """
        Ejecuta inferencia nnUNet para una tarea específica.
        
        Args:
            preprocessed_data: Datos preprocesados para el modelo
            model_task: Tarea específica del modelo ("prostate_whole", "prostate_zones", "lesion_detection")
            
        Returns:
            Diccionario con predicciones del modelo
        """
        # Aquí se integraría con nnUNetv2 real
        # Por ahora, simulamos la predicción
        
        image_data = preprocessed_data["image_data"]
        shape = image_data.shape
        
        if model_task == "prostate_whole":
            # Simular máscara de próstata completa
            mask = self._simulate_prostate_mask(shape)
            confidence_map = np.random.uniform(0.7, 0.95, shape)
            
            return {
                "prostate_mask": mask,
                "confidence_map": confidence_map,
                "processing_time": 2.5,
                "model_version": "nnUNet_prostate_v2.1"
            }
        
        elif model_task == "prostate_zones":
            # Simular máscaras de zonas prostáticas
            pz_mask = self._simulate_zone_mask(shape, "peripheral")
            tz_mask = self._simulate_zone_mask(shape, "transition")
            
            return {
                "peripheral_zone_mask": pz_mask,
                "transition_zone_mask": tz_mask,
                "confidence_maps": {
                    "peripheral": np.random.uniform(0.6, 0.9, shape),
                    "transition": np.random.uniform(0.6, 0.9, shape)
                }
            }
        
        elif model_task == "lesion_detection":
            # Simular detección de lesiones
            lesion_mask = self._simulate_lesion_mask(shape)
            
            return {
                "lesion_mask": lesion_mask,
                "lesion_confidence": np.random.uniform(0.5, 0.85, shape),
                "lesion_probability": np.random.uniform(0.1, 0.9, shape)
            }
        
        else:
            raise ValueError(f"Tarea de modelo '{model_task}' no reconocida")
    
    async def _create_segmentation_from_prediction(
        self,
        mask_data: np.ndarray,
        confidence_map: np.ndarray,
        anatomical_region: AnatomicalRegion,
        parent_image: MedicalImage
    ) -> MedicalSegmentation:
        """
        Crea una entidad MedicalSegmentation a partir de predicción de IA.
        
        Args:
            mask_data: Máscara binaria predicha
            confidence_map: Mapa de confianza de la predicción
            anatomical_region: Región anatómica segmentada
            parent_image: Imagen médica padre
            
        Returns:
            Segmentación médica del dominio
        """
        # Calcular confianza promedio de la región segmentada
        if np.any(mask_data):
            region_confidence = float(np.mean(confidence_map[mask_data > 0]))
        else:
            region_confidence = 0.0
        
        # Crear segmentación del dominio
        segmentation = MedicalSegmentation(
            mask_data=mask_data,
            anatomical_region=anatomical_region,
            segmentation_type=SegmentationType.AUTOMATIC,
            creation_date=datetime.now(),
            creator_id="nnunet_v2_system",
            confidence_score=region_confidence,
            parent_image_uid=parent_image.series_instance_uid,
            description=f"nnUNet automatic {anatomical_region.value} segmentation"
        )
        
        return segmentation
    
    def _simulate_prostate_mask(self, shape: Tuple[int, ...]) -> np.ndarray:
        """Simula una máscara de próstata para demostración."""
        mask = np.zeros(shape, dtype=bool)
        if len(shape) == 3:
            depth, height, width = shape
            # Crear una forma elipsoidal simple en el centro
            center_z, center_y, center_x = depth // 2, height // 2, width // 2
            radius_z, radius_y, radius_x = depth // 6, height // 4, width // 4
            
            for z in range(depth):
                for y in range(height):
                    for x in range(width):
                        dist = ((z - center_z) / radius_z) ** 2 + \
                               ((y - center_y) / radius_y) ** 2 + \
                               ((x - center_x) / radius_x) ** 2
                        if dist <= 1.0:
                            mask[z, y, x] = True
        
        return mask
    
    def _simulate_zone_mask(self, shape: Tuple[int, ...], zone_type: str) -> np.ndarray:
        """Simula máscaras de zonas prostáticas para demostración."""
        mask = np.zeros(shape, dtype=bool)
        if len(shape) == 3:
            depth, height, width = shape
            center_z, center_y, center_x = depth // 2, height // 2, width // 2
            
            if zone_type == "peripheral":
                # Zona periférica: anillo exterior
                outer_radius = min(depth // 6, height // 4, width // 4)
                inner_radius = outer_radius * 0.6
            else:  # transition zone
                # Zona de transición: región central
                outer_radius = min(depth // 6, height // 4, width // 4) * 0.6
                inner_radius = 0
            
            for z in range(depth):
                for y in range(height):
                    for x in range(width):
                        dist = np.sqrt((z - center_z) ** 2 + 
                                     (y - center_y) ** 2 + 
                                     (x - center_x) ** 2)
                        if inner_radius <= dist <= outer_radius:
                            mask[z, y, x] = True
        
        return mask
    
    def _simulate_lesion_mask(self, shape: Tuple[int, ...]) -> np.ndarray:
        """Simula máscaras de lesiones para demostración."""
        mask = np.zeros(shape, dtype=bool)
        if len(shape) == 3:
            depth, height, width = shape
            # Crear 1-3 lesiones pequeñas aleatorias
            num_lesions = np.random.randint(1, 4)
            
            for _ in range(num_lesions):
                center_z = np.random.randint(depth // 4, 3 * depth // 4)
                center_y = np.random.randint(height // 4, 3 * height // 4)
                center_x = np.random.randint(width // 4, 3 * width // 4)
                radius = np.random.randint(2, 6)
                
                for z in range(max(0, center_z - radius), min(depth, center_z + radius)):
                    for y in range(max(0, center_y - radius), min(height, center_y + radius)):
                        for x in range(max(0, center_x - radius), min(width, center_x + radius)):
                            dist = np.sqrt((z - center_z) ** 2 + 
                                         (y - center_y) ** 2 + 
                                         (x - center_x) ** 2)
                            if dist <= radius:
                                mask[z, y, x] = True
        
        return mask


class SegmentationEditingService:
    """
    Servicio para edición manual de segmentaciones médicas.
    
    Proporciona herramientas de alto nivel para que los médicos modifiquen
    segmentaciones automáticas, combinen regiones, y apliquen correcciones
    basadas en su criterio clínico experto.
    """
    
    def __init__(self, segmentation_repository: SegmentationRepository):
        self._segmentation_repository = segmentation_repository
    
    async def apply_brush_edit(
        self,
        segmentation: MedicalSegmentation,
        brush_coordinates: List[Tuple[int, int, int]],
        brush_radius: int,
        edit_mode: str,  # "add", "remove", "replace"
        editor_id: str
    ) -> MedicalSegmentation:
        """
        Aplica edición con pincel a una segmentación existente.
        
        Args:
            segmentation: Segmentación base a editar
            brush_coordinates: Lista de coordenadas donde aplicar el pincel
            brush_radius: Radio del pincel en voxels
            edit_mode: Modo de edición ("add", "remove", "replace")
            editor_id: ID del usuario editor
            
        Returns:
            Nueva segmentación con las ediciones aplicadas
        """
        if segmentation.is_locked:
            raise SegmentationEditingError(
                f"La segmentación {segmentation.segmentation_id} está bloqueada para edición"
            )
        
        # Crear copia de la máscara para edición
        edited_mask = segmentation.mask_data.copy()
        
        # Aplicar cada stroke del pincel
        for coord in brush_coordinates:
            brush_mask = self._create_spherical_brush(
                edited_mask.shape, coord, brush_radius
            )
            
            if edit_mode == "add":
                edited_mask = np.logical_or(edited_mask, brush_mask)
            elif edit_mode == "remove":
                edited_mask = np.logical_and(edited_mask, ~brush_mask)
            elif edit_mode == "replace":
                # Remover todo y luego agregar el pincel
                edited_mask = np.logical_and(edited_mask, ~brush_mask)
                edited_mask = np.logical_or(edited_mask, brush_mask)
            else:
                raise ValueError(f"Modo de edición '{edit_mode}' no reconocido")
        
        # Crear nueva segmentación editada
        edited_segmentation = MedicalSegmentation(
            mask_data=edited_mask,
            anatomical_region=segmentation.anatomical_region,
            segmentation_type=SegmentationType.MANUAL,
            creation_date=datetime.now(),
            creator_id=editor_id,
            parent_image_uid=segmentation._parent_image_uid,
            description=f"Manual edit of {segmentation._description}"
        )
        
        # Guardar la nueva segmentación
        await self._segmentation_repository.save_segmentation(edited_segmentation)
        
        return edited_segmentation
    
    async def merge_segmentations(
        self,
        segmentations: List[MedicalSegmentation],
        merge_strategy: str,  # "union", "intersection", "largest"
        editor_id: str
    ) -> MedicalSegmentation:
        """
        Combina múltiples segmentaciones en una sola.
        
        Args:
            segmentations: Lista de segmentaciones a combinar
            merge_strategy: Estrategia de combinación
            editor_id: ID del usuario que realiza la combinación
            
        Returns:
            Nueva segmentación combinada
        """
        if not segmentations:
            raise SegmentationEditingError("Se requiere al menos una segmentación para combinar")
        
        # Validar que todas las segmentaciones tengan las mismas dimensiones
        base_shape = segmentations[0].dimensions
        for seg in segmentations[1:]:
            if seg.dimensions != base_shape:
                raise SegmentationEditingError(
                    "Todas las segmentaciones deben tener las mismas dimensiones"
                )
        
        # Aplicar estrategia de combinación
        if merge_strategy == "union":
            merged_mask = segmentations[0].mask_data.copy()
            for seg in segmentations[1:]:
                merged_mask = np.logical_or(merged_mask, seg.mask_data)
        
        elif merge_strategy == "intersection":
            merged_mask = segmentations[0].mask_data.copy()
            for seg in segmentations[1:]:
                merged_mask = np.logical_and(merged_mask, seg.mask_data)
        
        elif merge_strategy == "largest":
            # Seleccionar la segmentación con mayor volumen
            largest_seg = max(segmentations, key=lambda s: s.voxel_count)
            merged_mask = largest_seg.mask_data.copy()
        
        else:
            raise ValueError(f"Estrategia de combinación '{merge_strategy}' no reconocida")
        
        # Crear nueva segmentación combinada
        merged_segmentation = MedicalSegmentation(
            mask_data=merged_mask,
            anatomical_region=segmentations[0].anatomical_region,
            segmentation_type=SegmentationType.MANUAL,
            creation_date=datetime.now(),
            creator_id=editor_id,
            parent_image_uid=segmentations[0]._parent_image_uid,
            description=f"Merged segmentation ({merge_strategy})"
        )
        
        # Guardar la segmentación combinada
        await self._segmentation_repository.save_segmentation(merged_segmentation)
        
        return merged_segmentation
    
    def _create_spherical_brush(
        self,
        shape: Tuple[int, ...],
        center: Tuple[int, int, int],
        radius: int
    ) -> np.ndarray:
        """
        Crea una máscara esférica para el pincel de edición.
        
        Args:
            shape: Dimensiones del volumen objetivo
            center: Coordenadas del centro del pincel
            radius: Radio del pincel
            
        Returns:
            Máscara binaria con la forma del pincel
        """
        brush_mask = np.zeros(shape, dtype=bool)
        
        if len(shape) != 3 or len(center) != 3:
            raise ValueError("Se requieren coordenadas 3D para el pincel")
        
        depth, height, width = shape
        center_z, center_y, center_x = center
        
        # Calcular límites del pincel para optimización
        z_min = max(0, center_z - radius)
        z_max = min(depth, center_z + radius + 1)
        y_min = max(0, center_y - radius)
        y_max = min(height, center_y + radius + 1)
        x_min = max(0, center_x - radius)
        x_max = min(width, center_x + radius + 1)
        
        # Crear máscara esférica
        for z in range(z_min, z_max):
            for y in range(y_min, y_max):
                for x in range(x_min, x_max):
                    distance = np.sqrt(
                        (z - center_z) ** 2 + 
                        (y - center_y) ** 2 + 
                        (x - center_x) ** 2
                    )
                    if distance <= radius:
                        brush_mask[z, y, x] = True
        
        return brush_mask


# Excepciones específicas del servicio
class AISegmentationError(Exception):
    """Excepción para errores en segmentación automática."""
    pass


class ImageValidationError(Exception):
    """Excepción para errores de validación de imágenes."""
    pass


class SegmentationEditingError(Exception):
    """Excepción para errores durante la edición de segmentaciones."""
    pass