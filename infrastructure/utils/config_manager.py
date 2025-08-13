"""
infrastructure/utils/config_manager.py

Gestor de configuración para la aplicación médica.
Maneja carga, validación y persistencia de configuraciones
para diferentes componentes del sistema.
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union
import logging


class ConfigurationManager:
    """
    Gestor centralizado de configuración para la aplicación médica.
    
    Maneja configuraciones para:
    - Rutas de almacenamiento y datos
    - Parámetros de IA y modelos
    - Configuraciones de visualización
    - Preferencias de usuario
    - Configuraciones de sistema
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Inicializa el gestor de configuración.
        
        Args:
            config_file: Ruta al archivo de configuración (opcional)
        """
        self._config_file = config_file or "./config/medical_imaging_config.yaml"
        self._config_data: Dict[str, Any] = {}
        self._default_config = self._get_default_configuration()
        self._logger = logging.getLogger(__name__)
        
        # Crear directorio de configuración si no existe
        config_dir = Path(self._config_file).parent
        config_dir.mkdir(parents=True, exist_ok=True)
    
    def load_configuration(self) -> bool:
        """
        Carga la configuración desde archivo.
        
        Returns:
            True si se cargó exitosamente, False si usa defaults
        """
        try:
            config_path = Path(self._config_file)
            
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    if config_path.suffix.lower() == '.yaml' or config_path.suffix.lower() == '.yml':
                        self._config_data = yaml.safe_load(f)
                    else:
                        self._config_data = json.load(f)
                
                # Validar y completar con defaults
                self._config_data = self._merge_with_defaults(self._config_data)
                
                self._logger.info(f"Configuración cargada desde {config_path}")
                return True
            
            else:
                # Usar configuración por defecto
                self._config_data = self._default_config.copy()
                self._logger.warning(f"Archivo de configuración no encontrado, usando defaults")
                
                # Crear archivo de configuración por defecto
                self.save_configuration()
                
                return False
                
        except Exception as e:
            self._logger.error(f"Error cargando configuración: {e}")
            self._config_data = self._default_config.copy()
            return False
    
    def save_configuration(self) -> bool:
        """
        Guarda la configuración actual en archivo.
        
        Returns:
            True si se guardó exitosamente
        """
        try:
            config_path = Path(self._config_file)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                if config_path.suffix.lower() == '.yaml' or config_path.suffix.lower() == '.yml':
                    yaml.dump(self._config_data, f, default_flow_style=False, indent=2)
                else:
                    json.dump(self._config_data, f, indent=2, ensure_ascii=False)
            
            self._logger.info(f"Configuración guardada en {config_path}")
            return True
            
        except Exception as e:
            self._logger.error(f"Error guardando configuración: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtiene un valor de configuración.
        
        Args:
            key: Clave de configuración (soporta notación punto)
            default: Valor por defecto si la clave no existe
            
        Returns:
            Valor de configuración o default
        """
        try:
            # Soportar notación punto para keys anidadas
            keys = key.split('.')
            value = self._config_data
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
            
        except Exception:
            return default
    
    def set(self, key: str, value: Any) -> None:
        """
        Establece un valor de configuración.
        
        Args:
            key: Clave de configuración (soporta notación punto)
            value: Valor a establecer
        """
        try:
            keys = key.split('.')
            config_dict = self._config_data
            
            # Navegar hasta el penúltimo nivel
            for k in keys[:-1]:
                if k not in config_dict:
                    config_dict[k] = {}
                config_dict = config_dict[k]
            
            # Establecer el valor final
            config_dict[keys[-1]] = value
            
        except Exception as e:
            self._logger.error(f"Error estableciendo configuración {key}: {e}")
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Obtiene una sección completa de configuración.
        
        Args:
            section: Nombre de la sección
            
        Returns:
            Diccionario con la sección de configuración
        """
        return self._config_data.get(section, {})
    
    def update_section(self, section: str, data: Dict[str, Any]) -> None:
        """
        Actualiza una sección completa de configuración.
        
        Args:
            section: Nombre de la sección
            data: Nuevos datos para la sección
        """
        if section not in self._config_data:
            self._config_data[section] = {}
        
        self._config_data[section].update(data)
    
    def validate_configuration(self) -> Dict[str, Any]:
        """
        Valida la configuración actual.
        
        Returns:
            Diccionario con resultados de validación
        """
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Validar rutas críticas
        critical_paths = [
            "storage_path",
            "models_path",
            "temp_path"
        ]
        
        for path_key in critical_paths:
            path_value = self.get(path_key)
            if path_value:
                path_obj = Path(path_value)
                if not path_obj.exists():
                    try:
                        path_obj.mkdir(parents=True, exist_ok=True)
                        validation_result["warnings"].append(
                            f"Created missing directory: {path_value}"
                        )
                    except Exception as e:
                        validation_result["errors"].append(
                            f"Cannot create directory {path_value}: {e}"
                        )
                        validation_result["is_valid"] = False
        
        # Validar configuraciones de IA
        ai_config = self.get_section("ai_models")
        if ai_config:
            model_path = ai_config.get("nnunet_model_path")
            if model_path and not Path(model_path).exists():
                validation_result["warnings"].append(
                    f"nnUNet model path not found: {model_path}"
                )
        
        # Validar configuraciones de visualización
        viz_config = self.get_section("visualization")
        if viz_config:
            max_memory_gb = viz_config.get("max_memory_usage_gb", 4)
            if max_memory_gb < 2:
                validation_result["warnings"].append(
                    "Low memory limit may affect 3D rendering performance"
                )
        
        return validation_result
    
    def _get_default_configuration(self) -> Dict[str, Any]:
        """
        Retorna la configuración por defecto del sistema.
        
        Returns:
            Diccionario con configuración por defecto
        """
        return {
            # Configuración general
            "application": {
                "name": "Medical Imaging Workstation",
                "version": "1.0.0",
                "debug_mode": False,
                "log_level": "INFO",
                "autosave_interval_minutes": 5
            },
            
            # Rutas del sistema
            "storage_path": "./medical_data",
            "models_path": "./models",
            "temp_path": "./temp",
            "exports_path": "./exports",
            "logs_path": "./logs",
            "backups_path": "./backups",
            
            # Configuración de base de datos/repositorio
            "repository": {
                "type": "file_system",  # "file_system" o "database"
                "index_cache_size": 1000,
                "enable_compression": True,
                "backup_frequency_hours": 24
            },
            
            # Configuración de modelos de IA
            "ai_models": {
                "nnunet_model_path": "./models/nnunet_prostate",
                "confidence_threshold": 0.7,
                "batch_size": 1,
                "use_gpu": True,
                "gpu_memory_fraction": 0.8,
                "preprocessing": {
                    "normalize_intensity": True,
                    "resample_spacing": [1.0, 1.0, 1.0],
                    "crop_to_roi": True
                },
                "postprocessing": {
                    "remove_small_objects": True,
                    "min_object_size": 100,
                    "smooth_contours": True,
                    "fill_holes": True
                }
            },
            
            # Configuración de visualización
            "visualization": {
                "default_theme": "dark",
                "max_memory_usage_gb": 4,
                "enable_gpu_rendering": True,
                "default_window_level": {
                    "CT": {"window": 400, "level": 40},
                    "MRI": {"window": 600, "level": 300}
                },
                "rendering_quality": "high",  # "low", "medium", "high", "ultra"
                "anti_aliasing": True,
                "volume_rendering": {
                    "sample_distance": 0.5,
                    "enable_shading": True,
                    "gradient_opacity": True
                }
            },
            
            # Configuración de herramientas de medición
            "measurement_tools": {
                "default_units": "mm",
                "precision_decimals": 2,
                "line_thickness": 2,
                "text_size": 12,
                "colors": {
                    "distance": "#FFFF00",
                    "angle": "#00FF00", 
                    "roi": "#FF00FF"
                },
                "auto_save_measurements": True
            },
            
            # Configuración de segmentación
            "segmentation": {
                "default_opacity": 0.4,
                "smooth_surfaces": True,
                "enable_editing": True,
                "max_undo_levels": 20,
                "auto_validate": True,
                "region_colors": {
                    "prostate_whole": "#CC9966",
                    "prostate_peripheral_zone": "#66CC66",
                    "prostate_transition_zone": "#6666CC",
                    "suspicious_lesion": "#FFCC00",
                    "confirmed_cancer": "#FF3333",
                    "benign_hyperplasia": "#99CC99",
                    "urethra": "#CC66CC",
                    "seminal_vesicles": "#CCCC66"
                }
            },
            
            # Configuración de exportación
            "export": {
                "default_format": "nifti",  # "nifti", "dicom", "stl"
                "include_metadata": True,
                "compress_exports": True,
                "export_measurements": True,
                "anonymize_exports": False
            },
            
            # Configuración de red (para integraciones futuras)
            "network": {
                "enable_dicom_server": False,
                "dicom_port": 11112,
                "enable_web_interface": False,
                "web_port": 8080,
                "ssl_enabled": False
            },
            
            # Configuración de seguridad y privacidad
            "security": {
                "require_user_authentication": False,
                "session_timeout_minutes": 120,
                "audit_user_actions": True,
                "encrypt_sensitive_data": True,
                "anonymize_logs": True
            },
            
            # Configuración de rendimiento
            "performance": {
                "max_concurrent_operations": 4,
                "cache_size_mb": 512,
                "preload_adjacent_slices": 3,
                "lazy_load_volumes": True,
                "memory_management": {
                    "enable_garbage_collection": True,
                    "gc_threshold_mb": 1024,
                    "clear_cache_on_memory_pressure": True
                }
            },
            
            # Configuración específica de próstata
            "prostate_analysis": {
                "default_protocols": {
                    "t2w_protocol": {
                        "sequence_name": "T2W",
                        "plane": "axial",
                        "slice_thickness_mm": 3.0
                    },
                    "dwi_protocol": {
                        "sequence_name": "DWI", 
                        "b_values": [0, 1000, 2000],
                        "adc_calculation": True
                    }
                },
                "pirads_scoring": {
                    "enable_pirads": True,
                    "version": "2.1",
                    "require_all_sequences": False
                },
                "lesion_detection": {
                    "min_lesion_size_mm": 5.0,
                    "confidence_threshold": 0.6,
                    "enable_size_filtering": True
                }
            }
        }
    
    def _merge_with_defaults(self, user_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Combina configuración de usuario con defaults.
        
        Args:
            user_config: Configuración del usuario
            
        Returns:
            Configuración combinada
        """
        def merge_dicts(default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
            """Combina diccionarios recursivamente."""
            result = default.copy()
            
            for key, value in user.items():
                if (key in result and 
                    isinstance(result[key], dict) and 
                    isinstance(value, dict)):
                    result[key] = merge_dicts(result[key], value)
                else:
                    result[key] = value
            
            return result
        
        return merge_dicts(self._default_config, user_config)
    
    def reset_to_defaults(self) -> None:
        """Resetea la configuración a valores por defecto."""
        self._config_data = self._default_config.copy()
        self._logger.info("Configuración reseteada a valores por defecto")
    
    def export_config(self, export_path: str) -> bool:
        """
        Exporta la configuración actual a un archivo.
        
        Args:
            export_path: Ruta donde exportar
            
        Returns:
            True si se exportó exitosamente
        """
        try:
            export_file = Path(export_path)
            
            with open(export_file, 'w', encoding='utf-8') as f:
                if export_file.suffix.lower() in ['.yaml', '.yml']:
                    yaml.dump(self._config_data, f, default_flow_style=False, indent=2)
                else:
                    json.dump(self._config_data, f, indent=2, ensure_ascii=False)
            
            self._logger.info(f"Configuración exportada a {export_path}")
            return True
            
        except Exception as e:
            self._logger.error(f"Error exportando configuración: {e}")
            return False