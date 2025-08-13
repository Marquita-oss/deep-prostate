"""
infrastructure/storage/dicom_repository.py

Implementación concreta del repositorio de imágenes médicas usando DICOM.
Esta implementación maneja archivos DICOM reales, metadatos, y almacenamiento
en sistema de archivos, cumpliendo con las interfaces del dominio.
"""

import os
import json
import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import numpy as np

# Librerías para manejo DICOM
import pydicom
from pydicom.dataset import Dataset, FileDataset
import SimpleITK as sitk

from ...domain.entities.medical_image import (
    MedicalImage, ImageSpacing, ImageModalityType, WindowLevel
)
from ...domain.repositories.repositories import (
    MedicalImageRepository, RepositoryError, ImageNotFoundError,
    DuplicateEntityError, InvalidQueryError
)


class DICOMImageRepository(MedicalImageRepository):
    """
    Implementación del repositorio de imágenes médicas usando archivos DICOM.
    
    Esta clase maneja el almacenamiento y recuperación de imágenes DICOM
    en el sistema de archivos local, manteniendo índices JSON para búsquedas
    rápidas y preservando toda la información médica crítica.
    """
    
    def __init__(self, storage_path: str):
        """
        Inicializa el repositorio DICOM.
        
        Args:
            storage_path: Ruta base donde se almacenan los archivos DICOM
        """
        self._storage_path = Path(storage_path)
        self._images_path = self._storage_path / "images"
        self._metadata_path = self._storage_path / "metadata" 
        self._index_file = self._storage_path / "index.json"
        
        # Crear directorios si no existen
        self._images_path.mkdir(parents=True, exist_ok=True)
        self._metadata_path.mkdir(parents=True, exist_ok=True)
        
        # Cargar o crear índice de imágenes
        self._index = self._load_or_create_index()
        
        # Formatos DICOM soportados
        self._supported_extensions = {'.dcm', '.dicom', '.ima'}
    
    async def save_image(self, image: MedicalImage) -> bool:
        """
        Guarda una imagen médica como archivo DICOM.
        
        Args:
            image: Imagen médica a guardar
            
        Returns:
            True si se guardó exitosamente
            
        Raises:
            RepositoryError: Si hay problemas durante el guardado
        """
        try:
            # Verificar si la imagen ya existe
            if await self.exists_image(image.series_instance_uid):
                raise DuplicateEntityError(
                    f"La imagen con series UID {image.series_instance_uid} ya existe"
                )
            
            # Crear estructura de directorios por paciente y estudio
            patient_dir = self._images_path / self._sanitize_filename(image.patient_id)
            study_dir = patient_dir / self._sanitize_filename(image.study_instance_uid)
            study_dir.mkdir(parents=True, exist_ok=True)
            
            # Generar nombre de archivo DICOM
            filename = f"{self._sanitize_filename(image.series_instance_uid)}.dcm"
            dicom_file_path = study_dir / filename
            
            # Convertir imagen del dominio a DICOM
            dicom_dataset = await self._create_dicom_from_image(image)
            
            # Guardar archivo DICOM
            dicom_dataset.save_as(str(dicom_file_path), write_like_original=False)
            
            # Guardar metadatos extendidos
            metadata_file = self._metadata_path / f"{image.series_instance_uid}.json"
            await self._save_extended_metadata(image, metadata_file)
            
            # Actualizar índice
            self._update_index(image, str(dicom_file_path))
            await self._save_index()
            
            return True
            
        except Exception as e:
            raise RepositoryError(f"Error guardando imagen DICOM: {e}") from e
    
    async def find_by_series_uid(self, series_uid: str) -> Optional[MedicalImage]:
        """
        Busca una imagen específica por su series UID.
        
        Args:
            series_uid: Identificador único de la serie DICOM
            
        Returns:
            Imagen médica si existe, None en caso contrario
        """
        try:
            # Buscar en el índice
            image_info = self._index.get("series", {}).get(series_uid)
            if not image_info:
                return None
            
            # Cargar archivo DICOM
            dicom_path = Path(image_info["file_path"])
            if not dicom_path.exists():
                # Limpiar entrada inválida del índice
                await self._remove_from_index(series_uid)
                return None
            
            # Cargar y convertir DICOM a imagen del dominio
            image = await self._load_dicom_as_image(dicom_path)
            
            return image
            
        except Exception as e:
            raise RepositoryError(f"Error buscando imagen por series UID: {e}") from e
    
    async def find_by_study_uid(self, study_uid: str) -> List[MedicalImage]:
        """
        Busca todas las imágenes de un estudio específico.
        
        Args:
            study_uid: Identificador único del estudio DICOM
            
        Returns:
            Lista de imágenes médicas del estudio
        """
        try:
            study_info = self._index.get("studies", {}).get(study_uid)
            if not study_info:
                return []
            
            # Cargar todas las series del estudio
            images = []
            series_uids = study_info.get("series_list", [])
            
            # Cargar imágenes en paralelo para mejor rendimiento
            load_tasks = [self.find_by_series_uid(uid) for uid in series_uids]
            loaded_images = await asyncio.gather(*load_tasks, return_exceptions=True)
            
            # Filtrar imágenes válidas
            for img in loaded_images:
                if isinstance(img, MedicalImage):
                    images.append(img)
                elif isinstance(img, Exception):
                    # Log del error pero continuar con otras imágenes
                    print(f"Warning: Error cargando imagen del estudio {study_uid}: {img}")
            
            return images
            
        except Exception as e:
            raise RepositoryError(f"Error buscando imágenes por study UID: {e}") from e
    
    async def find_by_patient_id(self, patient_id: str) -> List[MedicalImage]:
        """
        Busca todas las imágenes de un paciente específico.
        
        Args:
            patient_id: Identificador del paciente
            
        Returns:
            Lista de imágenes médicas del paciente
        """
        try:
            patient_info = self._index.get("patients", {}).get(patient_id)
            if not patient_info:
                return []
            
            # Obtener todos los estudios del paciente
            images = []
            study_uids = patient_info.get("study_list", [])
            
            # Cargar imágenes de todos los estudios
            for study_uid in study_uids:
                study_images = await self.find_by_study_uid(study_uid)
                images.extend(study_images)
            
            return images
            
        except Exception as e:
            raise RepositoryError(f"Error buscando imágenes por patient ID: {e}") from e
    
    async def find_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[MedicalImage]:
        """
        Busca imágenes dentro de un rango de fechas.
        
        Args:
            start_date: Fecha de inicio del rango
            end_date: Fecha de fin del rango
            
        Returns:
            Lista de imágenes en el rango especificado
        """
        try:
            if start_date > end_date:
                raise InvalidQueryError("La fecha de inicio debe ser anterior a la fecha de fin")
            
            matching_images = []
            
            # Buscar en el índice por fechas
            for series_uid, series_info in self._index.get("series", {}).items():
                acquisition_date_str = series_info.get("acquisition_date")
                if not acquisition_date_str:
                    continue
                
                try:
                    acquisition_date = datetime.fromisoformat(acquisition_date_str)
                    if start_date <= acquisition_date <= end_date:
                        image = await self.find_by_series_uid(series_uid)
                        if image:
                            matching_images.append(image)
                except ValueError:
                    # Fecha inválida en el índice, omitir
                    continue
            
            return matching_images
            
        except Exception as e:
            raise RepositoryError(f"Error buscando imágenes por rango de fechas: {e}") from e
    
    async def delete_image(self, series_uid: str) -> bool:
        """
        Elimina una imagen del repositorio.
        
        Args:
            series_uid: Identificador de la serie a eliminar
            
        Returns:
            True si se eliminó exitosamente
        """
        try:
            image_info = self._index.get("series", {}).get(series_uid)
            if not image_info:
                return False
            
            # Eliminar archivo DICOM
            dicom_path = Path(image_info["file_path"])
            if dicom_path.exists():
                dicom_path.unlink()
            
            # Eliminar metadatos extendidos
            metadata_file = self._metadata_path / f"{series_uid}.json"
            if metadata_file.exists():
                metadata_file.unlink()
            
            # Actualizar índice
            await self._remove_from_index(series_uid)
            await self._save_index()
            
            return True
            
        except Exception as e:
            raise RepositoryError(f"Error eliminando imagen: {e}") from e
    
    async def update_image_metadata(
        self, 
        series_uid: str, 
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Actualiza metadatos de una imagen existente.
        
        Args:
            series_uid: Identificador de la serie
            metadata: Nuevos metadatos a actualizar
            
        Returns:
            True si se actualizó exitosamente
        """
        try:
            if not await self.exists_image(series_uid):
                raise ImageNotFoundError(f"Imagen con series UID {series_uid} no encontrada")
            
            # Cargar metadatos existentes
            metadata_file = self._metadata_path / f"{series_uid}.json"
            existing_metadata = {}
            
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    existing_metadata = json.load(f)
            
            # Actualizar metadatos
            existing_metadata.update(metadata)
            existing_metadata["last_modified"] = datetime.now().isoformat()
            
            # Guardar metadatos actualizados
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(existing_metadata, f, indent=2, ensure_ascii=False)
            
            # Actualizar índice si es necesario
            if any(key in metadata for key in ["patient_id", "study_instance_uid", "acquisition_date"]):
                # Recargar imagen y actualizar índice
                image = await self.find_by_series_uid(series_uid)
                if image:
                    self._update_index(image, self._index["series"][series_uid]["file_path"])
                    await self._save_index()
            
            return True
            
        except Exception as e:
            raise RepositoryError(f"Error actualizando metadatos: {e}") from e
    
    async def exists_image(self, series_uid: str) -> bool:
        """
        Verifica si una imagen existe en el repositorio.
        
        Args:
            series_uid: Identificador de la serie
            
        Returns:
            True si la imagen existe
        """
        image_info = self._index.get("series", {}).get(series_uid)
        if not image_info:
            return False
        
        # Verificar que el archivo realmente existe
        dicom_path = Path(image_info["file_path"])
        return dicom_path.exists()
    
    async def _load_dicom_as_image(self, dicom_path: Path) -> MedicalImage:
        """
        Carga un archivo DICOM y lo convierte a entidad MedicalImage.
        
        Args:
            dicom_path: Ruta al archivo DICOM
            
        Returns:
            Entidad MedicalImage del dominio
        """
        try:
            # Usar SimpleITK para cargar el volumen completo si es serie multi-slice
            if dicom_path.is_dir():
                # Directorio con múltiples archivos DICOM
                reader = sitk.ImageSeriesReader()
                dicom_names = reader.GetGDCMSeriesFileNames(str(dicom_path))
                reader.SetFileNames(dicom_names)
                sitk_image = reader.Execute()
            else:
                # Archivo DICOM único
                sitk_image = sitk.ReadImage(str(dicom_path))
            
            # Extraer datos de imagen
            image_array = sitk.GetArrayFromImage(sitk_image)
            
            # Extraer espaciado
            spacing_sitk = sitk_image.GetSpacing()
            spacing = ImageSpacing(
                x=float(spacing_sitk[0]),
                y=float(spacing_sitk[1]),
                z=float(spacing_sitk[2]) if len(spacing_sitk) > 2 else 1.0
            )
            
            # Cargar dataset DICOM para metadatos
            if dicom_path.is_file():
                ds = pydicom.dcmread(str(dicom_path))
            else:
                # Para series, usar el primer archivo
                first_file = next(dicom_path.glob("*.dcm"))
                ds = pydicom.dcmread(str(first_file))
            
            # Extraer metadatos DICOM críticos
            modality = self._parse_modality(ds.get("Modality", ""))
            patient_id = str(ds.get("PatientID", ""))
            study_uid = str(ds.get("StudyInstanceUID", ""))
            series_uid = str(ds.get("SeriesInstanceUID", ""))
            
            # Parsear fecha de adquisición
            acquisition_date = self._parse_dicom_date(
                ds.get("AcquisitionDate"), 
                ds.get("AcquisitionTime")
            )
            
            # Crear diccionario de metadatos extendidos
            dicom_metadata = self._extract_dicom_metadata(ds)
            
            # Crear entidad MedicalImage
            medical_image = MedicalImage(
                image_data=image_array,
                spacing=spacing,
                modality=modality,
                patient_id=patient_id,
                study_instance_uid=study_uid,
                series_instance_uid=series_uid,
                acquisition_date=acquisition_date,
                dicom_metadata=dicom_metadata
            )
            
            return medical_image
            
        except Exception as e:
            raise RepositoryError(f"Error cargando archivo DICOM {dicom_path}: {e}") from e
    
    async def _create_dicom_from_image(self, image: MedicalImage) -> FileDataset:
        """
        Convierte una entidad MedicalImage a dataset DICOM.
        
        Args:
            image: Imagen médica del dominio
            
        Returns:
            Dataset DICOM válido
        """
        try:
            # Crear dataset DICOM básico
            file_meta = pydicom.Dataset()
            file_meta.MediaStorageSOPClassUID = pydicom.uid.SecondaryCaptureImageStorage
            file_meta.MediaStorageSOPInstanceUID = pydicom.uid.generate_uid()
            file_meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian
            
            # Crear dataset principal
            ds = FileDataset(
                "temp", {}, 
                file_meta=file_meta,
                preamble=b"\0" * 128
            )
            
            # Metadatos básicos del paciente
            ds.PatientName = image.patient_id
            ds.PatientID = image.patient_id
            
            # Metadatos del estudio
            ds.StudyInstanceUID = image.study_instance_uid
            ds.StudyDate = image.acquisition_date.strftime("%Y%m%d")
            ds.StudyTime = image.acquisition_date.strftime("%H%M%S")
            
            # Metadatos de la serie
            ds.SeriesInstanceUID = image.series_instance_uid
            ds.SeriesDate = image.acquisition_date.strftime("%Y%m%d")
            ds.SeriesTime = image.acquisition_date.strftime("%H%M%S")
            ds.Modality = image.modality.value
            
            # Metadatos de imagen
            ds.SOPInstanceUID = pydicom.uid.generate_uid()
            ds.SOPClassUID = pydicom.uid.SecondaryCaptureImageStorage
            
            # Datos de pixel
            image_data = image.image_data
            if len(image_data.shape) == 3:
                # Volumen 3D - guardar como multi-frame
                ds.NumberOfFrames = image_data.shape[0]
                ds.PixelData = image_data.astype(np.uint16).tobytes()
            else:
                # Imagen 2D
                ds.PixelData = image_data.astype(np.uint16).tobytes()
            
            # Información de pixel
            ds.SamplesPerPixel = 1
            ds.PhotometricInterpretation = "MONOCHROME2"
            ds.Rows, ds.Columns = image_data.shape[-2:]
            ds.BitsAllocated = 16
            ds.BitsStored = 16
            ds.HighBit = 15
            ds.PixelRepresentation = 0
            
            # Espaciado de pixel
            ds.PixelSpacing = [image.spacing.y, image.spacing.x]
            if len(image_data.shape) == 3:
                ds.SliceThickness = image.spacing.z
            
            # Información de ventana/nivel
            wl = image.current_window_level
            ds.WindowCenter = int(wl.level)
            ds.WindowWidth = int(wl.window)
            
            # Metadatos adicionales del dominio
            for key, value in image._dicom_metadata.items():
                if hasattr(ds, key) and value is not None:
                    setattr(ds, key, value)
            
            return ds
            
        except Exception as e:
            raise RepositoryError(f"Error creando DICOM desde imagen: {e}") from e
    
    def _parse_modality(self, modality_str: str) -> ImageModalityType:
        """Convierte string de modalidad DICOM a enum del dominio."""
        modality_map = {
            "CT": ImageModalityType.CT,
            "MR": ImageModalityType.MRI,
            "US": ImageModalityType.ULTRASOUND,
            "XA": ImageModalityType.XRAY,
            "CR": ImageModalityType.XRAY,
            "PT": ImageModalityType.PET
        }
        
        return modality_map.get(modality_str.upper(), ImageModalityType.CT)
    
    def _parse_dicom_date(self, date_str: str, time_str: str = None) -> datetime:
        """Convierte fecha y hora DICOM a datetime."""
        try:
            if not date_str:
                return datetime.now()
            
            # Formato DICOM: YYYYMMDD
            if len(date_str) >= 8:
                year = int(date_str[:4])
                month = int(date_str[4:6])
                day = int(date_str[6:8])
                
                # Parsear tiempo si está disponible
                hour = minute = second = 0
                if time_str and len(time_str) >= 6:
                    hour = int(time_str[:2])
                    minute = int(time_str[2:4])
                    second = int(time_str[4:6])
                
                return datetime(year, month, day, hour, minute, second)
            
            return datetime.now()
            
        except (ValueError, IndexError):
            return datetime.now()
    
    def _extract_dicom_metadata(self, ds: Dataset) -> Dict[str, Any]:
        """Extrae metadatos DICOM relevantes para el dominio."""
        metadata = {}
        
        # Lista de tags DICOM importantes para preservar
        important_tags = [
            "StudyDescription", "SeriesDescription", "ProtocolName",
            "ImageType", "AcquisitionMatrix", "RepetitionTime",
            "EchoTime", "FlipAngle", "MagneticFieldStrength",
            "SliceThickness", "SpacingBetweenSlices", "ImageOrientationPatient",
            "ImagePositionPatient", "PixelBandwidth", "InstitutionName",
            "Manufacturer", "ManufacturerModelName", "SoftwareVersions",
            "ContrastBolusAgent", "BodyPartExamined", "PatientPosition"
        ]
        
        for tag in important_tags:
            if hasattr(ds, tag):
                value = getattr(ds, tag)
                if value is not None:
                    # Convertir a tipos básicos de Python
                    if hasattr(value, 'decode'):
                        metadata[tag] = value.decode('utf-8', errors='ignore')
                    else:
                        metadata[tag] = str(value)
        
        return metadata
    
    def _load_or_create_index(self) -> Dict[str, Any]:
        """Carga el índice existente o crea uno nuevo."""
        if self._index_file.exists():
            try:
                with open(self._index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        
        # Crear índice vacío
        return {
            "version": "1.0",
            "created": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "series": {},      # series_uid -> info
            "studies": {},     # study_uid -> info  
            "patients": {}     # patient_id -> info
        }
    
    def _update_index(self, image: MedicalImage, file_path: str) -> None:
        """Actualiza el índice con información de una nueva imagen."""
        # Actualizar índice de series
        self._index["series"][image.series_instance_uid] = {
            "file_path": file_path,
            "patient_id": image.patient_id,
            "study_instance_uid": image.study_instance_uid,
            "modality": image.modality.value,
            "acquisition_date": image.acquisition_date.isoformat(),
            "dimensions": list(image.dimensions),
            "spacing": {
                "x": image.spacing.x,
                "y": image.spacing.y,
                "z": image.spacing.z
            },
            "added_date": datetime.now().isoformat()
        }
        
        # Actualizar índice de estudios
        if image.study_instance_uid not in self._index["studies"]:
            self._index["studies"][image.study_instance_uid] = {
                "patient_id": image.patient_id,
                "study_date": image.acquisition_date.isoformat(),
                "series_list": [],
                "series_count": 0
            }
        
        study_info = self._index["studies"][image.study_instance_uid]
        if image.series_instance_uid not in study_info["series_list"]:
            study_info["series_list"].append(image.series_instance_uid)
            study_info["series_count"] = len(study_info["series_list"])
        
        # Actualizar índice de pacientes
        if image.patient_id not in self._index["patients"]:
            self._index["patients"][image.patient_id] = {
                "study_list": [],
                "study_count": 0,
                "first_study_date": image.acquisition_date.isoformat()
            }
        
        patient_info = self._index["patients"][image.patient_id]
        if image.study_instance_uid not in patient_info["study_list"]:
            patient_info["study_list"].append(image.study_instance_uid)
            patient_info["study_count"] = len(patient_info["study_list"])
        
        # Actualizar timestamp
        self._index["last_updated"] = datetime.now().isoformat()
    
    async def _remove_from_index(self, series_uid: str) -> None:
        """Remueve una serie del índice y limpia referencias huérfanas."""
        series_info = self._index["series"].pop(series_uid, None)
        if not series_info:
            return
        
        study_uid = series_info["study_instance_uid"]
        patient_id = series_info["patient_id"]
        
        # Limpiar del índice de estudios
        if study_uid in self._index["studies"]:
            study_info = self._index["studies"][study_uid]
            if series_uid in study_info["series_list"]:
                study_info["series_list"].remove(series_uid)
                study_info["series_count"] = len(study_info["series_list"])
            
            # Si no quedan series, eliminar el estudio
            if not study_info["series_list"]:
                self._index["studies"].pop(study_uid, None)
        
        # Limpiar del índice de pacientes
        if patient_id in self._index["patients"]:
            patient_info = self._index["patients"][patient_id]
            # Verificar si el paciente aún tiene otros estudios
            remaining_studies = [
                uid for uid in patient_info["study_list"] 
                if uid in self._index["studies"]
            ]
            
            patient_info["study_list"] = remaining_studies
            patient_info["study_count"] = len(remaining_studies)
            
            # Si no quedan estudios, eliminar el paciente
            if not remaining_studies:
                self._index["patients"].pop(patient_id, None)
        
        self._index["last_updated"] = datetime.now().isoformat()
    
    async def _save_index(self) -> None:
        """Guarda el índice en disco."""
        try:
            with open(self._index_file, 'w', encoding='utf-8') as f:
                json.dump(self._index, f, indent=2, ensure_ascii=False)
        except IOError as e:
            raise RepositoryError(f"Error guardando índice: {e}") from e
    
    async def _save_extended_metadata(self, image: MedicalImage, metadata_file: Path) -> None:
        """Guarda metadatos extendidos en archivo JSON separado."""
        try:
            extended_metadata = {
                "series_instance_uid": image.series_instance_uid,
                "domain_metadata": {
                    "intensity_statistics": image.get_intensity_statistics(),
                    "physical_dimensions": image.get_physical_dimensions(),
                    "current_window_level": {
                        "window": image.current_window_level.window,
                        "level": image.current_window_level.level
                    }
                },
                "dicom_metadata": image._dicom_metadata,
                "created": datetime.now().isoformat(),
                "version": "1.0"
            }
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(extended_metadata, f, indent=2, ensure_ascii=False)
                
        except IOError as e:
            raise RepositoryError(f"Error guardando metadatos extendidos: {e}") from e
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitiza un string para uso como nombre de archivo/directorio."""
        # Reemplazar caracteres problemáticos
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Limitar longitud
        return filename[:200]