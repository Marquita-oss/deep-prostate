```
medical_imaging_workstation/
│
├── 📄 main.py                           # Punto de entrada principal
├── 📄 run_medical_workstation.py        # Launcher inteligente
├── 📄 demo_medical_workstation.py       # Script de demostración
├── 📄 install.py                        # Instalador automático
├── 📄 setup.py                          # Configuración del paquete
├── 📄 requirements.txt                  # Dependencias Python
├── 📄 README.md                         # Documentación principal
├── 📄 INSTALLATION_REPORT.md            # Reporte de instalación
├── 📄 PROJECT_STRUCTURE.md              # Este archivo
│
├── 📁 domain/                           # Capa de Dominio (Clean Architecture)
│   ├── 📁 entities/                     # Entidades del dominio médico
│   │   ├── 📄 __init__.py
│   │   ├── 📄 medical_image.py          # Entidad imagen médica
│   │   └── 📄 segmentation.py           # Entidad segmentación médica
│   │
│   └── 📁 repositories/                 # Interfaces de repositorio
│       ├── 📄 __init__.py
│       └── 📄 repositories.py           # Interfaces abstractas
│
├── 📁 application/                      # Capa de Aplicación (Casos de Uso)
│   └── 📁 services/                     # Servicios de aplicación
│       ├── 📄 __init__.py
│       ├── 📄 image_services.py         # Servicios de imagen
│       └── 📄 segmentation_services.py  # Servicios de segmentación e IA
│
├── 📁 infrastructure/                   # Capa de Infraestructura
│   ├── 📁 ui/                          # Interfaz de usuario (PyQt6)
│   │   ├── 📄 __init__.py
│   │   ├── 📄 main_window.py           # Ventana principal
│   │   └── 📁 widgets/                 # Widgets especializados
│   │       ├── 📄 __init__.py
│   │       ├── 📄 image_viewer_2d.py   # Visualizador 2D
│   │       ├── 📄 segmentation_panel.py # Panel de segmentación
│   │       └── 📄 patient_browser.py   # Navegador de pacientes
│   │
│   ├── 📁 storage/                     # Persistencia de datos
│   │   ├── 📄 __init__.py
│   │   └── 📄 dicom_repository.py      # Repositorio DICOM
│   │
│   ├── 📁 visualization/               # Motor de renderizado
│   │   ├── 📄 __init__.py
│   │   └── 📄 vtk_renderer.py          # Renderizado 3D con VTK
│   │
│   └── 📁 utils/                       # Utilidades del sistema
│       ├── 📄 __init__.py
│       ├── 📄 logging_config.py        # Configuración de logging
│       ├── 📄 config_manager.py        # Gestor de configuración
│       └── 📄 startup_validator.py     # Validador del sistema
│
├── 📁 tests/                           # Tests automatizados
│   ├── 📄 __init__.py
│   ├── 📄 test_medical_workstation.py  # Tests principales
│   ├── 📁 domain/                      # Tests del dominio
│   ├── 📁 application/                 # Tests de servicios
│   └── 📁 infrastructure/              # Tests de infraestructura
│
├── 📁 config/                          # Archivos de configuración
│   ├── 📄 medical_imaging_config.yaml  # Configuración principal
│   ├── 📄 logging_config.json          # Configuración de logs
│   └── 📄 ai_models_config.yaml        # Configuración de modelos IA
│
├── 📁 medical_data/                    # Datos médicos (creado en runtime)
│   ├── 📁 studies/                     # Estudios DICOM organizados
│   └── 📁 exports/                     # Exportaciones
│
├── 📁 models/                          # Modelos de IA
│   ├── 📁 nnunet_results/              # Resultados de nnUNet
│   ├── 📁 nnunet_raw/                  # Datos crudos de nnUNet
│   └── 📁 nnunet_preprocessed/         # Datos preprocesados
│
├── 📁 logs/                            # Archivos de log
│   ├── 📄 medical_imaging.log          # Log principal
│   ├── 📄 medical_imaging.errors.log   # Solo errores
│   └── 📄 medical_imaging.audit.jsonl  # Auditoría médica
│
├── 📁 temp/                            # Archivos temporales
├── 📁 exports/                         # Exportaciones de resultados
├── 📁 backups/                         # Respaldos automáticos
│
├── 📁 docs/                            # Documentación adicional
│   ├── 📄 API_REFERENCE.md             # Referencia de API
│   ├── 📄 USER_GUIDE.md                # Guía de usuario
│   ├── 📄 DEVELOPER_GUIDE.md           # Guía de desarrollo
│   └── 📁 images/                      # Imágenes de documentación
│
├── 📁 scripts/                         # Scripts de utilidad
│   ├── 📄 generate_system_report.py    # Generador de reportes
│   ├── 📄 backup_medical_data.py       # Respaldo de datos
│   └── 📄 convert_dicom_formats.py     # Conversión de formatos
│
└── 📁 resources/                       # Recursos de la aplicación
    ├── 📁 icons/                       # Iconos de la interfaz
    ├── 📁 themes/                      # Temas visuales
    └── 📁 fonts/                       # Fuentes personalizadas
```
