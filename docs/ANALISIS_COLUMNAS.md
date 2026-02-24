# Análisis de Columnas del Dashboard de Embargos

## Columnas FUNDAMENTALES (Se usan activamente en el dashboard)

### 1. Columnas de Filtrado (Críticas)
- **`entidad_bancaria`** - Filtro principal, gráfico Top 10 Entidades Bancarias
- **`ciudad`** - Filtro principal, gráfico Top 10 Ciudades, análisis geográfico
- **`estado_embargo`** - Filtro principal, gráfico de distribución por estado
- **`tipo_embargo`** - Filtro principal, gráfico de distribución, proporciones Judicial/Coactivo
- **`mes`** - Filtro principal, evolución temporal, proporciones mensuales

### 2. Columnas de Métricas y Cálculos (Críticas)
- **`montoaembargar`** - Métricas principales (total, promedio), estadísticas, análisis de montos
- **`es_cliente`** - Métricas de porcentaje de clientes, análisis de clientes

### 3. Columnas de Rankings y Visualizaciones (Importantes)
- **`funcionario`** - Gráfico Top 10 Funcionarios
- **`entidad_remitente`** - Gráfico Top 10 Entidades Remitentes
- **`tipo_documento`** - Análisis detallado, distribución de documentos

### 4. Columnas de Búsqueda Global (Opcionales pero útiles)
- **`nombres`** - Solo se usa en búsqueda global (no en análisis)
- **`identificacion`** - Solo se usa en búsqueda global (no en análisis)

### 5. Columnas Mencionadas pero Poco Usadas
- **`estado_demandado`** - Mencionada en columnas principales pero uso limitado
- **`tipo_carta`** - Mencionada en columnas principales pero uso limitado

---

## Columnas NO RELEVANTES (No se usan en el dashboard)

### Columnas de Contacto/Ubicación (No usadas)
- **`correo`** - Correo electrónico (no se usa en ningún análisis)
- **`direccion`** - Dirección física (no se usa en ningún análisis)

### Columnas de Fechas (Cargadas pero no visualizadas)
- **`fecha_banco`** - Se carga pero no se usa en visualizaciones
- **`fecha_oficio`** - Se carga pero no se usa en visualizaciones

### Columnas de Referencia/Identificación (No usadas)
- **`referencia`** - Referencia del oficio (no se usa)
- **`cuenta`** - Número de cuenta (no se usa en análisis)
- **`expediente`** - Número de expediente (no se usa)
- **`id`** - ID del registro (no se usa directamente en visualizaciones)
- **`tipo_identificacion_tipo`** - Tipo de identificación (no se usa)

---

## Resumen

### Total de Columnas Analizadas: ~23 columnas

**Columnas Fundamentales (12):**
1. entidad_bancaria
2. ciudad
3. estado_embargo
4. tipo_embargo
5. mes
6. montoaembargar
7. es_cliente
8. funcionario
9. entidad_remitente
10. tipo_documento
11. estado_demandado (uso limitado)
12. tipo_carta (uso limitado)

**Columnas de Búsqueda (2):**
- nombres
- identificacion

**Columnas No Relevantes (9+):**
- correo
- direccion
- fecha_banco
- fecha_oficio
- referencia
- cuenta
- expediente
- id
- tipo_identificacion_tipo

---

## Recomendaciones

1. **Mantener todas las columnas fundamentales** - Son esenciales para el funcionamiento del dashboard
2. **Considerar eliminar columnas no relevantes** del CSV procesado para:
   - Reducir el tamaño del archivo
   - Mejorar el rendimiento de carga
   - Simplificar el mantenimiento
3. **Las columnas de búsqueda** (`nombres`, `identificacion`) pueden mantenerse si la búsqueda global es importante
4. **Las fechas** (`fecha_banco`, `fecha_oficio`) podrían ser útiles para análisis futuros, pero actualmente no se usan

