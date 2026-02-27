# CONTEXT.md

## Contexto del Proyecto

### Nombre
**anthropic-resume-day-to-day**

### Propósito
Bot automatizado que genera resúmenes diarios de actualizaciones de Anthropic:
- Research papers
- Documentación de Claude
- Repositorios GitHub

### Ejecución
- **Frecuencia**: Cada 24 horas
- **Método**: GitHub Actions (cron schedule)
- **Hora**: 9:00 AM UTC (ajustable)

### Estructura del Repositorio

```
anthropic-resume-day-to-day/
├── .github/
│   └── workflows/
│       └── daily.yml          # Workflow de GitHub Actions
├── daily/                      # Resúmenes generados (auto)
│   ├── 2024-02-27.md
│   ├── 2024-02-28.md
│   └── ...
├── src/
│   ├── __init__.py
│   ├── scraper.py             # Lógica principal de scraping
│   ├── github_client.py       # Cliente GitHub API
│   └── utils.py               # Utilidades (fechas, markdown, etc.)
├── requirements.txt           # Dependencias Python
├── CLAUDE.md                  # Instrucciones para Claude
├── CONTEXT.md                 # Este archivo
└── README.md                  # Documentación pública
```

### Fuentes de Datos

#### 1. Anthropic Research
- **URL**: https://www.anthropic.com/research
- **Método**: Web scraping (requests + BeautifulSoup)
- **Selectores esperados**:
  - Papers: `.research-item`, `.publication-card`, o similar
  - Título: `h2`, `h3`, o clase específica
  - Descripción: `p` o `.description`
  - Fecha: `.date` o similar
- **Nota**: Revisar estructura HTML actual al implementar

#### 2. Anthropic Docs
- **URL principal**: https://docs.anthropic.com/en/api/changelog
- **Alternativa**: https://docs.anthropic.com/en/release-notes
- **Método**: Web scraping o API si disponible
- **Nota**: Los docs pueden estar en GitHub (docs repo), verificar

#### 3. GitHub - Organización Anthropic
- **Org**: `anthropics`
- **API**: GitHub REST API v3
- **Endpoint**: `https://api.github.com/orgs/anthropics/repos`
- **Datos por repo**:
  - `updated_at` para detectar actividad reciente
  - `/commits` para commits recientes
  - `/releases` para nuevas versiones
  - `/events` para actividad general

### Dependencias

```txt
requests>=2.31.0
beautifulsoup4>=4.12.0
PyGithub>=2.1.0
python-dateutil>=2.8.0
pytz>=2023.0
```

### Variables de Entorno (GitHub Secrets)

| Variable | Descripción | Requerida |
|----------|-------------|-----------|
| `GITHUB_TOKEN` | Token de GitHub para API | Sí |
| `ANTHROPIC_API_KEY` | Si usamos API Anthropic (opcional) | No |

### Lógica del Scraper

```python
# Pseudocódigo

def main():
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    
    # 1. Scrapear Research
    research = scrape_anthropic_research()
    
    # 2. Scrapear Docs
    docs = scrape_anthropic_docs()
    
    # 3. Obtener GitHub updates
    github_updates = get_github_updates(org="anthropics")
    
    # 4. Generar markdown
    markdown = generate_daily_markdown(
        date=fecha_hoy,
        research=research,
        docs=docs,
        github=github_updates
    )
    
    # 5. Guardar archivo
    save_to_daily_folder(markdown, fecha_hoy)
    
    # 6. Actualizar índice
    update_readme_index()

if __name__ == "__main__":
    main()
```

### Formato de Salida

Cada archivo `daily/YYYY-MM-DD.md` debe incluir:

1. **Header** con fecha
2. **Research** sección con papers del día
3. **Docs** sección con cambios en documentación
4. **GitHub** sección con repos actualizados
5. **Resumen** estadístico
6. **Links rápidos**

### GitHub Actions Workflow

```yaml
name: Daily Anthropic Resume

on:
  schedule:
    - cron: '0 9 * * *'  # 9 AM UTC todos los días
  workflow_dispatch:  # Permitir ejecución manual

jobs:
  generate-resume:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run scraper
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: python src/scraper.py
      
      - name: Commit and push
        run: |
          git config --local user.email "bot@github.com"
          git config --local user.name "Daily Bot"
          git add daily/
          git commit -m "[BOT] Daily update - $(date +%Y-%m-%d)" || echo "No changes"
          git push
```

### Consideraciones de Diseño

#### Idempotencia
- Si se ejecuta 2 veces el mismo día, no duplicar contenido
- Verificar si archivo ya existe antes de crear
- Actualizar en lugar de sobrescribir si es necesario

#### Manejo de Errores
```python
try:
    research = scrape_research()
except Exception as e:
    research = [{
        "error": True,
        "message": f"No se pudo obtener research: {e}"
    }]
```

#### Rate Limiting
- GitHub API: Usar autenticación para 5000 req/hora
- Anthropic web: Agregar delays de 1-2 segundos entre requests
- Implementar retry con backoff exponencial

### Mantenimiento

#### Si Anthropic cambia su web
1. Revisar selectores CSS
2. Actualizar `scraper.py`
3. Commit con fix

#### Si GitHub API cambia
1. Actualizar `github_client.py`
2. Verificar nuevos endpoints

#### Si hay fallos recurrentes
1. Revisar logs en GitHub Actions
2. Añadir más manejo de errores
3. Considerar fallback sources

### Roadmap Futuro (Opcional)

- [ ] RSS feeds como fuente alternativa
- [ ] Notificaciones (email/Discord/Slack)
- [ ] Análisis de tendencias semanales
- [ ] Comparativa día vs día anterior
- [ ] Resumen semanal automático
- [ ] API propia para consultar histórico

### Notas para Implementación

1. Empezar con GitHub (más estable, API documentada)
2. Luego Research (scraping simple)
3. Docs puede ser más complejo, dejar para el final
4. Probar localmente antes de push
5. Hacer prueba manual del workflow antes de dejarlo en cron
