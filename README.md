# Medical Imaging Workstation - Prostate Cancer Detection

Una aplicación profesional de visualización médica especializada en análisis de cáncer prostático, desarrollada con **arquitectura hexagonal (Clean Architecture)** y integración con **nnUNetv2** para segmentación automática con IA.

## 🏥 Características Principales

### Visualización Médica Avanzada
- **Visualización 2D multi-planar**: Cortes axiales, sagitales y coronales simultáneos
- **Renderizado 3D volumétrico**: Motor VTK con renderizado GPU-acelerado
- **Configuración de ventana/nivel**: Presets optimizados para diferentes modalidades (CT, MRI)
- **Tema oscuro profesional**: Optimizado para entornos médicos y reducción de fatiga visual

### Inteligencia Artificial Médica
- **Integración nnUNetv2**: Segmentación automática de próstata y detección de lesiones
- **Análisis multi-región**: Próstata completa, zona periférica, zona de transición
- **Detección de lesiones sospechosas**: Con niveles de confianza interpretables
- **Validación automática**: Sistema de QA para predicciones de IA

### Herramientas de Medición Profesionales
- **Mediciones 2D/3D**: Distancias, ángulos, áreas y volúmenes precisos
- **Calibración automática**: Basada en espaciado DICOM real
- **Herramientas de ROI**: Selección de regiones de interés irregulares
- **Estadísticas cuantitativas**: Análisis automático de intensidades y métricas geométricas

### Gestión de Datos DICOM
- **Carga nativa DICOM**: Soporte completo para estándares médicos
- **Navegación de pacientes**: Organización por paciente/estudio/serie
- **Metadatos preservados**: Información médica crítica mantenida
- **Exportación estándar**: Formatos NIFTI, STL, DICOM secundario

## 🏗️ Arquitectura del Sistema

### Arquitectura Hexagonal (Clean Architecture)

```
┌─────────────────────────────────────────────────────────────┐
│                     INFRAESTRUCTURA                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │     UI      │  │   Storage   │  │   Visualization     │  │
│  │   (PyQt6)   │  │  (DICOM)    │  │       (VTK)         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
┌────────────────────────────────────────────────────────────────┐
│                      APLICACIÓN                                │
│  ┌─────────────────────┐  ┌─────────────────────────────────┐  │
│  │   Image Services    │  │   Segmentation Services         │  │
│  │                     │  │                                 │  │
│  │ • Loading           │  │ • AI Prediction (nnUNet)        │  │
│  │ • Visualization     │  │ • Manual Editing                │  │
│  │ • Window/Level      │  │ • Quantitative Analysis         │  │
│  └─────────────────────┘  └─────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
                            │
┌────────────────────────────────────────────────────────────────┐
│                       DOMINIO                                  │
│  ┌─────────────────┐      ┌─────────────────────────────────┐  │
│  │ MedicalImage    │      │  MedicalSegmentation            │  │
│  │                 │      │                                 │  │
│  │ • Metadatos     │      │ • Anatomical Regions            │  │
│  │ • Espaciado     │      │ • Confidence Levels             │  │
│  │ • Window/Level  │      │ • Geometric Metrics             │  │
│  │ • Validaciones  │      │ • Morphological Operations      │  │
│  └─────────────────┘      └─────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

### Beneficios de la Arquitectura

1. **Independencia de Frameworks**: La lógica médica no depende de PyQt6, VTK o bases de datos específicas
2. **Testabilidad**: Cada capa puede probarse independientemente
3. **Mantenibilidad**: Cambios en UI no afectan la lógica médica
4. **Escalabilidad**: Fácil adición de nuevas modalidades o algoritmos de IA
5. **Compliance Médico**: Separación clara entre lógica de negocio y infraestructura

## 🚀 Instalación y Configuración

### Requisitos del Sistema

#### Mínimos
- **Python**: 3.8 o superior
- **RAM**: 4GB mínimo
- **Espacio en disco**: 10GB
- **GPU**: Opcional (recomendada para IA)

#### Recomendados
- **Python**: 3.10+
- **RAM**: 16GB
- **Espacio en disco**: 100GB
- **GPU**: NVIDIA con CUDA (8GB+ VRAM)
- **CPU**: 4+ núcleos

### Instalación de Dependencias

```bash
# Clonar repositorio
git clone https://github.com/medical-imaging/prostate-workstation.git
cd prostate-workstation

