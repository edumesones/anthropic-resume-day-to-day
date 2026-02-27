# CLAUDE.md

## Instrucciones para Claude - Anthropic Daily Resume

### Propósito
Generar automáticamente cada 24 horas un resumen de actualizaciones de:
1. **Anthropic Research** - Nuevos papers/publicaciones
2. **Anthropic Docs** - Cambios en documentación de Claude
3. **Anthropic GitHub** - Actualizaciones en repos públicos

### Fuentes de Datos

#### 1. Research (anthropic.com/research)
- URL: https://www.anthropic.com/research
- Scrapear: Títulos de papers, descripciones, fechas
- Selector CSS: `.research-item` o similar
- Output: Lista con título, resumen (2-3 líneas), link directo

#### 2. Docs (platform.claude.com/docs)
- URL: https://platform.claude.com/docs/en/home
- Scrapear: Cambios recientes, nuevas secciones, updates
- Nota: Puede requerir autenticación, alternativa es usar changelog público
- Alternativa: https://docs.anthropic.com/en/api/changelog
- Output: Resumen de cambios en API/docs con links

#### 3. GitHub (github.com/anthropics)
- Org: `anthropics`
- Repos: Todos los públicos
- Datos a extraer por repo:
  - Commits del último día
  - Nuevos releases
  - Issues/PRs importantes
- API: GitHub REST API v3
- Output: Lista de repos con cambios, descripción del cambio, utilidad

### Formato de Salida

Cada día se genera: `daily/YYYY-MM-DD.md`

```markdown
# Resumen Anthropic - 2024-02-27

## 🔬 Research

### [Título del Paper](link)
**Fecha**: 2024-02-27

Resumen detallado de 3-4 líneas explicando:
- Qué investigación presentan
- Por qué es importante
- Aplicaciones potenciales

**Link**: [Ver publicación](URL)

---

## 📚 Documentación

### Actualizaciones en Claude Docs

#### [Título del Cambio](link)
**Tipo**: Nueva funcionalidad | Mejora | Fix

Descripción detallada del cambio:
- Qué cambió exactamente
- Cómo afecta a los usuarios
- Ejemplo de uso si aplica

**Utilidad**: Alta/Media/Baja - Explicar por qué

---

## 💻 GitHub Repositories

### `repo-name-1`
**Cambio**: [Commit message o descripción](link-to-commit)

Detalles del cambio:
- Qué funcionalidad añade/modifica
- Por qué es útil para desarrolladores
- Breaking changes si los hay

**Utilidad**: ⭐⭐⭐⭐⭐ (5/5) - Explicación

### `repo-name-2`
**Cambio**: [Release vX.Y.Z](link-to-release)

Novedades en esta versión:
- Feature 1: Descripción
- Feature 2: Descripción

**Utilidad**: ⭐⭐⭐ (3/5) - Explicación

---

## 📊 Resumen del Día

- **Research**: X nuevos papers
- **Docs**: X actualizaciones  
- **GitHub**: X repos con actividad

## 🔗 Links Rápidos

- [Anthropic Research](https://www.anthropic.com/research)
- [Claude Docs](https://docs.anthropic.com)
- [Anthropic GitHub](https://github.com/anthropics)
```

### Proceso Diario (GitHub Actions)

1. **Trigger**: Cron schedule (cada día a las 9 AM UTC)
2. **Checkout**: Clonar repo
3. **Setup**: Instalar dependencias Python
4. **Scrape**:
   - Research: requests + BeautifulSoup
   - Docs: requests + BeautifulSoup (o API si disponible)
   - GitHub: PyGithub o requests a API
5. **Generate**: Crear markdown con formato especificado
6. **Commit**: Hacer commit con `[BOT] Daily update - YYYY-MM-DD`
7. **Push**: Subir cambios

### Consideraciones Técnicas

#### Rate Limiting
- GitHub API: 5000 requests/hora con token
- Anthropic web: Respetar robots.txt, delays entre requests
- Implementar retries con backoff

#### Manejo de Errores
- Si un source falla, continuar con los demás
- Loggear errores en el markdown (sección de errores)
- Notificar si fallan todos los sources

#### Storage
- Mantener histórico: todos los archivos en `daily/`
- Index: Crear `README.md` con índice de todos los días
- No borrar archivos antiguos

### Prompt para Claude

Cuando ejecutes este workflow, Claude debe:

1. Leer las 3 fuentes (research, docs, github)
2. Analizar qué es realmente importante vs ruido
3. Escribir resúmenes en ESPAÑOL (el usuario lo pidió en español)
4. Ser crítico: no todo cambio es importante, filtrar
5. Enfatizar utilidad práctica para desarrolladores
6. Incluir ejemplos de código cuando sea relevante

### Ejemplo de Utilidad

En lugar de:
> "Se actualizó el README"

Escribir:
> "Se actualizó el README con nuevos ejemplos de uso de la API de Claude. **Utilidad**: Media - Ayuda a nuevos desarrolladores a entender mejor la autenticación, aunque no hay cambios funcionales."

### Archivos a Crear

- `CLAUDE.md` - Este archivo (instrucciones)
- `CONTEXT.md` - Contexto y setup del proyecto
- `scraper.py` - Script principal de scraping
- `.github/workflows/daily.yml` - Workflow de GitHub Actions
- `README.md` - Documentación pública
- `daily/` - Carpeta con archivos diarios (generada automáticamente)
