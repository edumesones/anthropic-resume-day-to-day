# Anthropic Daily Resume

📰 Resumen diario automatizado de actualizaciones de Anthropic: Research y GitHub.

## 🎯 Qué incluye cada día

- **🔬 Research**: Nuevos papers y publicaciones de anthropic.com/research
- **💻 GitHub**: Actividad en repos de github.com/anthropics (incluye changelog de claude-code)

## 📅 Histórico

| Fecha | Research | GitHub | Resumen |
|-------|----------|--------|---------|
| 2026-02-27 | [Research](./daily/research/2026-02-27.md) | [GitHub](./daily/github/2026-02-27.md) | [Resumen](./daily/2026-02-27.md) |

## 🚀 Cómo funciona

1. **GitHub Actions** ejecuta el scraper cada día a las 9 AM UTC
2. El bot obtiene datos de 2 fuentes:
   - Web scraping de Anthropic Research
   - GitHub API para repos de `anthropics` (incluye changelog de claude-code)
3. Genera archivo Markdown con resumen en español
4. Hace commit automático al repo

## 📁 Estructura

```
anthropic-resume-day-to-day/
├── daily/                    # Resúmenes diarios generados
│   ├── research/            # Papers de investigación
│   ├── github/              # Actividad en repos
│   └── YYYY-MM-DD.md        # Resumen del día
├── src/
│   └── scraper.py           # Script principal
├── .github/workflows/
│   └── daily.yml            # Workflow de GitHub Actions
├── requirements.txt         # Dependencias Python
└── README.md                # Documentación
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