# Crear entorno virtual
python -m venv medical_env
source medical_env/bin/activate  # Linux/Mac
# medical_env\Scripts\activate     # Windows

# Instalar dependencias críticas
pip install PyQt6>=6.0.0
pip install numpy>=1.20.0
pip install pydicom>=2.0.0
pip install SimpleITK>=2.0.0
pip install vtk>=9.0.0

# Dependencias de IA (opcionales)
pip install torch torchvision  # Para GPU: torch+cu118
pip install nnunet

# Dependencias adicionales
pip install scipy scikit-image matplotlib Pillow
pip install psutil pyyaml
```

### Configuración Inicial

```bash
# Ejecutar validación del sistema
python -c "from infrastructure.utils.startup_validator import SystemValidator; print(SystemValidator().validate_system())"

# Crear directorios necesarios
mkdir -p medical_data logs temp exports models

# Configurar modelos nnUNet (si están disponibles)
# Descargar modelo preentrenado para próstata
# Configurar NNUNET_RESULTS en variables de entorno
```

### Configuración de nnUNet (Opcional)

```bash
# Descargar modelo preentrenado para próstata
# (Reemplazar con URLs reales de modelos)
wget https://example.com/nnunet_prostate_model.zip
unzip nnunet_prostate_model.zip -d ./models/

# Configurar variables de entorno
export NNUNET_RESULTS="./models/nnunet_results"
export NNUNET_RAW_DATA="./models/nnunet_raw"
export NNUNET_PREPROCESSED="./models/nnunet_preprocessed"
```

## 🖥️ Uso de la Aplicación

### Inicio Básico

```bash
# Iniciar aplicación
python main.py

# Con configuración personalizada
python main.py --storage /path/to/medical/data --debug

# Sin splash screen
python main.py --no-splash
```

### Flujo de Trabajo Típico

#### 1. Cargar Imágenes DICOM
- **Archivo único**: `File > Open Image/Study...`
- **Directorio completo**: `File > Import DICOM Directory...`
- **Navegador de pacientes**: Panel izquierdo para navegar estudios existentes

#### 2. Visualización y Análisis
- **Vista 2D**: Navegación por slices con mouse wheel
- **Vista 3D**: Renderizado volumétrico interactivo
- **Ventana/Nivel**: Ajuste manual o presets automáticos
- **Mediciones**: Herramientas de distancia, ángulo y ROI

#### 3. Análisis con IA
1. Seleccionar imagen en visualizador
2. Ir a panel "AI Analysis"
3. Configurar parámetros:
   - Umbral de confianza
   - Regiones a segmentar
   - Detección de lesiones
4. Ejecutar análisis: `Run Full Analysis`

#### 4. Edición Manual
- Usar herramientas de pincel para correcciones
- Aplicar operaciones morfológicas
- Combinar múltiples segmentaciones

#### 5. Análisis Cuantitativo
- Ver métricas geométricas automáticas
- Estadísticas de intensidad
- Exportar resultados

### Atajos de Teclado

| Acción | Atajo | Descripción |
|--------|-------|-------------|
| Slice anterior | ↑ | Navegar al slice previo |
| Slice siguiente | ↓ | Navegar al slice siguiente |
| Saltar slices | Page Up/Down | Navegar 10 slices |
| Vista 2D | 1 | Cambiar a vista 2D |
| Vista 3D | 2 | Cambiar a vista 3D |
| Herramienta distancia | M | Activar medición de distancia |
| Herramienta ángulo | A | Activar medición de ángulo |
| Herramienta ROI | R | Activar selección de ROI |
| Análisis IA completo | Ctrl+Shift+A | Ejecutar análisis completo |

## 📊 Características Médicas Específicas

### Regiones Anatómicas Soportadas

```python
# Próstata
PROSTATE_WHOLE              # Próstata completa
PROSTATE_PERIPHERAL_ZONE     # Zona periférica
PROSTATE_TRANSITION_ZONE     # Zona de transición
PROSTATE_CENTRAL_ZONE        # Zona central

