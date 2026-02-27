# Anthropic Daily Resume

📰 Resumen diario automatizado de actualizaciones de Anthropic: Research, Documentación y GitHub.

## 🎯 Qué incluye cada día

- **🔬 Research**: Nuevos papers y publicaciones de anthropic.com/research
- **📚 Docs**: Cambios en documentación de docs.anthropic.com
- **💻 GitHub**: Actividad en repos de github.com/anthropics

## 📅 Histórico

| Fecha | Research | Docs | GitHub | Resumen |
|-------|----------|------|--------|---------|
| 2026-02-27 | [Research](./daily/research/2026-02-27.md) | [Docs](./daily/docs/2026-02-27.md) | [GitHub](./daily/github/2026-02-27.md) | [Resumen](./daily/2026-02-27.md) |

## 🚀 Cómo funciona

1. **GitHub Actions** ejecuta el scraper cada día a las 9 AM UTC
2. El bot obtiene datos de 3 fuentes:
   - Web scraping de Anthropic Research
   - Web scraping de Anthropic Docs  
   - GitHub API para repos de `anthropics`
3. Genera archivo Markdown con resumen en español
4. Hace commit automático al repo

## 📁 Estructura

```
anthropic-resume-day-to-day/
├── daily/                    # Resúmenes diarios generados
│   ├── 2024-02-27.md
│   ├── 2024-02-28.md
│   └── ...
├── src/
│   └── scraper.py           # Script principal
├── .github/workflows/
│   └── daily.yml            # Workflow de GitHub Actions
├── requirements.txt         # Dependencias Python
├── CLAUDE.md                # Instrucciones para Claude
└── CONTEXT.md               # Contexto técnico
```

## 🛠️ Tecnologías

- **Python 3.11**
- **BeautifulSoup4** - Web scraping
- **PyGithub** - GitHub API
- **GitHub Actions** - Automatización

## 🔗 Fuentes consultadas

- [Anthropic Research](https://www.anthropic.com/research)
- [Claude Documentation](https://docs.anthropic.com)
- [Anthropic GitHub](https://github.com/anthropics)

## 🌐 Idiomas

- 🇬🇧 [English](README.md) (Default)
- 🇪🇸 [Español](README.es.md)

## ⚠️ Notas

- Los resúmenes se generan automáticamente, pueden contener errores
- El scraping depende de la estructura actual de las webs (puede romperse)
- GitHub API requiere token para acceso sin rate limits

## 📄 Licencia

MIT - Libre uso y modificación.