# Patología
SUSPICIOUS_LESION            # Lesión sospechosa
CONFIRMED_CANCER            # Cáncer confirmado
BENIGN_HYPERPLASIA          # Hiperplasia benigna

# Estructuras relacionadas
URETHRA                     # Uretra
SEMINAL_VESICLES           # Vesículas seminales
```

### Modalidades de Imagen

- **CT**: Configuraciones optimizadas para pelvis
- **MRI**: Secuencias T1, T2, DWI, DCE
- **Ultrasonido**: Próstata transrectal

### Métricas Cuantitativas

```python
# Métricas Geométricas
- Volumen (mm³)
- Área de superficie (mm²)
- Diámetro máximo
- Esfericidad
- Compacidad

# Estadísticas de Intensidad
- Media, mediana, desviación estándar
- Percentiles 25, 75
- Entropía de Shannon
- Uniformidad
```

## 🔧 Configuración Avanzada

### Archivo de Configuración

La aplicación usa `./config/medical_imaging_config.yaml`:

```yaml
# Configuración de IA
ai_models:
  nnunet_model_path: "./models/nnunet_prostate"
  confidence_threshold: 0.7
  use_gpu: true
  preprocessing:
    normalize_intensity: true
    resample_spacing: [1.0, 1.0, 1.0]

# Configuración de visualización
visualization:
  default_theme: "dark"
  max_memory_usage_gb: 4
  rendering_quality: "high"
  
# Configuración de próstata específica
prostate_analysis:
  pirads_scoring:
    enable_pirads: true
    version: "2.1"
  lesion_detection:
    min_lesion_size_mm: 5.0
```

### Logging y Auditoría

```python
# Configurar logging médico
from infrastructure.utils.logging_config import get_medical_logger

logger = get_medical_logger("my_module")
logger.set_medical_context(
    patient_id="PATIENT_001",
    study_uid="1.2.3.4.5",
    user_id="DR_SMITH"
)

# Log con contexto médico automático
logger.info("Loaded MRI study")
logger.audit("image_loaded", outcome="success")
```

## 🧪 Testing y Validación

### Pruebas Unitarias

```bash
# Ejecutar tests del dominio
python -m pytest tests/domain/ -v

# Tests de servicios de aplicación
python -m pytest tests/application/ -v

# Tests de integración
python -m pytest tests/integration/ -v
```

### Validación del Sistema

```bash
# Validación completa del sistema
python -c "
from infrastructure.utils.startup_validator import SystemValidator
result = SystemValidator().validate_system()
print(result)
"

# Generar reporte del sistema
python scripts/generate_system_report.py
```

## 📈 Rendimiento y Optimización

### Configuraciones de Rendimiento

```yaml
# En config.yaml
performance:
  max_concurrent_operations: 4
  cache_size_mb: 512
  preload_adjacent_slices: 3
  lazy_load_volumes: true
  
visualization:
  volume_rendering:
    sample_distance: 0.5  # Menor = mejor calidad, más lento
    enable_shading: true
    gradient_opacity: true
```

### Optimización de Memoria

La aplicación implementa gestión inteligente de memoria:

- **Lazy loading**: Imágenes se cargan bajo demanda
- **Cache LRU**: Mantiene solo imágenes recientes en memoria
- **Submuestreo adaptativo**: Para renderizado 3D fluido
- **Garbage collection**: Liberación automática de recursos

## 🔒 Consideraciones Médicas y de Seguridad

### Compliance y Regulaciones

- **DICOM**: Cumplimiento completo con estándares DICOM
- **HIPAA**: Logging sin información personal identificable
- **Auditoría**: Trazabilidad completa de acciones de usuario
- **Anonimización**: Herramientas para remover datos sensibles

### Validación Clínica

```python
# Validación automática de predicciones IA
validation_result = ai_service.validate_ai_predictions(
    segmentations,
    validation_criteria={
        "min_quality_threshold": 0.7,
        "anatomical_consistency": True,
        "size_validation": True
    }
)

if validation_result["requires_manual_review"]:
    # Señalar al médico para revisión
    pass
```

## 🤝 Contribución y Desarrollo

### Estructura del Proyecto

```
medical_imaging_app/
├── domain/                 # Lógica de negocio pura
│   ├── entities/          # Entidades médicas
│   └── repositories/      # Interfaces abstractas
├── application/           # Casos de uso
│   └── services/         # Servicios de aplicación  
├── infrastructure/       # Implementaciones concretas
│   ├── ui/               # Interfaz PyQt6
│   ├── storage/          # Persistencia DICOM
│   ├── visualization/    # Motor VTK
│   └── utils/            # Utilidades del sistema
├── tests/                # Tests automatizados
├── config/              # Configuraciones
├── models/              # Modelos de IA
└── main.py             # Punto de entrada
```

### Agregar Nueva Modalidad

1. **Dominio**: Extender `ImageModalityType` enum
2. **Servicios**: Agregar presets en `ImageVisualizationService`
3. **UI**: Actualizar configuraciones de ventana/nivel
4. **Tests**: Validar nueva modalidad

### Integrar Nuevo Modelo de IA

1. **Wrapper**: Crear adaptador en `infrastructure/ai/`
2. **Servicio**: Integrar en `AISegmentationService`
3. **UI**: Agregar opciones en `SegmentationPanel`
4. **Config**: Definir parámetros en configuración

## 📚 Referencias y Documentación

### Standards Médicos
- [DICOM Standard](https://www.dicomstandard.org/)
- [PI-RADS v2.1](https://www.acr.org/Clinical-Resources/Reporting-and-Data-Systems/PI-RADS)
- [nnU-Net Documentation](https://github.com/MIC-DKFZ/nnUNet)

### Arquitectura
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)

### Tecnologías
- [PyQt6 Documentation](https://doc.qt.io/qtforpython/)
- [VTK User Guide](https://vtk.org/documentation/)
- [SimpleITK Examples](https://simpleitk.readthedocs.io/)

## 📄 Licencia

```
Medical Imaging Workstation - Prostate Cancer Detection
Copyright (C) 2024 Medical Software Solutions

Este software está diseñado para uso médico profesional.
Debe usarse bajo supervisión médica calificada.

AVISO MÉDICO: Este software es una herramienta de asistencia
diagnóstica y no reemplaza el juicio clínico profesional.
Todas las decisiones médicas deben ser validadas por
profesionales médicos calificados.
```

## 🆘 Soporte y Resolución de Problemas

### Problemas Comunes

#### 1. Error de OpenGL/VTK
```bash
# Linux: Instalar drivers de GPU
sudo apt-get install mesa-utils
# Verificar: glxinfo | grep OpenGL

# Windows: Actualizar drivers de GPU
```

#### 2. Memoria Insuficiente
```yaml
# Reducir en config.yaml
visualization:
  max_memory_usage_gb: 2
performance:
  cache_size_mb: 256
```

#### 3. Modelo nnUNet No Encontrado
```bash
# Verificar rutas en config.yaml
ai_models:
  nnunet_model_path: "./models/nnunet_prostate"
  
# Verificar variables de entorno
echo $NNUNET_RESULTS
```

### Logs y Diagnóstico

```bash
# Ver logs en tiempo real
tail -f logs/medical_imaging.log

# Ver logs de errores solamente
tail -f logs/medical_imaging.errors.log

# Auditoría médica
tail -f logs/medical_imaging.audit.jsonl
```

### Reporte de Bugs

Para reportar problemas:

1. **Capturar logs**: Incluir archivos de log relevantes
2. **Información del sistema**: Ejecutar validador del sistema
3. **Pasos para reproducir**: Secuencia exacta de acciones
4. **Imágenes de muestra**: Si es posible, incluir datos DICOM anónimos

---

**⚕️ IMPORTANTE**: Esta aplicación es una herramienta de asistencia diagnóstica. Todas las decisiones clínicas deben ser validadas por profesionales médicos calificados.